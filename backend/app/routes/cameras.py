"""Camera CRUD + zone/threshold configuration."""
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Camera, Alert

bp = Blueprint("cameras", __name__)


@bp.get("")
@jwt_required()
def list_cameras():
    cams = []

    for c in Camera.query.all():
        data = c.to_dict()

        data["active_alerts"] = Alert.query.filter_by(
            camera_id=c.id,
            status="active"
        ).count()

        cams.append(data)

    return jsonify(cams)


@bp.post("")
@jwt_required()
def create_camera():
    data = request.get_json() or {}
    if not data.get("id"):
        return jsonify({"error": "id is required"}), 400
    if Camera.query.get(data["id"]):
        return jsonify({"error": "camera already exists"}), 409
    threshold = data.get("disappear_threshold", 15)
    try:
        threshold = int(threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "disappear_threshold must be an integer"}), 400
    if threshold < 1:
        return jsonify({"error": "disappear_threshold must be positive"}), 400
    cam = Camera(
        id=data["id"],
        location_name=data.get("location_name"),
        lat=data.get("lat"),
        lng=data.get("lng"),
        zone_polygon=data.get("zone_polygon"),
        disappear_threshold=threshold,
    )
    db.session.add(cam)
    db.session.commit()
    return jsonify(cam.to_dict()), 201


@bp.get("/<camera_id>")
@jwt_required()
def get_camera(camera_id: str):
    cam = db.session.get(Camera, camera_id)
    return jsonify(cam.to_dict())


@bp.put("/<camera_id>/config")
@jwt_required()
def update_config(camera_id: str):
    """Update zone_polygon and/or disappear_threshold."""
    cam = Camera.query.get_or_404(camera_id)
    data = request.get_json() or {}
    if "zone_polygon" in data:
        cam.zone_polygon = data["zone_polygon"]
    if "disappear_threshold" in data:
        try:
            threshold = int(data["disappear_threshold"])
        except (TypeError, ValueError):
            return jsonify({"error": "disappear_threshold must be an integer"}), 400
        if threshold < 1:
            return jsonify({"error": "disappear_threshold must be positive"}), 400
        cam.disappear_threshold = threshold
    if "location_name" in data:
        cam.location_name = data["location_name"]
    if "is_active" in data:
        cam.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify(cam.to_dict())


@bp.get("/status")
@jwt_required()
def camera_status():
    return jsonify([
        {
            "id": c.id,
            "online": c._is_online(),
            "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
        }
        for c in Camera.query.order_by(Camera.id).all()
    ])
