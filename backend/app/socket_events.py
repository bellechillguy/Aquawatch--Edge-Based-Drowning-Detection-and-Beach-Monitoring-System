"""Socket.IO event handlers."""
from flask import current_app
from flask_socketio import emit
from app import socketio


@socketio.on("connect")
def on_connect():
    current_app.logger.info("Client connected to Socket.IO")
    emit("connected", {"message": "AquaWatch realtime channel ready"})


@socketio.on("disconnect")
def on_disconnect():
    current_app.logger.info("Client disconnected from Socket.IO")


@socketio.on("ping_server")
def on_ping():
    emit("pong_server", {"ok": True})
