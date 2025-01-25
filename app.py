#!/usr/bin/env python3

from flask import Flask, jsonify, render_template_string
import subprocess
import time
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)

# Store historical data (last 60 seconds)
history = {
    "timestamps": [],
    "gpu_util": [],
    "used_mem_percent": [],
}

def fetch_gpu_data():
    """
    Periodically fetch GPU utilization and memory data via nvidia-smi,
    then store in the 'history' dict.
    """
    while True:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.total,memory.used",
                    "--format=csv,noheader,nounits"
                ],
                stdout=subprocess.PIPE,
                text=True,
            )
            gpu_data = result.stdout.strip().split("\n")[0].split(", ")

            gpu_util = int(gpu_data[0])
            total_mem = int(gpu_data[1])
            used_mem = int(gpu_data[2])
            used_mem_percent = (used_mem / total_mem) * 100

            # Update history
            timestamp = time.time()
            history["timestamps"].append(timestamp)
            history["gpu_util"].append(gpu_util)
            history["used_mem_percent"].append(used_mem_percent)

            # Keep only the last 60 data points
            if len(history["timestamps"]) > 60:
                for key in history.keys():
                    history[key] = history[key][-60:]
        except Exception as e:
            print(f"Error fetching GPU data: {e}")

        # Fetch every 1 second
        time.sleep(1)

def fetch_gpu_general_info():
    """
    Fetch general info (GPU name, driver version) via nvidia-smi.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version",
                "--format=csv,noheader,nounits"
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        gpu_info = result.stdout.strip().split(", ")
        return {"name": gpu_info[0], "driver_version": gpu_info[1]}
    except Exception as e:
        print(f"Error fetching GPU general information: {e}")
        return {"name": "Unknown", "driver_version": "Unknown"}

def fetch_gpu_processes():
    """
    Fetch processes (PID, name, used_memory) currently running on the GPU.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader,nounits"
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        processes = result.stdout.strip().split("\n")
        return [
            {
                "pid": p.split(", ")[0],
                "name": p.split(", ")[1],
                "used_memory": p.split(", ")[2]
            }
            for p in processes
            if p
        ]
    except Exception as e:
        print(f"Error fetching GPU processes: {e}")
        return []

