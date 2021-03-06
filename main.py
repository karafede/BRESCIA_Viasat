
import os
from load_DB import obu
from load_DB import upload_DB
from load_DB import idterm_vehtype_portata
import glob
import db_connect

os.chdir('D:/ViaSat/Brescia/obu')
cwd = os.getcwd()
## load OBU data (idterm, vehicle type and other metadata)
obu_CSV = "VST_ENEA_BS_DATISTATICI_20201118_new.csv"

### upload Viasat data for into the DB (only dataraw, NOT OBU data!!!)
extension = 'csv'
os.chdir('D:/ViaSat/Brescia')
viasat_filenames = glob.glob('*.{}'.format(extension))

# connect to new DB to be populated with Viasat data
conn_HAIG = db_connect.connect_HAIG_Viasat_BS()
cur_HAIG = conn_HAIG.cursor()


#########################################################################################
### upload OBU data into the DB. Create table with idterm, vehicle type and put into a DB

obu(obu_CSV)

### upload viasat data into the DB  # long time run...
upload_DB(viasat_filenames)


###########################################################
### ADD a SEQUENTIAL ID to the dataraw table ##############
###########################################################

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

########################################################################################
#### create table with 'idterm', 'vehtype' and 'portata' and load into the DB ##########

idterm_vehtype_portata()   # long time run...

#########################################################################################
##### create table routecheck ###########################################################

## multiprocess.....
os.chdir('D:/ENEA_CAS_WORK/BRESCIA')
exec(open("routecheck_viasat_BRESCIA_FK.py").read())

#########################################################################################
##### create table route ################################################################

## multiprocess....
exec(open("route_FK.py").read())

### change type of "idterm" from text to bigint
cur_HAIG.execute("""
ALTER TABLE public.route_november_2019 ALTER COLUMN "idterm" TYPE bigint USING "idterm"::bigint
""")
conn_HAIG.commit()


cur_HAIG.execute("""
ALTER TABLE public.route_march_2019 ALTER COLUMN "idterm" TYPE bigint USING "idterm"::bigint
""")
conn_HAIG.commit()

### create index for 'idterm'
cur_HAIG.execute("""
CREATE index route_november_2019_idterm_idx on public.route_november_2019(idterm);
""")
conn_HAIG.commit()


### create index for 'idterm'
cur_HAIG.execute("""
CREATE index route_march_2019_idterm_idx on public.route_march_2019(idterm);
""")
conn_HAIG.commit()


#################################################
##### map-matching ##############################

## multiprocess....
exec(open("map_matching_FK_BRESCIA_MULTIPROCESS.py.py").read())


## create index on the column (u,v) togethers in the table 'mapmatching_2017' ###
cur_HAIG.execute("""
CREATE INDEX UV_march_only_idx_2019 ON public."mapmatching_ONLY_UNIBS_march_2019"(u,v);
""")
conn_HAIG.commit()


## create index on the "TRIP_ID" column
cur_HAIG.execute("""
CREATE index trip_march_only_2019_idx on public."mapmatching_ONLY_UNIBS_march_2019"("TRIP_ID");
""")
conn_HAIG.commit()


## create index on the "TRIP_ID" column
cur_HAIG.execute("""
CREATE index idtrajectory_march_only_2019_idx on public."mapmatching_ONLY_UNIBS_march_2019"("idtrajectory");
""")
conn_HAIG.commit()


## create index on the "idtrace" column
cur_HAIG.execute("""
CREATE index idrace_march_only_2019_idx on public."mapmatching_ONLY_UNIBS_march_2019"("idtrace");
""")
conn_HAIG.commit()


cur_HAIG.execute("""
CREATE index timedate_march_only_2019_idx on public."mapmatching_ONLY_UNIBS_march_2019"(timedate);
""")
conn_HAIG.commit()
