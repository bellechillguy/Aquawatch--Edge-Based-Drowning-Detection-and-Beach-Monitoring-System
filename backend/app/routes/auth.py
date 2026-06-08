"""Authentication endpoints (JWT, 8h expiry)."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(
        identity=user.username,
        additional_claims={"role": user.role, "id": user.id},
    )
    return jsonify({"access_token": token, "user": user.to_dict()})


@bp.post("/register")
def register():
    """Admin-only registration helper (open in dev)."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "lifeguard")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@bp.get("/me")
@jwt_required()
def me():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user.to_dict())
