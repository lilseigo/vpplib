import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

### Input:
n = 10                                         # Anzahl Schichten
T_ambient = 12                                 # Umgebungstemperatur in °C
T = 60                                       # Anfangstemperatur der Schichten in °C

### Geomotrie Tank:
height = 2                                     # Höhe Tank in m
diameter = 0.69                                # Durchmesser Tank in m
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

### Physikalische Größen:
lambda_eff = 1.52                                 # WMischung merher
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K

tolerance = height_node # für lokalisierung von komponenten
### Erzeugerdaten: 
#Inlet Supply
inlet_supply_T = 60                                     # Einspeisetemperatur in °C
inlet_supply_massflow = 0                                # Massenstrom vom Erzeuger kg/s
### Verbraucherdaten:
#Inlet Load
inlet_load_T= 12                                  # Rücklauftemperatur des Verbrauchers in °C
inlet_load_massflow = 0                                     # Massenstrom vom verbraucher kg/s
#Heizstab
auxiliary_heater_power = 0 # in Watt bzw J/s
auxiliary_heater_height = 1.1
#Wärmeübertrager 1 für Wärmeabgabe !!!Inlet unter Outlet!!!
heat_exchanger_1_inlet_T = 40
heat_exchanger_1_inlet_height = 0.3
heat_exchanger_1_outlet_height = 0.7
heat_exchanger_1_massflow = 0
heat_exchanger_1_nodes = max(math.ceil((heat_exchanger_1_outlet_height - heat_exchanger_1_inlet_height) / height_node),1)
#Wärmeübertrager 2 
heat_exchanger_2_inlet_T = 40
heat_exchanger_2_inlet_height = 0
heat_exchanger_2_outlet_height = 1
heat_exchanger_2_massflow = 0
heat_exchanger_2_nodes = max(math.ceil((heat_exchanger_2_outlet_height - heat_exchanger_2_inlet_height) / height_node),1)

#Wärmeübertrager 3 für Wärmeentnahme !!!Inlet über Outlet!!!
heat_exchanger_3_inlet_T = 12
heat_exchanger_3_inlet_height = 1
heat_exchanger_3_outlet_height = 0.3
heat_exchanger_3_massflow = 0
heat_exchanger_3_nodes = max(math.ceil((heat_exchanger_3_inlet_height - heat_exchanger_3_outlet_height) / height_node),1)
#Wärmeübertrager 4 für Wärmeentnahme 
heat_exchanger_4_inlet_T = 12
heat_exchanger_4_inlet_height = 1
heat_exchanger_4_outlet_height = 0.3
heat_exchanger_4_massflow = 0
heat_exchanger_4_nodes = max(math.ceil((heat_exchanger_4_inlet_height - heat_exchanger_4_outlet_height) / height_node),1)

### effektiver Massflow
massflow_eff = inlet_supply_massflow  - inlet_load_massflow                              
### Diese Bedingungen beschreiben wie der Fluß im Tank ist für die Bilanzierung
### Befüllen -> down = 1 und up = 0
### Entladen -> down = 0 und up = 1
if massflow_eff > 0:
    delta_down = 1
else:
    delta_down = 0
    
if massflow_eff < 0:
    delta_up = 1
else:
    delta_up = 0

