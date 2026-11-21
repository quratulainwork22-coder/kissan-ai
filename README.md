# Kissan AI – IoT-Enabled Crop Disease Detection and Case Management System

Final Year Project – BS Computer Science, MTB College, Khalid Campus, Sadiqabad
(Affiliated with The Islamia University of Bahawalpur)

Student: Quratul Ain Tahir (22445025), Session 2022-2026
Supervisors: Mr. Faizan Awan, Mr. Muhammad Umer

Interface demo (sample data): https://quratulainwork22-coder.github.io/kissan-ai/

## Features
- Farmer registration, login and farm records
- Leaf photo upload with AI disease screening (cotton: healthy, leaf curl virus, bacterial blight)
- "Uncertain" result when model confidence is low
- ESP32 IoT node (temperature, humidity, soil moisture) sending data over Wi-Fi
- Live sensor charts and disease-risk alerts
- Adviser review of cases and approval of treatment guidance
- Case history with follow-ups

## Setup
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python seed.py
    python run.py

Open http://127.0.0.1:5000

Demo accounts (created by seed.py):
- Farmer: farmer@kissan.local / farmer123
- Adviser: adviser@kissan.local / adviser123

## IoT
- Without hardware: `python iot/simulator.py --scenario humid` (sends SYNTHETIC readings)
- With hardware: open `iot/esp32_sensor/esp32_sensor.ino` in Arduino IDE, set Wi-Fi, laptop IP and API key.

## AI model
Train in Google Colab with `ml/train_model.py`. Copy `cotton_model.keras` and `labels.txt`
into the `models/` folder. Until then the app shows "Model not trained yet".

## Limitations
- Prototype, not a deployed agricultural service.
- Model is trained on public datasets and not field-tested in Sadiqabad.
- Risk thresholds are demonstration values and must be reviewed by an agriculture expert.
- Treatment guidance must come from official sources and be approved by an adviser.
