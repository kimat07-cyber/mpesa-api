from flask import Flask, request, jsonify
import requests
import base64
from datetime import datetime
import os

app = Flask(__name__)

# =========================
# ENV VARIABLES (Render)
# =========================
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
PASSKEY = os.environ.get("PASSKEY")
SHORTCODE = os.environ.get("SHORTCODE")
CALLBACK_URL = os.environ.get("CALLBACK_URL")


# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return "M-Pesa STK Push API is running"
@app.route("/env-check")
def env_check():
    return {
        "CONSUMER_KEY_EXISTS": bool(CONSUMER_KEY),
        "CONSUMER_SECRET_EXISTS": bool(CONSUMER_SECRET),
        "PASSKEY_EXISTS": bool(PASSKEY),
        "SHORTCODE": SHORTCODE,
        "CALLBACK_URL": CALLBACK_URL
    }
@app.route("/token")
def token():
    return {"access_token": get_access_token()}

# =========================
# GET ACCESS TOKEN
# =========================
def get_access_token():
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))

    print("TOKEN STATUS:", response.status_code)
    print("TOKEN RESPONSE:", response.text)

    try:
        data = response.json()
        return data.get("access_token")
    except Exception as e:
        print("TOKEN ERROR:", e)
        return None


# =========================
# GENERATE PASSWORD
# =========================
def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(data.encode()).decode("utf-8")

    print("GENERATED PASSWORD:", password)
    print("TIMESTAMP:", timestamp)

    return password, timestamp


# =========================
# =========================
# STK PUSH ENDPOINT
# =========================
@app.route("/stkpush", methods=["POST"])
def stkpush():
    data = request.json

    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount are required"}), 400

    # Get token
    access_token = get_access_token()

    if not access_token:
        return jsonify({"error": "Failed to generate access token"}), 500

    password, timestamp = generate_password()

    url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "MPESA API",
        "TransactionDesc": "Payment"
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    print("STK STATUS:", response.status_code)
    print("STK RESPONSE:", response.text)

    return jsonify(response.json())

# =========================
# CALLBACK ENDPOINT
# =========================
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json
    print("🔥 CALLBACK RECEIVED:")
    print(data)

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


if __name__ == "__main__":
    app.run(debug=True)
