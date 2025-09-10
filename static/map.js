


let map;
let playerMarker;
let currentMarkers;
let playerPos = { lat: 0, lng: 0 };
let discoveredPlaces = [];
const MOVE_STEP = 0.002; // smaller step = slower movement
const DISCOVERY_RADIUS = 0.005; // distance threshold to "discover" places
const TILE_SIZE = 0.1; // size of the grid cell in degrees
let loadedTiles = new Set(); // track loaded tiles


// Initialize map centered on player
function initMap(lat = 0, lng = 0) {
    if (map) {
        map.remove(); // Remove previous map instance
        map = null;
    }

    playerPos = { lat, lng };
    map = L.map('map').setView([lat, lng], 12);  // default view

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
        //maxZoom: 19
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

        // Call once when map initializes
    map.on("load", () => {
        loadVisibleTiles();
    });

    let tileLoadTimer;
    // Call whenever user pans or zooms
    map.on("moveend", () => {
        clearTimeout(tileLoadTimer);
        tileLoadTimer = setTimeout(() => {
            loadVisibleTiles();
        }, 300); // wait 300ms after movement stops
    });

    // Initial load of markers
    //loadVisibleTile();
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
    playerMarker.setLatLng([playerPos.lat, playerPos.lng],{ animate: true, duration: 0.25 });
        // Smoothly pan map to follow player
    map.panTo([playerPos.lat, playerPos.lng], {
        animate: true,
        duration: 0.25,   // seconds
        easeLinearity: 0.25
    });
    checkDiscoveries();
    loadVisibleTiles();
}

// ----------------------------
// TILE GRID LOGIC
// ----------------------------
function getTileKey(lat, lng) {
    const x = Math.floor(lng / TILE_SIZE);
    const y = Math.floor(lat / TILE_SIZE);
    return `${x},${y}`;
}

function getTileBounds(lat, lng) {
    const x = Math.floor(lng / TILE_SIZE);
    const y = Math.floor(lat / TILE_SIZE);
    const minLat = (lat - TILE_SIZE).toFixed(5);
    const maxLat = (lat + TILE_SIZE).toFixed(5);
    const minLon = (lng - TILE_SIZE).toFixed(5);
    const maxLon = (lng + TILE_SIZE).toFixed(5);
    return [minLon, minLat, maxLon, maxLat];
}

async function loadVisibleTiles() {
    const key = getTileKey(playerPos.lat, playerPos.lng);
    if (loadedTiles.has(key)) return; // already loaded
    loadedTiles.add(key);

    const [minLon, minLat, maxLon, maxLat] = getTileBounds(playerPos.lat, playerPos.lng);
    const bbox = `${minLon},${minLat},${maxLon},${maxLat}`;

    try {
        const res = await fetch(`/api/places?bbox=${bbox}`);
        const data = await res.json();

        renderMarkers(data);
    } catch (err) {
        console.error("Error loading tile:", err);
    }
}



function renderMarkers(data) {
    // keep markers in a dictionary by place ID
if (!window.currentMarkers) {
    window.currentMarkers = {};
}
    document.getElementById("places-list").innerHTML = "";

    // Make sure we loop correctly (some APIs return {features: []})
    const places = Array.isArray(data) ? data : (data.features || []);

    places.forEach(place => {
        const coords = place.geometry?.coordinates;
        const props = place.properties || {};
        if (!coords || coords.length < 2) return;

        const [lon, lat] = coords;
        const name = props.names?.primary || props.ext_name || "Unnamed Place";
        const id = place.id || props.id;  // use stable id if available
        
        if (!id) return;
        // Skip if we already rendered this place
        if (window.currentMarkers[id]) return;

        // Create marker
        const marker = L.marker([lat, lon])
            .addTo(map)
            .bindPopup(`<b>${name}</b><br>${props.categories?.primary || "Unknown"}`);
        window.currentMarkers[id] = marker;

        // Add sidebar entry
        const div = document.createElement("div");
        div.className = "place-item";
        div.innerHTML = `
            <strong>${name}</strong><br>
            <small>${props.addresses?.[0]?.freeform || ""}</small>
        `;
        div.addEventListener("click", () => {
            map.setView([lat, lon], 16);
            marker.openPopup();
        });
        document.getElementById("places-list").appendChild(div);
    });
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
    console.log("Discovered:", place.name, place.coords);
}

function placeMarkerPopup(place) {
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

    const userData = document.getElementById("user-data").dataset.user;
    const displayEl = document.getElementById("user-display");

    if (userData && userData.trim() !== "") {
        displayEl.textContent = `Logged in as: ${userData}`;
    } else {
        displayEl.textContent = "Logged in as: Guest";
    }


    if (btn) {
        // Start button calls backend
        btn.addEventListener("click", async () => {
            if (!selectedCity) return;

            const res = await fetch("/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(selectedCity)
            });
            const data = await res.json();
            if (data.lat && data.lng) {
                // update map here
                initMap(selectedCity.lat, selectedCity.lng); // reinit map at new city}

                // Preload surrounding tiles (current tile + neighbors)
                preloadSurroundingTiles(selectedCity.lat, selectedCity.lng);
            }
        });
    }


    const input = document.getElementById("city-input");
    const suggestionsEl = document.getElementById("suggestions");

    // On input, fetch & show city list
    let debounceTimer;
    input.addEventListener("input", e => {
        btn.disabled = true; // lock until selection
        selectedCity = null;

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
            const results = await searchCities(e.target.value);
            renderSuggestions(results, input);
        }, 300);
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


    let cities = [];

    async function loadCities() {
        try {
            const response = await fetch("/static/cities.json"); // or an API endpoint
            cities = await response.json();
        } catch (err) {
            console.error("Error loading cities:", err);
        }
    }

    // Fetch city candidates from Nominatim
    async function searchCities(query) {
        if (!query || query.length < 2) return [];
        //const url = `https://nominatim.openstreetmap.org/search?city=${encodeURIComponent(query)}&format=json&limit=5`;
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        return res.json();
    }

    // Render suggestions list
    function renderSuggestions(cities, input) {
        suggestionsEl.innerHTML = "";
        cities.forEach(city => {
            const li = document.createElement("li");
            li.textContent = city.display_name;
            li.addEventListener("click", () => {
                input.value = city.display_name;
                selectedCity = {
                    name: city.display_name,
                    lat: parseFloat(city.lat),
                    lng: parseFloat(city.lon)
                };
                suggestionsEl.innerHTML = "";
                btn.disabled = false; // enable start
            });
            suggestionsEl.appendChild(li);
        });
    }

    // --- Preload surrounding tiles (3x3 grid around city) ---
    function preloadSurroundingTiles(lat, lng) {
        const centerX = Math.floor(lng / TILE_SIZE);
        const centerY = Math.floor(lat / TILE_SIZE);

        for (let dx = -1; dx <= 1; dx++) {
            for (let dy = -1; dy <= 1; dy++) {
                const tileLat = (centerY + dy) * TILE_SIZE;
                const tileLng = (centerX + dx) * TILE_SIZE;
                loadVisibleTiles(tileLat, tileLng);
            }
        }
    }


    mapContainer.addEventListener("touchstart", e => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    });
    mapContainer.addEventListener("touchend", e => {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    });
}

)
