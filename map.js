var select = document.getElementById('categorySelect');
if(select){
    select.addEventListener('change', function(){
        var val = select.value;
        if(window.pywebview){ window.pywebview.api.on_category_change(val); }
    });
}

// Use Leaflet click event
var map = window.map; // Folium generates 'map' variable
if(map){
    map.on('click', function(e){
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        if(window.pywebview){ window.pywebview.api.on_click(lat, lng); }
    });
}
