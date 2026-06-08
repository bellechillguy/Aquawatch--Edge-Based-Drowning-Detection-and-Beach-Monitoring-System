"""AquaWatch edge runtime — runs on Raspberry Pi.

Pipeline per spec 6a:
  Video Capture -> Preprocess -> YOLOv8 -> DeepSORT ->
  Zone Classifier -> Drowning Logic Engine -> (MQTT + GPIO buzzer/LED)
"""
import base64
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import cv2
import numpy as np
import paho.mqtt.client as mqtt
import torch

# Monkey patch torch.load for PyTorch 2.6+ compatibility with YOLOv8 weights loading
_orig_load = torch.load
def _patched_load(*args, **kwargs):
    if "weights_only" not in kwargs:
        kwargs["weights_only"] = False
    return _orig_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

try:  # GPIO available only on Raspberry Pi
    import RPi.GPIO as GPIO  # type: ignore
    HAS_GPIO = True
except (ImportError, RuntimeError):  # pragma: no cover - dev machine
    HAS_GPIO = False

from config import CONFIG
from drowning_logic import DrowningState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aquawatch.edge")


# ---------- GPIO ---------------------------------------------------------- #
def gpio_init():
    if not HAS_GPIO:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CONFIG["BUZZER_PIN"], GPIO.OUT)
    GPIO.setup(CONFIG["LED_PIN"], GPIO.OUT)
    GPIO.output(CONFIG["BUZZER_PIN"], GPIO.LOW)
    GPIO.output(CONFIG["LED_PIN"], GPIO.LOW)


def gpio_alert(on: bool) -> None:
    if not HAS_GPIO:
        log.info("[GPIO MOCK] buzzer/LED -> %s", on)
        return
    GPIO.output(CONFIG["BUZZER_PIN"], GPIO.HIGH if on else GPIO.LOW)
    GPIO.output(CONFIG["LED_PIN"], GPIO.HIGH if on else GPIO.LOW)


# ---------- Zone Classifier ----------------------------------------------- #
def in_polygon(point, polygon) -> bool:
    if not polygon:
        return False
    contour = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(contour, point, False) >= 0


# ---------- MQTT ---------------------------------------------------------- #
def build_mqtt_client():
    try:
        client = mqtt.Client(client_id=f"edge-{CONFIG['CAMERA_ID']}")
        client.connect(CONFIG["MQTT_BROKER"], CONFIG["MQTT_PORT"], 60)
        client.loop_start()
        log.info("Connected to MQTT broker")
        return client
    except Exception as e:
        log.warning("MQTT disabled: %s", e)
        return None

def publish_alert(client, track_id: int, position, duration: float, frame) -> None:
    if client is None:
        log.warning(
            "[LOCAL ALERT] track=%s duration=%.1fs",
            track_id,
            duration,
        )
        return

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    thumb = base64.b64encode(buf.tobytes()).decode("ascii") if ok else ""

    payload = {
        "camera_id": CONFIG["CAMERA_ID"],
        "track_id": int(track_id),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_position": {"x": int(position[0]), "y": int(position[1])},
        "disappear_duration_seconds": round(duration, 2),
        "thumbnail_base64": thumb,
    }

    topic = f"aquawatch/{CONFIG['CAMERA_ID']}/alert"
    client.publish(topic, json.dumps(payload), qos=1)

    log.warning(
        "Alert published track_id=%s duration=%.1fs",
        track_id,
        duration,
    )


def publish_cancel(client, track_id: int, position) -> None:
    if client is None:
        return

    payload = {
        "event": "cancel",
        "camera_id": CONFIG["CAMERA_ID"],
        "track_id": int(track_id),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_position": {"x": int(position[0]), "y": int(position[1])},
    }

    topic = f"aquawatch/{CONFIG['CAMERA_ID']}/alert"
    client.publish(topic, json.dumps(payload), qos=1)

    log.info("Alert cancel published track_id=%s", track_id)


def heartbeat_loop(client) -> None:
    if client is None:
        return

    topic = f"aquawatch/{CONFIG['CAMERA_ID']}/heartbeat"

    while True:
        client.publish(topic, json.dumps({"ts": time.time()}))
        time.sleep(30)


