import pandas as pd
import numpy as np
import pypsa
import matplotlib.pyplot as plt


# Basic Information of Elektrolyseur
# Hersteller:     Elogen SAS
# Typ:            ELYTE 200
# Verfahren:      PEM
# Nennleistung:   1.000 kW

# Benötigte H2-Produktion:    15 kt/a
# [15,000,000 kg/a / 8,760 h/a ≈ 1,712.33 kg/h]
# h2-Produktionsrate [kg/h]:  1.1712,33 kg/h 
# Betriebszeit/Betriebszyklus:               
# Effizienz:                  
# Energiequellen:                 PV
# Berechnung des Strombedarfs:    [A oder kW] unter berücksichtigung des Wirkungsggrades

# Dimensionierung des Elektrolyseurs:
# Temperatur
# Betriebsdruck
# Wirkunksgrad
# Verwendeter Elektrolyt



# Einlesen der PV-Daten
#einlesen = "C:\\Users\\katri\\h2design\\ninja_pv_16.3471_47.8915.csv"
pv_data=pd.read_csv('1kWp_ninja_pv.csv', sep=',', decimal='.', header=3)
loadprofile=pd.read_csv('z_Lastprofil.csv', sep = ',', decimal = '.')
#---------------------------------------------------------------------
#Technische Daten PV
invest_pv = 700 #€/kW
lifetime_pv = 20  #years
running_costs_pv = 0.05*invest_pv #€/(kW*a)

#Technische Daten Elektrolyseur
invest_electrolyser = 610 #€/kW, including compressor
lifetime_electrolyser = 12 #years
running_costs_electrolyser = 0.03*invest_electrolyser #€/(kW*a)
efficiency_electrolyser  =  0.63 #including compressor (Heizwertbezogen)

#Technische Daten Haber-Bosch-Verfahren  #keine Richtige Werte
invest_Haber_Bosch_Verfahren = 200 #€/kWh
lifetime_Haber_Bosch_Verfahren = 20 #years
running_costs_Haber_Bosch_Verfahren = 0.03*invest_Haber_Bosch_Verfahren #€/(kW*a)
efficiency_Haber_Bosch_Verfahren  =  0.9 #including compressor (Heizwertbezogen)

#Technische Daten Ammoniak-Speicher             #keine Richtige Werte
invest_Ammoniak_storage = 12 #€/kWh
lifetime_Ammoniak_storage = 20 #years
running_costs_Ammoniak_storage = 0.01*invest_Ammoniak_storage #€/(kW*a)


#Transport Schiff                   #Keine Richtigen Werte
invest_Schiff = 0.03 #€/kWh
lifetime_Schiff = 20 #years
running_costs_Schiff = 0.01*invest_Schiff #€/(kW*a)
efficiency_Schiff  =  0.98

#Technische Daten Ammoniak Cracking             #Keine richtigen Werte
invest_Ammoniak_Cracking = 300 #€/kW
lifetime_Ammoniak_Cracking = 12 #years
running_costs_Ammoniak_Cracking = 0.03*invest_electrolyser #€/(kW*a)
efficiency_Ammoniak_Cracking  =  0.8 #including compressor (Heizwertbezogen)

#Transport Pipeline                   #Keine Richtigen Werte
invest_Pipeline = 15 #€/kWh
lifetime_Pipeline = 20 #years
running_costs_Pipeline = 0.01*invest_Ammoniak_Cracking #€/(kW*a)
efficiency_Pipeline  =  0.99

#Technische Daten H2-Speicher
invest_GH2_storage_Köln = 15 #€/kWh
lifetime_GH2_storage_Köln = 20 #years
running_costs_GH2_storage_Köln = 0.01*invest_h2_storage #€/(kW*a)
efficiency_GH2_storage_Köln  =  1 


#------------------------------------------------------------------------------

# Implementierung des System
network = pypsa.Network()
network.set_snapshots(pv_data.index)

# Busse
network.add("Bus", "Solar_bus") 
network.add("Bus", "Elektrolyseur_bus", ) 
network.add("Bus", "Yemen" ) # 
network.add("Bus", "Antwerpen")
network.add("Bus", "Antwerpen_GH2")
network.add("Bus", "Köln")

network.add('Generator', name='PV', bus='Solar_bus',
            p_max_pu=pv_data['electricity'],
            p_nom_extendable=True,
            capital_cost=invest_pv/lifetime_pv+running_costs_pv)

# Elektrolyseur zu Ammoniak Link

network.add("Link", "Elektrolyseur",
            bus0 = "Solar_bus",
            bus1 = "Elektrolyseur_bus",
            p_nom_extendable=True, 
            capital_cost=invest_electrolyser/lifetime_electrolyser+running_costs_electrolyser,
            efficiency=efficiency_electrolyser)

