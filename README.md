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

Installation

Clone the repository:

git clone https://github.com/yourusername/world-adventure.git
cd world-adventure


Create a virtual environment and install dependencies:

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt


Set up environment variables (.env file):

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

