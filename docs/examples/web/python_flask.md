# Python Flask Example

Ứng dụng mẫu sử dụng Flask framework để hiển thị dữ liệu từ IoT Data Server.

## Python Flask Example App

```python
from flask import Flask, render_template, jsonify, request
import requests
import json

app = Flask(__name__)

# Configuration
API_KEY = "YOUR_API_KEY"
IOT_SERVER_URL = "http://{{ server_host }}:5000"

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/data')
def get_data():
  # Get parameters from request
  device = request.args.get('device', 'default_device')
  topic = request.args.get('topic', 'temperature')
  limit = request.args.get('limit', 10)
  
  # Fetch data from IoT server
  url = f"{IOT_SERVER_URL}/api/data/{device}/{topic}"
  headers = {"X-API-Key": API_KEY}
  
  try:
    response = requests.get(url, headers=headers, params={"limit": limit})
    if response.status_code == 200:
      return jsonify(response.json())
    else:
      return jsonify({"error": f"API request failed with status code {response.status_code}"}), 500
  except Exception as e:
    return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
  return render_template('dashboard.html')

# Helper function to get latest data for all devices
def get_latest_data():
  url = f"{IOT_SERVER_URL}/api/data"
  headers = {"X-API-Key": API_KEY}
  
  try:
    response = requests.get(url, headers=headers, params={"latest": True})
    if response.status_code == 200:
      return response.json()
    else:
      return []
  except:
    return []

if __name__ == '__main__':
  app.run(debug=True, port=5001)
```

## templates/index.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>IoT Data Viewer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container mt-5">
        <h1>IoT Data Viewer</h1>
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Temperature</div>
                    <div class="card-body">
                        <canvas id="tempChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Latest Reading</div>
                    <div class="card-body">
                        <table class="table" id="dataTable">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Value</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Fetch data and update charts
        async function fetchData() {
            const response = await fetch('/data?device=esp8266_sensor&topic=temperature&limit=20');
            const data = await response.json();
            
            // Update table
            const tableBody = document.querySelector('#dataTable tbody');
            tableBody.innerHTML = '';
            
            // Update chart
            const labels = [];
            const values = [];
            
            data.forEach(item => {
                // Add to table
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(item.timestamp).toLocaleString()}</td>
                    <td>${item.payload.value}°C</td>
                `;
                tableBody.appendChild(row);
                
                // Add to chart data
                labels.push(new Date(item.timestamp).toLocaleTimeString());
                values.push(item.payload.value);
            });
            
            // Create chart
            const ctx = document.getElementById('tempChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels.reverse(),
                    datasets: [{
                        label: 'Temperature (°C)',
                        data: values.reverse(),
                        backgroundColor: 'rgba(0, 123, 255, 0.2)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });
        }
        
        // Initial fetch
        fetchData();
        
        // Update every 30 seconds
        setInterval(fetchData, 30000);
    </script>
</body>
</html>
```