network.add("Link", "Haber-Bosch-Verfahren",  # GH2 zu Ammoniak
            bus0 = "Elektrolyseur_bus",
            bus1 = "Yemen",
            p_nom_extendable=True,
            capital_cost=invest_Haber_Bosch_Verfahren/lifetime_Haber_Bosch_Verfahren+running_costs_Haber_Bosch_Verfahren,
            efficiency=efficiency_Haber_Bosch_Verfahren) 



network.add("Link", "Transport_Schiff",
                bus0="Yemen",
                bus1="Antwerpen",
                capital_cost=invest_Schiff/lifetime_Schiff+running_costs_Schiff,
                p_nom_extendable=True,
                efficiency=efficiency_Schiff,) 

network.add("Link", "Ammoniak_Cracking",
            bus0="Antwerpen",
            bus1="Antwerpen_GH2",
            capital_cost=invest_Ammoniak_Cracking/lifetime_Ammoniak_Cracking+running_costs_Ammoniak_Cracking,
            p_nom_extendable=True,
            efficiency=efficiency_Ammoniak_Cracking)  
network.add("Link", "Pipeline",
            bus0="Antwerpen_GH2",
            bus1="Köln",
            p_nom_extendable=True,
            capital_cost=invest_Pipeline/lifetime_Pipeline+running_costs_Pipeline,
            efficiency=efficiency_Pipeline) 


#Load
network.add('Load', name='GH2_Verbrauch', bus='Köln', p_set=loadprofile["Energie"])

#Store
network.add('Store', name='Yemen_Speicher', bus='Yemen',e_nom_extendable=True, e_cyclic=1,
            capital_cost=invest_Ammoniak_storage/lifetime_Ammoniak_storage+running_costs_Ammoniak_storage,
            e_nom=42000)

network.add('Store', name='Antwerpen_Speicher', bus='Antwerpen',e_nom_extendable=True, e_cyclic=1,
            capital_cost=invest_Ammoniak_storage/lifetime_Ammoniak_storage+running_costs_Ammoniak_storage,
            e_nom=42000)



network.add('Store', name='Köln_Speicher', bus='Köln',e_nom_extendable=True, e_cyclic=1,
            capital_cost=invest_h2_storage/lifetime_h2_storage+running_costs_h2_storage,
            e_nom=42000)









#Berechnung der anfänglichen Investitionskosten aller Komponenten
absolute_invest_pv=network.generators.p_nom_opt["PV"]*invest_pv
absolute_invest_electrolyser=network.links.p_nom_opt["Elektrolyseur"]*invest_electrolyser
absolute_invest_Haber_Bosch_Verfahren=network.links.p_nom_opt["Haber-Bosch-Verfahren"]*invest_Haber_Bosch_Verfahren
absolute_invest_Ammoniak_storage_Yemen=network.stores.e_nom_opt["Yemen_Speicher"]*invest_Ammoniak_storage
absolute_invest_Schiff=network.links.p_nom_opt["Transport_Schiff"]*invest_Schiff
absolute_invest_Ammoniak_storage_Antwerpen=network.stores.e_nom_opt["Antwerpen_Speicher"]*invest_Ammoniak_storage
absolute_invest_Ammoniak_Cracking=network.links.p_nom_opt["Ammoniak_Cracking"]*invest_Ammoniak_Cracking
absolute_invest_Pipeline=network.links.p_nom_opt["Pipeline"]*invest_Pipeline
absolute_invest_GH2_storage_Köln=network.stores.e_nom_opt["Köln_Speicher"]*invest_GH2_storage_Köln


absolute_invest_total = (
    absolute_invest_pv +
    absolute_invest_electrolyser +
    absolute_invest_Haber_Bosch_Verfahren +
    absolute_invest_Ammoniak_storage_Yemen +
    absolute_invest_Schiff +
    absolute_invest_Ammoniak_storage_Antwerpen +
    absolute_invest_Ammoniak_Cracking +
    absolute_invest_Pipeline +
    absolute_invest_GH2_storage_Köln)


#Prozentuale Investitionkosten der einzelnen Komponenten
# Berechnung der prozentualen Anteile
percental_invest_pv = (absolute_invest_pv / absolute_invest_total) * 100
percental_invest_electrolyser = (absolute_invest_electrolyser / absolute_invest_total) * 100
percental_invest_Haber_Bosch_Verfahren = (absolute_invest_Haber_Bosch_Verfahren / absolute_invest_total) * 100
percental_invest_Ammoniak_storage_Yemen = (absolute_invest_Ammoniak_storage_Yemen / absolute_invest_total) * 100
percental_invest_Schiff = (absolute_invest_Schiff / absolute_invest_total) * 100
percental_invest_Ammoniak_storage_Antwerpen = (absolute_invest_Ammoniak_storage_Antwerpen / absolute_invest_total) * 100
percental_invest_Ammoniak_Cracking = (absolute_invest_Ammoniak_Cracking / absolute_invest_total) * 100
percental_invest_Pipeline = (absolute_invest_Pipeline / absolute_invest_total) * 100
percental_invest_GH2_storage_Köln = (absolute_invest_GH2_storage_Köln / absolute_invest_total) * 100

