let map;
let mapMarkers = [];
let routeLine;

function initMap() {
  map = L.map('map').setView([43.6532, -79.3832], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
}

function clearMapLayers() {
  mapMarkers.forEach(marker => marker.remove());
  mapMarkers = [];
  if (routeLine) {
    routeLine.remove();
    routeLine = null;
  }
}

function showDeliveryOnMap(delivery) {
  if (!map) return;

  clearMapLayers();

  const depot = [43.6532, -79.3832];
  const stop = [delivery.latitude, delivery.longitude];

  const depotMarker = L.marker(depot).addTo(map).bindPopup('Dispatch Hub');
  const stopMarker = L.marker(stop).addTo(map).bindPopup(delivery.address);

  mapMarkers.push(depotMarker, stopMarker);

  routeLine = L.polyline([depot, stop]).addTo(map);
  map.fitBounds(routeLine.getBounds(), { padding: [30, 30] });
}
