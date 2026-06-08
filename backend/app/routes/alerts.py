"""Alert endpoints: list, filter, resolve / mark false alarm."""
from datetime import datetime, UTC
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models import Alert

bp = Blueprint("alerts", __name__)
VALID_STATUSES = {"active", "resolved", "false_alarm"}


def _parse_iso_datetime(value: str, field: str):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be an ISO-8601 datetime") from None


@bp.get("")
@jwt_required()
def list_alerts():
    q = Alert.query
    camera_id = request.args.get("camera_id")
    status = request.args.get("status")
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    if limit < 1 or limit > 1000:
        return jsonify({"error": "limit must be between 1 and 1000"}), 400

    if camera_id:
        q = q.filter(Alert.camera_id == camera_id)
    if status:
        if status not in VALID_STATUSES:
            return jsonify({"error": "invalid status"}), 400
        q = q.filter(Alert.status == status)
    try:
        if date_from:
            q = q.filter(Alert.triggered_at >= _parse_iso_datetime(date_from, "from"))
        if date_to:
            q = q.filter(Alert.triggered_at <= _parse_iso_datetime(date_to, "to"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    rows = q.order_by(Alert.triggered_at.desc()).limit(limit).all()
    return jsonify([a.to_dict() for a in rows])


@bp.get("/<int:alert_id>")
@jwt_required()
def get_alert(alert_id: int):
    alert = db.session.get(Alert, alert_id)

    if alert is None:
        abort(404)

    return jsonify(alert.to_dict())

@bp.patch("/<int:alert_id>")
@jwt_required()
def update_alert(alert_id: int):
    """Set status to 'resolved' or 'false_alarm'."""
    alert = Alert.query.get_or_404(alert_id)
    
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in {"resolved", "false_alarm"}:
        return jsonify({"error": "status must be 'resolved' or 'false_alarm'"}), 400

    alert.status = new_status
    alert.resolved_at = datetime.now(UTC)
    alert.resolved_by = get_jwt_identity()
    db.session.commit()

    socketio.emit("alert_updated", alert.to_dict())
    return jsonify(alert.to_dict())
