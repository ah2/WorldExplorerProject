World Adventure – Map-Based Game

A web-based adventure game where players explore real-world locations using the Overture Maps API, earn points, and track visited places. Includes a login system, admin panel, and dynamic interactive map.

Features

Login and Signup: Players must create an account or login to start the adventure.

City Selection: Start your adventure in one of several cities (Dubai, Paris, New York, Tokyo).

Interactive Map:

Player marker with WASD / arrow key movement.

Nearby places loaded dynamically from Overture Maps Places API.

Bonus points awarded when visiting/clicking places.

Sidebar: Lists nearby places, clickable to zoom and open popups.

Admin Panel:

View all players and scores.

Review visited places.

Check last 50 log entries.

Gallery: Keep track of visited places and remove unwanted entries.

Scoreboard: Track player scores.

Responsive Design: Clean layout with navigation bar, sidebar, and map.

Project Structure
WorldAdventure/
├─ app.py                 # Main Flask application
├─ world_adventure.db     # SQLite database (auto-generated)
├─ .env                   # Environment variables (API key, Flask secret)
├─ requirements.txt       # Python dependencies
├─ static/
│  ├─ map.js              # Map and player logic
│  ├─ styles.css          # Styles for map, sidebar, nav, and forms
│  ├─ player.svg          # Player icon for map
├─ templates/
│  ├─ index.html          # Main game page
│  ├─ login.html          # Login page
│  ├─ signup.html         # Signup page
│  ├─ admin.html          # Admin panel page
│  ├─ scoreboard.html     # Player scoreboard
│  ├─ gallery.html        # Visited places gallery

Installation

Clone the repository:

git clone https://github.com/yourusername/world-adventure.git
cd world-adventure


Create a virtual environment and install dependencies:

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt


Setup environment variables (.env file):

OVERTURE_API_KEY=your_overture_api_key
OVERTURE_API_URL=https://api.overturemaps.com/places
FLASK_SECRET=supersecretkey

Usage

Run the Flask app:

python app.py


Open browser: Navigate to http://127.0.0.1:5000/

Login or signup, choose a city, and start exploring!

Use WASD or arrow keys to move the player.

Click on markers to earn bonus points.

Check sidebar for nearby places.

Admins can log in with username admin / password adminpass.

Database

Uses SQLite (world_adventure.db)

Tables:

users – stores username/password

player – stores player location and score

visited_places – stores places visited by players

Auto-initializes with:

Admin account: admin/adminpass

Test users: alice/alicepass, bob/bobpass

Dependencies

Python 3.9+

Flask

Requests

python-dotenv

Leaflet.js (via CDN in templates)

Customizations

Add more cities in index.html → <select> options.

Modify map.js to change player speed or fetch radius.

Replace player.svg with a custom icon.

Add more bonus mechanics, rarity for places, or additional points system.

Error Handling

Gracefully logs database errors and API failures.

Players can still explore even if marker API fails temporarily.

License

MIT License – feel free to modify and extend.
