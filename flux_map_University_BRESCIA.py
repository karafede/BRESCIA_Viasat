
import os
os.chdir('D:/ENEA_CAS_WORK/BRESCIA')
os.getcwd()

import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
import folium
import osmnx as ox
import networkx as nx
import math
import momepy
from funcs_network_FK import roads_type_folium
from shapely import geometry
from shapely.geometry import Point, Polygon
import psycopg2
import db_connect
import datetime
from datetime import datetime
from datetime import date
from datetime import datetime
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import *
import sqlalchemy as sal
import geopy.distance
import momepy
from shapely import wkb


# today date
today = date.today()
today = today.strftime("%b-%d-%Y")

os.chdir('D:/ENEA_CAS_WORK/BRESCIA')
os.getcwd()

########################################################################################
########## DATABASE OPERATIONS #########################################################
########################################################################################

# connect to new DB to be populated with Viasat data after route-check
conn_HAIG = db_connect.connect_HAIG_Viasat_BS()
cur_HAIG = conn_HAIG.cursor()


# Function to generate WKB hex
def wkb_hexer(line):
    return line.wkb_hex

## function to transform Geometry from text to LINESTRING
def wkb_tranformation(line):
   return wkb.loads(line.geom, hex=True)

# Create an SQL connection engine to the output DB
engine = sal.create_engine('postgresql://postgres:superuser@192.168.132.18:5432/HAIG_Viasat_BS')

## load EDGES from OSM
gdf_edges = pd.read_sql_query('''
                            SELECT u,v, length, geom
                            FROM "OSM_edges" ''',conn_HAIG)
gdf_edges['geometry'] = gdf_edges.apply(wkb_tranformation, axis=1)
gdf_edges.drop(['geom'], axis=1, inplace= True)
gdf_edges = gpd.GeoDataFrame(gdf_edges)


## eventually....remove duplicates
gdf_edges.drop_duplicates(['u', 'v'], inplace=True)
# gdf_edges.plot()



viasat_data_march_2019 = pd.read_sql_query('''
                           SELECT  
                              "mapmatching_UNIBS_march_2019".u, "mapmatching_UNIBS_march_2019".v,
                               "mapmatching_UNIBS_march_2019".timedate, "mapmatching_UNIBS_march_2019".mean_speed, 
                               "mapmatching_UNIBS_march_2019".idtrace, "mapmatching_UNIBS_march_2019".sequenza,
                               "mapmatching_UNIBS_march_2019".idtrajectory,
                                dataraw.idterm, dataraw.vehtype
                              FROM "mapmatching_UNIBS_march_2019"
                              LEFT JOIN dataraw 
                                          ON "mapmatching_UNIBS_march_2019".idtrace = dataraw.id  
                                          /*WHERE date(mapmatching_2019.timedate) = '2019-02-25' AND*/
                                           WHERE EXTRACT(MONTH FROM "mapmatching_UNIBS_march_2019".timedate) = '03'
                                          /*WHERE dataraw.vehtype::bigint = 1*/
                                          ''', conn_HAIG)



viasat_data_november_2019 = pd.read_sql_query('''
                           SELECT  
                              "mapmatching_UNIBS_november_2019".u, "mapmatching_UNIBS_november_2019".v,
                               "mapmatching_UNIBS_november_2019".timedate, "mapmatching_UNIBS_november_2019".mean_speed, 
                               "mapmatching_UNIBS_november_2019".idtrace, "mapmatching_UNIBS_november_2019".sequenza,
                               "mapmatching_UNIBS_november_2019".idtrajectory,
                                dataraw.idterm, dataraw.vehtype
                              FROM "mapmatching_UNIBS_november_2019"
                              LEFT JOIN dataraw 
                                          ON "mapmatching_UNIBS_november_2019".idtrace = dataraw.id  
                                          /*WHERE date(mapmatching_2019.timedate) = '2019-02-25' AND*/
                                           WHERE EXTRACT(MONTH FROM "mapmatching_UNIBS_november_2019".timedate) = '11'
                                          /*WHERE dataraw.vehtype::bigint = 1*/
                                          ''', conn_HAIG)



viasat_data_march_2019_only_UNIBS = pd.read_sql_query('''
                                   SELECT  
                                      "mapmatching_ONLY_UNIBS_march_2019".u, "mapmatching_ONLY_UNIBS_march_2019".v,
                                       "mapmatching_ONLY_UNIBS_march_2019".timedate, "mapmatching_ONLY_UNIBS_march_2019".mean_speed, 
                                       "mapmatching_ONLY_UNIBS_march_2019".idtrace, "mapmatching_ONLY_UNIBS_march_2019".sequenza,
                                       "mapmatching_ONLY_UNIBS_march_2019".idtrajectory,
                                        dataraw.idterm, dataraw.vehtype
                                      FROM "mapmatching_ONLY_UNIBS_march_2019"
                                      LEFT JOIN dataraw 
                                                  ON "mapmatching_ONLY_UNIBS_march_2019".idtrace = dataraw.id  
                                                  /*WHERE date(mapmatching_2019.timedate) = '2019-02-25' AND*/
                                                   WHERE EXTRACT(MONTH FROM "mapmatching_ONLY_UNIBS_march_2019".timedate) = '03'
                                                  /*WHERE dataraw.vehtype::bigint = 1*/
                                                  ''', conn_HAIG)


### get counts for all edges ########
# all_data = viasat_data_march_2019[['u','v']]
# all_data = viasat_data_november_2019[['u','v']]
all_data = viasat_data_march_2019_only_UNIBS[['u','v']]
all_counts_uv = all_data.groupby(all_data.columns.tolist(), sort=False).size().reset_index().rename(columns={0:'counts'})

########################################################
##### build the map ####################################

all_counts_uv = pd.merge(all_counts_uv, gdf_edges, on=['u', 'v'], how='left')
## remove none values
all_counts_uv = all_counts_uv.dropna()
all_counts_uv = gpd.GeoDataFrame(all_counts_uv)
all_counts_uv.drop_duplicates(['u', 'v'], inplace=True)
# all_counts_uv.plot()

## rescale all data by an arbitrary number
all_counts_uv["scales"] = (all_counts_uv.counts/max(all_counts_uv.counts)) * 7


####################################################################################
### create basemap (Brescia)
ave_LAT = 45.56499
ave_LON = 10.23051
my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11, tiles='cartodbpositron')
####################################################################################


folium.GeoJson(
all_counts_uv[['u','v', 'counts', 'scales', 'geometry']].to_json(),
    style_function=lambda x: {
        'fillColor': 'red',
        'color': 'red',
        'weight':  x['properties']['scales'],
        'fillOpacity': 1,
        },
highlight_function=lambda x: {'weight':3,
        'color':'blue',
        'fillOpacity':1
    },
    # fields to show
    tooltip=folium.features.GeoJsonTooltip(
        fields=['u', 'v', 'counts']),
    ).add_to(my_map)

path = 'D:/ENEA_CAS_WORK/BRESCIA/viasat_data/'
my_map.save(path + "March_trip_CARS_only_UNIBS.html")
# my_map.save(path + "March_CARS_traffic_UNIBS.html")
# my_map.save(path + "November_CARS_traffic_UNIBS.html")


