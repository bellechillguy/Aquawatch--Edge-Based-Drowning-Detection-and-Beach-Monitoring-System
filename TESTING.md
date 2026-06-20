# AquaWatch Testing Matrix

## Automated tests in this workspace

Recommended local verification:

```sh
docker compose run --rm -v "$PWD:/repo" -w /repo/backend app python -m pytest tests
cd frontend && npm run build && cd ..
docker compose config
docker compose up --build -d app
```

Optional edge smoke test through Docker:

```sh
docker compose --profile edge up --build -d edge
docker compose logs --no-color --tail=120 edge
docker compose exec db psql -U aw_user -d aquawatch -c 'select id, location_name, last_heartbeat from cameras order by id;'
```

Expected edge smoke signals:

- Logs show `Loading YOLOv26 model`.
- Logs show `DeepSort Tracker initialised`.
- Logs show `Connected to MQTT broker`.
- Logs show `Opening video source: pool_test.mp4`.
- Logs show `Video opened successfully`.
- The `cameras` table receives or updates `cam_01.last_heartbeat`.

Optional direct edge inference smoke test outside Docker:

```sh
python3 -m venv .venv-edge
.venv-edge/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv-edge/bin/pip install -r edge/requirements.txt
.venv-edge/bin/python -c "from ultralytics import YOLO; import numpy as np; m=YOLO('yolo26n.pt'); m(np.zeros((640,640,3),dtype=np.uint8), conf=0.4, classes=[0], verbose=False)"
```

Covered by `backend/tests/test_alerts.py`:

- MQTT alert payload is persisted to DB with camera, track, position, duration, and active status.
- Malformed MQTT alert JSON raises a decode error in the unit hook; runtime subscriber catches it and logs a warning.
- Heartbeat creates/updates camera `last_heartbeat`; `/api/cameras/status` reports online/offline from timeout.
- REST auth rejects missing, invalid, and expired JWT.
- REST alert list filters by camera/status/date/limit and validates bad inputs.
- `PATCH /api/alerts/{id}` supports `resolved` and `false_alarm`.
- `GET /api/alerts/{id}/thumbnail` returns an authenticated JPEG preview when available.
- Missing camera detail requests return `404` instead of `500`.
- Alert query for 1,000+ rows returns bounded results using indexed columns.
- Drowning logic T01-T05:
  - T01 vanished track triggers alert after threshold.
  - T02 visible track leaving zone resets without alert.
  - T03 reappearing before threshold resets timer.
  - T04 two simultaneous vanished tracks produce two events.
  - T05 reappearing after alert emits auto-cancel.

Covered by frontend build:

- Login, dashboard, popup, history, camera views, config modal, and preview modal compile successfully.
- Socket reconnect path reloads alerts immediately after reconnect.
- Mobile CSS keeps tables scrollable inside their wrappers and alert popup readable on small screens.
- The redesigned UI uses a responsive dashboard hero, metric cards, table toolbar, status badges, and modal surfaces.
- Alert preview uses authenticated thumbnail fetching and blob URLs in the browser.

Covered by Docker verification:

- Root `Dockerfile` target `app` builds backend and frontend into one deployable image.
- Root `docker-compose.yml` validates DB, MQTT, app, and optional edge profile wiring.
- The app container serves the React dashboard from Flask at `http://127.0.0.1:5001/`.
- The edge profile can run headless with `DISPLAY_PREVIEW=0` and the bundled `pool_test.mp4` sample.

## Manual browser smoke test

With the app running:

```sh
docker compose up --build -d app
```

Open:

```text
http://127.0.0.1:5001/
```

Use the default development credentials:

```text
username: admin
password: aquawatch
```

Verify:

- The dashboard is not blank and has no browser console errors.
- The hero metrics render alert counts.
- The camera table renders online/offline state and active alert count.
- The alert history table renders `Preview`, `Resolve`, and `False` actions where applicable.
- Clicking `Preview` opens the alert detection frame modal.
- Clicking `Tutup` closes the preview modal.
- On a narrow viewport, the page body does not overflow horizontally; wide tables scroll inside their table wrappers.

## Field tests requiring Raspberry Pi, camera, model, or real video

Record the video clip, model version, camera ID, lighting condition, and measured value for every run.

### Edge - Model & Detection

- YOLOv26 accuracy in bright day, afternoon, and night IR: run the same labeled clip set through `edge/main.py`; calculate precision/recall per condition.
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
