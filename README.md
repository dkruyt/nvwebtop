# GPU Monitor

A real-time NVIDIA GPU monitoring web application built with Flask and Chart.js.

## Features

- Real-time GPU utilization and memory usage graphs
- Dark/light mode toggle
- Detailed GPU statistics including:
  - GPU utilization percentage
  - Memory usage
  - Temperature
  - Running processes
- Color-coded indicators for quick status assessment
- Responsive design that works on desktop and mobile
- Auto-refreshing data every second

## Requirements

- NVIDIA GPU
- NVIDIA drivers and nvidia-smi tool
- Docker and Docker Compose
- NVIDIA Container Toolkit

## Quick Start

1. Clone this repository:
```bash
git clone <repository-url>
cd gpu-monitor
```

2. Start the application using Docker Compose:
```bash
docker compose up --build
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Docker Configuration

The application is containerized using Docker with NVIDIA GPU support. The configuration includes:

- Base image: nvidia/cuda:12.3.1-base-ubuntu22.04
- Python 3 environment
- Gunicorn WSGI server
- Automatic container restart policy
- GPU device passthrough

## API Endpoints

- `/api/data` - Historical GPU utilization and memory usage data
- `/api/stats` - Current detailed GPU statistics
- `/api/processes` - List of processes currently using the GPU

## Development

To run the application in development mode without Docker:

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

## License

MIT License
