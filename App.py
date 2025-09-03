import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import requests

# Load env
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
DEBUG_FLAG = (os.getenv('DEBUG_FLAG', 'False') == 'True')

if (DEBUG_FLAG):
    print(f"API key: {API_KEY}")
    print(f"api url: {BASE_URL}")

app = Flask(__name__, static_folder="web", static_url_path="")

@app.route("/")
def index():
    # Serve index.html from the web folder
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/places")
def get_places():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if not lat or not lng:
        return jsonify({"error": "lat and lng required"}), 400

    try:
        resp = requests.get(
            BASE_URL,
            headers={"x-api-key": API_KEY},
            params={"lat": lat, "lng": lng, "radius": 500, "limit": 20},
            timeout=10
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=DEBUG_FLAG)