### Definition des Differentialgleichungssystems für die Energiegleichungen. T Temperatur und t die Zeit
def differentialgleichungen(T, t):      
    # dTdt ist die Änderungsrate (Ableitung)
    # mithilfe der Funktion wird ein Array erstellt mit gleicher Dimension wie T und die Einträge sind alle 0                  
    dTdt = np.zeros_like(T)
    auxiliary_heater_activated = False

    heat_exchanger_1_activated = False 
    heat_exchanger_1_outlet_T = 0
    heat_exchanger_2_activated = False
    heat_exchanger_2_outlet_T = 0
    heat_exchanger_3_activated = False 
    heat_exchanger_3_outlet_T = 0
    heat_exchanger_4_activated = False
    heat_exchanger_4_outlet_T = 0

    a = 0 
    b = 0 
    c = 0
    d = 0
    for i in range(n):
        # Bedingung für die Mantelfläche
        if i == 0 or i == n-1:
            A_lateral_i = math.pi * diameter * height_node + A_node
        else:
            A_lateral_i = math.pi * diameter * height_node

        # Heizstab:            
        if not auxiliary_heater_activated and abs(height - auxiliary_heater_height - ((i-0.5)* height_node)) <= tolerance:
            delta_auxiliary_heater = 1
            auxiliary_heater_activated = True
        else:
            delta_auxiliary_heater = 0

        # Wärmeübertrager 1 Beladung:
        if not heat_exchanger_1_activated and abs(height - heat_exchanger_1_outlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_1_activated = True
            delta_heat_exchanger_1 = 1
            heat_exchanger_1_outlet_T = T[i]
        elif heat_exchanger_1_activated and a < heat_exchanger_1_nodes-1:
            delta_heat_exchanger_1 = 1
            a += 1
        else:
            delta_heat_exchanger_1 = 0

        # Wärmeübertrager 2 beladung:
        if not heat_exchanger_2_activated and abs(height - heat_exchanger_2_outlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_2_activated = True
            delta_heat_exchanger_2 = 1
            heat_exchanger_2_outlet_T = T[i]
        elif heat_exchanger_2_activated and b < heat_exchanger_2_nodes-1:
            delta_heat_exchanger_2 = 1
            b += 1
        else:
            delta_heat_exchanger_2 = 0
        # Wärmeübertrager 3 Entladung:
        if not heat_exchanger_3_activated and abs(height - heat_exchanger_3_inlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_3_activated = True
            delta_heat_exchanger_3 = 1
            heat_exchanger_3_outlet_T = T[i+(heat_exchanger_3_nodes-1)]
        elif heat_exchanger_3_activated and b < heat_exchanger_3_nodes-1:
            delta_heat_exchanger_3 = 1
            c += 1
        else:
            delta_heat_exchanger_3 = 0
        # Wärmeübertrager 4 Entladung:
        if not heat_exchanger_4_activated and abs(height - heat_exchanger_4_inlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_4_activated = True
            delta_heat_exchanger_4 = 1
            heat_exchanger_4_outlet_T = T[i+(heat_exchanger_4_nodes-1)]
        elif heat_exchanger_4_activated and b < heat_exchanger_4_nodes-1:
            delta_heat_exchanger_4 = 1
            d += 1
        else:
            delta_heat_exchanger_4 = 0

        # Oberste Schicht:
        if i == 0:
            dTdt[i] = (1 /(m * cw))*(- ((A_node*lambda_eff)/height_node)*(T[i] - T[i+1])  # Wärmerübetragung zwischen Knoten
                                     - U * A_lateral_i * (T[i] - T_ambient)    #Umgebungsverluste
                                     + delta_up * massflow_eff * cw * (T[i] - T[i+1])   # Massenstrom falls entladen wird      
                                     + inlet_supply_massflow * cw * (inlet_supply_T-T[i]) #Massenstrom supply
                                     + delta_auxiliary_heater * auxiliary_heater_power
                                     + (delta_heat_exchanger_1 * heat_exchanger_1_massflow * cw * (heat_exchanger_1_inlet_T-heat_exchanger_1_outlet_T))/heat_exchanger_1_nodes
                                     + (delta_heat_exchanger_2 * heat_exchanger_2_massflow * cw * (heat_exchanger_2_inlet_T-heat_exchanger_2_outlet_T))/heat_exchanger_2_nodes
                                     - (delta_heat_exchanger_3 * heat_exchanger_3_massflow * cw * (heat_exchanger_3_outlet_T-heat_exchanger_3_inlet_T))/heat_exchanger_3_nodes
                                     - (delta_heat_exchanger_4 * heat_exchanger_4_massflow * cw * (heat_exchanger_4_outlet_T-heat_exchanger_4_inlet_T))/heat_exchanger_4_nodes)  
        # Unterste Schicht:    
        elif i == n-1:
            dTdt[i] = (1 /(m * cw))*(+ ((A_node*lambda_eff)/height_node)*(T[i-1] - T[i])
                                     - U * A_lateral_i *   (T[i] - T_ambient)
                                     + delta_down *massflow_eff*cw* (T[i-1] - T[i])
                                     + inlet_load_massflow * cw * (inlet_load_T-T[i])  
                                     + delta_auxiliary_heater * auxiliary_heater_power
                                     + (delta_heat_exchanger_1 * heat_exchanger_1_massflow * cw * (heat_exchanger_1_inlet_T-heat_exchanger_1_outlet_T))/heat_exchanger_1_nodes
                                     + (delta_heat_exchanger_2 * heat_exchanger_2_massflow * cw * (heat_exchanger_2_inlet_T-heat_exchanger_2_outlet_T))/heat_exchanger_2_nodes
                                     - (delta_heat_exchanger_3 * heat_exchanger_3_massflow * cw * (heat_exchanger_3_outlet_T-heat_exchanger_3_inlet_T))/heat_exchanger_3_nodes
                                     - (delta_heat_exchanger_4 * heat_exchanger_4_massflow * cw * (heat_exchanger_4_outlet_T-heat_exchanger_4_inlet_T))/heat_exchanger_4_nodes)                             
        # mittlere Schichten:
        else:
            dTdt[i] = (1 /(m * cw))*(+ ((A_node*lambda_eff)/height_node)*(T[i-1] - T[i])
                                     - ((A_node*lambda_eff)/height_node)*(T[i] - T[i+1])
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_down *massflow_eff*cw* (T[i-1] - T[i])        
                                     + delta_up *massflow_eff*cw* (T[i] - T[i+1])         
                                     + delta_auxiliary_heater * auxiliary_heater_power
                                     + (delta_heat_exchanger_1 * heat_exchanger_1_massflow * cw * (heat_exchanger_1_inlet_T-heat_exchanger_1_outlet_T))/heat_exchanger_1_nodes
                                     + (delta_heat_exchanger_2 * heat_exchanger_2_massflow * cw * (heat_exchanger_2_inlet_T-heat_exchanger_2_outlet_T))/heat_exchanger_2_nodes
                                     - (delta_heat_exchanger_3 * heat_exchanger_3_massflow * cw * (heat_exchanger_3_outlet_T-heat_exchanger_3_inlet_T))/heat_exchanger_3_nodes
                                     - (delta_heat_exchanger_4 * heat_exchanger_4_massflow * cw * (heat_exchanger_4_outlet_T-heat_exchanger_4_inlet_T))/heat_exchanger_4_nodes)  
    return dTdt

### Eine Liste wird mit den Anfangsbedingungen erstellt
T0 = [T] * n

### erstellen einer Liste mit Start, Stop, step
t_values = np.arange(0, 10000, 300) 

### odeint löst das System. T_values ist ein array mit den verschiednen temperaturen der Schichten
T_values = odeint(differentialgleichungen, T0, t_values) 


 #Ausgabe der Temperaturen der Schichten
for i, temp in enumerate(T_values[15]):
    print(f"Schicht {i}: {temp}")

### Plot
for i in range(n):
    plt.plot(t_values/3600, T_values[:, i], label=f'Schicht {i+1}')
plt.xlabel('Zeit (h)')
plt.ylabel('Temperatur (°C)')
plt.title('Entwicklung der Temperaturen der Schichten über die Zeit')
plt.legend()
plt.show()
