let map;
let playerMarker;
let playerPos = null;
let discoveredPlaces = [];
const MOVE_STEP = 0.002; // smaller step = slower movement
const DISCOVERY_RADIUS = 0.005; // distance threshold to "discover" places

// Initialize map centered on player
function initMap(lat, lng) {
 if (map) {
        map.remove();  // Remove previous map instance
        map = null;
    }
    map = L.map('map').setView([playerPos.lat, playerPos.lng], 16); // zoom in

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    // Add player icon
    const playerIcon = L.icon({
        iconUrl: '/static/icons/player.svg',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    playerMarker = L.marker([playerPos.lat, playerPos.lng], { icon: playerIcon }).addTo(map);

    // Keyboard controls
    document.addEventListener("keydown", handleMove);

    // Fetch nearby places
    fetchPlaces(lat, lng);
}

// Move player with WASD or Arrow Keys
function handleMove(e) {
    switch (e.key) {
        case "ArrowUp":
        case "w":
            playerPos.lat += MOVE_STEP;
            break;
        case "ArrowDown":
        case "s":
            playerPos.lat -= MOVE_STEP;
            break;
        case "ArrowLeft":
        case "a":
            playerPos.lng -= MOVE_STEP;
            break;
        case "ArrowRight":
        case "d":
            playerPos.lng += MOVE_STEP;
            break;
        default:
            return;
    }
    updatePlayer();
}

// Update player position and check discoveries
function updatePlayer() {
    playerMarker.setLatLng([playerPos.lat, playerPos.lng]);
    map.panTo([playerPos.lat, playerPos.lng]); // always follow the player
    checkDiscoveries();
}

// Fetch places from our API
async function fetchPlaces(lat, lng) {
    try {
        const res = await fetch(`/api/places?lat=${lat}&lng=${lng}&radius=1500`);
        const data = await res.json();
        if (data && data.features) {
            discoveredPlaces = data.features.map(f => ({
                name: f.properties?.name || "Unknown",
                coords: f.geometry?.coordinates?.reverse() // [lat, lng]
                //discovered: false
            }));
        }
    } catch (err) {
        console.error("Error loading places:", err);
    }
}

// Check if player is near a place
function checkDiscoveries() {
    discoveredPlaces.forEach(place => {
        if (!place.discovered) {
            const dist = Math.sqrt(
                Math.pow(playerPos.lat - place.coords[0], 2) +
                Math.pow(playerPos.lng - place.coords[1], 2)
            );
            if (dist < DISCOVERY_RADIUS) {
                place.discovered = true;
                showDiscoveredPlace(place);
            }
        }
    });
}

// Show marker + popup when discovered
function showDiscoveredPlace(place) {
    const marker = L.marker(place.coords).addTo(map);
    marker.bindPopup(`<b>${place.name}</b><br>+10 points!`).openPopup();
}

// ------------------------
// City selection handler
// ------------------------
document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("start-btn");
    if (btn) {
        btn.addEventListener("click", function() {
            const city = document.getElementById("city-select").value;
            if (!city) return alert("Please choose a city!");

            // Fetch city coordinates from server
            fetch(`/start?city=${city}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) return alert(data.error);
                    initMap(data.lat, data.lng);
                    document.getElementById("city-screen").style.display = "none";
                    document.getElementById("map-container").style.display = "block";

                })
                .catch(err => console.error("Failed to start adventure:", err));
        });
    }
});