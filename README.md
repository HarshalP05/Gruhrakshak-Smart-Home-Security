# Gruhrakshak-Smart-Home-Security
A comprehensive, AI-powered home security system designed to detect environmental hazards and intrusions, and to communicate threats via a central unit and a responsive web application.

---

## 📖 Project Overview

This project presents a robust **Smart Home Security System** featuring:

- A **central unit** connected to multiple **distributed sensor nodes**
- Real-time **threat detection** using:
  - Gas sensors (e.g., MQ6)
  - Temperature and humidity sensors (e.g., AHT21)
  - Smoke detectors
- **YOLOv3-based AI object detection** to identify potential intruders
- A **Flask-powered backend** serving a live, responsive **web interface**
- Secure access via **password-protected authentication**
- Communication between sensor units and the backend over **WiFi/Bluetooth**

---

## 🧠 Features

✅ Real-time detection of fire, gas leaks, and environmental anomalies  
✅ AI-based object detection to catch intrusions using YOLOv3  
✅ Automatic alerts and system response protocols  
✅ Responsive web interface with visual sensor data  
✅ ESP32-based microcontroller communication  
✅ User authentication for secure access to camera streams and data

---

## 🌐 Web Interface

Built using:

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Data Source**: Bluetooth/WiFi-enabled sensor units

### Web App Modules:

- 📊 Sensor Dashboard (Temperature, Gas, Humidity)
- 🎥 Security Camera (AI Object Detection)
- 🔐 Login Authentication
- 📈 Real-Time Data Visualization

---

## 🏗️ System Architecture

```
[Sensor Units (ESP32)]
        ⇅ Bluetooth/WiFi
    [Central Flask Server]
        ⇅
[YOLOv3 Object Detection]
        ⇅
[Web Dashboard]
```

---

## 📁 Folder Structure

```
.
├── app.py                  # Flask server
├── trial.py                # Test/utility script
├── requirements.txt        # Python dependencies
├── README.md
├── .env / .gitignore / Procfile
│
├── object_detection/
│   ├── main.py
│   ├── detection.py
│   ├── coco_names
│   ├── yolov3.cfg          # Ignored by Git
│   ├── yolov3.weights      # Ignored by Git
│   └── esp_code/
│       └── esp_code.ino    # Arduino code for ESP32
│
└── template/
    ├── index.html
    ├── aht21.html
    ├── mq6.html
    ├── overall.html
    ├── plot_aht21.html
    ├── plot_mq6.html
    ├── script.js
    ├── styles.css
    └── images/
        ├── battery-icon.svg
        ├── graph.jpeg
        └── home.png
```

---

## 🚀 Getting Started

1. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask server**  
   ```bash
   python app.py
   ```

3. **Upload `esp_code.ino`** to your ESP32 devices via Arduino IDE

4. **Access the Web App** at `http://localhost:5000`

---

## ⚠️ Notes

- The YOLOv3 model weights and config are large files and are **excluded** from version control.  
  Ensure you download them manually and place them in the `object_detection/` directory.

- Sensor readings are simulated/tested with ESP32 devices. Ensure appropriate hardware connections.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [YOLOv3 - Joseph Redmon](https://pjreddie.com/darknet/yolo/)
- [Flask Web Framework](https://flask.palletsprojects.com/)
- Sensor libraries: AHT21, MQ6, and Arduino ESP32

---