name = [
    'PV',
    'Elektrolyseur',
    'Haber_Bosch_Verfahren',
    'Ammoniak-Speicher-Yemen',
    'Schiff',
    'Ammoniak-Speicher-Antwerpen',
    'Ammoniak_Cracking',
    'Pipeline',
    'GH2-Speicher-Köln'
]

    
    
werte = [
    percental_invest_pv,
    percental_invest_electrolyser,
    percental_invest_Haber_Bosch_Verfahren,
    percental_invest_Ammoniak_storage_Yemen,
    percental_invest_Schiff,
    percental_invest_Ammoniak_storage_Antwerpen,
    percental_invest_Ammoniak_Cracking,
    percental_invest_Pipeline,
    -percental_invest_GH2_storage_Köln
]
    
kosten_werte = [
    absolute_invest_pv,
    absolute_invest_electrolyser,
    absolute_invest_Haber_Bosch_Verfahren,
    absolute_invest_Ammoniak_storage_Yemen,
    absolute_invest_Schiff,
    absolute_invest_Ammoniak_storage_Antwerpen,
    absolute_invest_Ammoniak_Cracking,
    absolute_invest_Pipeline,
    absolute_invest_GH2_storage_Köln
]
    
kosten_werte_formatiert = ['{} €'.format(round(kosten,2)) for kosten in kosten_werte] #Kostenwerte werden gerundet

labels = [f'{begriff}: {wert}' for begriff, wert in zip(name, kosten_werte_formatiert)]
# Zeigt nur die Werte die über 0€ sind
non_zero_werte = [wert for wert in werte if wert != 0]
non_zero_labels = [label for label, wert in zip(labels, werte) if wert != 0]

plt.pie(non_zero_werte, labels=non_zero_labels, autopct='%1.1f%%', startangle=140)
plt.title('Anteil der Investitionskosten der einzelnen Komponenten')
plt.axis('equal')

total_costs_formatted = '{} €'.format(round(absolute_invest_total,2))
plt.text(0.0, -1.3, 'Investitionskosten: {}'.format(total_costs_formatted), ha='center', fontsize=12)
plt.show()




print("Absolute Investitionskosten PV: {:.2f} €".format(absolute_invest_pv))
print("Absolute Investitionskosten Elektrolyseur: {:.2f} €".format(absolute_invest_electrolyser))
print("Absolute Investitionskosten Haber-Bosch-Verfahren: {:.2f} €".format(absolute_invest_Haber_Bosch_Verfahren))
print("Absolute Investitionskosten Ammoniak-Speicher Yemen: {:.2f} €".format(absolute_invest_Ammoniak_storage_Yemen))
print("Absolute Investitionskosten Transport Schiff: {:.2f} €".format(absolute_invest_Schiff))
print("Absolute Investitionskosten Ammoniak-Speicher Antwerpen: {:.2f} €".format(absolute_invest_Ammoniak_storage_Antwerpen))
print("Absolute Investitionskosten Ammoniak-Cracking: {:.2f} €".format(absolute_invest_Ammoniak_Cracking))
print("Absolute Investitionskosten Pipeline: {:.2f} €".format(absolute_invest_Pipeline))
print("Absolute Investitionskosten H2-Speicher Köln: {:.2f} €".format(absolute_invest_GH2_storage_Köln))


































#jährliche Kosten der Komponenten
yearly_costs_pv=network.generators.p_nom_opt["PV"]*(invest_pv/lifetime_pv+running_costs_pv)
yearly_costs_electrolyser=network.links.p_nom_opt["Elektrolyseur"]*(invest_electrolyser/lifetime_electrolyser+running_costs_electrolyser)
yearly_costs_Haber_Bosch_Verfahren=network.links.p_nom_opt["Haber-Bosch-Verfahren"]*(invest_Haber_Bosch_Verfahren/lifetime_Haber_Bosch_Verfahren+running_costs_Haber_Bosch_Verfahren)
yearly_costs_Ammoniak_storage_Yemen=network.stores.e_nom_opt["Yemen_Speicher"]*(invest_Ammoniak_storage/lifetime_Ammoniak_storage+running_costs_Ammoniak_storage)
yearly_costs_Schiff=network.links.p_nom_opt["Transport_Schiff"]*(invest_Schiff/lifetime_Schiff+running_costs_Schiff)
yearly_costs_invest_Ammoniak_storage_Antwerpen=network.stores.e_nom_opt["Antwerpen_Speicher"]*(invest_Ammoniak_storage/lifetime_Ammoniak_storage+running_costs_Ammoniak_storage)
yearly_costs_Ammoniak_Cracking=network.links.p_nom_opt["Ammoniak_Cracking"]*(invest_Ammoniak_Cracking/lifetime_Ammoniak_Cracking+running_costs_Ammoniak_Cracking)
yearly_costs_Pipeline=network.links.p_nom_opt["Pipeline"]*(invest_Pipeline/lifetime_Pipeline+running_costs_Pipeline)
yearly_costs_GH2_storage_Köln=network.stores.e_nom_opt["Köln_Speicher"]*(invest_GH2_storage_Köln/lifetime_GH2_storage_Köln+running_costs_GH2_storage_Köln)

