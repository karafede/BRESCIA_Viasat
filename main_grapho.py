
############################
######### RUNS #############
############################
import os
from funcs_network_FK import graph
from funcs_network_FK import cost_assignment
from funcs_network_FK import roads_type_folium
from funcs_network_FK import centrality
# from query_db_viasat import viasat_map_data
from add_VIASAT_data import viasat_map_data
import osmnx as ox
import folium

# input name of City and Country
place_country = "Brescia, Italy"


road_type = ['motorway', 'motorway_link', 'secondary', 'primary', 'tertiary', 'residential',
             'unclassified', 'trunk', 'trunk_link', 'tertiary_link', 'secondary_link', 'service']

# roads = road_type.replace(', ', '|')
# filter = '["highway"~' + '"' + roads + '"' + "]"
distance = 110000 # distance from the center of the map (in meters)

# make grapho, save .graphml, save shapefile (node and edges) and get statistics (basic and extended)
###########################################
#### download OSM graph from the network ##
###########################################
network_city = graph(place_country, distance) # filter

# file_graphml = 'Catania__Italy_60km.graphml'
file_graphml = 'Brescia__Italy.graphml'
grafo = ox.load_graphml(file_graphml)
# ox.plot_graph(grafo)
gdf_nodes, gdf_edges = ox.graph_to_gdfs(grafo)
gdf_edges.to_csv('grapho_ROMA_70km_2021.csv')
gdf_edges.plot()

## make an iterative map

################################################################################
# create basemap BRESCIA (45.543465573267916, 10.21423540375533
ave_LAT = 45.543465573267916
ave_LON = 10.21423540375533
my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11, tiles='cartodbpositron')
#################################################################################

folium.GeoJson(
gdf_edges[['u','v','geometry']].to_json(),
    style_function=lambda x: {
        'fillColor': 'black',
        'color': 'black',
        'weight':  1,
        'fillOpacity': 1,
        },
highlight_function=lambda x: {'weight':3,
        'color':'blue',
        'fillOpacity':1
    },
    # fields to show
    tooltip=folium.features.GeoJsonTooltip(
        fields=['u', 'v']),
    ).add_to(my_map)

path = os.getcwd() + '\\viasat_data\\'
my_map.save(path + "grapho_edges_2021.html")


# assign weight and cost (==time) to the grapho
file_graphml = 'Brescia__Italy.graphml'
cost_assignment(file_graphml, place_country)


'''
# plot all the network on the map with folium
# load file graphml
Catania = ox.load_graphml('partial_OSM.graphml')
Catania = ox.plot_graph_folium(Catania, graph_map=None, popup_attribute=None, tiles='cartodbpositron', zoom=10,
                  fit_bounds=True, edge_width=1, edge_opacity=1)
Catania.save("partial_OSM.html")
'''


### select road type and make a map (to be used as base map for the viasat data)
file_graphml = 'Brescia__Italy.graphml'
my_map = roads_type_folium(file_graphml, road_type, place_country)


#####################################################################
##### ---- CENTRALITY ---------- ####################################
#####################################################################

## load graph with "cost".....
file_graphml = 'Catania_VIASAT_Italy_for_CENTRALITY_cost.graphml'

# edge centrality (make a map) (bc = betweenness centrality; cc = closeness centrality)
centrality(file_graphml, place_country, bc=True, cc=False)  # road_type

# OSM map & viasat data (make a map)
# !!! use the _cost.graphml
viasat_data = viasat_map_data(file_graphml, road_type, place_country)


