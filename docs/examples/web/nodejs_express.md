# Node.js Express Example

Ứng dụng mẫu sử dụng Express.js framework để hiển thị dữ liệu từ IoT Data Server.

## Node.js Express Example App

```javascript
const express = require('express');
const path = require('path');
const axios = require('axios');

const app = express();
const port = 5001;

// Configuration
const API_KEY = 'YOUR_API_KEY';
const IOT_SERVER_URL = 'http://{{ server_host }}:5000';

// Middleware
app.use(express.json());
app.use(express.static('public'));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Routes
app.get('/', (req, res) => {
  res.render('index');
});

app.get('/api/data', async (req, res) => {
  try {
    const device = req.query.device || 'default_device';
    const topic = req.query.topic || 'temperature';
    const limit = req.query.limit || 10;
    
    const response = await axios.get(
      `${IOT_SERVER_URL}/api/data/${device}/${topic}?limit=${limit}`,
      { headers: { 'X-API-Key': API_KEY } }
    );
    
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching data:', error);
    res.status(500).json({ error: 'Failed to fetch data' });
  }
});

app.post('/api/publish', async (req, res) => {
  try {
    const { device, topic, payload } = req.body;
    
    const response = await axios.post(
      `${IOT_SERVER_URL}/api/publish`,
      { device, topic, payload },
      { headers: { 'X-API-Key': API_KEY } }
    );
    
    res.json(response.data);
  } catch (error) {
    console.error('Error publishing data:', error);
    res.status(500).json({ error: 'Failed to publish data' });
  }
});

app.get('/dashboard', (req, res) => {
  res.render('dashboard');
});

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
```

## views/index.ejs

```html
<!DOCTYPE html>
<html>
<head>
  <title>IoT Data Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <div class="container mt-4">
    <h1>IoT Data Dashboard</h1>
    
    <div class="row mt-4">
      <div class="col-lg-8">
        <div class="card">
          <div class="card-header">
            <h5>Temperature Trends</h5>
          </div>
          <div class="card-body">
            <canvas id="tempChart"></canvas>
          </div>
        </div>
      </div>
      
      <div class="col-lg-4">
        <div class="card">
          <div class="card-header">
            <h5>Latest Reading</h5>
          </div>
          <div class="card-body">
            <div class="d-flex justify-content-center">
              <div class="display-1" id="currentTemp">--</div>
              <div class="h1 mt-2">°C</div>
            </div>
            <p class="text-center" id="lastUpdate">Last updated: --</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let tempChart;
    
    async function fetchData() {
      const response = await fetch('/api/data?device=esp8266_sensor&topic=temperature&limit=20');
      const data = await response.json();
      
      if (data.length > 0) {
        // Update current temperature
        const latestReading = data[0];
        document.getElementById('currentTemp').textContent = latestReading.payload.value;
        document.getElementById('lastUpdate').textContent = 'Last updated: ' + 
          new Date(latestReading.timestamp).toLocaleString();
        
        // Update chart
        const labels = [];
        const values = [];
        
        data.reverse().forEach(reading => {
          labels.push(new Date(reading.timestamp).toLocaleTimeString());
          values.push(reading.payload.value);
        });
        
        if (tempChart) {
          tempChart.data.labels = labels;
          tempChart.data.datasets[0].data = values;
          tempChart.update();
        } else {
          const ctx = document.getElementById('tempChart').getContext('2d');
          tempChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: labels.reverse(),
              datasets: [{
                label: 'Temperature (°C)',
                data: values.reverse(),
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
              }]
            },
            options: {
              responsive: true,
              scales: {
                y: {
                  beginAtZero: false,
                  title: {
                    display: true,
                    text: 'Temperature (°C)'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: 'Time'
                  }
                }
              }
            }
          });
        }
      }
    }
    
    // Initial fetch
    fetchData();
    
    // Update every 30 seconds
    setInterval(fetchData, 30000);
  </script>
</body>
</html>
```
