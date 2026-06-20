# AquaWatch

AquaWatch is an AI-powered drowning detection and monitoring system that combines Computer Vision and IoT technologies to improve swimmer safety in aquatic environments.

The system uses YOLOv26 for human detection, DeepSORT for object tracking, and a rule-based drowning detection engine to identify potential drowning incidents. Alerts are sent through MQTT, stored in PostgreSQL, and delivered to a web dashboard in real time using Socket.IO.

<img width="1470" height="835" alt="Image" src="https://github.com/user-attachments/assets/3f052edb-10ea-46dc-91fa-6be643973395" />

## Features

* Real-time human detection using YOLOv26
* Multi-object tracking with DeepSORT
* Configurable danger zone monitoring
* Automatic drowning alert generation
* MQTT-based communication between edge devices and backend services
* Real-time alert notifications via Socket.IO
* Alert history management
* Camera configuration management
* Alert thumbnail preview for detected incidents
* Polished responsive operator dashboard
* Docker-based deployment
* Web dashboard for monitoring and incident response

## System Architecture

AquaWatch consists of three main layers:

### Edge Layer

Runs on an edge device such as Raspberry Pi.

Responsibilities:

* Capture video stream from camera
* Detect humans using YOLOv26
* Track detected objects using DeepSORT
* Evaluate danger zone violations
* Generate drowning alerts
* Attach a JPEG detection preview to each alert
* Publish alerts and heartbeat messages through MQTT

### Backend Layer

Built using Flask and PostgreSQL.

Responsibilities:

* Receive alerts from MQTT broker
* Store alerts and camera information
* Serve authenticated alert thumbnails
* Provide REST API endpoints
* Manage user authentication
* Deliver real-time notifications through Socket.IO

### Client Layer

Built using React.

Responsibilities:

* Display active alerts
* Show alert history
* Preview detection frames from stored alerts
* Monitor camera status
* Configure camera parameters
* Provide real-time updates to operators

## Technology Stack

### AI & Computer Vision

* YOLOv26 (Ultralytics 8.4+)
* DeepSORT
* OpenCV

### Backend

* Flask
* Flask-JWT-Extended
* Flask-SocketIO
* SQLAlchemy
* PostgreSQL

### Frontend

* React
* Vite
* Axios
* Socket.IO Client

### Communication

* MQTT
* Eclipse Mosquitto

### Deployment

* Docker
* Docker Compose

## Project Structure

```text
aquawatch/
├── edge/
│   ├── main.py
│   ├── drowning_logic.py
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── models.py
│   │   ├── mqtt_handler.py
│   │   └── ...
│   └── ...
│
├── frontend/
│   ├── src/
│   └── ...
│
├── docs/
├── docker-compose.yml
└── README.md
```

## Alert Workflow

1. Camera captures video frames.
2. YOLOv26 detects people in the scene.
3. DeepSORT assigns tracking IDs.
4. The drowning detection engine evaluates tracked objects.
5. If a drowning condition is detected, an alert is generated.
6. The edge device publishes the alert via MQTT.
7. Backend stores the alert in PostgreSQL.
8. Dashboard receives a real-time notification through Socket.IO.
9. Operators can preview the detection frame for the incident.
10. Operators can review and update alert status.

## Running the Project

### Prerequisites

* Docker
* Docker Compose

### Start Services

```bash
docker compose up --build
```

This starts PostgreSQL, Mosquitto, and the Flask app that serves both the API and the built React dashboard.

Open the dashboard at:

```text
http://127.0.0.1:5001/
```

Default development credentials:

```text
username: admin
password: aquawatch
```

### Start Edge Detection

The edge service is optional and runs under the `edge` profile:

```bash
docker compose --profile edge up --build edge
```

By default the edge container uses:

* `CAMERA_ID=cam_01`
* `CAMERA_URL=pool_test.mp4`
* `MODEL_PATH=yolo26n.pt`
* `DISPLAY_PREVIEW=0`

`yolo26n.pt` is downloaded automatically on first run. Override `MODEL_PATH` for a custom fine-tuned YOLOv26 checkpoint. Override `CAMERA_URL` to use another video file, webcam, or RTSP stream.

`DISPLAY_PREVIEW=0` is the recommended default for Docker/headless environments. Set `DISPLAY_PREVIEW=1` only when running somewhere that can open an OpenCV preview window.

### Stop Services

```bash
docker compose down
```

### Check Running Containers

```bash
docker compose ps
```

To include the optional edge profile in status output:

```bash
docker compose --profile edge ps
```

## Dashboard

The web dashboard provides:

* Login with JWT-based authentication
* Responsive operator dashboard with live alert metrics
* Active alert monitoring
* Alert history with filtering
* Alert preview modal for stored detection thumbnails
* Camera management
* Real-time notifications
* Alert status updates

Alert preview frames are available from the alert history table. Click `Preview` on any alert that has a stored thumbnail.

## Future Improvements

* Support for multiple camera streams
* Mobile application integration
* Advanced behavior analysis
* Edge device performance optimization
* Cloud deployment support
* Automatic lifeguard notification system

## License

This project was developed for academic and research purposes.
