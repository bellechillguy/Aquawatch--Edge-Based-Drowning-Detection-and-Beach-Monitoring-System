"""SQLAlchemy models matching the AquaWatch PostgreSQL schema."""
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON
from app import db


class Camera(db.Model):
    __tablename__ = "cameras"

    id = db.Column(db.String, primary_key=True)  # e.g. 'cam_01'
    location_name = db.Column(db.String)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    zone_polygon = db.Column(JSON)  # piksel zona bahaya
    disappear_threshold = db.Column(db.Integer, default=15)  # detik
    is_active = db.Column(db.Boolean, default=True)
    last_heartbeat = db.Column(db.DateTime)

    alerts = db.relationship("Alert", backref="camera", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_name": self.location_name,
            "lat": self.lat,
            "lng": self.lng,
            "zone_polygon": self.zone_polygon,
            "disappear_threshold": self.disappear_threshold,
            "is_active": self.is_active,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "online": self._is_online(),
        }
    
    
    def _is_online(self) -> bool:
        if not self.last_heartbeat:
            return False

        heartbeat = self.last_heartbeat

        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=UTC)

        return (datetime.now(UTC) - heartbeat).total_seconds() < 90


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String, db.ForeignKey("cameras.id"), index=True)
    track_id = db.Column(db.Integer)
    triggered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)
    status = db.Column(db.String, default="active")  # active | resolved | false_alarm
    resolved_by = db.Column(db.String)
    last_position_x = db.Column(db.Integer)
    last_position_y = db.Column(db.Integer)
    disappear_duration_seconds = db.Column(db.Float)
    thumbnail_path = db.Column(db.String)

    __table_args__ = (
        db.Index("idx_alerts_camera_status_triggered", "camera_id", "status", "triggered_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "track_id": self.track_id,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "status": self.status,
            "resolved_by": self.resolved_by,
            "last_position": {"x": self.last_position_x, "y": self.last_position_y},
            "disappear_duration_seconds": self.disappear_duration_seconds,
            "thumbnail_path": self.thumbnail_path,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default="lifeguard")  # lifeguard | admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
