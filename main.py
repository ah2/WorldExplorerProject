import os
import requests
import folium
import webview
import json

# --- CONFIG ---
API_KEY = "live_hjhCLZC77ZllJ5OCoJlp7zXS2s2uGAbQzzwie6aMzaYB6JuzouDu88j106WCYlz0"
BASE_URL = "https://api.overturemapsapi.com/places"
CATEGORIES = ["restaurant", "cafe", "park", "landmark", "all"]

# --- Fetch places ---
def fetch_places(lat, lng, category="all"):
    headers = {"x-api-key": f"{API_KEY}"}
    params = {"lat": lat, "lng": lng, "radius": 5000, "limit": 50}
    if category != "all":
        params["category"] = category

    resp = requests.get(BASE_URL, headers=headers, params=params)
    if resp.status_code != 200:
        return []

    data = resp.json()
    features = data if isinstance(data, list) else data.get("features", [])
    places = []

    for feat in features:
        if "geometry" in feat:
            coords = feat["geometry"]["coordinates"]
            props = feat.get("properties", {})
            name = props.get("name", "Unnamed")
            cat = props.get("category", "Unknown")
            places.append((coords[1], coords[0], name, cat))
        else:
            lat_ = feat.get("lat")
            lon_ = feat.get("lon")
            name = feat.get("name", "Unnamed")
            cat = feat.get("category", "Unknown")
            if lat_ and lon_:
                places.append((lat_, lon_, name, cat))
    return places

# --- Map generation ---
def generate_map(lat, lng, category="all"):
    places = fetch_places(lat, lng, category)
    m = folium.Map(location=[lat, lng], zoom_start=13)

    for lat_, lon_, name, cat in places:
        folium.Marker([lat_, lon_], popup=f"<b>{name}</b><br>{cat}", tooltip=name).add_to(m)

    # Add click listener to map
    m.add_child(folium.LatLngPopup())

    # Add custom JS to call Python callback
    m.get_root().html.add_child(folium.Element("""
        <script>
        function sendLatLng(lat, lng){
            if(window.pywebview){
                window.pywebview.api.on_click(lat, lng);
            }
        }

        document.addEventListener('click', function(e){
            var coords = document.getElementsByClassName('leaflet-popup-content');
            if(coords.length){
                var text = coords[0].innerText.split(",");
                var lat = parseFloat(text[0]);
                var lng = parseFloat(text[1]);
                sendLatLng(lat, lng);
            }
        });
        </script>
    """))

    map_file = os.path.join(os.getcwd(), "click_map.html")
    m.save(map_file)
    return map_file

# --- API exposed to JS ---
class Api:
    def __init__(self, category="all"):
        self.category = category

    def on_click(self, lat, lng):
        print(f"Clicked at: {lat}, {lng}")
        map_file = generate_map(lat, lng, self.category)
        webview.load_url(map_file)  # reload map with new markers

# --- Launch app ---
def start_app():
    lat, lng = 25.2048, 55.2708  # default starting point (Dubai)
    map_file = generate_map(lat, lng)
    api = Api(category="all")
    window = webview.create_window("🌍 Click to Explore", map_file, width=900, height=650, js_api=api)
    webview.start(gui="tk")

start_app()
