import tkinter as tk
from tkinter import messagebox
import requests
import folium
import webview
import os


# --- CONFIG ---
API_KEY = "live_hjhCLZC77ZllJ5OCoJlp7zXS2s2uGAbQzzwie6aMzaYB6JuzouDu88j106WCYlz0"
BASE_URL = "https://api.overturemapsapi.com/places"

# Predefined city centers (lat, lon)
CITIES = {
    "Dubai": (25.2048, 55.2708),
    "Paris": (48.8566, 2.3522),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6895, 139.6917),
}


def fetch_places(lat, lng):
    """Fetch places around given coordinates from OvertureMaps"""
    bbox_size = 0.05
    bbox = f"{lng - bbox_size},{lat - bbox_size},{lng + bbox_size},{lat + bbox_size}"

    radius = 1000

    headers = {"x-api-key": f"{API_KEY}"}
    params = { "lat": lat,"lng": lng, "radius": radius,"limit": 20, "dataset": "places"}

    resp = requests.get(BASE_URL, headers=headers, params=params)
    if resp.status_code != 200:
        messagebox.showerror("API Error", f"Failed: {resp.status_code}\n{resp.text}")
        print(resp.text)
        return []

    data = resp.json()
    print(data)

    # Handle both dict (GeoJSON) or list formats
    if isinstance(data, dict):
        features = data.get("features", [])
    elif isinstance(data, list):
        features = data
    else:
        features = []

    places = []
    for feat in features:
        if "geometry" in feat:  # GeoJSON
            coords = feat["geometry"]["coordinates"]
            props = feat.get("properties", {})
            name = props.get("name", "Unnamed")
            category = props.get("category", "Unknown")
            places.append((coords[1], coords[0], name, category))
        else:  # Flat list
            lat_ = feat.get("lat")
            lon_ = feat.get("lon")
            name = feat.get("name", "Unnamed")
            category = feat.get("category", "Unknown")
            if lat_ and lon_:
                places.append((lat_, lon_, name, category))
    return places


def show_map(city_name):
    lat, lon = CITIES[city_name]
    places = fetch_places(lat, lon)

    if not places:
        messagebox.showinfo("No Results", f"No places found for {city_name}.")
        return

    # Create folium map
    m = folium.Map(location=[lat, lon], zoom_start=13)
    for lat_, lon_, name, category in places:
        folium.Marker(
            [lat_, lon_],
            popup=f"<b>{name}</b><br>Category: {category}",
            tooltip=name,
        ).add_to(m)

    # Save HTML map
    map_file = os.path.join(os.getcwd(), "map.html")
    m.save(map_file)

    # Open map inside pywebview
    webview.create_window(f"🌍 World Explorer - {city_name}", map_file, width=800, height=600)


# --- GUI ---
root = tk.Tk()
root.title("🌍 World Explorer")

tk.Label(root, text="Select a City:").pack(pady=5)

city_var = tk.StringVar(value="Dubai")
city_menu = tk.OptionMenu(root, city_var, *CITIES.keys())
city_menu.pack(pady=5)


def on_search():
    city = city_var.get()
    show_map(city)


tk.Button(root, text="Explore", command=on_search).pack(pady=10)

root.mainloop()
