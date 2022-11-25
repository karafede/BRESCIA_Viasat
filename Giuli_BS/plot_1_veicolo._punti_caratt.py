# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 18:34:49 2021

@author: asus pc
"""

_1a_Casa_Giorno = dati1v.TipoSosta==211
_1a_Casa_Notte  = dati1v.TipoSosta==221
_2a_Casa_Giorno = dati1v.TipoSosta==212
_2a_Casa_Notte  = dati1v.TipoSosta==222

_1o_Lavoro      = dati1v.TipoSosta==215
_2o_Lavoro      = dati1v.TipoSosta==216

_GENERICA_Giorno= dati1v.TipoSosta==220
_GENERICA_Notte = dati1v.TipoSosta==210


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

_1a_Casa_Giorno = dati1v.TipoSosta==211
_1a_Casa_Notte  = dati1v.TipoSosta==221
_2a_Casa_Giorno = dati1v.TipoSosta==212
_2a_Casa_Notte  = dati1v.TipoSosta==222

_1o_Lavoro      = dati1v.TipoSosta==215
_2o_Lavoro      = dati1v.TipoSosta==216

_GENERICA_Giorno= dati1v.TipoSosta==220
_GENERICA_Notte = dati1v.TipoSosta==210

ax50 = Plot_mappa(50, 'Punti Caratteristici.',   dati1v.TipoSosta == -1, '.', 'm')
Plot_viaggio(ax50, 3157, 3179, '.', 'm')  # Alla Fig. "ax51" aggiunge il
#                                          tratto di viaggio da 3157 a 3182
Plot_viaggio(ax50, 3157, 3179, '-', 'm')  


