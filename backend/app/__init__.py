"""AquaWatch Flask backend application factory."""
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
migrate = Migrate()


def create_app(config: dict | None = None) -> Flask:
    frontend_dist = os.getenv("FRONTEND_DIST_DIR")
    app = Flask(
        __name__,
        static_folder=frontend_dist if frontend_dist else None,
        static_url_path="",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "postgresql://aw_user:aw_pass@db/aquawatch"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 8 * 60 * 60  # 8 hours
    app.config["THUMBNAIL_DIR"] = os.getenv("THUMBNAIL_DIR", "/var/aquawatch/thumbnails")
    app.config["MQTT_BROKER"] = os.getenv("MQTT_BROKER", "mosquitto")
    app.config["MQTT_PORT"] = int(os.getenv("MQTT_PORT", "1883"))

    if config:
        app.config.update(config)

    os.makedirs(app.config["THUMBNAIL_DIR"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    from app.routes.alerts import bp as alerts_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.cameras import bp as cameras_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(cameras_bp, url_prefix="/api/cameras")

    if frontend_dist:
        @app.get("/")
        def frontend_index():
            return app.send_static_file("index.html")

        @app.errorhandler(404)
        def frontend_fallback(error):
            if not request_path_is_api():
                return app.send_static_file("index.html")
            return {"error": "not found"}, 404

    # Register socket events
    from app import socket_events  # noqa: F401

    # Start MQTT subscriber in background
    if not app.config.get("TESTING"):
        from app.mqtt_handler import start_mqtt_client
        start_mqtt_client(app)

    return app


def request_path_is_api() -> bool:
    from flask import request

    return request.path.startswith("/api/")
