from app import create_app

app = create_app()

if __name__ == "__main__":
    # host 0.0.0.0 lets the ESP32 on the same Wi-Fi reach the server
    app.run(debug=True, host="0.0.0.0", port=5001)
