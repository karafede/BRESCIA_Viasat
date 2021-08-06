
import os
from load_DB import obu
from load_DB import upload_DB
from load_DB import idterm_vehtype_portata
import glob
import db_connect
import sqlalchemy as sal


os.chdir('D:/ViaSat/Brescia/obu')
cwd = os.getcwd()
## load OBU data (idterm, vehicle type and other metadata)
obu_CSV = "VST_ENEA_BS_DATISTATICI_20201118_new.csv"

### upload Viasat data for into the DB (only dataraw, NOT OBU data!!!)
extension = 'csv'
os.chdir('D:/ViaSat/Brescia/marzo_2019')
viasat_filenames_march_2019 = glob.glob('*.{}'.format(extension))

os.chdir('D:/ViaSat/Brescia/novembre_2019')
viasat_filenames_november_2019 = glob.glob('*.{}'.format(extension))

# join two lists together
# viasat_filenames =  viasat_filenames_march_2019 + viasat_filenames_november_2019

# connect to new DB to be populated with Viasat data
conn_HAIG = db_connect.connect_HAIG_BRESCIA()
cur_HAIG = conn_HAIG.cursor()


## create extension postgis on the database HAIG_CATANIA  (only one time)

'''

cur_HAIG.execute("""
    CREATE EXTENSION postgis
""")

cur_HAIG.execute("""
CREATE EXTENSION postgis_topology
""")
conn_HAIG.commit()

'''

#########################################################################################
### upload OBU data into the DB. Create table with idterm, vehicle type and put into a DB

obu(obu_CSV)

### upload viasat data into the DB  # long time run...
os.chdir('D:/ViaSat/Brescia/marzo_2019')
upload_DB(viasat_filenames_march_2019)

os.chdir('D:/ViaSat/Brescia/novembre_2019')
upload_DB(viasat_filenames_november_2019)

###########################################################
### ADD a SEQUENTIAL ID to the dataraw table ##############
###########################################################

#### long time run...
## add geometry WGS84 4326
cur_HAIG.execute("""
alter table dataraw add column geom geometry(POINT,4326)
""")

cur_HAIG.execute("""
update dataraw set geom = st_setsrid(st_point(longitude,latitude),4326)
""")
conn_HAIG.commit()



# long time run...
## create a consecutive ID for each row
cur_HAIG.execute("""
alter table "dataraw" add id serial PRIMARY KEY
     """)
conn_HAIG.commit()

#### add an index to the "idterm"

cur_HAIG.execute("""
CREATE index dataraw_idterm_idx on public.dataraw(idterm);
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index dataraw_timedate_idx on public.dataraw(timedate);
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index dataraw_vehtype_idx on public.dataraw(vehtype);
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index dataraw_id_idx on public.dataraw("id");
""")
conn_HAIG.commit()



cur_HAIG.execute("""
CREATE index dataraw_lat_idx on public.dataraw(latitude);
""")
conn_HAIG.commit()

cur_HAIG.execute("""
CREATE index dataraw_lon_idx on public.dataraw(longitude);
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index dataraw_geom_idx on public.dataraw(geom);
""")
conn_HAIG.commit()

########################################################################################
#### create table with 'idterm', 'vehtype' and 'portata' and load into the DB ##########

idterm_vehtype_portata()   # long time run...

## add an index to the 'idterm' column of the "idterm_portata" table
cur_HAIG.execute("""
CREATE index idtermportata_idterm_idx on public.idterm_portata(idterm);
""")
conn_HAIG.commit()

## add an index to the 'idterm' column of the "obu" table
cur_HAIG.execute("""
CREATE index obu_idterm_idx on public.obu(idterm);
""")
conn_HAIG.commit()


#########################################################################################
##### create table routecheck ###########################################################

## multiprocess.....
os.chdir('D:/ENEA_CAS_WORK/BRESCIA')
# exec(open("routecheck_viasat_BRESCIA_FK.py").read())



## add indices ######

### change type of "idterm" from text to bigint
cur_HAIG.execute("""
ALTER TABLE public.routecheck ALTER COLUMN "idterm" TYPE bigint USING "idterm"::bigint
""")
conn_HAIG.commit()

cur_HAIG.execute("""
CREATE index routecheck_id_idx on public.routecheck("id");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_idterm_idx on public.routecheck("idterm");
""")
conn_HAIG.commit()



cur_HAIG.execute("""
CREATE index routecheck_TRIP_ID_idx on public.routecheck("TRIP_ID");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_idtrajectory_ID_idx on public.routecheck("idtrajectory");
""")
conn_HAIG.commit()




cur_HAIG.execute("""
CREATE index routecheck_timedate_idx on public.routecheck("timedate");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_grade_idx on public.routecheck("grade");
""")
conn_HAIG.commit()



cur_HAIG.execute("""
CREATE index routecheck_anomaly_idx on public.routecheck("anomaly");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_speed_idx on public.routecheck("speed");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_lat_idx on public.routecheck(latitude);
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index routecheck_lon_idx on public.routecheck(longitude);
""")
conn_HAIG.commit()


#########################################################################################
##### create table route ################################################################

## multiprocess....
# exec(open("route_FK.py").read())


# Create an SQL connection engine to the output DB
engine = sal.create_engine('postgresql://postgres:superuser@10.1.0.1:5432/HAIG_BRESCIA')


#### setup multiprocessing.......

### change type of "idterm" from text to bigint
cur_HAIG.execute("""
ALTER TABLE public.route ALTER COLUMN "idterm" TYPE bigint USING "idterm"::bigint
""")
conn_HAIG.commit()


### create index for 'idterm'
cur_HAIG.execute("""
CREATE index route_idterm_idx on public.route(idterm);
""")
conn_HAIG.commit()


##### convert "geometry" field on LINESTRING

## Convert the `'geom'` column back to Geometry datatype, from text
with engine.connect() as conn, conn.begin():
    print(conn)
    sql = """ALTER TABLE public."route"
                                  ALTER COLUMN geom TYPE Geometry(LINESTRING, 4326)
                                    USING ST_SetSRID(geom::Geometry, 4326)"""
    conn.execute(sql)