# ---------- Drowning Logic Engine ----------------------------------------- #
class DrowningEngine:
    """Watch tracks inside the danger zone and emit alerts when they vanish.

    Logic per spec section 6c:
      - Record (last_seen, last_position) for every track inside the zone.
      - In a background thread, every 1s check: if `now - last_seen` exceeds
        the disappear threshold AND the last position is not near zone edge,
        raise an alert. Auto-cancel if the track reappears before the
        lifeguard acknowledges.
    """

    def __init__(self, mqtt_client: mqtt.Client):
        self.state = DrowningState(CONFIG["DISAPPEAR_THRESHOLD_SECONDS"])
        self.last_frame = None
        self.lock = threading.Lock()
        self.mqtt = mqtt_client
        threading.Thread(target=self._loop, daemon=True).start()

    def update(self, track_id: int, position, frame) -> None:
        with self.lock:
            event = self.state.seen(int(track_id), position, time.time())
            if event:
                log.info("Track %s reappeared -> auto-cancel alert", track_id)
                gpio_alert(False)
                publish_cancel(self.mqtt, track_id, position)
            self.last_frame = frame

    def _loop(self) -> None:
        while True:
            time.sleep(1)
            now = time.time()
            with self.lock:
                for event in self.state.due_alerts(now):
                    gpio_alert(True)
                    if self.last_frame is not None:
                        publish_alert(
                            self.mqtt,
                            event["track_id"],
                            event["position"],
                            event["duration"],
                            self.last_frame,
                        )


# ---------- Main loop ----------------------------------------------------- #
def main() -> None:
    gpio_init()
    log.info("Loading YOLOv8 model from %s", CONFIG["MODEL_PATH"])
    model = YOLO(CONFIG["MODEL_PATH"])
    tracker = DeepSort(max_age=CONFIG["MAX_AGE_FRAMES"])

    mqtt_client = build_mqtt_client()

    if mqtt_client is not None:
        threading.Thread(
            target=heartbeat_loop,
            args=(mqtt_client,),
            daemon=True,
        ).start()

    engine = DrowningEngine(mqtt_client)
 
    cap = cv2.VideoCapture(CONFIG["CAMERA_URL"])

    log.info(
        "Opening video source: %s",
        CONFIG["CAMERA_URL"]
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open video source: {CONFIG['CAMERA_URL']}"
        )
    log.info("Video opened successfully")

    polygon = CONFIG["ZONE_POLYGON"]

    frame_count = 0
    start_time = time.time()

    while True:
        ok, frame = cap.read()

        if not ok:
            log.info("Video finished")
            break

        frame_count += 1

        resized = cv2.resize(frame, (640, 640))

        results = model(
            resized,
            conf=0.4,
            classes=[0],
            verbose=False,
        )

        detections = []

        if len(results) and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .tolist()
                )

                conf = float(box.conf[0])

                detections.append(
                    (
                        [x1, y1, x2 - x1, y2 - y1],
                        conf,
                        "person",
                    )
                )

        tracks = tracker.update_tracks(
            detections,
            frame=resized,
        )

        visible_outside_zone = set()

        for t in tracks:
            if not t.is_confirmed():
                continue

            l, top, r, b = map(int, t.to_ltrb())

            cx = int((l + r) / 2)
            cy = int((top + b) / 2)

            inside = in_polygon(
                (cx, cy),
                polygon,
            )

            color = (0, 255, 0) if inside else (0, 165, 255)

            cv2.rectangle(
                resized,
                (l, top),
                (r, b),
                color,
                2,
            )

            cv2.circle(
                resized,
                (cx, cy),
                4,
                color,
                -1,
            )

            cv2.putText(
                resized,
                f"ID {t.track_id}",
                (l, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

            if inside:
                engine.update(
                    t.track_id,
                    (cx, cy),
                    resized.copy(),
                )
            else:
                visible_outside_zone.add(
                    int(t.track_id)
                )

        with engine.lock:
            for track_id in visible_outside_zone:
                if track_id not in engine.state.alerted:
                    engine.state.left_zone(track_id)

        cv2.polylines(
            resized,
            [np.array(polygon, dtype=np.int32)],
            True,
            (0, 0, 255),
            2,
        )

        elapsed = max(
            time.time() - start_time,
            0.001,
        )

        fps = frame_count / elapsed

        cv2.putText(
            resized,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            resized,
            f"People: {len(detections)}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow(
            "AquaWatch Detection",
            resized,
        )

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        if HAS_GPIO:
            GPIO.cleanup()