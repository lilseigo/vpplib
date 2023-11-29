import pandas as pd
import numpy as np
import pypsa
import matplotlib.pyplot as plt

'''
Basic Information of Elektrolyseur
Hersteller:     Elogen SAS
Typ:            ELYTE 200
Verfahren:      PEM
Nennleistung:   1.000 kW

Benötigte H2-Produktion:    15 kt/a
[15,000,000 kg/a / 8,760 h/a ≈ 1,712.33 kg/h]
h2-Produktionsrate [kg/h]:  1.1712,33 kg/h 
Betriebszeit/Betriebszyklus:               
Effizienz:                  
Energiequellen:                 PV
Berechnung des Strombedarfs:    [A oder kW] unter berücksichtigung des Wirkungsggrades

Dimensionierung des Elektrolyseurs:
Temperatur
Betriebsdruck
Wirkunksgrad
Verwendeter Elektrolyt

'''

# Einlesen der PV-Daten
einlesen = "C:\\Users\\katri\\h2design\\ninja_pv_16.3471_47.8915.csv"
pv_data = pd.read_csv('ninja_pv_16.3471_47.8915.csv', sep=',', decimal='.', header=3)
loadprofile = pd.read_csv("Irgendeinprofiil.csv", sep = ',', decimal = '.')

#Technische Daten PV
invest_pv = 700 #€/kW
lifetime_pv = 20  #years
running_costs_pv = 0.05*invest_pv #€/(kW*a)

#Technische Daten Batteriespeicher
invest_battery = 500 #€/kWh
lifetime_battery = 20 #years
running_costs_battery = 0.01*invest_battery #€/(kW*a)
efficiency_battery_loading_unloading = 0.98 #Wirkungsgrad

#Technische Daten Elektrolyseur
invest_electrolyser = 610 #€/kW, including compressor
lifetime_electrolyser = 12 #years
running_costs_electrolyser = 0.03*invest_electrolyser #€/(kW*a)
efficiency_electrolyser  =  0.59 #including compressor (Heizwertbezogen)

#Technische Daten H2-Speicher
invest_h2_storage = 15 #€/kWh
lifetime_h2_storage = 20 #years
running_costs_h2_storage = 0.01*invest_h2_storage #€/(kW*a)

#Technische Daten Windkraft
invest_wind = 700 #€/kW
lifetime_wind = 25 #years
running_costs_wind = 13 #€/(kW*a)


# Implementierung des System
network = pypsa.Network()
network.set_snapshots(pv_data.index)

# Busse
network.add("Bus", "Solar_bus") # Verluste von PV zu Elektrolyseur
network.add("Bus", "Elektrolyseur_bus", ) # Verluste sind im Wirkungsgrad vermerkt (63 %)
network.add("Bus", "Ammoniak_bus", ) # 
network.add("Bus", "Speicher_bus") 

network.add('Generator', name='PV', bus='Solar_bus',
            p_max_pu=pv_data['electricity'],
            p_nom_extendable=True,
            capital_cost=invest_pv/lifetime_pv+running_costs_pv, p_nom=1750)

# Elektrolyseur zu Ammoniak Link

network.add("Link", "Elektrolyseur_link",
            bus0 = "Solar_bus",
            bus1 = "Elektrolyseur_bus",
            p_nom_extendable=True, 
            capital_cost=invest_electrolyser/lifetime_electrolyser+running_costs_electrolyser,
            efficiency=efficiency_electrolyser)

network.add("Link", "Grid_link",
            bus0 = "Elektrolyseur_bus",
            bus1 = "Grid_bus",
            p_nom = 50) # Übertragungskapazität in MW

network.add("Link", "Speicher_link",
            bus0="Elektrolyseur_bus",
            bus1="Wasserstoffspeicher_bus",
            p_nom=50)  # Übertragungskapazität in MW


#Load
network.add('Load', name='load_h2', bus='Elektrolyseur_bus', p_set=loadprofile["Energie"])


# # Plotten der Elektrolyseurleistung
# network.stores_t.e.plot()
# dataframe = pd.DataFrame(network.links_t.p0)
# dataframe.to_csv("Elektrolyseur.csv", index = False, sep =";", decimal = ",")

#Berechnung des Volumens des H2-Speichers
#size_h2_storage=network.stores.e_nom_opt["storage_h2"]/(33*24) #in Kubikmetern
#Berechnung der Fläche der PV-Anlage
#size_pv=network.generators.p_nom_opt["pv"]*8 #in Quadratmetern, mit 8m²/kwp