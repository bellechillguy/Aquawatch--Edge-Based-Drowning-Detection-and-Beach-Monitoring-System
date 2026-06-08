"""MQTT subscriber: consume alerts/heartbeats from edge devices."""
import base64
import json
import os
import threading
from datetime import datetime, UTC
from pathlib import Path

import paho.mqtt.client as mqtt
from flask import Flask

from app import db, socketio
from app.models import Alert, Camera


def _resolve_existing_alert(app: Flask, camera_id: str, payload: dict) -> bool:
    track_id = payload.get("track_id")
    if track_id is None:
        return False
    alert = (
        Alert.query.filter_by(camera_id=camera_id, track_id=track_id, status="active")
        .order_by(Alert.triggered_at.desc())
        .first()
    )
    if not alert:
        return False
    alert.status = "resolved"
    alert.resolved_at = datetime.now(UTC)
    alert.resolved_by = "edge-auto-cancel"
    db.session.commit()
    socketio.emit("alert_updated", alert.to_dict())
    app.logger.info("Alert auto-cancelled id=%s camera=%s track=%s", alert.id, camera_id, track_id)
    return True


def _on_alert(app: Flask, camera_id: str, payload: dict) -> None:
    with app.app_context():
        if payload.get("event") == "cancel":
            _resolve_existing_alert(app, camera_id, payload)
            return

        # Decode + persist thumbnail
        thumb_path = None
        thumb_b64 = payload.get("thumbnail_base64")
        if thumb_b64:
            try:
                data = base64.b64decode(thumb_b64)
                fname = f"{camera_id}_{int(datetime.now(UTC).timestamp())}.jpg"
                full = Path(app.config["THUMBNAIL_DIR"]) / fname
                full.write_bytes(data)
                thumb_path = str(full)
            except Exception as exc:  # noqa: BLE001
                app.logger.warning("Failed to decode thumbnail: %s", exc)

        last_pos = payload.get("last_position") or {}
        alert = Alert(
            camera_id=camera_id,
            track_id=payload.get("track_id"),
            triggered_at=datetime.now(UTC),
            status="active",
            last_position_x=last_pos.get("x"),
            last_position_y=last_pos.get("y"),
            disappear_duration_seconds=payload.get("disappear_duration_seconds"),
            thumbnail_path=thumb_path,
        )
        db.session.add(alert)
        db.session.commit()
        socketio.emit("new_alert", alert.to_dict())
        app.logger.info("New alert persisted id=%s camera=%s", alert.id, camera_id)


def _on_heartbeat(app: Flask, camera_id: str) -> None:
    with app.app_context():
        db.session.get(Camera, id)
        if not cam:
            cam = Camera(id=camera_id)
            db.session.add(cam)
        cam.last_heartbeat = datetime.now(UTC)
        db.session.commit()


def handle_mqtt_message(app: Flask, topic: str, payload_bytes: bytes) -> bool:
    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != "aquawatch":
        return False
    _, camera_id, kind = parts
    if kind == "alert":
        payload = json.loads(payload_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("alert payload must be a JSON object")
        _on_alert(app, camera_id, payload)
        return True
    if kind == "heartbeat":
        _on_heartbeat(app, camera_id)
        return True
    return False


def start_mqtt_client(app: Flask) -> mqtt.Client:
    client = mqtt.Client(client_id=f"aquawatch-backend-{os.getpid()}")

    def on_connect(c, userdata, flags, rc):
        app.logger.info("MQTT connected rc=%s", rc)
        c.subscribe("aquawatch/+/alert")
        c.subscribe("aquawatch/+/heartbeat")

    def on_message(c, userdata, msg):
        try:
            handle_mqtt_message(app, msg.topic, msg.payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            app.logger.warning("Ignoring invalid MQTT payload on %s: %s", msg.topic, exc)
        except Exception as exc:  # noqa: BLE001
            app.logger.exception("MQTT handler error: %s", exc)

    client.on_connect = on_connect
    client.on_message = on_message

    def _run():
        try:
            client.connect(app.config["MQTT_BROKER"], app.config["MQTT_PORT"], 60)
            client.loop_forever()
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("MQTT loop stopped: %s", exc)

    threading.Thread(target=_run, daemon=True).start()
    return client
