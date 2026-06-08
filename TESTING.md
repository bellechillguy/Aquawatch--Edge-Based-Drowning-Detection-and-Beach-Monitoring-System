# AquaWatch Testing Matrix

## Automated tests in this workspace

Run:

```sh
cd backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run build
cd ..
docker compose config
docker build --target app -t aquawatch-app:test .
```

Covered by `backend/tests/test_alerts.py`:

- MQTT alert payload is persisted to DB with camera, track, position, duration, and active status.
- Malformed MQTT alert JSON raises a decode error in the unit hook; runtime subscriber catches it and logs a warning.
- Heartbeat creates/updates camera `last_heartbeat`; `/api/cameras/status` reports online/offline from timeout.
- REST auth rejects missing, invalid, and expired JWT.
- REST alert list filters by camera/status/date/limit and validates bad inputs.
- `PATCH /api/alerts/{id}` supports `resolved` and `false_alarm`.
- Alert query for 1,000+ rows returns bounded results using indexed columns.
- Drowning logic T01-T05:
  - T01 vanished track triggers alert after threshold.
  - T02 visible track leaving zone resets without alert.
  - T03 reappearing before threshold resets timer.
  - T04 two simultaneous vanished tracks produce two events.
  - T05 reappearing after alert emits auto-cancel.

Covered by frontend build:

- Dashboard, popup, history, camera views compile successfully.
- Socket reconnect path reloads alerts immediately after reconnect.
- Mobile CSS keeps tables scrollable and alert popup readable on small screens.

Covered by Docker verification:

- Root `Dockerfile` target `app` builds backend and frontend into one deployable image.
- Root `docker-compose.yml` validates DB, MQTT, app, and optional edge profile wiring.

## Field tests requiring Raspberry Pi, camera, model, or real video

Record the video clip, model version, camera ID, lighting condition, and measured value for every run.

### Edge - Model & Detection

- YOLOv8 accuracy in bright day, afternoon, and night IR: run the same labeled clip set through `edge/main.py`; calculate precision/recall per condition.
- Partial body detection: labeled clips for head-only, shoulder-only, and half-body; compare detected person boxes against labels.
- False positives: clips containing floats, beach balls, hats, large waves; report false positive count per minute.
- Raspberry Pi FPS without Coral and with Coral: run for 10 minutes per mode and log frames processed per second.
- Raspberry Pi CPU temperature stability: run inference for at least 1 hour and log `vcgencmd measure_temp` every minute.
- Camera reconnect: unplug/drop RTSP stream for 10 seconds; verify logs show reconnect and processing resumes.

### Edge - Tracking

- DeepSORT ID consistency: clip with a person exiting and re-entering frame; inspect whether `track_id` remains stable or a new ID is assigned.
- DeepSORT ID swap: clip with two people crossing closely; count ID swaps.

### Real-time & Performance

- Socket.IO alert popup latency: publish MQTT alert and measure from broker publish timestamp to dashboard popup; target <1 second.
- Audio notification: verify browser plays `/alert.mp3` when a new alert arrives. Browser autoplay settings may require one user interaction first.
- End-to-end latency: timestamp GPIO trigger, MQTT publish, backend persist, and popup render.
- 24-hour Raspberry Pi stability: run edge process for 24 hours and record RSS memory, CPU temperature, FPS, and reconnect events.
- Multi-camera: run two camera IDs simultaneously; verify alerts remain separated by `camera_id`.
- MQTT burst: publish 10 alert messages simultaneously and verify 10 DB rows and 10 dashboard events.
