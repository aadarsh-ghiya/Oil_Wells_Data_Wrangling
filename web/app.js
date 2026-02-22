const statusEl = document.getElementById("status");
const popupEl = document.getElementById("popup");
const popupContentEl = document.getElementById("popup-content");
const popupCloserEl = document.getElementById("popup-closer");

const popupOverlay = new ol.Overlay({
  element: popupEl,
  autoPan: {
    animation: {
      duration: 250
    }
  }
});

const markerStyle = new ol.style.Style({
  image: new ol.style.Circle({
    radius: 6,
    fill: new ol.style.Fill({ color: "#dc2626" }),
    stroke: new ol.style.Stroke({ color: "#ffffff", width: 2 })
  })
});

const vectorSource = new ol.source.Vector();
const vectorLayer = new ol.layer.Vector({
  source: vectorSource
});

const map = new ol.Map({
  target: "map",
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    }),
    vectorLayer
  ],
  view: new ol.View({
    center: ol.proj.fromLonLat([-102, 47]),
    zoom: 6
  }),
  overlays: [popupOverlay]
});

popupCloserEl.onclick = function () {
  popupOverlay.setPosition(undefined);
  popupCloserEl.blur();
  return false;
};

map.on("singleclick", (event) => {
  const feature = map.forEachFeatureAtPixel(event.pixel, (candidate) => candidate);
  if (!feature) {
    popupOverlay.setPosition(undefined);
    return;
  }

  const wellData = feature.get("wellData");
  popupContentEl.innerHTML = buildPopupHtml(wellData);
  popupOverlay.setPosition(event.coordinate);
});

function buildPopupHtml(wellData) {
  const rows = Object.entries(wellData || {}).map(([key, value]) => {
    const label = toTitleCase(key.replace(/_/g, " "));
    const displayValue = value === null || value === undefined || value === "" ? "N/A" : String(value);
    return `<tr><th>${escapeHtml(label)}</th><td>${escapeHtml(displayValue)}</td></tr>`;
  });

  const title = (wellData && (wellData.well_name_clean || wellData.well_name)) || "Well Details";
  return `<h2 class="popup-title">${escapeHtml(title)}</h2>
    <table class="popup-table">${rows.join("")}</table>`;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function toTitleCase(text) {
  return text.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function readCoordinate(row, name) {
  const matchingKey = Object.keys(row).find((key) => key.toLowerCase() === name);
  return matchingKey ? Number.parseFloat(row[matchingKey]) : Number.NaN;
}

function isValidCoordinate(latitude, longitude) {
  return Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180;
}

async function loadWells() {
  try {
    const response = await fetch("api/wells.php");
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const payload = await response.json();
    const wells = Array.isArray(payload.wells) ? payload.wells : [];
    let markerCount = 0;

    wells.forEach((well) => {
      const latitude = readCoordinate(well, "latitude");
      const longitude = readCoordinate(well, "longitude");

      if (!isValidCoordinate(latitude, longitude)) {
        return;
      }

      const feature = new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude]))
      });
      feature.setStyle(markerStyle);
      feature.set("wellData", well);
      vectorSource.addFeature(feature);
      markerCount += 1;
    });

    if (markerCount > 0) {
      map.getView().fit(vectorSource.getExtent(), {
        padding: [30, 30, 30, 30],
        maxZoom: 12
      });
      statusEl.textContent = `Loaded ${wells.length} wells from MySQL. Displaying ${markerCount} map markers.`;
    } else {
      statusEl.textContent = `Loaded ${wells.length} wells from MySQL. No valid latitude/longitude values were found.`;
    }
  } catch (error) {
    statusEl.textContent = "Could not load well data from the API endpoint. Check MySQL config and Apache/PHP setup.";
    console.error(error);
  }
}

loadWells();
