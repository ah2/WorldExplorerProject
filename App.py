import os
import tkinter as tk
from tkinter import messagebox
import webview
from dotenv import load_dotenv

# Load .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

CATEGORIES = ["all", "restaurant", "cafe", "park", "landmark"]

# ------------------------------
# JS API for pywebview
# ------------------------------
class Api:
    def __init__(self, api_key, base_url, default_lat=25.2048, default_lng=55.2708):
        self._api_key = api_key
        self._base_url = base_url
        self.current_lat = default_lat
        self.current_lng = default_lng

    # JS must call functions to get these
    def get_api_key(self):
        return self._api_key

    def get_base_url(self):
        return self._base_url

# ------------------------------
# Tkinter GUI
# ------------------------------
def start_gui():
    root = tk.Tk()
    root.title("🌍 World Explorer")

    tk.Label(root, text="Latitude (-90 to 90):").pack()
    lat_entry = tk.Entry(root)
    lat_entry.insert(0, "25.2048")
    lat_entry.pack()

    tk.Label(root, text="Longitude (-180 to 180):").pack()
    lng_entry = tk.Entry(root)
    lng_entry.insert(0, "55.2708")
    lng_entry.pack()

    tk.Label(root, text="Select Category:").pack()
    category_var = tk.StringVar(value="all")
    tk.OptionMenu(root, category_var, *CATEGORIES).pack()

    def on_explore():
        try:
            lat = float(lat_entry.get())
            lng = float(lng_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Latitude and Longitude must be numbers.")
            return

        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            messagebox.showerror("Input Error", "Latitude must be -90 to 90, Longitude -180 to 180.")
            return

        category = category_var.get()
        root.destroy()

        api = Api(API_KEY, BASE_URL, lat, lng)
        map_file = os.path.join(os.getcwd(), "interactive_map.html")
        window = webview.create_window(
            "🌍 World Explorer",
            map_file,
            width=1000,
            height=650,
            js_api=api
        )
        webview.start(gui="tk")

    tk.Button(root, text="Explore", command=on_explore).pack(pady=10)
    root.mainloop()

# ------------------------------
# Start the app
# ------------------------------
if __name__ == "__main__":
    start_gui()
