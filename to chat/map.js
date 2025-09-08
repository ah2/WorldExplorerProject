


let map;
let playerMarker;
let discoveredPlaces = [];
const MOVE_STEP = 0.002; // smaller step = slower movement
const DISCOVERY_RADIUS = 0.005; // distance threshold to "discover" places

// --- Swipe Controls ---
let touchStartX = 0;
let touchStartY = 0;
let touchEndX = 0;
let touchEndY = 0;

// Initialize map centered on player
function initMap(lat, lng) {
    if (map) {
        map.remove(); // Remove previous map instance
        map = null;
    }
    map = L.map('map').setView([lat, lng], 16); // zoom in

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    // Add player icon
    const playerIcon = L.icon({
        iconUrl: '/static/icons/player.svg',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    playerMarker = L.marker([lat, lng], {
        icon: playerIcon
    }).addTo(map);

    // Keyboard controls
    document.addEventListener("keydown", handleMove);

    // Fetch nearby places
    fetchPlaces(lat, lng);
}

// Move player with WASD or Arrow Keys
function handleMove(e) {
    switch (e.key.toLowerCase()) { // normalize input
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

function handleSwipe() {
    const dx = touchEndX - touchStartX;
    const dy = touchEndY - touchStartY;

    if (Math.abs(dx) > Math.abs(dy)) {
        // Horizontal swipe
        if (dx > 30) {
            playerPos.lng += MOVE_STEP; // swipe right
        } else if (dx < -30) {
            playerPos.lng -= MOVE_STEP; // swipe left
        }
    } else {
        // Vertical swipe
        if (dy > 30) {
            playerPos.lat -= MOVE_STEP; // swipe down
        } else if (dy < -30) {
            playerPos.lat += MOVE_STEP; // swipe up
        }
    }
    updatePlayer();
}

// Update player position and check discoveries
function updatePlayer() {
    playerMarker.setLatLng([lat, lng]);
    map.panTo([lat, lng]); // always follow the player
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
                    Math.pow(playerPos.lng - place.coords[1], 2));
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
document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("start-btn");
    const errorMsg = document.getElementById("error-msg");
        let selectedCity = null;
    if (btn) {
        btn.addEventListener("click", function () {
            const city = document.getElementById("city-select").value;
            if (!city) {
                errorMsg.textContent = "Please pick a valid city from the list.";
                errorMsg.style.display = "block";
                return;
            }

            // Fetch city coordinates from server
            fetch(`/start?city=${encodeURIComponent(city)}&lat=${lat}&lng=${lng}`)
            .then(res => res.json())
            .then(data => {
                if (data.error)
                    errorMsg.textContent = data.error;
                    errorMsg.style.display = "block";
                    //return alert(data.error);
                errorMsg.style.display = "none";
                initMap(selectedCity.lat, selectedCity.lng);
                //document.getElementById("city-screen").style.display = "none";
                document.getElementById("map-container").style.display = "block";
            playerPos = { selectedCity.lat, selectedCity.lng };

            })
            .catch(err => console.error("Failed to start adventure:", err));
        });
    }

    const input = document.getElementById("city-select");
    const suggestions = document.getElementById("suggestions");


    input.addEventListener("input", async() => {
        const q = input.value.trim();
        if (!q) {
            suggestions.innerHTML = "";
            return;
        }

        const res = await fetch(`/search_cities?q=${encodeURIComponent(q)}`);
        const data = await res.json();

        suggestions.innerHTML = "";
        data.forEach(city => {
            const li = document.createElement("li");
            li.textContent = city.name;
            li.addEventListener("click", () => {
                input.value = city.name;
                selectedCity = city; // Save full object with coords
                suggestions.innerHTML = "";
            });
            suggestions.appendChild(li);
        });
    });

    // Attach listeners to the map container
    const mapContainer = document.getElementById("map");
    mapContainer.addEventListener("touchstart", e => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    });

    mapContainer.addEventListener("touchend", e => {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    });

});
