// --- MAP INITIALIZATION ---
var southWest = L.latLng(-7.771000, 110.372000);
var northEast = L.latLng(-7.762000, 110.382000);
var bounds = L.latLngBounds(southWest, northEast);

var map = L.map('map', {
    center: [-7.766554, 110.376808],
    zoom: 18,
    minZoom: 15,
    maxZoom: 19,
    maxBounds: bounds,
    maxBoundsViscosity: 1.0,
    zoomControl: false
});
L.control.zoom({ position: 'bottomright' }).addTo(map);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

L.DomEvent.disableClickPropagation(document.getElementById('main-sidebar'));

// --- GLOBAL STATE ---
let allLocations = [];
let activeDestination = null;
let activeRouteLayer = null;
let mapMarkers = [];
let isSelectingStart = false;
let selectedStartNodeId = null;

const iconMap = {
    'mosque': '🕌', 'canteen': '🍜', 'bus_stop': '🚌',
    'sport': '🏀', 'laboratory': '🔬', 'auditorium': '🎭', 'building': '🏢'
};

// --- UI ELEMENTS ---
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const viewLocationCard = document.getElementById('view-location-card');
const viewDirections = document.getElementById('view-directions');
const routeSummaryBox = document.getElementById('route-summary');
const cardTitle = document.getElementById('card-title');
const cardCategory = document.getElementById('card-category');
const endNodeDisplay = document.getElementById('end-node-display');
const mainSidebar = document.getElementById('main-sidebar');
const minimizeBtn = document.getElementById('minimize-btn');
const startSearch = document.getElementById('start-search');
const startResults = document.getElementById('start-results');

// --- DATA INGESTION ---
fetch('/api/locations')
    .then(res => res.json())
    .then(data => {
        if (data.error) return;
        allLocations = data;

        data.forEach(location => {
            if (location.lat && location.lng) {
                let iconSymbol = iconMap[location.category] || iconMap['building'];
                let customIcon = L.divIcon({
                    className: 'custom-map-icon',
                    html: `<div style="font-size: 26px; filter: drop-shadow(0px 3px 3px rgba(0,0,0,0.3));">${iconSymbol}</div>`,
                    iconSize: [30, 30], iconAnchor: [15, 15]
                });

                var marker = L.marker([location.lat, location.lng], { icon: customIcon }).addTo(map);
                marker.bindTooltip(location.name, { direction: 'top', offset: [0, -15], className: 'map-tooltip' });

                marker.on('click', () => {
                    if (isSelectingStart) {
                        startSearch.value = location.name;
                        selectedStartNodeId = location.node_id;

                        if (activeDestination) {
                            calculateRoute(selectedStartNodeId, activeDestination.node_id);
                        }
                    } else {
                        selectLocation(location);
                    }
                });

                mapMarkers.push(marker);
            }
        });
    });

// --- MAIN SEARCH BAR LOGIC ---
searchInput.addEventListener('input', function () {
    const query = this.value.toLowerCase();
    searchResults.innerHTML = '';

    if (query.length < 1) {
        searchResults.style.display = 'none';
        return;
    }

    const filtered = allLocations.filter(loc => loc.name.toLowerCase().includes(query));

    if (filtered.length > 0) {
        searchResults.style.display = 'block';
        filtered.forEach(loc => {
            const li = document.createElement('li');
            let iconSymbol = iconMap[loc.category] || iconMap['building'];
            li.innerHTML = `<span class="icon">${iconSymbol}</span> ${loc.name}`;
            li.addEventListener('click', () => {
                selectLocation(loc);
                searchInput.value = loc.name;
                searchResults.style.display = 'none';
            });
            searchResults.appendChild(li);
        });
    } else {
        searchResults.style.display = 'none';
    }
});

// --- MINIMIZE PANEL LOGIC ---
minimizeBtn.addEventListener('click', () => {
    mainSidebar.classList.toggle('is-minimized');
    if (mainSidebar.classList.contains('is-minimized')) {
        minimizeBtn.innerText = '▲';
    } else {
        minimizeBtn.innerText = '▼';
    }
});

// --- FAST ACCESS LOGIC ---
document.querySelectorAll('.fast-access-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const targetId = parseInt(this.getAttribute('data-node'));
        const targetLocation = allLocations.find(loc => loc.node_id === targetId);

        if (targetLocation) {
            selectLocation(targetLocation);
        } else {
            console.error("Location data is loading or missing.");
        }
    });
});

