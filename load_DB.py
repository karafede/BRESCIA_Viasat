
import os
import glob
import pandas as pd
import db_connect
import sqlalchemy as sal
import csv
import codecs
import psycopg2
import db_connect
import datetime
from datetime import datetime
from datetime import date
import numpy as np


os.chdir('D:/ViaSat/Brescia')
cwd = os.getcwd()

# connect to new DB to be populated with Viasat data after route-check
conn_HAIG = db_connect.connect_HAIG_Viasat_BS()
cur_HAIG = conn_HAIG.cursor()


## create extension postgis on the database HAIG_Viasat_RM_2019  (only one time)

# cur_HAIG.execute("""
# CREATE EXTENSION postgis
# """)

# cur_HAIG.execute("""
#  CREATE EXTENSION postgis_topology
# """)

# conn_HAIG.commit()


# Create an SQL connection engine to the output DB
engine = sal.create_engine('postgresql://postgres:superuser@10.0.0.1:5432/HAIG_Viasat_BS')
connection = engine.connect()

# erase existing table
# cur_HAIG.execute("DROP TABLE IF EXISTS obu CASCADE")
# conn_HAIG.commit()


######################################################################
## create OBU table ##################################################
######################################################################

## load .csv file with idterm and vehicle type info
## create table with idterm, vehicle type and put into a DB
def obu(obu_CSV):
    static_data = pd.read_csv(obu_CSV, delimiter=',', encoding='latin-1', header=None)
    ## There about 1000 linkes with wrong format (This line have been skipped)
    static_data = static_data[pd.to_numeric(static_data[4], errors='coerce').notnull()]
    ## drop last column
    del static_data[8]

    ## assigna header
    static_data.columns = ['idterm', 'devicetype', 'idvehcategory', 'brand', 'anno',
                           'portata', 'gender', 'age']
    ## remove row with empty columns
    static_data['anno'] = static_data['anno'].astype(str).astype(int)
    static_data['anno'] = static_data['anno'].astype('Int64')
    static_data['portata'] = static_data['portata'].astype('Int64')
    len(static_data)

    ## insert static_data into the DB
    static_data.to_sql("obu", con=connection, schema="public", index=False)


##################################################
########## VIASAT dataraw ########################
##################################################

## erase existing table
# cur_HAIG.execute("DROP TABLE IF EXISTS dataraw CASCADE")
# conn_HAIG.commit()


def upload_DB(viasat_filenames):
    ## loop over all the .csv file with the raw VIASAT data
    for csv_file in viasat_filenames:
        print(csv_file)
        reader = csv.reader(codecs.open(csv_file, 'rU', 'utf-16'))
        ## get length of the csv file
        lines = len(list(reader))
        print(lines)
        slice = 100000  # slice of data to be insert into the DB during the loop
        ## calculate the neccessary number of iteration to carry out in order to upload all data into the DB
        iter = int(round(lines / slice, ndigits=0)) + 1
        for i in range(0, iter):
            try:
                print(i)
                print(i, csv_file)
                # csv_file = viasat_filenames[0]
                # df = pd.read_csv(csv_file, header=None, delimiter=',' ,nrows=slice)
                df = pd.read_csv(csv_file, header=None, delimiter=',', skiprows=i * slice, nrows=slice,
                                 encoding='utf-16')
                ## define colum names
                df.columns = ['idrequest', 'idterm', 'timedate', 'latitude', 'longitude',
                              'speed', 'direction', 'grade', 'panel', 'event', 'vehtype',
                              'progressive', 'millisec', 'timedate_gps', 'distance']
                # df['id'] = pd.Series(range(i * slice, i * slice + slice))
                df['timedate'] = df['timedate'].astype('datetime64[ns]')
                df['timedate_gps'] = df['timedate_gps'].astype('datetime64[ns]')
                ## upload into the DB
                df.to_sql("dataraw", con=connection, schema="public",
                          if_exists='append', index=False)
                with open("last_file.txt", "w") as text_file:
                    text_file.write("last csv_file ID: %s" % (csv_file))
            except pd.errors.EmptyDataError:
                pass

###################################################################
###################################################################
###################################################################
#### create table with 'idterm', 'vehtype' and 'portata' ##########

def idterm_vehtype_portata():
    idterm_vehtype_portata = pd.read_sql_query('''
                           WITH ids AS (SELECT idterm, vehtype
                                        FROM
                                   dataraw)
                               select ids.idterm,
                                      ids.vehtype,
                                      obu.portata
                            FROM ids
                            LEFT JOIN obu ON ids.idterm = obu.idterm
                            ''', conn_HAIG)

    ## drop duplicates ###
    idterm_vehtype_portata.drop_duplicates(['idterm'], inplace=True)
    idterm_vehtype_portata = idterm_vehtype_portata[['idterm', 'vehtype', 'portata']]
    ## populate DB
    idterm_vehtype_portata.to_sql("idterm_portata", con=connection, schema="public",
              if_exists='append', index=False)


########################################################################################
########################################################################################
########################################################################################


