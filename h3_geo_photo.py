from collections import defaultdict
from typing import Dict, List
from h3 import h3
import folium

def visualize_hexagons(hexagons, color="red", folium_map=None):
    """
    hexagons is a list of hexcluster. Each hexcluster is a list of hexagons. 
    eg. [[hex1, hex2], [hex3, hex4]]
    """
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v:v[0],polyline))
        lng.extend(map(lambda v:v[1],polyline))
        polylines.append(polyline)
    
    if folium_map is None:
        m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
    else:
        m = folium_map
    for polyline in polylines:
        my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
        m.add_child(my_PolyLine)
    return m
    

def visualize_polygon(polyline, color):
    polyline.append(polyline[0])
    lat = [p[0] for p in polyline]
    lng = [p[1] for p in polyline]
    m = folium.Map(location=[sum(lat)/len(lat), sum(lng)/len(lng)], zoom_start=13, tiles='cartodbpositron')
    my_PolyLine=folium.PolyLine(locations=polyline,weight=8,color=color)
    m.add_child(my_PolyLine)
    return m

hex_counts: Dict[int, int] = defaultdict(int)

def ring_dx(lat:float, lon:float):
    h3_address = h3.geo_to_h3(lat, lon, 12) # lat, lng, hex resolution
    hex_center_coordinates = h3.h3_to_geo(h3_address) # array of [lat, lng]                                                                                                                  
    hex_boundary = h3.h3_to_geo_boundary(h3_address) # array of arrays of [lat, lng]                                                                                                                                                                                                                                                         
    m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[3]), color="purple")
    #m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[2]), color="blue", folium_map=m)
    #m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[1]), color="green", folium_map=m)
    #m = visualize_hexagons(list(h3.k_ring_distances(h3_address, 4)[0]), color = "red", folium_map=m)
    html_string = m.get_root().render()
    with open("ring_dx.html", "w") as f:
        f.write(html_string)

if __name__ == "__main__":
    with open("data/photos_latlong.csv", "r") as f:
        lines = f.readlines()
        for line in lines[1:]:
            lat, lon = line.strip().split(",")
            #h3_address = h3.geo_to_h3(lat, lon, 10)
            ring_dx(float(lat), float(lon))
            exit(0)
