from collections import defaultdict
from email.policy import default
from typing import Dict, List
import h3.api.basic_str as h3
import folium
import geopandas as gpd
from shapely.geometry import Polygon, Point
import math

from tqdm import tqdm

def fade_blue_to_red(value):
    """
    Generate an RGB hex string that fades from blue to red based on a sigmoid-scaled value between 0 and 1.

    Parameters:
    - value (float): A float between 0 (blue) and 1 (red).

    Returns:
    - str: The RGB hex string representing the color.
    """
    # Clamp the value to the range [0, 1]
    value = max(0, min(1, value))

    # Apply sigmoid transformation
    # Adjust the sigmoid to center around 0.5 and make the transition sharper
    #adjusted_value = 1 / (1 + math.exp(-10 * (value - 0.5)))
    adjusted_value = value

    # Calculate red and blue values
    red = int(adjusted_value * 255.0)
    blue = int((1 - adjusted_value) * 255.0)

    # Format as a hex color string
    hex_color = f"#{red:02X}00{blue:02X}"
    return hex_color

def visualize_hexagons(hexagons: Dict[str, int], folium_map=None, color=None):
    """
    hexagons is a list of hexcluster. Each hexcluster is a list of hexagons.
    eg. [[hex1, hex2], [hex3, hex4]]
    """
    polylines = []
    lat = []
    lng = []
    max_value = max(hexagons.values())
    for hex, value in hexagons.items():
        polyline = h3.cells_to_geo([hex])['coordinates'][0]
        polyline = [[p[1], p[0]] for p in polyline]
        # flatten polygons into loops.
        #outlines = [loop for polygon in polygons for loop in polygon]
        #polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v:v[0],polyline))
        lng.extend(map(lambda v:v[1],polyline))
        polylines.append([polyline, color if color else fade_blue_to_red(float(value)/float(max_value)), float(value)/float(max_value) * 0.1])

    if folium_map is None:
        m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
    else:
        m = folium_map

    for polyline, color, opacity in polylines:
        my_PolyLine=folium.Polygon(locations=polyline, stroke=False, fill_color=color, fill_opacity=opacity)
        m.add_child(my_PolyLine)

    return m



def visualize_polygon(polyline, color):
    polyline.append(polyline[0])
    lat = [p[0] for p in polyline]
    lng = [p[1] for p in polyline]
    m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
    my_PolyLine=folium.Polygon(locations=polyline,weight=8,color=color, fill_color=color, fill_opacity=0.2)
    m.add_child(my_PolyLine)
    return m


def load_points():
    gdf = gpd.read_file("shapefiles/tl_2024_us_county.shp")
    boulder_county = gdf[gdf['NAME'] == 'Boulder']
    assert len(boulder_county) == 1
    boulder_boundary = boulder_county.geometry.iloc[0]

    location_list: Dict[str, list] = defaultdict(list)

    with open("data/photos_latlong.csv", "r") as f:
        lines = f.readlines()
        for line in tqdm(lines[1:]):
            lat, lon = [float(x) for x in line.strip().split(",")]
            child = (lat, lon)
            h3_address = h3.latlng_to_cell(lat, lon, 11)
            for _ in range(8):
                location_list[h3_address].append(child)
                child = h3_address
                h3_address = h3.cell_to_parent(h3_address)

    m = visualize_hexagons({k: 1 for k, v in location_list.items()}, folium_map=None)
    """

    new_hex_counts = location_tree.copy()

    for h3_address in tqdm(location_tree.keys()):
        h3_address_center = h3.cell_to_latlng(h3_address)
        for hex in h3.grid_disk(h3_address, 10):
            hex_center = h3.cell_to_latlng(hex)
            new_hex_counts[hex] += 0


    location_tree = new_hex_counts
    in_boulder_hexes = {}
    for h3_address in tqdm(location_tree.keys()):
        polyline = h3.cells_to_geo([h3_address])['coordinates'][0]
        hex_boundary = Polygon(polyline)
        if boulder_boundary.contains(hex_boundary.centroid):
            in_boulder_hexes[h3_address] = location_tree[h3_address]

    in_boulder_locs = [h3.cell_to_latlng(hex) for hex in in_boulder_hexes if in_boulder_hexes[hex] > 0]

    min_distances = {}
    for hex in tqdm(in_boulder_hexes):
        hex_center = h3.cell_to_latlng(hex)
        min_distance = min([h3.great_circle_distance(hex_center, other_hex) for other_hex in in_boulder_locs])
        min_distances[hex] = min_distance

    max_min_distance = max(min_distances.values())
    for hex, min_distance in min_distances.items():
        in_boulder_hexes[hex] = 1.0 - min_distance / max_min_distance

    m = visualize_hexagons(in_boulder_hexes, folium_map=None)

    smallest_hex = min(in_boulder_hexes, key=in_boulder_hexes.get)
    print(h3.cell_to_latlng(smallest_hex))
    largest_hex = max(in_boulder_hexes, key=in_boulder_hexes.get)
    m = visualize_hexagons({smallest_hex: 1, largest_hex: 1}, folium_map=m, color="green")
    """
    html_string = m.get_root().render()
    with open("ring_dx.html", "w") as f:
        f.write(html_string)

if __name__ == "__main__":
    load_points()
