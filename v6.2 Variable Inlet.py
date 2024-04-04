import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

### Input:
n = 10                                         # Anzahl Schichten
T_ambient = 12                                 # Umgebungstemperatur in °C
T = 60                                         # Anfangstemperatur der Schichten in °C

### Geomotrie Tank:
height = 2                                     # Höhe Tank in m
diameter = 0.69                                # Durchmesser Tank in m
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

### Physikalische Größen:
lambda_w = 1.56                                 # Wasserleitfähigkeit in W/m*K
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K

tolerance = height_node
### Erzeugerdaten: 
#Inlet Supply
inlet_supply_T = 60                                     # Einspeisetemperatur in °C
inlet_supply_massflow = 0                               # Massenstrom vom Erzeuger kg/s
inlet_supply_height = 1
### Verbraucherdaten:
#Inlet Load
inlet_load_T= 12                                  # Rücklauftemperatur des Verbrauchers in °C
inlet_load_massflow = 500/3600                                     # Massenstrom vom verbraucher kg/s
inlet_load_height = 0
#Heizstab
auxiliary_heater_power = 0 #in Watt bzw J/s
auxiliary_heater_height = 1.1

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
    inlet_supply_activated = False
    inlet_load_activated = False
    auxiliary_heater_activated = False
    for i in range(n):
        # Bedingung für die Mantelfläche
        if i == 0 or i == n-1:
            A_lateral_i = math.pi * diameter * height_node + A_node
        else:
            A_lateral_i = math.pi * diameter * height_node

        # Inlet Supply:            
        if not inlet_supply_activated and abs(height - inlet_supply_height - (i* height_node)) <= tolerance:
            delta_inlet_supply = 1
            inlet_supply_activated = True
        else:
            delta_inlet_supply = 0

        # Inlet Load:            
        if not inlet_load_activated and abs(height - inlet_load_height - (i* height_node)) <= tolerance:
            delta_inlet_load = 1
            inlet_load_activated = True
        else:
            delta_inlet_load = 0

        # Heizstab:            
        if not auxiliary_heater_activated and abs(height - auxiliary_heater_height - (i* height_node)) <= tolerance:
            delta_auxiliary_heater = 1
            auxiliary_heater_activated = True
        else:
            delta_auxiliary_heater = 0

        # Oberste Schicht:
        if i == 0:
            dTdt[i] = (1 /(m * cw))*(- ((A_node*lambda_w)/height_node)*(T[i] - T[i+1])  # Wärmerübetragung zwischen Knoten
                                     - U * A_lateral_i * (T[i] - T_ambient)    #Umgebungsverluste
                                     + delta_up * massflow_eff * cw * (T[i] - T[i+1])   # Massenstrom falls entladen wird      
                                     + delta_inlet_supply * inlet_supply_massflow * cw * (inlet_supply_T-T[i]) 
                                     + delta_inlet_load * inlet_load_massflow * cw * (inlet_load_T-T[i])
                                     + delta_auxiliary_heater * auxiliary_heater_power)
        # Unterste Schicht:    
        elif i == n-1:
            dTdt[i] = (1 /(m * cw))*(+ ((A_node*lambda_w)/height_node)*(T[i-1] - T[i])
                                     - U * A_lateral_i *   (T[i] - T_ambient)
                                     + delta_down *massflow_eff*cw* (T[i-1] - T[i])
                                     + delta_inlet_supply * inlet_supply_massflow * cw * (inlet_supply_T-T[i])
                                     + delta_inlet_load * inlet_load_massflow * cw * (inlet_load_T-T[i])  
                                     + delta_auxiliary_heater * auxiliary_heater_power)                               
        # mittlere Schichten:
        else:
            dTdt[i] = (1 /(m * cw))*(+ ((A_node*lambda_w)/height_node)*(T[i-1] - T[i])
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i+1])
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_down *massflow_eff*cw* (T[i-1] - T[i])        
                                     + delta_up *massflow_eff*cw* (T[i] - T[i+1])         
                                     + delta_inlet_supply * inlet_supply_massflow * cw * (inlet_supply_T-T[i])
                                     + delta_inlet_load * inlet_load_massflow * cw * (inlet_load_T-T[i])  
                                     + delta_auxiliary_heater * auxiliary_heater_power)
    return dTdt

### Eine Liste wird mit den Anfangsbedingungen erstellt
T0 = [T] * n

### erstellen einer Liste mit Start, Stop, step
t_values = np.arange(0, 10000, 300) 

### odeint löst das System. T_values ist ein array mit den verschiednen temperaturen der Schichten
T_values = odeint(differentialgleichungen, T0, t_values) 



### Tabelle für erste und zweite Schicht
#df = pd.DataFrame({'Zeit': t_values, 'Schicht 1' : T_values[:,0], 'Schicht 2' : T_values[:,1]})
#print(df)



# Ausgabe der Temperaturen der Schichten
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