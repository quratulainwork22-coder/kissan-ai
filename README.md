# Kissan AI – IoT-Enabled Crop Disease Detection and Case Management System

Final Year Project – BS Computer Science, MTB College, Khalid Campus, Sadiqabad
(Affiliated with The Islamia University of Bahawalpur)

Student: Quratul Ain Tahir (22445025), Session 2022-2026
Student: Eman shoukat ( 22445001), Session 2022-2026
Supervisor: Mr. Faizan Awan

## Live demo
- Live web app: https://quratulain.pythonanywhere.com
- Live sensor data (Demo Farm): https://quratulain.pythonanywhere.com/farms/1
- Interface demo (static sample data): https://quratulainwork22-coder.github.io/kissan-ai/

### How to open the live demo
1. Open https://quratulain.pythonanywhere.com
2. Log in with a demo account:
   - Farmer: farmer@kissan.local / farmer123
   - Adviser: adviser@kissan.local / adviser123
3. Open https://quratulain.pythonanywhere.com/farms/1 (or click **Demo Farm** on the dashboard)
   to see the sensor readings, chart and alerts.

The chart only shows data after readings have been sent. To send live synthetic readings
to the online app, run this from the project folder:

    python iot/simulator.py --scenario humid --url https://quratulain.pythonanywhere.com/api/readings --key demo-key-123

## Features
- Farmer registration, login and farm records
- Leaf photo upload with AI disease screening (cotton: healthy, leaf curl virus, bacterial blight)
- "Uncertain" result when model confidence is low
- ESP32 IoT node (temperature, humidity, soil moisture) sending data over Wi-Fi
- Live sensor charts and disease-risk alerts
- Adviser review of cases and approval of treatment guidance
- Case history with follow-ups

## Run locally
Windows:

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python seed.py
    python run.py

macOS / Linux:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python seed.py
    python run.py

Open http://127.0.0.1:5001

Demo accounts (created by seed.py):
- Farmer: farmer@kissan.local / farmer123
- Adviser: adviser@kissan.local / adviser123

## IoT
- Without hardware (local): `python iot/simulator.py --scenario humid` (sends SYNTHETIC readings)
- Without hardware (live site): add `--url https://quratulain.pythonanywhere.com/api/readings --key demo-key-123`
- Scenarios: `normal`, `humid` (whitefly / leaf curl risk alert), `dry` (low soil moisture alert)
- With hardware: open `iot/esp32_sensor/esp32_sensor.ino` in Arduino IDE and set the Wi-Fi details,
  the server URL (laptop IP for local, or `http://quratulain.pythonanywhere.com/api/readings` for the
  live site) and the farm's API key.

## AI model
Train in Google Colab with `ml/train_model.py`. Copy `cotton_model.keras` and `labels.txt`
into the `models/` folder. Until then the app shows "Model not trained yet".
(The live demo runs without the model because of free-hosting storage limits.)

## Limitations
- Prototype hosted for demonstration only, not a production agricultural service.
- Model is trained on public datasets and not field-tested in Sadiqabad.
- Risk thresholds are demonstration values and must be reviewed by an agriculture expert.
- Treatment guidance must come from official sources and be approved by an adviser.
- Sensor data shown in the live demo is synthetic unless stated otherwise.
