


import os
os.chdir('D:/ENEA_CAS_WORK/BRESCIA')
os.getcwd()

from math import radians, cos, sin, asin, sqrt
from funcs_mapmatching import great_circle_track_node, great_circle_track
import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from collections import OrderedDict
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
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
import sqlalchemy as sal
import geopy.distance
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None  # default='warn'


import multiprocessing as mp
from multiprocessing import Process, freeze_support, Manager
from time import sleep
from collections import deque
from multiprocessing.managers import BaseManager
import contextlib
from multiprocessing import Manager
from multiprocessing import Pool

import dill as Pickle
from joblib import Parallel, delayed
from joblib.externals.loky import set_loky_pickler
set_loky_pickler('pickle')
from multiprocessing import Pool,RLock

# today date
today = date.today()
today = today.strftime("%b-%d-%Y")



##################################################
### -------- Codifica stile guida -------- #######
##################################################

### Frenata longitudinale brusca: 184  (con Accelerometro)
### Accelerazione longitudinale brusca: 185 (con Accelerometro)
### Frenata longitudinale brusca: 188  (con GNSS)
### Accelerazione longitudinale brusca: 189 (con GNSS)

###----- BRESCIA ----#########
## connect to DB
conn_HAIG = db_connect.connect_HAIG_BRESCIA()
cur_HAIG = conn_HAIG.cursor()

## select all events in "frenata and accelerazione####
len_all_data_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               ''', conn_HAIG)

len_frenata_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               WHERE event = 184
                ''', conn_HAIG)

## percentuale di tracce GPS che hanno una frenata brusca
BRESCIA_perc_frenata_brusca = round( (len_frenata_viasat/len_all_data_viasat)*100, 3)
print("frenate brusche BRESCIA:", BRESCIA_perc_frenata_brusca)


### ----- ROMA ------ ########
## select all events in "frenata and accelerazione####

## connect to DB
conn_HAIG = db_connect.connect_HAIG_ROMA()
cur_HAIG = conn_HAIG.cursor()

## select all events in "frenata and accelerazione####
len_all_data_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               ''', conn_HAIG)

len_frenata_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               WHERE event = 184 
                ''', conn_HAIG)

## percentuale di tracce GPS che hanno una frenata brusca
ROMA_perc_frenata_brusca = round( (len_frenata_viasat/len_all_data_viasat)*100, 3)
print("frenate brusche ROMA:",ROMA_perc_frenata_brusca)


### ---- SALERNO ---- ########
## select all events in "frenata and accelerazione####

## connect to DB
conn_HAIG = db_connect.connect_HAIG_SALERNO()
cur_HAIG = conn_HAIG.cursor()

## select all events in "frenata and accelerazione####
len_all_data_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               ''', conn_HAIG)

len_frenata_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               WHERE event = 184
                ''', conn_HAIG)

## percentuale di tracce GPS che hanno una frenata brusca
SALERNO_perc_frenata_brusca = round( (len_frenata_viasat/len_all_data_viasat)*100, 3)
print("frenate brusche SALERNO:", SALERNO_perc_frenata_brusca)


### ---- CATANIA ---- #########
## select all events in "frenata and accelerazione####

## connect to DB
conn_HAIG = db_connect.connect_HAIG_CATANIA()
cur_HAIG = conn_HAIG.cursor()

## select all events in "frenata and accelerazione####
len_all_data_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               ''', conn_HAIG)

len_frenata_viasat = pd.read_sql_query(''' 
               SELECT count(*) FROM dataraw
               WHERE event = 184
                ''', conn_HAIG)

## percentuale di tracce GPS che hanno una frenata brusca
CATANIA_perc_frenata_brusca = round( (len_frenata_viasat/len_all_data_viasat)*100, 3)
print("frenate brusche CATANIA:", CATANIA_perc_frenata_brusca)


print("frenate brusche ROMA:",ROMA_perc_frenata_brusca['count'].iloc[0], "%", sep='')
print("frenate brusche CATANIA:", CATANIA_perc_frenata_brusca['count'].iloc[0], "%", sep='')
print("frenate brusche BRESCIA:", BRESCIA_perc_frenata_brusca['count'].iloc[0], "%", sep='')
print("frenate brusche SALERNO:", SALERNO_perc_frenata_brusca['count'].iloc[0], "%", sep='')

