"""Backend API, MQTT, database, and edge logic tests."""
import json
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path

import pytest
from flask_jwt_extended import create_access_token

from app import create_app, db
from app.models import User, Camera, Alert
from app.mqtt_handler import handle_mqtt_message

sys.path.append(str(Path(__file__).resolve().parents[2] / "edge"))
from drowning_logic import DrowningState  # type: ignore


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test",
        "THUMBNAIL_DIR": "/private/tmp/aquawatch-test-thumbnails",
    })
    with app.app_context():
        db.create_all()
        u = User(username="lg1", role="lifeguard")
        u.set_password("pw")
        db.session.add(u)
        db.session.add(Camera(id="cam_01", location_name="Pantai A"))
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def _token(client):
    r = client.post("/api/auth/login", json={"username": "lg1", "password": "pw"})
    return r.get_json()["access_token"]


def test_login_and_list(client, app):
    token = _token(client)
    with app.app_context():
        db.session.add(Alert(camera_id="cam_01", track_id=7, disappear_duration_seconds=16.3))
        db.session.commit()
    r = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_resolve_alert(client, app):
    token = _token(client)
    with app.app_context():
        a = Alert(camera_id="cam_01", track_id=1)
        db.session.add(a)
        db.session.commit()
        aid = a.id
    r = client.patch(
        f"/api/alerts/{aid}",
        json={"status": "resolved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.get_json()["status"] == "resolved"


def test_auth_missing_invalid_and_expired(client, app):
    assert client.get("/api/alerts").status_code == 401
    assert client.get("/api/alerts", headers={"Authorization": "Bearer nope"}).status_code == 422

    with app.app_context():
        expired = create_access_token(identity="lg1", expires_delta=timedelta(seconds=-1))
    r = client.get("/api/alerts", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_alert_filters_and_validation(client, app):
    token = _token(client)
    now = datetime.now(UTC)
    with app.app_context():
        db.session.add_all(
            [
                Alert(camera_id="cam_01", track_id=1, status="active", triggered_at=now),
                Alert(camera_id="cam_02", track_id=2, status="resolved", triggered_at=now - timedelta(days=2)),
            ]
        )
        db.session.add(Camera(id="cam_02", location_name="Pantai B"))
        db.session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/alerts?camera_id=cam_01&status=active&limit=10", headers=headers)
    assert r.status_code == 200
    rows = r.get_json()
    assert len(rows) == 1
    assert rows[0]["camera_id"] == "cam_01"

    assert client.get("/api/alerts?status=bad", headers=headers).status_code == 400
    assert client.get("/api/alerts?limit=0", headers=headers).status_code == 400
    assert client.get("/api/alerts?from=not-a-date", headers=headers).status_code == 400
    assert client.get("/api/alerts/999", headers=headers).status_code == 404


def test_patch_false_alarm(client, app):
    token = _token(client)
    with app.app_context():
        a = Alert(camera_id="cam_01", track_id=3)
        db.session.add(a)
        db.session.commit()
        aid = a.id
    r = client.patch(
        f"/api/alerts/{aid}",
        json={"status": "false_alarm"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "false_alarm"
    assert data["resolved_by"] == "lg1"


def test_camera_validation_and_heartbeat_status(client, app):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/cameras", json={}, headers=headers).status_code == 400
    assert client.post("/api/cameras", json={"id": "cam_01"}, headers=headers).status_code == 409
    assert client.put("/api/cameras/cam_01/config", json={"disappear_threshold": 0}, headers=headers).status_code == 400

    handle_mqtt_message(app, "aquawatch/cam_new/heartbeat", b"{}")
    r = client.get("/api/cameras/status", headers=headers)
    assert r.status_code == 200
    assert any(row["id"] == "cam_new" and row["online"] for row in r.get_json())


def test_mqtt_alert_persist_malformed_and_auto_cancel(app):
    payload = {
        "track_id": 42,
        "last_position": {"x": 11, "y": 22},
        "disappear_duration_seconds": 16.5,
    }
    assert handle_mqtt_message(app, "aquawatch/cam_01/alert", json.dumps(payload).encode())
    with app.app_context():
        alert = Alert.query.filter_by(camera_id="cam_01", track_id=42).first()
        assert alert is not None
        assert alert.status == "active"
        assert alert.last_position_x == 11
        assert alert.disappear_duration_seconds == 16.5

    with pytest.raises(json.JSONDecodeError):
        handle_mqtt_message(app, "aquawatch/cam_01/alert", b"{bad json")

    cancel = {"event": "cancel", "track_id": 42}
    assert handle_mqtt_message(app, "aquawatch/cam_01/alert", json.dumps(cancel).encode())
    with app.app_context():
        alert = Alert.query.filter_by(camera_id="cam_01", track_id=42).first()
        assert alert.status == "resolved"
        assert alert.resolved_by == "edge-auto-cancel"


def test_alert_history_query_1000_rows(client, app):
    token = _token(client)
    with app.app_context():
        now = datetime.now(UTC)
        db.session.add_all(
            Alert(camera_id="cam_01", track_id=i, status="active", triggered_at=now - timedelta(seconds=i))
            for i in range(1005)
        )
        db.session.commit()

    r = client.get(
        "/api/alerts?camera_id=cam_01&status=active&limit=1000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    rows = r.get_json()
    assert len(rows) == 1000
    assert rows[0]["track_id"] == 0


def test_drowning_logic_t01_to_t05():
    state = DrowningState(threshold_seconds=10)

    state.seen(1, (100, 100), now=0)
    assert state.due_alerts(now=10)[0]["track_id"] == 1  # T01

    state.seen(2, (10, 10), now=0)
    state.left_zone(2)
    assert state.due_alerts(now=20) == []  # T02

    state.seen(3, (20, 20), now=0)
    state.seen(3, (21, 21), now=9)
    assert state.due_alerts(now=10) == []  # T03 threshold reset

    state.seen(4, (40, 40), now=0)
    state.seen(5, (50, 50), now=0)
    alerts = state.due_alerts(now=11)
    assert {a["track_id"] for a in alerts} == {4, 5}  # T04

    assert state.seen(4, (41, 41), now=12)["event"] == "cancel"  # T05
