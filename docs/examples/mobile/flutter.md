# Flutter Example

Ứng dụng mẫu sử dụng Flutter framework để hiển thị dữ liệu IoT trên nền tảng di động.

## Flutter Example App (main.dart)

```dart
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IoT Data Viewer',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // Configuration
  final String apiKey = 'YOUR_API_KEY';
  final String serverUrl = 'http://{{ server_host }}:5000';
  final String deviceName = 'esp8266_sensor';
  final String topicName = 'temperature';
  
  List<DataReading> readings = [];
  Timer? refreshTimer;
  bool isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    fetchData();
    // Set up periodic refresh
    refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      fetchData();
    });
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchData() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final response = await http.get(
        Uri.parse('$serverUrl/api/data/$deviceName/$topicName?limit=20'),
        headers: {'X-API-Key': apiKey},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          readings = data.map((item) => DataReading.fromJson(item)).toList();
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = 'Error fetching data: ${response.statusCode}';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Network error: $e';
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('IoT Data Viewer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: fetchData,
            tooltip: 'Refresh data',
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
              ? Center(child: Text(errorMessage!, style: const TextStyle(color: Colors.red)))
              : readings.isEmpty
                  ? const Center(child: Text('No data available'))
                  : _buildDashboard(),
    );
  }

  Widget _buildDashboard() {
    final latestReading = readings.isNotEmpty ? readings.first : null;
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Latest reading card
          if (latestReading != null) ...[    
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Latest Reading', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '${latestReading.value.toStringAsFixed(1)}°C',
                          style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    Center(
                      child: Text(
                        'Last updated: ${DateFormat('MMM d, HH:mm:ss').format(latestReading.timestamp)}',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Chart
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Temperature History', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Expanded(
                      child: _buildChart(),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChart() {
    if (readings.isEmpty) {
      return const Center(child: Text('No data available for chart'));
    }

    // Reverse readings to show oldest to newest (left to right)
    final data = readings.reversed.toList();
    
    return LineChart(
      LineChartData(
        gridData: FlGridData(show: true),
        titlesData: FlTitlesData(
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (value, meta) {
                if (value.toInt() >= 0 && value.toInt() < data.length) {
                  // Show time for every 4th reading to avoid crowding
                  if (value.toInt() % 4 == 0) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text(
                        DateFormat('HH:mm').format(data[value.toInt()].timestamp),
                        style: const TextStyle(fontSize: 10),
                      ),
                    );
                  }
                }
                return const SizedBox.shrink();
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: Text('${value.toInt()}°C', style: const TextStyle(fontSize: 10)),
                );
              },
            ),
          ),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: true),
        lineBarsData: [
          LineChartBarData(
            spots: List.generate(data.length, (index) {
              return FlSpot(index.toDouble(), data[index].value);
            }),
            isCurved: true,
            color: Colors.blue,
            barWidth: 3,
            dotData: FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blue.withOpacity(0.2),
            ),
          ),
        ],
      ),
    );
  }
}

class DataReading {
  final DateTime timestamp;
  final double value;

  DataReading({required this.timestamp, required this.value});

  factory DataReading.fromJson(Map<String, dynamic> json) {
    return DataReading(
      timestamp: DateTime.parse(json['timestamp']),
      value: json['payload']['value'].toDouble(),
    );
  }
}
```

## pubspec.yaml

```yaml
name: iot_data_viewer
description: A mobile app to view IoT sensor data

publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: ">=2.17.0 <3.0.0"

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
  http: ^0.13.5
  fl_chart: ^0.55.0
  intl: ^0.17.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
```

> **Lưu ý:** Để chạy ứng dụng Flutter, bạn cần cài đặt Flutter SDK từ [flutter.dev](https://flutter.dev/docs/get-started/install).
