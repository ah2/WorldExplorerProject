let map, playerLat, playerLng;
let playerMarker;
let allMarkers = [];
let lastFetch = {lat: null, lng: null};
const fetchDistance = 2000; // meters before fetching new markers
const moveSpeed = 0.0015;   // adjust for map zoom

// Player icon
const playerIcon = L.icon({
    iconUrl: '/static/player.svg',
    iconSize: [32,32],
    iconAnchor: [16,16]
});

// Initialize map
function initMap(lat,lng){
    map = L.map("map").setView([lat,lng],13);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19}).addTo(map);

    // Add player marker
    playerMarker = L.marker([lat,lng], {icon: playerIcon}).addTo(map);

    // Set initial fetch
    lastFetch.lat = lat;
    lastFetch.lng = lng;
    loadMarkers(lat,lng);
}

// Load markers from API
function loadMarkers(lat,lng){
    fetch(`/api/move?lat=${lat}&lng=${lng}`)
    .then(r=>r.json())
    .then(data=>{
        if(data.error) console.warn(data.error);
        const features = data.places || [];
        features.forEach(place=>{
            const coords = place.geometry?.coordinates;
            const props = place.properties || {};
            const name = props.name || props.subcategory || props.category || "Unknown";
            const category = props.category || "place";

            if(coords && coords.length>=2){
                const [lng,lat] = coords;
                const marker = L.marker([lat,lng]).addTo(map);
                marker.bindPopup(`<b>${name}</b><br>+10 Bonus Points!`);
                marker.on('click', ()=>{
                    // Example: award bonus points
                    alert(`You visited ${name} and earned 10 points!`);
                });
                allMarkers.push(marker);

                // Add to sidebar
                const div = document.createElement("div");
                div.className = "place";
                div.textContent = name;
                div.onclick = ()=>{ map.setView([lat,lng],16); marker.openPopup(); };
                document.getElementById("places-list").appendChild(div);
            }
        });
    })
    .catch(err=>{
        console.error("Failed to load markers:", err);
    });
}

// Check if player moved far enough to fetch new markers
function checkFetch(){
    if(lastFetch.lat === null) return;
    const dist = map.distance([playerLat,playerLng],[lastFetch.lat,lastFetch.lng]);
    if(dist > fetchDistance){
        lastFetch.lat = playerLat;
        lastFetch.lng = playerLng;
        loadMarkers(playerLat,playerLng);
    }
}

// Handle WASD / arrow keys
window.addEventListener("keydown", function(e){
    if(!playerMarker) return;
    let lat = playerMarker.getLatLng().lat;
    let lng = playerMarker.getLatLng().lng;

    switch(e.key){
        case "ArrowUp":
        case "w":
        case "W":
            lat += moveSpeed;
            break;
        case "ArrowDown":
        case "s":
        case "S":
            lat -= moveSpeed;
            break;
        case "ArrowLeft":
        case "a":
        case "A":
            lng -= moveSpeed;
            break;
        case "ArrowRight":
        case "d":
        case "D":
            lng += moveSpeed;
            break;
    }

    playerLat = lat;
    playerLng = lng;
    playerMarker.setLatLng([lat,lng]);
    map.setView([lat,lng]);
    checkFetch();
});

// Start Adventure button
window.addEventListener("DOMContentLoaded", ()=>{
    document.getElementById("start-btn").addEventListener("click", ()=>{
        const val = document.getElementById("city-select").value.split(",");
        playerLat = parseFloat(val[1]);
        playerLng = parseFloat(val[2]);

        document.getElementById("city-select-screen").style.display = "none";
        document.getElementById("app").style.display = "flex";

        initMap(playerLat,playerLng);
    });
});
