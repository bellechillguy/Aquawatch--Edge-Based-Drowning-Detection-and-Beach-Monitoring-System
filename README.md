# AquaWatch

AquaWatch is an AI-powered drowning detection and monitoring system that combines Computer Vision and IoT technologies to improve swimmer safety in aquatic environments.

The system uses YOLOv8 for human detection, DeepSORT for object tracking, and a rule-based drowning detection engine to identify potential drowning incidents. Alerts are sent through MQTT, stored in PostgreSQL, and delivered to a web dashboard in real time using Socket.IO.

## Features

* Real-time human detection using YOLOv8
* Multi-object tracking with DeepSORT
* Configurable danger zone monitoring
* Automatic drowning alert generation
* MQTT-based communication between edge devices and backend services
* Real-time alert notifications via Socket.IO
* Alert history management
* Camera configuration management
* Docker-based deployment
* Web dashboard for monitoring and incident response

## System Architecture

AquaWatch consists of three main layers:

### Edge Layer

Runs on an edge device such as Raspberry Pi.

Responsibilities:

* Capture video stream from camera
* Detect humans using YOLOv8
* Track detected objects using DeepSORT
* Evaluate danger zone violations
* Generate drowning alerts
* Publish alerts and heartbeat messages through MQTT

### Backend Layer

Built using Flask and PostgreSQL.

Responsibilities:

* Receive alerts from MQTT broker
* Store alerts and camera information
* Provide REST API endpoints
* Manage user authentication
* Deliver real-time notifications through Socket.IO

### Client Layer

Built using React.

Responsibilities:

* Display active alerts
* Show alert history
* Monitor camera status
* Configure camera parameters
* Provide real-time updates to operators

## Technology Stack

### AI & Computer Vision

* YOLOv8
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
2. YOLOv8 detects people in the scene.
3. DeepSORT assigns tracking IDs.
4. The drowning detection engine evaluates tracked objects.
5. If a drowning condition is detected, an alert is generated.
6. The edge device publishes the alert via MQTT.
7. Backend stores the alert in PostgreSQL.
8. Dashboard receives a real-time notification through Socket.IO.
9. Operators can review and update alert status.

## Running the Project

### Prerequisites

* Docker
* Docker Compose

### Start Services

```bash
docker compose up --build
```

### Stop Services

```bash
docker compose down
```

### Check Running Containers

```bash
docker compose ps
```

## Dashboard

The web dashboard provides:

* Active alert monitoring
* Alert history
* Camera management
* Real-time notifications
* Alert status updates

## Future Improvements

* Support for multiple camera streams
* Mobile application integration
* Advanced behavior analysis
* Edge device performance optimization
* Cloud deployment support
* Automatic lifeguard notification system

## License

This project was developed for academic and research purposes.
