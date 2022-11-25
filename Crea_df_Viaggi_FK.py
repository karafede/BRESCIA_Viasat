# -*- coding: utf-8 -*-
"""
Created on Thursday Apr 01 12:07:35 2020

@author: KARAGULIAN
"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.pyplot import *
import time
import db_connect
from routines_viaggi_FK import tempo
from routines_viaggi_FK import Setta_Fl_Viaggio
from routines_viaggi_FK import Crea_Vett_x_INFO_Veic
from routines_viaggi_FK import Crea_Id_Viaggi
from routines_viaggi_FK import Tab_Sintetica
from routines_viaggi_FK import Tab_Completa
from routines_viaggi_FK import Setta_Soste_Generiche_Notte_e_Giorno
from routines_viaggi_FK import Calcola_Coord_Case
from routines_viaggi_FK import Calcola_Coord_Lavori
from routines_viaggi_FK import Setta_Soste_Specifica
from routines_viaggi_FK import Calcola_Coord_Case
from routines_viaggi_FK import  Calcola_Coord_Lavori
from routines_viaggi_FK import Trova_Luogo
from routines_viaggi_FK import Crea_df_Viaggi_Vuoto
from routines_viaggi_FK import Crea_df_Viaggi_1_Veicolo
from routines_viaggi_FK import Aggiungi_1Veic_ai_Vett_di_INFO_Veic
from routines_viaggi_FK import Aggiungi_1Veic_Eliminato


##############################################################################
##############################################################################
##############################################################################
########## -------------------------------------------------- ################
########## -------------------------------------------------- ################
########## -------------------------------------------------- ################
##############################################################################
##############################################################################

conn_HAIG = db_connect.connect_HAIG_Viasat_BS()
cur_HAIG = conn_HAIG.cursor()

# ==============================================================================
#                                 I N I Z I O
# ==============================================================================

D_sec = 300  # [sec].  SOSTA MINIMA CONSIDERATA
# Con soste inferiori i viaggi sono CONCATENATI
# USATO ANCHE per determinare FUORIUSCITA-INGRESSO dal riquadro

Sosta_Lav_Min = 2.0  # [ORE] Sosta Minima di lovoro (per identificarne il luogo)

Registr_Min = 50  # Al disotto di queste registrazioni il veicolo è scartato

Fl_Diag = False  # = True --> stampa diagnostiche
#           Fl_Tab     stampa la tabella dei viaggi in fase iniziale
#                                    compresi ACCENSIONI-SPEGNIMENTI
Fl_Tab = False  # = True --> stampa tabella preliminare e sintetica
#           Fl_Tab1   stampa la tabella dei viaggi CORRETTI in fase finale
Fl_Tab1 = False  # = True --> stampa tabella
Fl_Tempi = False  # = True --> stampa i tempi di esecuzione
Fl_Tab_Notte_Giorno = False  # = True --> Stampa soste NOTTE - GIORNO

if not (Fl_Diag):  print('Settare:  "Fl_Diag = True"  per Stampare le Diagnostiche')
if not (Fl_Tab):   print('Settare:  "Fl_Tab  = True"  per Stampare le Tabelle INIZIALI')
if not (Fl_Tab1):  print('Settare:  "Fl_Tab1 = True"  per Stampare le Tabelle FINALI CORRETTE')
if not (Fl_Tempi): print('Settare:  "Fl_Tempi= True"  per avere i tempi di esecuzione')

# ______________________________ CREA data-Frame vuoto MA CON TUTTE LE VARIABILI
#                                 poi verranno aggiunti i veicoli, 1 alla volta
df_Viag = Crea_df_Viaggi_Vuoto()

# ___________________________________________ Inizializza, come VUOTE, i vettori
#                                                    che comporranno: INFO_Veic

_Id_Term, _Veh_Type, _N_Giorni_Pres, _Km_Percorsi, \
_N_Case, _N_Lavori, _Coord_1_Casa, _Coord_2_Casa, \
_Coord_1_Lavoro, _Coord_2_Lavoro, _Notti_In, _Notti_Out, \
_Notti_1Casa, _Notti_2Casa, _Trans_Confine, _N_Soste_Univ, \
_Giorni_al_1Lav, _Giorni_al_2Lav = Crea_Vett_x_INFO_Veic()

#


M = 5  # Fattore Moltiplicativo (per variare il riquadro interno)
# D_lon = 0.00065; D_lat = 0.00045   # Delta gradi, corrispondenti a 50 m.
D_lon = 0.0065;
D_lat = 0.0045  # Delta gradi, corrispondenti a 500 m.

# _______________________________________________Dichiarati da LORO
Lon_Min_Dic = 9.69;
Lon_Max_Dic = 11.30
Lat_Min_Dic = 45.13;
Lat_Max_Dic = 46.43
# ________________________________________________Riscontrati
Lon_Min_Ris = 9.77;
Lon_Max_Ris = 10.9
Lat_Min_Ris = 45.1;
Lat_Max_Ris = 46.39996
# ________________________________________________Riquadro interno
Lon_Min_Int = Lon_Min_Ris + D_lon * M;
Lon_Max_Int = Lon_Max_Ris - D_lon * M
Lat_Min_Int = Lat_Min_Ris + D_lat * M;
Lat_Max_Int = Lat_Max_Ris - D_lat * M

M = 1;  # M = 1.5
# ________________________________________________Coord. UNIVERSITA'
Coord_Univ = [10.21759, 45.53764]
Parcheggio_Ingegneria = [10.23051, 45.56499]  ## parcheggio all'aperto
Lon_Univ = Coord_Univ[0];
Lat_Univ = Coord_Univ[1]
Lon_Min_Univ = Lon_Univ - D_lon * M;
Lon_Max_Univ = Lon_Univ + D_lon * M
Lat_Min_Univ = Lat_Univ - D_lat * M;
Lat_Max_Univ = Lat_Univ + D_lat * M

t0 = tempo('INIZIO: ', 0)

# filed = 'C:\\Users\\asus pc\\.spyder-py3\\Mio_BRESCIA_dati\\Marzo_2019\\Dati_con_1576_Veic.csv'

# dati = pd.read_csv("pippo_11_2.csv", index_col=None)
# dati = pd.read_csv(filed, index_col=0)
# dati.to_csv(filed, sep=',', endcoding='utf-8')

'''# Per inserire le coordinate in metri prodotte dall'applicativo ReGeo
dati_coord = pd.read_csv(filed[:-4]+'_trasf.csv')
dati_coord.rename(columns={dati_coord.columns[0] : 'XUTM32', dati_coord.columns[1] : 'YUTM32' } , inplace=True)
dati['XUTM32'] = dati_coord.XUTM32
dati['YUTM32'] = dati_coord.YUTM32
del dati_coord
'''

tempo("==== Dopo aver caricato il file            ", t0)

if Fl_Tempi:   tempo("==== Dopo aver CARICATO il file          ", t0)

'''___________________________# ELENCO VARIABILI GIA' PRESENTI

'idrequest'  =  E' il cliente (ENEA) (sempre = 1)
'idterm'     =  Terminale (veicolo)
'timedate'   =  Data RTC
'latitude'   =  in direz. Y
'longitude'  =  in direz. X
'speed'      =
'direction'  =
'grade'      =  Qualità segnale
'panel'      =  Stato Motore: 0 (spento) 1 (acceso)
'event'      =  Tipo Evento
'vehtype'    =  Tipo Veicolo
'progressive'=  Odo viaggio
'millisec'   =  Millisec. RTC
'timedate_gps'= Data GPS
'distance'   =  Odo Assoluta
'id'         =  ????
_____________________________Vaiabili di GIANCARLO da Aggiungere

'Day_of_year' = Giorno dell'anno: 1 - 365
'Day_of_week' = Giorno della settimana: 0 - 6 (Domenica = 6)
'Delta_sec'   = Delta secondi calcolati dalla precedente registrazione
'Km'          = Km percorsi dalla preced. registrazione
'Km_prog'     = Km progressivi da inizio registrazioni
'Fl_Viag'
'Id_Viaggi'   = Nelle  cifre dopo "_" c'è il N* viaggio (0:N°Viaggi-1)
                nelle cifre precedenti c'è l'  Id_Veicolo
'TipoSosta'   =
'Univ'        =
'''

# elenco_Term_x_Freq = dati.idterm.value_counts(ascending=True) # Terminali ordinati per freq.
# elenco_Term_x_Id   = elenco_Term_x_Freq[ np.sort( elenco_Term_x_Freq.index ) ]

# Veic_considerati = elenco_Term_x_Id[ elenco_Term_x_Id > Registr_Min ].index

# tempo("==== I veicoli caricati sono: " + str(len(elenco_Term_x_Id))+"         ", t0)
# tempo("==== "+ str(len(Veic_considerati))+ " sono i veicoli utili             ", t0)

# ==============================================================================
#  I N I Z I O   F O R     per caricare 1 veicolo x volta
# ==============================================================================
N_elim = 0  # N° veicoli eliminati
Id_veic_elim = []
Reg_veic_elim = []
Causa_veic_elim = []

# ____________________ Se si vuole analizzare 1 solo veicolo, ad es.il; 2725098
# ____________________ Settare:


# get all ID terminal of Viasat data
# all_VIASAT_IDterminals = pd.read_sql_query(
#    ''' SELECT *
#        FROM public.obu''', conn_HAIG)

#### select only CARS
all_VIASAT_IDterminals = pd.read_sql_query(
    ''' SELECT *
        FROM public.idterm_portata
        WHERE vehtype = 1 ''', conn_HAIG)

all_VIASAT_IDterminals['idterm'] = all_VIASAT_IDterminals['idterm'].astype('Int64')
all_VIASAT_IDterminals['vehtype'] = all_VIASAT_IDterminals['vehtype'].astype('Int64')
# all_VIASAT_IDterminals['anno'] = all_VIASAT_IDterminals['anno'].astype('Int64')
# all_VIASAT_IDterminals['portata'] = all_VIASAT_IDterminals['portata'].astype('Int64')
# make a list of all IDterminals (GPS ID of Viasata data) each ID terminal (track) represent a distinct vehicle
Veic_considerati = list(all_VIASAT_IDterminals.idterm.unique())
# Veic_considerati = Veic_considerati[0:20000]
Veic_considerati = Veic_considerati[20001:40000]
Veic_considerati = Veic_considerati[0:30]

# track_ID = '4165307'
# for kv in  range( len(Veic_considerati[0:3]) ):
for kv, track_ID in enumerate(Veic_considerati):
    # ==============================================================================
    #  C A R I C A   1   V E I C O L O  in   dati1v
    # ______________________________________________________________________________

    # ___________ Ordina per data e RICREA la colonna degli indici (index)

    # dati1v = dati[dati.idterm==id_veic ].sort_values('timedate')
    # print(track_ID)
    print("veicolo num: ", kv)
    track_ID = str(track_ID)
    dati1v = pd.read_sql_query('''
                    SELECT * FROM public.dataraw
                    WHERE idterm = '%s' ''' % track_ID, conn_HAIG)
    dati1v = dati1v.sort_values('timedate')

    dati1v = pd.DataFrame(np.array(dati1v), \
                          index=np.arange(len(dati1v)), columns=dati1v.columns)

    dati1v['timedate'] = dati1v.timedate.astype('datetime64[ns]')
    dati1v['speed'] = dati1v.speed.astype('int64')
    dati1v['progressive'] = dati1v.progressive.astype('int64')
    dati1v['distance'] = dati1v.distance.astype('int64')

    dati1v['latitude'] = dati1v.latitude.astype('float64')
    dati1v['longitude'] = dati1v.longitude.astype('float64')

    # ___________________________________Crea variabili:____________________________
    #
    #    'Day_of_year' = Giorno dell'anno: 1 - 365
    #    'Delta_sec'   = Delta secondi calcolati dalla precedente registrazione
    #    'Km'          = Km percorsi dalla preced. registrazione
    #    'Km_prog'     = Km progressivi da inizio registrazioni
    # ______________________________________________________________________________
    Day_of_year = np.zeros(len(dati1v), dtype='int')
    Day_of_week = np.zeros(len(dati1v), dtype='int')

    Delta_sec = np.zeros(len(dati1v), dtype='int')

    for k in range(len(dati1v)):
        Day_of_year[k] = dati1v.timedate[k].dayofyear
        Day_of_week[k] = dati1v.timedate[k].dayofweek

    Delta_sec[1:] = (dati1v.timedate[1:].values - dati1v.timedate[:-1].values) / 1e9

    dati1v['Day_of_year'] = Day_of_year
    dati1v['Day_of_week'] = Day_of_week
    dati1v['Delta_sec'] = Delta_sec

    # dati1v['Km'] = (dati1v.speed * dati1v.Delta_sec / 3600).round(4)

    ### modifica by Federico Karagulian 26 Febbraio 2021 #################
    ## --------------------------------------------------- ###############
    dati1v['last_progressive'] = dati1v.progressive.shift()  # <-------
    dati1v.last_progressive = dati1v.last_progressive.fillna(-1)  # <-------
    dati1v['km'] = dati1v.progressive - dati1v.last_progressive
    for i in range(len(dati1v)):
        if dati1v.km.iloc[i] > 0:
            dati1v.km.iloc[i] = dati1v.km.iloc[i] / 1000
        elif dati1v.km.iloc[i] < 0:
            dati1v.km.iloc[i] = 0

    dati1v['Km_prog'] = np.cumsum(dati1v.km)

    if Fl_Tempi:   tempo("==== Dopo creazione nuove Variabili        ", t0)

    # ==============================================================================
    #   Calcolo e settaggio FLAG VIAGGIO: Fl_Viag
    #
    #   Se ci sono problemi: setta "Veic_da_Eliminare" con un codice diverso da ZERO
    #   ( il valore dei codici è nella routine: Setta_Fl_Viaggio()  )
    # ==============================================================================

    if Fl_Tempi:   tempo("==== Prima del calcolo: Fl_Viag            ", t0)

    # from Routine_Viaggi import Setta_Fl_Viaggio
    Fl_Viag, Veic_da_Eliminare = Setta_Fl_Viaggio(dati1v)
    dati1v['Fl_Viag'] = Fl_Viag

    if Fl_Tempi:   tempo("==== Dopo del calcolo: Fl_Viag             ", t0)

    # ==============================================================================
    #   Composizione e settaggio :  Id_Viaggi
    #
    #  Id_Viaggi è composto da: Id_term e N°Viaggio (saparati da '_')
    #            è tipo text
    # ==============================================================================

    # Id_Viaggi = Crea_Id_Viaggi()
    dati1v['Id_Viaggi'] = Crea_Id_Viaggi(dati1v)

    # ==================================================================
    #   Stampa 2 diagnostiche dei  VIAGGI (una sintetica e una complta)
    # ==================================================================
    if Fl_Tab:
        print(' ' * 40, 'Tab. Preliminare SINTETICA')
        Tab_Sintetica(dati1v)

    # ==================================================================
    #          FA PARTIRE DA ZERO:  DISTANCE e PROGRESSIVE
    # ==================================================================
    # dati1v['distance']    = dati1v.distance - dati1v.distance [0]
    # dati1v['progressive'] = dati1v.progressive - dati1v.progressive [0]

    # ...............................................
    if Veic_da_Eliminare == 0:  # = 0 il veicolo viene ELABORATO
        # = 1  "     "   è eliminato

        #######################################################################
        #           I N I Z I O  di   Trova casa
        #######################################################################
        #                          Le soste sono classificate in: Notturne (20)
        #                                                    e Giornaliere (10)
        TipoSosta, pun_Notti_Strane_D, pun_Notti_Strane_O = \
            Setta_Soste_Generiche_Notte_e_Giorno(dati1v)

        dati1v['TipoSosta'] = TipoSosta

        # __________________________________________Soste notturne fuori confine
        # _____________________________________ e nell'intervallo Marzo-Novembre
        Notti_Out = sum(dati1v.Fl_Viag[dati1v.TipoSosta == 220] == 21) + \
                    sum(dati1v.Fl_Viag[dati1v.TipoSosta == 220] == 22) + \
                    sum(dati1v.Fl_Viag[dati1v.TipoSosta == 220] == 23)
        # ________________________________________________Soste notturne interne
        Notti_In = sum(dati1v.Fl_Viag[dati1v.TipoSosta == 220] == 20)
        Notti_Tot = sum(dati1v.TipoSosta == 220)
        if Fl_Diag:
            print('Notti Interne =', Notti_In, '   Notti Esterne e Salto_Mesi =', Notti_Out)
            print('Notti Totali =', Notti_Tot)

        # ==============================================================================
        #  Stampa le PRESENZE REALI (Dalle presenze sui giorni-anno)
        # ___________________________________________________________________
        elenco_day_1v = dati1v.Day_of_year.value_counts(ascending=True)  # Elenco GiorniAnno di.presenza veicolo
        elenco_day_1v = elenco_day_1v.sort_index()

        N_Presenze_Giornaliere = len(elenco_day_1v)
        if sum(dati1v.Day_of_year == 0) > 0:
            N_Presenze_Giornaliere = N_Presenze_Giornaliere - 1
        N_Presenze_Giornaliere_Reali = sum(elenco_day_1v > 3)
        if Fl_Diag:
            print('N_Presenze_Giornaliere:       ', N_Presenze_Giornaliere)
            print('N_Presenze_Giornaliere_Reali: ', N_Presenze_Giornaliere_Reali)

        # ==============================================================================
        #        C A S A       Trova Coord.   e    Setta "TipoSosta"
        # ______________________________________________________________________________
        #                                   T R O V A   coordinate PRIMA e SECONDA CASA
        Coord_1_Casa, Coord_2_Casa, N_Case = Calcola_Coord_Case(dati1v)
        #                                              Inserisce Soste Anomale
        #                                              Dovute ad ACCENSIONI-SPEGNIMENTI
        dati1v.loc[dati1v.Fl_Viag == 5, 'TipoSosta'] = 5

        #                       S E T T A   soste PRIMA e SECONDA CASA in  "TipoSosta"
        #                                   In pratica quando sosta a casa CAMBIA la Sosta
        #                                   definita precedentemente Generica (220 o 210)
        #                                   in sosta 1 casa (221, 121, 211, 111) e
        #                                            2 casa (222, 122, 212, 112)
        if Coord_1_Casa[0] > 0:

            #                         Cambia da sosta NOTTE  GENERICA in NOTTE  1° CASA
            Setta_Soste_Specifica(dati1v, 220, 221, 121, Coord_1_Casa)
            #                         Cambia da sosta GIORNO GENERICA in GIORNO 1° CASA
            Setta_Soste_Specifica(dati1v, 210, 211, 111, Coord_1_Casa)

            if Coord_2_Casa[0] > 0:
                #                     Cambia da sosta NOTTE  GENERICA in NOTTE  2° CASA
                Setta_Soste_Specifica(dati1v, 220, 222, 122, Coord_2_Casa)
                #                     Cambia da sosta GIORNO GENERICA in GIORNO 2° CASA
                Setta_Soste_Specifica(dati1v, 210, 212, 112, Coord_2_Casa)

        # ..............................................................................
        # Se le rimanenti soste generiche ( di giorno o notte ) sono al confine:
        #          ==> mettere codice CONFINE xx7
        # ..............................................................................
        dati1v.loc[(dati1v.Fl_Viag == 21) & (dati1v.TipoSosta == 220), 'TipoSosta'] = 227
        dati1v.loc[(dati1v.Fl_Viag == 11) & (dati1v.TipoSosta == 120), 'TipoSosta'] = 127

        dati1v.loc[(dati1v.Fl_Viag == 21) & (dati1v.TipoSosta == 210), 'TipoSosta'] = 217
        dati1v.loc[(dati1v.Fl_Viag == 11) & (dati1v.TipoSosta == 110), 'TipoSosta'] = 117

        # ==============================================================================
        #   L A V O R O     Trova Coord.   e    Setta "TipoSosta"
        # ______________________________________________________________________________

        #                                 T R O V A   coordinate PRIMO e SECONDO LAVORO
        Coord_1_Lavoro, Coord_2_Lavoro, N_Lavori = Calcola_Coord_Lavori(dati1v,Sosta_Lav_Min)

        # ______________________S E T T A   soste PRIMO e SECONDO LAVORO in  "TipoSosta"
        if Coord_1_Lavoro[0] > 0:
            #                         Cambia da sosta GIORNO GENERICA in GIORNO 1° LAVORO
            Setta_Soste_Specifica(dati1v, 210, 215, 115, Coord_1_Lavoro)

            if Coord_2_Lavoro[0] > 0:
                #                     Cambia da sosta GIORNO GENERICA in GIORNO 2° CASA
                Setta_Soste_Specifica(dati1v, 210, 216, 116, Coord_2_Lavoro)

        # ==============================================================================
        #   U N I V E R S I T A'     Trova Soste Università    e  Setta "Univ"
        # ______________________________________________________________________________

        Univ = Trova_Luogo(dati1v, Coord_Univ)
        dati1v['Univ'] = Univ

        # ==============================================================================
        #       C H E C K   V E I C O L O
        # ==============================================================================
        if Fl_Diag:
            print('\nCheck su Sosta minima riscontrata:', \
                  min(dati1v.Delta_sec[(dati1v.TipoSosta < 120) & \
                                       (dati1v.TipoSosta > 5)]), 'sec')

        if Fl_Diag:
            print('Notti  1° Casa : ', sum(dati1v.TipoSosta == 221))
            print('Notti  2° Casa : ', sum(dati1v.TipoSosta == 222))
            print('Notti  Generica: ', sum(dati1v.TipoSosta == 220))

            print('\nGiorni 1° Casa : ', sum(dati1v.TipoSosta == 211))
            print('Giorni 2° Casa : ', sum(dati1v.TipoSosta == 212))
            print('Giorni 1° Lavoro : ', sum(dati1v.TipoSosta == 215))
            print('Giorni 2° Lavoro: ', sum(dati1v.TipoSosta == 216))
            print('Giorni Generici: ', sum(dati1v.TipoSosta == 210))

        # freq = int(elenco_Term_x_Id [elenco_Term_x_Id.index==id_veic].values)
        # tempo(str(kv)+" == FINE Veic.N° "+str(id_veic)+" ( "+str(freq)+" reg.)    ", t0)

        # ==============================================================================
        #     P R E P A R A   F I L E    V I A G G I   e lo aggiunge a   df_Viag
        # ==============================================================================

        if sum(dati1v.Fl_Viag > 19) > 2:  # ALMENO 2 VIAGGI FINITI

            # crea i viaggidi 1 veicolo  da:  dati1v
            df_Viag_1v = Crea_df_Viaggi_1_Veicolo(dati1v, Fl_Viag)

            df_Viag = df_Viag.append(df_Viag_1v)

            if Fl_Tab1:  # STAMPA TAB VIAGGI CORRETTI
                print(' ' * 40, 'Tab. Finale più COMPLETA')
                Tab_Completa(dati1v)

            # ==============================================================================
            #   aggiunge ai vettori  I N F O    V E I C O L O
            # ==============================================================================

            # Aggiunge 1 nuovo veicolo ai vettori di INFO_Veic
            Aggiungi_1Veic_ai_Vett_di_INFO_Veic(dati1v, N_Presenze_Giornaliere_Reali,
                                                N_Case, N_Lavori,
                                                Coord_1_Casa, Coord_2_Casa, Coord_1_Lavoro, Coord_2_Lavoro,
                                                Notti_In, Notti_Out, df_Viag_1v)

        else:
            Veic_da_Eliminare = 2  # 2= Il N° viaggi è < 3

            # N_elim = Aggiungi_1Veic_Eliminato(Veic_da_Eliminare, N_elim)
            N_elim = Aggiungi_1Veic_Eliminato(Id_veic_elim, dati1v, Reg_veic_elim, Causa_veic_elim,
                             Veic_da_Eliminare, '( Il N° viaggi è < 3 )', N_elim)

    else:
        # N_elim = Aggiungi_1Veic_Eliminato(Veic_da_Eliminare, N_elim)
        N_elim = Aggiungi_1Veic_Eliminato(Id_veic_elim, dati1v, Reg_veic_elim, Causa_veic_elim,
                             Veic_da_Eliminare, '(Punt. Arrive e Partenze hanno diverse dimensioni)', N_elim)

########################################
#       F I N E      F O R   id_veic
########################################

INFO_Veic = pd.DataFrame({'Id_Term': _Id_Term,
                          'Veh_Type': _Veh_Type,
                          'N_Giorni_Pres': _N_Giorni_Pres,
                          'Km_Percorsi': _Km_Percorsi,
                          'N_Case': _N_Case,
                          'N_Lavori': _N_Lavori,
                          'Coord_1_Casa': _Coord_1_Casa,
                          'Coord_2_Casa': _Coord_2_Casa,
                          'Coord_1_Lavoro': _Coord_1_Lavoro,
                          'Coord_2_Lavoro': _Coord_2_Lavoro,
                          'Notti_In': _Notti_In,
                          'Notti_Out': _Notti_Out,

                          'Notti_1Casa': _Notti_1Casa,
                          'Notti_2Casa': _Notti_2Casa,
                          'Trans_Confine': _Trans_Confine,
                          'N_Soste_Univ': _N_Soste_Univ,
                          'Giorni_al_1Lav': _Giorni_al_1Lav,
                          'Giorni_al_2Lav': _Giorni_al_2Lav})

df_Eliminati = pd.DataFrame({'Id_veic_elim': Id_veic_elim,
                             'Reg_veic_elim': Reg_veic_elim,
                             'Causa_veic_elim': Causa_veic_elim})

tempo("==== Sta salvando il file 'df_Viag'        ", t0)
# df_Viag.to_csv('df_Viag_0_10000_auto.csv', sep=',')
# df_Viag.to_csv('df_Viag_0_20000_auto.csv', sep=',')
# df_Viag.to_csv('df_Viag_20001_40000_auto.csv', sep=',')
df_Viag.to_csv('df_Viag_prova.csv', sep=',')

tempo("==== Sta salvando il file 'INFO_Veic'      ", t0)
# INFO_Veic.to_csv('INFO_Veic_0_10000_auto.csv', sep=',')
# INFO_Veic.to_csv('INFO_Veic_0_20000_auto.csv', sep=',')
# INFO_Veic.to_csv('INFO_Veic_20001_40000_auto.csv', sep=',')
INFO_Veic.to_csv('INFO_Veic_prova.csv', sep=',')

# df_Eliminati.to_csv('df_Eliminati_0_10000_auto.csv', sep=',')
# df_Eliminati.to_csv('df_Eliminati_0_20000_auto.csv', sep=',')
# df_Eliminati.to_csv('df_Eliminati_20001_40000_auto.csv', sep=',')
df_Eliminati.to_csv('df_Eliminati_prova.csv', sep=',')

'''  
#  PLOT di punti caratteristici di un veicolo

ax51 = Plot_mappa(51, '1° Casa Giorno',   dati1v.TipoSosta==211, '.', 'm')
ax52 = Plot_mappa(52, '1° Casa Notte',    dati1v.TipoSosta==221, '.', 'k')
ax53 = Plot_mappa(53, '2° Casa Giorno',   dati1v.TipoSosta==212, '.', 'm')
ax54 = Plot_mappa(54, '2° Casa Notte',    dati1v.TipoSosta==222, '.', 'k')
ax55 = Plot_mappa(55, 'GENERICA Notte',   dati1v.TipoSosta==220, '.', 'k')
ax56 = Plot_mappa(56, 'GENERICA Giorno',  dati1v.TipoSosta==210, '.', 'k')
ax57 = Plot_mappa(57, 'TUTTE le soste',  dati1v.TipoSosta > 0, '.', 'r')


ax61 = Plot_mappa(61, '1° Lavoro',   dati1v.TipoSosta==215, '.', 'm')
ax62 = Plot_mappa(62, '2° Lavoro',   dati1v.TipoSosta==216, '.', 'm')

Plot_viaggio(ax51, 5157, 5182, '.', 'm')  # Alla Fig. "ax51" aggiunge il
#                                          tratto di viaggio da 5157 a 5182

'''

tempo("==== FINE                                  ", t0)