// --- STATE TRANSITIONS ---
function selectLocation(loc) {
    activeDestination = loc;
    isSelectingStart = false;

    mainSidebar.classList.remove('is-minimized');
    minimizeBtn.innerText = '▼';

    viewDirections.style.display = 'none';
    routeSummaryBox.style.display = 'none';
    viewLocationCard.style.display = 'block';

    cardTitle.innerText = loc.name;
    cardCategory.innerText = (loc.category || 'building').replace('_', ' ');

    map.flyTo([loc.lat, loc.lng], 19, { animate: true, duration: 1.0 });

    if (activeRouteLayer) map.removeLayer(activeRouteLayer);
}

document.getElementById('btn-directions').addEventListener('click', () => {
    viewLocationCard.style.display = 'none';
    viewDirections.style.display = 'block';

    endNodeDisplay.value = "📍 " + activeDestination.name;
    isSelectingStart = true;

    startSearch.focus();
    startSearch.placeholder = "Search or click map...";
});

document.getElementById('btn-back').addEventListener('click', () => {
    viewDirections.style.display = 'none';
    routeSummaryBox.style.display = 'none';
    viewLocationCard.style.display = 'block';
    if (activeRouteLayer) map.removeLayer(activeRouteLayer);

    isSelectingStart = false;
    startSearch.value = "";
    selectedStartNodeId = null;
});

document.getElementById('btn-start-nav').addEventListener('click', () => {
    alert("Live GPS Navigation requires location permissions and HTTPS. For now, please use the Directions feature to preview paths.");
});

// --- START POINT SEARCH LOGIC ---
startSearch.addEventListener('input', function () {
    const query = this.value.toLowerCase();
    startResults.innerHTML = '';

    if (query.length < 1) {
        startResults.style.display = 'none';
        return;
    }

    const filtered = allLocations.filter(loc => loc.name.toLowerCase().includes(query));

    if (filtered.length > 0) {
        startResults.style.display = 'block';
        filtered.forEach(loc => {
            const li = document.createElement('li');
            let iconSymbol = iconMap[loc.category] || iconMap['building'];
            li.innerHTML = `<span class="icon">${iconSymbol}</span> ${loc.name}`;

            li.addEventListener('click', () => {
                startSearch.value = loc.name;
                selectedStartNodeId = loc.node_id;
                startResults.style.display = 'none';

                if (activeDestination) {
                    calculateRoute(selectedStartNodeId, activeDestination.node_id);
                }
            });
            startResults.appendChild(li);
        });
    } else {
        startResults.style.display = 'none';
    }
});

// --- ROUTING ENGINE ---
function calculateRoute(startId, endId) {
    if (!startId || !endId) return;

    const outputContainer = document.getElementById('route-output');
    routeSummaryBox.style.display = "block";

    outputContainer.innerHTML = `
        <div class="route-loading">
            <div class="loading-spinner"></div>
            Analyzing network pathways...
        </div>
    `;

    fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_node: startId, end_node: endId })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                outputContainer.innerHTML = "<div class='route-loading' style='color:#dc3545;'>❌ Route unavailable.</div>";
                return;
            }

            if (activeRouteLayer) map.removeLayer(activeRouteLayer);

            activeRouteLayer = L.polyline(data.coordinates, {
                color: '#1B4FD8', weight: 6, opacity: 0.9, lineCap: 'round', lineJoin: 'round'
            }).addTo(map);

            map.fitBounds(activeRouteLayer.getBounds(), { padding: [50, 50] });

            outputContainer.innerHTML = `
            <div class="route-stat-card">
                <div class="route-stat-icon">🚶‍♂️</div>
                <div>
                    <div class="route-stat-time">${data.time_string}</div>
                    <div class="route-stat-label">Estimated walk</div>
                </div>
            </div>
            <div class="route-distance-tag">
                <div class="route-distance-dot"></div>
                <span>Total distance: <b>${data.distance_meters} m</b></span>
            </div>
        `;
        })
        .catch(err => {
            outputContainer.innerHTML = "<div class='route-loading' style='color:#dc3545;'>⚠️ Network error. Please try again.</div>";
        });
}

// --- NAVBAR MODAL LOGIC ---
const aboutBtn = document.getElementById('nav-about-btn');
const modalOverlay = document.getElementById('about-modal-overlay');
const closeModalBtn = document.getElementById('close-modal-btn');

aboutBtn.addEventListener('click', () => {
    modalOverlay.classList.add('active');
});

closeModalBtn.addEventListener('click', () => {
    modalOverlay.classList.remove('active');
});

modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
    }
});