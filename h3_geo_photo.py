from collections import defaultdict
from typing import Dict, List
import h3.api.basic_str as h3
import folium
import geopandas as gpd
from shapely.geometry import Polygon, Point
import math

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

def visualize_hexagons(hexagons: Dict[str, int], folium_map=None):
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
        polylines.append([polyline, fade_blue_to_red(float(value)/float(max_value))])
    
    if folium_map is None:
        m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
    else:
        m = folium_map

    for polyline, color in polylines:
        my_PolyLine=folium.Polygon(locations=polyline,weight=1  ,color=color, fill_color=color, fill_opacity=0.2) 
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

    hex_counts: Dict[str, float] = defaultdict(float)

    with open("data/photos_latlong.csv", "r") as f:
        lines = f.readlines()
        for line in lines[1:]:
            lat, lon = [float(x) for x in line.strip().split(",")]
            h3_address = h3.latlng_to_cell(lat, lon, 7)
            hex_counts[h3_address] = 1

    new_hex_counts = hex_counts.copy()
    for h3_address in hex_counts.keys():
        h3_address_center = h3.cell_to_latlng(h3_address)
        for hex in h3.grid_disk(h3_address, 10):
            hex_center = h3.cell_to_latlng(hex)
            distance = h3.great_circle_distance(hex_center, h3_address_center)
            new_hex_counts[hex] += 1.0/(distance + 1)


    hex_counts = new_hex_counts
    in_boulder_hexes = {}
    for h3_address in hex_counts.keys():
        polyline = h3.cells_to_geo([h3_address])['coordinates'][0]
        #polyline = [[p[1], p[0]] for p in polyline]
        hex_boundary = Polygon(polyline)
        if boulder_boundary.contains(hex_boundary.centroid):
            in_boulder_hexes[h3_address] = hex_counts[h3_address]


    m = visualize_hexagons(in_boulder_hexes, folium_map=None)
    html_string = m.get_root().render()
    with open("ring_dx.html", "w") as f:
        f.write(html_string)

if __name__ == "__main__":
    load_points()