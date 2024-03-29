
import os
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

########################################################################################
########## DATABASE OPERATIONS #########################################################
########################################################################################

# connect to new DB to be populated with Viasat data after route-check
conn_HAIG = db_connect.connect_HAIG_Viasat_BS()
cur_HAIG = conn_HAIG.cursor()

# Function to generate WKB hex
def wkb_hexer(line):
    return line.wkb_hex

# Create an SQL connection engine to the output DB
engine = sal.create_engine('postgresql://postgres:superuser@10.0.0.1:5432/HAIG_Viasat_BS')


## create extension postgis on the database HAIG_Viasat_CT  (only one time)
# erase existing table
# cur_HAIG.execute("DROP TABLE IF EXISTS routecheck_november_2019 CASCADE")
# conn_HAIG.commit()


# get all ID terminal of Viasat data
all_VIASAT_IDterminals = pd.read_sql_query(
    ''' SELECT *
        FROM public.obu''', conn_HAIG)
all_VIASAT_IDterminals['idterm'] = all_VIASAT_IDterminals['idterm'].astype('Int64')
all_VIASAT_IDterminals['anno'] = all_VIASAT_IDterminals['anno'].astype('Int64')
all_VIASAT_IDterminals['portata'] = all_VIASAT_IDterminals['portata'].astype('Int64')

# make a list of all IDterminals (GPS ID of Viasata data) each ID terminal (track) represent a distinct vehicle
all_ID_TRACKS = list(all_VIASAT_IDterminals.idterm.unique())

# track_ID = '4033118'  vehtype = '1'
# all_ID_TRACKS = ['track_ID']
# track_ID = '3297372'


def func(arg):
    last_track_idx, track_ID = arg

## to be used when the query stop. Start from the last saved index
# for last_track_idx, track_ID in enumerate(all_ID_TRACKS):
    print(track_ID)
    track_ID = str(track_ID)
    # print('VIASAT GPS track:', track_ID)
    viasat_data = pd.read_sql_query('''
                SELECT * FROM public.dataraw 
                WHERE idterm = '%s' ''' % track_ID, conn_HAIG)
    # remove duplicate GPS tracks (@ same position)
    viasat_data.drop_duplicates(['latitude', 'longitude'], inplace=True)
    # sort data by timedate:
    viasat_data['timedate'] = viasat_data['timedate'].astype('datetime64[ns]')
    # sort by 'timedate'
    viasat_data = viasat_data.sort_values('timedate')

    # remove viasat data with 'progressive' == 0
    # viasat_data = viasat_data[viasat_data['progressive'] != 0]
    # remove viasat data with 'speed' == 0
    # viasat_data = viasat_data[viasat_data['speed'] != 0]
    # select only rows with different reading of the odometer (vehicle is moving on..)
    # viasat_data.drop_duplicates(['progressive'], inplace= True)
    # remove viasat data with 'panel' == 0  (when the car does not move, the engine is OFF)
    # viasat_data = viasat_data[viasat_data['panel'] != 0]
    # remove data with "speed" ==0  and "odometer" != 0 AT THE SAME TIME!
    viasat_data = viasat_data[~((viasat_data['progressive'] != 0) & (viasat_data['speed'] == 0))]
    # select only VIASAT point with accuracy ("grade") between 1 and 22
    viasat_data = viasat_data[(1 <= viasat_data['grade']) & (viasat_data['grade'] <= 15)]
    # viasat_data = viasat_data[viasat_data['direction'] != 0]
    if len(viasat_data) == 0:
        print('============> no VIASAT data for that day ==========')

