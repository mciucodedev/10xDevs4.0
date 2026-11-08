(function () {
  var DEFAULT_ORIGIN = [50.0614, 19.9366];
  var origin = DEFAULT_ORIGIN.slice();
  var map = L.map('map').setView(DEFAULT_ORIGIN, 13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  var markers = L.layerGroup().addTo(map);
  var originMarker = L.circleMarker(origin, { radius: 8, color: '#c0392b' }).addTo(map);
  var form = document.getElementById('filters');
  var list = document.getElementById('results');
  var empty = document.getElementById('empty');
  var note = document.getElementById('origin-note');

  function params() {
    var p = new URLSearchParams();
    new FormData(form).forEach(function (v, k) { if (v !== '') p.append(k, v); });
    p.set('lat', origin[0]); p.set('lng', origin[1]);
    return p;
  }

  function popup(r) {
    var box = document.createElement('div');
    var a = document.createElement('a');
    a.href = r.url; a.textContent = r.name;
    box.appendChild(a);
    box.appendChild(document.createElement('br'));
    box.appendChild(document.createTextNode(ratingText(r)));
    return box;
  }

  function ratingText(r) {
    return r.rating_count ? r.avg_rating.toFixed(1) + '★ (' + r.rating_count + ')' : 'no ratings yet';
  }

  function render(data) {
    markers.clearLayers();
    list.replaceChildren();
    empty.hidden = data.count !== 0;
    data.results.forEach(function (r) {
      L.marker([r.lat, r.lng]).bindPopup(popup(r)).addTo(markers);
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = r.url; a.textContent = r.name;
      var meta = document.createElement('div');
      meta.className = 'meta';
      var open = r.is_open === true ? 'open now · ' : '';
      meta.textContent = open + r.distance_km.toFixed(1) + ' km · ' + ratingText(r) +
        (r.food_types.length ? ' · ' + r.food_types.join(', ') : '');
      li.appendChild(a); li.appendChild(meta);
      list.appendChild(li);
    });
  }

  function refresh() {
    fetch('/api/places/?' + params().toString())
      .then(function (res) { return res.json(); })
      .then(render)
      .catch(function () { empty.hidden = false; empty.textContent = 'Could not load places.'; });
  }

  function setOrigin(latlng, label) {
    origin = [latlng.lat, latlng.lng];
    originMarker.setLatLng(latlng);
    note.textContent = label;
    refresh();
  }

  map.on('click', function (e) { setOrigin(e.latlng, 'Reference point: pin on the map.'); });
  document.getElementById('use-location').addEventListener('click', function () {
    if (!navigator.geolocation) { note.textContent = 'Location is not available in this browser.'; return; }
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        var ll = L.latLng(pos.coords.latitude, pos.coords.longitude);
        map.setView(ll, 14);
        setOrigin(ll, 'Reference point: your location.');
      },
      function () { note.textContent = 'Location denied — click the map to set a reference point.'; }
    );
  });
  form.addEventListener('change', refresh);
  refresh();
})();
