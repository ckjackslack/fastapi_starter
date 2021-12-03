import folium
import random
import json
import requests

# additional = {
#     'tiles': 'Stamen Terrain', 'zoom_start': 7
# }
# location1 = [45.5236, -122.6750]
# location2 = [45.372, -121.6972]
# location3 = [46.8527, -121.7649]
# location4 = [46.3014, -123.7390]
# m = folium.Map(location = location4, **additional)
# tooltip = 'Click me!'
# folium.Marker([45.3288, -121.6625],
#     popup = '<i>Mt. Hood Meadows</i>',
#     tooltip = tooltip
# ).add_to(m)
# folium.Marker([45.3311, -121.7113],
#     popup = '<b>Timberline Lodge</b>',
#     tooltip = tooltip
# ).add_to(m)
# icon = random.choice([
#     {'icon': 'cloud'},
#     {'color': 'green'},
#     {'color': 'red', 'icon': 'info-sign'}
# ])
# folium.Marker([45.3300, -121.6823],
#     popup = '<b>Some other location</b>',
#     icon = folium.Icon(**icon),
# ).add_to(m)
# folium.Circle(radius = 100, location = [45.5244, -122.6699],
#     popup = 'The Waterfront', color = 'crimson', fill = False).add_to(m)
# folium.Circle(radius = 50, location = [45.5215, -122.6261],
#     popup = 'Laurelhurst Park', color = '#3186cc', fill = True,
#     fill_color = '#3186cc').add_to(m)
# m.add_child(folium.LatLngPopup())
# folium.Marker([46.8354, -121.7325], popup = 'Camp Muir').add_to(m)
# m.add_child(folium.ClickForMarker(popup = 'Waypoint'))
url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data"
# vis = json.loads(requests.get(f"{url}/vis2.json").text)
# folium.Marker(
#     location = [46.216, -124.1280],
#     popup = folium.Popup(max_width = 450).add_child(
#         folium.Vega(vis, width = 450, height = 250)
#     ),
# ).add_to(m)

antarctic_ice_edge = f"{url}/antarctic_ice_edge.json"
antarctic_ice_shelf_topo = f"{url}/antarctic_ice_shelf_topo.json"

m = folium.Map(
    location = [-59.1759, -11.6016],
    tiles = 'cartodbpositron',
    zoom_start = 2,
)
folium.GeoJson(antarctic_ice_edge, name = 'geojson').add_to(m)
folium.TopoJson(
    json.loads(requests.get(antarctic_ice_shelf_topo).text),
    'objects.antarctic_ice_shelf',
    name = 'topojson',
).add_to(m)
folium.LayerControl().add_to(m)
m.save('index.html')

# https://python-visualization.github.io/folium/quickstart.html