########################################################################################
########################################################################################
########################################################################################

    # if len(viasat_data) > 5  and len(viasat_data) < 90:
    if (len(viasat_data) > 5) and sum(viasat_data.progressive)> 0:  # <----
        fields = ["id", "longitude", "latitude", "progressive", 'panel', 'grade', "timedate", "speed", "vehtype"]
        # viasat = pd.read_csv(viasat_data, usecols=fields)
        viasat = viasat_data[fields]
        ## add a field for "anomalies"
        viasat['anomaly'] = '0123456'
        # transform "datetime" into seconds
        # separate date from time
        # transform object "datetime" into  datetime format
        viasat['timedate'] = viasat['timedate'].astype('datetime64[ns]')
        base_time = datetime(1970, 1, 1)
        viasat['totalseconds'] = pd.to_datetime(viasat['timedate'], format='% M:% S.% f')
        viasat['totalseconds'] = pd.to_datetime(viasat['totalseconds'], format='% M:% S.% f') - base_time
        viasat['totalseconds'] = viasat['totalseconds'].dt.total_seconds()
        viasat['totalseconds'] = viasat.totalseconds.astype('int')
        # date
        viasat['date'] = viasat['timedate'].apply(lambda x: x.strftime("%Y-%m-%d"))
        # date and month
        viasat['year_month'] = viasat['timedate'].apply(lambda x: x.strftime("%Y-%m"))
        # year
        viasat['year'] = viasat['timedate'].apply(lambda x: x.strftime("%Y"))
        # hour
        viasat['hour'] = viasat['timedate'].apply(lambda x: x.hour)
        # minute
        viasat['minute'] = viasat['timedate'].apply(lambda x: x.minute)
        # seconds
        viasat['seconds'] = viasat['timedate'].apply(lambda x: x.second)

        #### select only YEAR 2019 ######
        #################################
        # viasat = viasat[viasat.year_month == '2019-03']  ## March
        viasat = viasat[viasat.year_month == '2019-11']  ## November
        if len(viasat) > 0:
            viasat = viasat.sort_values('timedate')
            # make one field with time in seconds
            viasat['path_time'] = viasat['hour'] * 3600 + viasat['minute'] * 60 + viasat['seconds']
            viasat = viasat.reset_index()
            # make difference in totalaseconds from the start of the first trip of each TRACK_ID (need this to compute trips)
            viasat['path_time'] = viasat['totalseconds'] - viasat['totalseconds'][0]
            viasat = viasat[["id", "longitude", "latitude", "progressive", "path_time", "totalseconds",
                             "panel", "grade", "speed", "hour", "timedate", "vehtype", "anomaly"]]
            viasat['last_totalseconds'] = viasat.totalseconds.shift()   # <-------
            viasat['last_progressive'] = viasat.progressive.shift()  # <-------
            ## set nan values to -1
            viasat.last_totalseconds = viasat.last_totalseconds.fillna(-1)   # <-------
            viasat.last_progressive = viasat.last_progressive.fillna(-1)  # <-------
            ## get only VIASAT data where difference between two consecutive points is > 600 secx (10 minutes)
            ## this is to define the TRIP after a 'long' STOP time
            viasat1 = viasat
            ## compute difference in seconds between two consecutive tracks
            diff_time = viasat.path_time.diff()
            diff_time = diff_time.fillna(0)
            VIASAT_TRIPS_by_ID = pd.DataFrame([])
            row = []
            ## define a list with the starting indices of each new TRIP
            for i in range(len(diff_time)):
                if diff_time.iloc[i] >= 600:
                    row.append(i)
            # get next element of the list row
            # row_next = [x+1 for x in row]
            # row_previous = [x-1 for x in row]
            if len(row)>0:
                row.append("end")
                # split Viasat data by TRIP (for a given ID..."idterm")
                for idx, j in enumerate(row):
                    # print(j)
                    # print(idx)
                    # assign an unique TRIP ID
                    TRIP_ID = str(track_ID) + "_" + str(idx)
                    print(TRIP_ID)

                    if j == row[0]:  # first TRIP
                        lista = [i for i in range(0,j)]
                        # print(lista)
                        ## get  subset of VIasat data for each list:
                        viasat = viasat1.iloc[lista, :]
                        viasat['TRIP_ID'] = TRIP_ID
                        viasat['idtrajectory'] = viasat.id.iloc[0]
                        # print(viasat)
                        VIASAT_TRIPS_by_ID = VIASAT_TRIPS_by_ID.append(viasat)

                    if (idx > 0 and j != 'end'):   # intermediate TRIPS
                        lista = [i for i in range(row[idx - 1], row[idx])]
                        # print(lista)
                        ## get  subset of VIasat data for each list:
                        viasat = viasat1.iloc[lista, :]
                        viasat['TRIP_ID'] = TRIP_ID
                        viasat['idtrajectory'] = viasat.id.iloc[0]
                        # print(viasat)
                        VIASAT_TRIPS_by_ID = VIASAT_TRIPS_by_ID.append(viasat)

                    if j == "end":  # last trip for that ID
                        # lista = [i for i in range(row[idx-1], len(viasat))]
                        lista = [i for i in range(row[idx-1], len(viasat1))]
                        # print(lista)
                        ## get  subset of VIasat data for each list:
                        viasat = viasat1.iloc[lista, :]
                        viasat['TRIP_ID'] = TRIP_ID
                        viasat['idtrajectory'] = viasat.id.iloc[0]
                        # print(viasat)
                        ## append all TRIPS by ID
                        VIASAT_TRIPS_by_ID = VIASAT_TRIPS_by_ID.append(viasat)


                        ##############################################
                        ### get CONCATENATED TRIPS ##################
                        ##############################################

                        ## get indices where diff_progressive < 0
                        diff_progressive = VIASAT_TRIPS_by_ID.progressive.diff()
                        diff_progressive = diff_progressive.fillna(0)
                        row_progr = []
                        ## define a list with the starting indices of each new TRIP
                        for i in range(len(diff_progressive)):
                            if diff_progressive.iloc[i] < 0:
                                row_progr.append(i)
                        # split Viasat data by TRIP (for a given ID..."idterm")
                        for idx, j in enumerate(row_progr):
                            # print(idx)
                            # print(j)
                            # assign an unique TRIP ID
                            TRIP_ID_conc = str(track_ID) + "_conc_" + str(idx)
                            idtrajectory = str(VIASAT_TRIPS_by_ID['id'].iloc[j])

                            if idx < len(row_progr)-1:  # intermediate TRIPS
                                lista_conc = [i for i in range(row_progr[idx], row_progr[idx+1])]
                                # print(lista_conc)
                                ## get  subset of VIasat data for each list:
                                VIASAT_TRIPS_by_ID["TRIP_ID"].iloc[lista_conc] = TRIP_ID_conc
                                VIASAT_TRIPS_by_ID["idtrajectory"].iloc[lista_conc] = idtrajectory

                    #############################################
                    ### add anomaly codes from Carlo Liberto ####
                    #############################################

                        # final_TRIPS = pd.DataFrame([])
                        # get unique trips
                        all_TRIPS = list(VIASAT_TRIPS_by_ID.TRIP_ID.unique())
                        VIASAT_TRIPS_by_ID['last_panel'] = VIASAT_TRIPS_by_ID.panel.shift()
                        VIASAT_TRIPS_by_ID['last_lon'] = VIASAT_TRIPS_by_ID.longitude.shift()
                        VIASAT_TRIPS_by_ID['last_lat'] = VIASAT_TRIPS_by_ID.latitude.shift()
                        VIASAT_TRIPS_by_ID['last_totalseconds'] = VIASAT_TRIPS_by_ID.totalseconds.shift()
                        ## set nan values to -1
                        VIASAT_TRIPS_by_ID.last_panel= VIASAT_TRIPS_by_ID.last_panel.fillna(-1)
                        VIASAT_TRIPS_by_ID.last_lon = VIASAT_TRIPS_by_ID.last_lon.fillna(-1)
                        VIASAT_TRIPS_by_ID.last_lat = VIASAT_TRIPS_by_ID.last_lat.fillna(-1)
                        VIASAT_TRIPS_by_ID['last_panel'] = VIASAT_TRIPS_by_ID.last_panel.astype('int')
                        ## get TRIP sizes
                        # TRIP_sizes = VIASAT_TRIPS_by_ID.groupby(["TRIP_ID"]).size()
                        for idx_trip, trip in enumerate(all_TRIPS):
                            # trip = '3297372_conc_14'
                            VIASAT_TRIP = VIASAT_TRIPS_by_ID[VIASAT_TRIPS_by_ID.TRIP_ID == trip]
                            diff_path_time = VIASAT_TRIP.path_time.diff()
                            diff_path_time = diff_path_time.fillna(0)
                            row_path_time = []
                            for i in range(len(diff_path_time)):
                                if diff_path_time.iloc[i] > 300:   ## seconds
                                    row_path_time.append(i)
                                    ## get all data from the last index till the end of the data
                            if len(row_path_time) > 0:
                                VIASAT_TRIP = VIASAT_TRIP[max(row_path_time):len(VIASAT_TRIP)]
                            else:
                                VIASAT_TRIP.reset_index(drop=True, inplace=True)
                                # print(VIASAT_TRIP)
                                timeDiff = VIASAT_TRIP.totalseconds.iloc[0] - VIASAT_TRIP.last_totalseconds.iloc[0]
                                progr = VIASAT_TRIP.progressive.iloc[0] - VIASAT_TRIP.last_progressive.iloc[0]
                                for idx_row, row in VIASAT_TRIP.iterrows():
                                    coords_1 = (row.latitude, row.longitude)
                                    coords_2 = (row.last_lat, row.last_lon)
                                    lDist = (geopy.distance.geodesic(coords_1, coords_2).km)*1000  # in meters
                                    ####### PANEL ###################################################
                                    if (row.panel == 1 and row.last_panel == 1):  # errore on-on
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[len(VIASAT_TRIP)-1, "anomaly"] = s
                                        # set the intermediates anomaly to "I"
                                        s = (list(row.anomaly))
                                        s[0] = "I"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        s = (list(row.anomaly))
                                        s[0] = "S"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[0, "anomaly"] = s
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)

                                    elif (row.panel == 0 and row.last_panel == -1):
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        # VIASAT_TRIP.at[0, "anomaly"] = s
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)
                                    elif (row.panel == 0 and row.last_panel == 0):  # off-off
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        # VIASAT_TRIP.at[0, "anomaly"] = s
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[len(VIASAT_TRIP) - 1, "anomaly"] = s
                                    elif (row.panel == 0 and row.last_panel == 1):  # ON-off
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)

                                    elif (row.panel == 1 and row.last_panel == -1):
                                        s = (list(row.anomaly))
                                        s[0] = "I"
                                        s = "".join(s)
                                        # VIASAT_TRIP.at[0, "anomaly"] = s
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        # print(VIASAT_TRIP)
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)
                                    elif (row.panel == 1 and row.last_panel == 0):
                                        s = (list(row.anomaly))
                                        s[0] = "E"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[len(VIASAT_TRIP)-1, "anomaly"] = s
                                        s = (list(row.anomaly))
                                        s[0] = "S"
                                        s = "".join(s)
                                        # VIASAT_TRIP.at[0, "anomaly"] = s
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        # print(VIASAT_TRIP)
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)

                              ####### TRAVEL time > 10 min ###############################################

                                    if (row.last_panel ==1 and row.panel ==1 and timeDiff > 10*60):
                                        s = list(VIASAT_TRIP.iloc[0].anomaly)
                                        s[0] = "S"
                                        s[4] = "T"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[0, "anomaly"] = s
                                        s = list(VIASAT_TRIP.iloc[len(VIASAT_TRIP) - 1].anomaly)
                                        s[0] = "E"
                                        s[4] = "T"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[len(VIASAT_TRIP) - 1, "anomaly"] = s
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)

                                    if (row.grade <= 15):
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[1] = "Q"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                    elif (row.grade > 15):
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[1] = "q"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                    if (lDist > 0 and VIASAT_TRIP["anomaly"].iloc[idx_row] != "S"):
                                        # if (row.progressive/lDist < 0.9):
                                        if (progr / lDist < 0.9):
                                            s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                            s[2] = "c"
                                            s = "".join(s)
                                            VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        # elif (row.progressive/lDist > 10 and row.progressive > 2200):
                                        elif (progr / lDist > 10 and progr > 2200):
                                            s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                            s[3] = "C"
                                            s = "".join(s)
                                            VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                    # if (timeDiff > 0 and 3.6 * 1000 * row.progressive / timeDiff > 250):
                                    if (timeDiff > 0 and 3.6 * 1000 * progr / timeDiff > 250):
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[5] = "V"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                    # if (row.panel !=1 and row.progressive > 10000):
                                    if (row.panel != 1 and progr > 10000):
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[0] = "S"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[6] = "D"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                        VIASAT_TRIP.at[len(VIASAT_TRIP) - 1, "anomaly"] = s
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[0] = "E"
                                        s = "".join(s)
                                        VIASAT_TRIP.at[len(VIASAT_TRIP) - 1, "anomaly"] = s
                                    # elif (row.panel != 0 and row.progressive <= 0):
                                    elif (row.panel != 0 and progr <= 0):
                                        s = list(VIASAT_TRIP.iloc[idx_row].anomaly)
                                        s[6] = "d"
                                        s = "".join(s)
                                        VIASAT_TRIP["anomaly"].iloc[idx_row] = s
                                ### add all TRIPS together ##################
                                # final_TRIPS = final_TRIPS.append(VIASAT_TRIP)

                                ### remove columns and add terminal ID
                                # VIASAT_TRIP['track_ID'] = track_ID
                                VIASAT_TRIP['idterm'] = track_ID
                                VIASAT_TRIP['segment'] = VIASAT_TRIP.index
                                VIASAT_TRIP.drop(['last_panel', 'last_lon', 'last_lat',    # <------
                                                  'last_totalseconds', 'last_progressive'], axis=1,
                                                 inplace=True)

                                #### Connect to database using a context manager and populate the DB ####
                                connection = engine.connect()
                                VIASAT_TRIP.to_sql("routecheck_november_2019", con=connection, schema="public",
                                                   if_exists='append')
                                connection.close()


################################################
##### run all script using multiprocessing #####
################################################

## check how many processer we have available:
# print("available processors:", mp.cpu_count())

if __name__ == '__main__':
    # pool = mp.Pool(processes=mp.cpu_count()) ## use all available processors
    pool = mp.Pool(processes=55)     ## use 60 processors
    print("++++++++++++++++ POOL +++++++++++++++++", pool)
    results = pool.map(func, [(last_track_idx, track_ID) for last_track_idx, track_ID in enumerate(all_ID_TRACKS)])
    pool.close()
    pool.close()
    pool.join()