yearly_costs_total = (
    yearly_costs_pv +
    yearly_costs_electrolyser +
    yearly_costs_Haber_Bosch_Verfahren +
    yearly_costs_Ammoniak_storage_Yemen +
    yearly_costs_Schiff +
    yearly_costs_Ammoniak_storage_Antwerpen +
    yearly_costs_Ammoniak_Cracking +
    yearly_costs_Pipeline +
    yearly_costs_GH2_storage_Köln



#Prozentuale jährliche Kosten der einzelnen Komponenten
percental_yearly_costs_pv = (yearly_costs_pv / total_yearly_costs) * 100
percental_yearly_costs_electrolyser = (yearly_costs_electrolyser / total_yearly_costs) * 100
percental_yearly_costs_Haber_Bosch_Verfahren = (yearly_costs_Haber_Bosch_Verfahren / total_yearly_costs) * 100
percental_yearly_costs_Ammoniak_storage_Yemen = (yearly_costs_Ammoniak_storage_Yemen / total_yearly_costs) * 100
percental_yearly_costs_Schiff = (yearly_costs_Schiff / total_yearly_costs) * 100
percental_yearly_costs_Ammoniak_storage_Antwerpen = (yearly_costs_Ammoniak_storage_Antwerpen / total_yearly_costs) * 100
percental_yearly_costs_Ammoniak_Cracking = (yearly_costs_Ammoniak_Cracking / total_yearly_costs) * 100
percental_yearly_costs_Pipeline = (yearly_costs_Pipeline / total_yearly_costs) * 100
percental_yearly_costs_GH2_storage_Köln = (yearly_costs_GH2_storage_Köln / total_yearly_costs) * 100


name = [
    'PV',
    'Elektrolyseur',
    'Haber_Bosch_Verfahren',
    'Ammoniak-Speicher-Yemen',
    'Schiff',
    'Ammoniak-Speicher-Antwerpen',
    'Ammoniak_Cracking',
    'Pipeline',
    'GH2-Speicher-Köln'
]

werte = [
    percental_yearly_costs_pv,
    percental_yearly_costs_electrolyser,
    percental_yearly_costs_Haber_Bosch_Verfahren,
    percental_yearly_costs_Ammoniak_storage_Yemen,
    percental_yearly_costs_Schiff,
    percental_yearly_costs_Ammoniak_storage_Antwerpen,
    percental_yearly_costs_Ammoniak_Cracking,
    percental_yearly_costs_Pipeline,
    percental_yearly_costs_GH2_storage_Köln
    

kosten_werte=[
    yearly_costs_pv,
    yearly_costs_electrolyser,
    yearly_costs_Haber_Bosch_Verfahren,
    yearly_costs_Ammoniak_storage_Yemen,
    yearly_costs_Schiff,
    yearly_costs_invest_Ammoniak_storage_Antwerpen,
    yearly_costs_Ammoniak_Cracking,
    yearly_costs_Pipeline,
    yearly_costs_GH2_storage_Köln
]

    kosten_werte_formatiert = ['{} €'.format(round(kosten,2)) for kosten in kosten_werte]
labels = ['{}: {}'.format(begriff, wert) for begriff, wert in zip(name, kosten_werte_formatiert)]

# Zeigt nur die Werte die über 0€ sind an
non_zero_werte = [wert for wert in werte if wert != 0]
non_zero_labels = [label for label, wert in zip(labels, werte) if wert != 0]

plt.pie(non_zero_werte, labels=non_zero_labels, autopct='%1.1f%%',startangle=136)
plt.title('Anteil der jährlichen Kosten der einzelnen Komponenten')
plt.axis('equal')

total_costs_formatted = '{} €'.format(round(yearly_costs_total,2))
plt.text(0.0, -1.3, 'Jährliche Gesamtkosten: {}'.format(total_costs_formatted), ha='center', fontsize=12)












