let apiKey = null;
let baseUrl = null;
let map = null;
let markers = [];
let currentLat = 25.2048;
let currentLng = 55.2708;
let score = 0;
let collectedPlaces = [];

async function initApi() {
    if (window.pywebview) {
        apiKey = await window.pywebview.api.get_api_key();
        baseUrl = await window.pywebview.api.get_base_url();

        if (!apiKey || !baseUrl) { // If data is falsy (e.g., null, undefined, 0, false, empty string)
        throw new Error("api key or url missing");
      }

        currentLat = window.pywebview.api.current_lat;
        currentLng = window.pywebview.api.current_lng;
    }
}

async function fetchPlaces(lat, lng) {

    try {
        // Make sure lat/lng are floats
        lat = parseFloat(lat);
        lng = parseFloat(lng);

        if (isNaN(lat) || isNaN(lng)) {
            console.error("Invalid coordinates:", lat, lng);
            return;
        }

        const url = `${baseUrl}?lat=${lat}&lng=${lng}&radius=800&limit=20`;
        console.log("Fetching:", url);

        const resp = await fetch(url, {
            headers: {
                "x-api-key": apiKey,
                "Accept": "application/json"
            }
        });

        if (!resp.ok) {
            const errText = await resp.text();
            console.error("Fetch error:", resp.status, errText);
            return;
        }

        const data = await resp.json();
        console.log("Raw API response:", data);

        // Handle different response shapes
        let places = [];
        if (Array.isArray(data)) {
            places = data;
        } else if (data && Array.isArray(data.features)) {
            places = data.features.map(f => ({
                lat: f.geometry?.coordinates[1],
                lng: f.geometry?.coordinates[0],
                name: f.properties?.name || "Unknown",
                cat: f.properties?.category || "unknown"
            }));
        }

        console.log("Processed places:", places);
        updateMarkers(places);

    } catch (err) {
        console.error("Exception in fetchNearbyPlaces:", err);
    }
}


function clearMarkers(){
    markers.forEach(m=>map.removeLayer(m));
    markers=[];
}

async function collectPlace(place){
  console.log("clicked!");
    if(window.pywebview){
        const result = await window.pywebview.api.collect_place(JSON.stringify(place));
        collectedPlaces = JSON.parse(result);
        score = collectedPlaces.reduce((s,p)=> s+(p.rare?25:10),0);
        document.getElementById("score").textContent = "Score: "+score;
        document.getElementById("message").textContent = `Collected: ${place.name||"Unnamed"} ${place.rare?"✨Rare +25!":"(+10)"}`;
        if(place.story) addStoryFragment(place.story);
        setTimeout(()=>{document.getElementById("message").textContent="";},2500);
    }
}

function addStoryFragment(fragment){
    const ul = document.getElementById("storyList");
    const li = document.createElement("li");
    li.textContent = fragment;
    ul.appendChild(li);
}

function updateMarkers(places){



    clearMarkers();
    const listDiv = document.getElementById("placesList");
    listDiv.innerHTML="";
    if(places.length===0){ listDiv.innerHTML="<p>No places nearby.</p>"; return; }

    places.forEach(feat=>{
        let lat,lng,name,cat;
        if(feat.geometry){
            lat = feat.geometry.coordinates[1]; lng=feat.geometry.coordinates[0];
            name = feat.properties?.name||"Unnamed";
            cat = feat.properties?.category||"Unknown";
        }else{
            lat = feat.lat; lng=feat.lon;
            name = feat.name||"Unnamed";
            cat = feat.category||"Unknown";
        }

        const isRare = Math.random()<0.1;
        const color = isRare?"gold":"blue";
        const story = isRare?"A rare event occurs here!":"You discover a new part of the city.";

        const marker = L.marker([lat,lng],{
            icon:L.icon({
                iconUrl:`https://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${color}`,
                iconSize:[21,34],
                iconAnchor:[10,34]
            })
        }).bindPopup(`<b>${name}</b><br>${cat}${isRare?" ✨Rare✨":""}`).addTo(map);
        marker.on('click',()=>collectPlace({lat,lng,name,cat,rare:isRare,story}));
        markers.push(marker);

        const div = document.createElement("div");
        div.className="place-item"; if(isRare) div.classList.add("rare");
        div.textContent = `${name} (${cat})${isRare?" ✨Rare✨":""}`;
        div.onclick = ()=>{map.setView([lat,lng],16); marker.openPopup(); collectPlace({lat,lng,name,cat,rare:isRare,story});};
        listDiv.appendChild(div);
    });
}

async function init(){
    await initApi();
    map = L.map('map').setView([currentLat,currentLng],15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);

    const initialPlaces = await fetchPlaces(currentLat,currentLng);
    updateMarkers(initialPlaces);

    map.on('click',async e=>{
        currentLat=e.latlng.lat;
        currentLng=e.latlng.lng;
        const newPlaces = await fetchPlaces(currentLat,currentLng);
        updateMarkers(newPlaces);
    });
}

init();
