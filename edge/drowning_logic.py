"""Unit-testable drowning alert state machine."""


class DrowningState:
    def __init__(self, threshold_seconds: float):
        self.threshold_seconds = threshold_seconds
        self.last_seen: dict[int, float] = {}
        self.last_position: dict[int, tuple[int, int]] = {}
        self.alerted: set[int] = set()

    def seen(self, track_id: int, position: tuple[int, int], now: float) -> dict | None:
        event = None
        if track_id in self.alerted:
            self.alerted.remove(track_id)
            event = {"event": "cancel", "track_id": track_id, "position": position}
        self.last_seen[track_id] = now
        self.last_position[track_id] = position
        return event

    def left_zone(self, track_id: int) -> None:
        self.last_seen.pop(track_id, None)
        self.last_position.pop(track_id, None)
        self.alerted.discard(track_id)

    def due_alerts(self, now: float) -> list[dict]:
        alerts = []
        for track_id, last_seen in list(self.last_seen.items()):
            if track_id in self.alerted:
                continue
            duration = now - last_seen
            if duration >= self.threshold_seconds:
                self.alerted.add(track_id)
                alerts.append(
                    {
                        "event": "alert",
                        "track_id": track_id,
                        "position": self.last_position.get(track_id, (0, 0)),
                        "duration": duration,
                    }
                )
        return alerts
