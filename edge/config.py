"""Edge runtime configuration. Override via environment variables."""
import json
import os

CONFIG = {
    "CAMERA_ID": os.getenv("CAMERA_ID", "cam_01"),
    "CAMERA_URL": os.getenv("CAMERA_URL", "pool_test.mp4"),
    "MODEL_PATH": os.getenv("MODEL_PATH", "models/best.pt"),
    "MQTT_BROKER": os.getenv("MQTT_BROKER", "localhost"),
    "MQTT_PORT": int(os.getenv("MQTT_PORT", "1883")),
    "DISAPPEAR_THRESHOLD_SECONDS": int(os.getenv("DISAPPEAR_THRESHOLD", "15")),
    "MAX_AGE_FRAMES": int(os.getenv("MAX_AGE_FRAMES", "30")),
    "BUZZER_PIN": int(os.getenv("BUZZER_PIN", "18")),
    "LED_PIN": int(os.getenv("LED_PIN", "23")),
    # Polygon = list of [x, y] pixel pairs covering the danger zone (640x640 frame).
    "ZONE_POLYGON": json.loads(
        os.getenv("ZONE_POLYGON", "[[100,200],[540,200],[540,560],[100,560]]")
    ),
}