@app.route("/")
def index():
    """
    Serve the main HTML page with:
    - Responsive Bootstrap layout
    - Dark mode toggle
    - Real-time charts (Chart.js)
    - Dynamic color-coded stats
    """
    gpu_info = fetch_gpu_general_info()

    # Note: No more `!important` on td/th color in dark mode, so inline styles can override.
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>GPU Monitor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" />
        <!-- Chart.js -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {{
                margin: 0;
                padding: 0;
                transition: background-color 0.3s, color 0.3s;
                font-family: Arial, sans-serif;
            }}
            .dark-mode {{
                background-color: #2c2c2c;
                color: #f0f0f0;
            }}
            /* Navbar color in dark mode */
            .dark-mode .navbar {{
                background-color: #3a3a3a !important;
            }}
            .dark-mode .navbar-light .navbar-brand,
            .dark-mode .navbar-light .navbar-nav .nav-link {{
                color: #f0f0f0 !important;
            }}

            /* Override Bootstrap's default table colors via CSS variables */
            .dark-mode .table {{
                --bs-table-bg: #2c2c2c;
                --bs-table-border-color: #555555;
                --bs-table-striped-bg: #343434;
                --bs-table-striped-color: #ffffff;
                --bs-table-hover-bg: #3b3b3b;
                --bs-table-hover-color: #ffffff;
                --bs-table-active-bg: #424242;
                --bs-table-active-color: #ffffff;
            }}
            /* Default text for all table cells in dark mode */
            .dark-mode .table td,
            .dark-mode .table th {{
                color: #f0f0f0;  /* No !important here, so inline style can override */
            }}
            .dark-mode .table thead th {{
                background-color: #444444 !important;
            }}

            canvas {{
                width: 100% !important;
                height: 400px !important;
            }}
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <span class="navbar-brand mb-0 h1">GPU Performance</span>
                <button id="darkModeToggle" class="btn btn-outline-secondary" type="button">
                    Toggle Dark Mode
                </button>
            </div>
        </nav>

        <!-- Main Container -->
        <div class="container mt-4 mb-5" id="mainContainer">
            <!-- GPU Info -->
            <div class="row">
                <div class="col-12 col-md-6">
                    <h3>General GPU Information</h3>
                    <table class="table table-bordered">
                        <tr><th>GPU Name</th><td>{gpu_info['name']}</td></tr>
                        <tr><th>Driver Version</th><td>{gpu_info['driver_version']}</td></tr>
                    </table>
                </div>
            </div>

            <!-- GPU Chart -->
            <div class="row">
                <div class="col-12">
                    <h3>Real-Time GPU Utilization</h3>
                    <canvas id="gpuChart"></canvas>
                </div>
            </div>

            <!-- Detailed Stats -->
            <div class="row">
                <div class="col-12">
                    <h3>Detailed GPU Stats</h3>
                    <table class="table table-bordered text-center">
                        <thead>
                            <tr>
                                <th>GPU Util (%)</th>
                                <th>Used Mem (%)</th>
                                <th>Total Mem (MiB)</th>
                                <th>Used Mem (MiB)</th>
                                <th>Free Mem (MiB)</th>
                                <th>Temperature (°C)</th>
                            </tr>
                        </thead>
                        <tbody id="gpuStats"></tbody>
                    </table>
                </div>
            </div>

            <!-- Processes -->
            <div class="row">
                <div class="col-12">
                    <h3>Processes Running on GPU</h3>
                    <table class="table table-bordered text-center">
                        <thead>
                            <tr>
                                <th>PID</th>
                                <th>Process Name</th>
                                <th>GPU Memory Usage (MiB)</th>
                            </tr>
                        </thead>
                        <tbody id="gpuProcesses"></tbody>
                    </table>
                </div>
            </div>
        </div> <!-- /container -->

        <!-- Bootstrap JS (Optional) -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

        <script>
            // 1. Dark Mode Toggle
            const darkModeButton = document.getElementById("darkModeToggle");
            darkModeButton.addEventListener("click", () => {{
                document.body.classList.toggle("dark-mode");
            }});

            // 2. Fetch Functions
            async function fetchData() {{
                const response = await fetch("/api/data");
                return response.json();
            }}

            async function fetchProcesses() {{
                const response = await fetch("/api/processes");
                return response.json();
            }}

            // 3. Update Chart
            async function updateChart(chart) {{
                const data = await fetchData();
                chart.data.labels = data.timestamps.map(
                    t => new Date(t * 1000).toLocaleTimeString()
                );
                chart.data.datasets[0].data = data.gpu_util;
                chart.data.datasets[1].data = data.used_mem_percent;
                chart.update("none");
            }}

            // 4. Update Stats (with color-coded indicators)
            async function updateStats() {{
                const response = await fetch("/api/stats");
                const stats = await response.json();

                if (stats.error) {{
                    console.error(stats.error);
                    return;
                }}

                // Define color threshold functions
                function getColorForUtil(u) {{
                    const val = parseFloat(u);
                    if (val >= 80) return "red";
                    if (val >= 50) return "orange";
                    return "green";
                }}

                function getColorForMem(m) {{
                    if (m >= 80) return "red";
                    if (m >= 50) return "orange";
                    return "green";
                }}

                function getColorForTemp(t) {{
                    const val = parseFloat(t);
                    if (val >= 85) return "red";
                    if (val >= 70) return "orange";
                    return "green";
                }}

                // Color-coded inline styles (higher specificity than normal CSS)
                const gpuStats = document.getElementById("gpuStats");
                gpuStats.innerHTML = `
                    <tr>
                        <td style="color: ${{getColorForUtil(stats.gpu_util)}};">
                            ${{stats.gpu_util}}
                        </td>
                        <td style="color: ${{getColorForMem(stats.used_mem_percent)}};">
                            ${{stats.used_mem_percent.toFixed(2)}}
                        </td>
                        <td>${{stats.total_mem}}</td>
                        <td>${{stats.used_mem}}</td>
                        <td>${{stats.free_mem}}</td>
                        <td style="color: ${{getColorForTemp(stats.temperature)}};">
                            ${{stats.temperature}}
                        </td>
                    </tr>
                `;
            }}

            // 5. Update Processes
            async function updateProcesses() {{
                const processes = await fetchProcesses();
                const gpuProcesses = document.getElementById("gpuProcesses");
                gpuProcesses.innerHTML = processes.map(p => `
                    <tr>
                        <td>${{p.pid}}</td>
                        <td>${{p.name}}</td>
                        <td>${{p.used_memory}}</td>
                    </tr>
                `).join("");
            }}

            // 6. Initialize Chart
            const ctx = document.getElementById('gpuChart').getContext('2d');
            const gpuChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: [],
                    datasets: [
                        {{
                            label: 'GPU Util (%)',
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            data: [],
                            pointRadius: 0,
                            fill: true,
                            tension: 0.4
                        }},
                        {{
                            label: 'Used Memory (%)',
                            borderColor: 'rgb(192, 75, 75)',
                            backgroundColor: 'rgba(192, 75, 75, 0.2)',
                            data: [],
                            pointRadius: 0,
                            fill: true,
                            tension: 0.4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{ display: true, text: 'Time' }}
                        }},
                        y: {{
                            title: {{ display: true, text: 'Percentage (%)' }},
                            min: 0,
                            max: 100
                        }}
                    }}
                }}
            }});

            // 7. Auto-refresh every second
            setInterval(() => {{
                updateChart(gpuChart);
                updateStats();
                updateProcesses();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/api/data")
def api_data():
    """
    Provide the last 60 seconds of GPU utilization and memory usage data.
    """
    return jsonify(history)


@app.route("/api/stats")
def api_stats():
    """
    Provide a single snapshot of detailed GPU stats:
    - utilization.gpu, memory.total, memory.used, memory.free, temperature.gpu
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.total,memory.used,memory.free,temperature.gpu",
                "--format=csv,noheader,nounits"
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        gpu_data = result.stdout.strip().split("\n")[0].split(", ")

        gpu_util = gpu_data[0]
        total_mem = int(gpu_data[1])
        used_mem = int(gpu_data[2])
        free_mem = gpu_data[3]
        temperature = gpu_data[4]

        used_mem_percent = (used_mem / total_mem) * 100

        return jsonify({
            "gpu_util": gpu_util,
            "used_mem_percent": used_mem_percent,
            "total_mem": total_mem,
            "used_mem": used_mem,
            "free_mem": free_mem,
            "temperature": temperature,
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/processes")
def api_processes():
    """
    Provide the list of GPU processes.
    """
    return jsonify(fetch_gpu_processes())


# Start background thread to periodically fetch GPU data
data_thread = Thread(target=fetch_gpu_data, daemon=True)
data_thread.start()

if __name__ == "__main__":
    # Run Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)
