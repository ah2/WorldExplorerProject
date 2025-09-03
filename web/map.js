let map = L.map('map').setView([25.276987, 55.296249], 12); // default: Dubai

// Tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Layer group for places
let markersLayer = L.layerGroup().addTo(map);

// Sidebar
let placesList = document.getElementById("places-list");

// Map click listener
map.on("click", function (e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    console.log("Map clicked at:", lat, lng); // debug

    fetch(`/api/places?lat=${lat}&lng=${lng}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Places API response:", data); // debug
            displayPlaces(data);
        })
        .catch(err => {
            console.error("Fetch error:", err);
            placesList.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
        });
});

function displayPlaces(data) {
    markersLayer.clearLayers();
    placesList.innerHTML = "";

    let features = data.features || data; // FeatureCollection or raw list
    if (!features || features.length === 0) {
        placesList.innerHTML = "<p>No places found here.</p>";
        return;
    }

    features.forEach((place, i) => {
        let coords = place.geometry?.coordinates;
        let props = place.properties || {};

        // Improved naming logic
        let name =
            props.name ||
            props.subcategory ||
            props.category ||
            `Unknown Place (${coords ? coords.join(", ") : "?"})`;

        if (coords && coords.length >= 2) {
            let [lng, lat] = coords;

            // Add marker
            let marker = L.marker([lat, lng]).addTo(markersLayer);
            marker.bindPopup(`<b>${name}</b>`);

            // Add to sidebar
            let div = document.createElement("div");
            div.className = "place";
            div.textContent = name;
            div.onclick = () => {
                map.setView([lat, lng], 16);
                marker.openPopup();
            };
            placesList.appendChild(div);
        }
    });
}

