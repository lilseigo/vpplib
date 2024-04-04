import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
#################################################################################################
### Angaben:
# Allgemein:
n = 10                                         # Anzahl Schichten
T_ambient = 12                                 # Umgebungstemperatur in °C
T_start = 12                                  # Anfangstemperatur der Schichten in °C

# Tank:
height = 2                                   # Höhe Tank in m
diameter = 0.7                                   # Durchmesser Tank in m
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K

# Physikalische Größen:
lambda_eff = 1.52                              # effektiver Lambda Wert um Einbauten und Wand zu berücksichtigen
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
inversion = 100

# Berechnungen Tank:
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
m = m_tank / n                                 # masse einer einzelnen Schicht in kg
#################################################################################################
### Komponenten:
## Erzeuger:
# Heizstab
auxiliary_heater_power = 2000 # in Watt bzw J/s
auxiliary_heater_height = 1.1

# Wärmeübertrager 1 für Wärmezufuhr ( Inlet über Outlet)
heat_exchanger_1_massflow = 0 # Massenstrom des WÜ
heat_exchanger_1_inlet_T = 50        # Temeperatur des WÜ am Einlass
heat_exchanger_1_inlet_height = 1
heat_exchanger_1_outlet_height = 0.5

# Wärmeübertrager 2 für Wärmezufuhr 
heat_exchanger_2_massflow = 0
heat_exchanger_2_inlet_T = 25
heat_exchanger_2_inlet_height = 0.6
heat_exchanger_2_outlet_height = 0.2

# Direkte Beladung 1 !!!Inlet über outlet!!!
direct_supply_1_massflow = 0        # Massenstrom vom Erzeuger kg/s
direct_supply_1_inlet_T = 55        # Einspeisetemperatur in °C
direct_supply_1_inlet_height  = 2
direct_supply_1_outlet_height  = 0.2
#################################################################################################
### Verbraucherdaten:
# Wärmeübertrager 3 für Wärmeentnahme !!!Inlet unter Outlet!!!
heat_exchanger_3_massflow = 0
heat_exchanger_3_inlet_T = 35
heat_exchanger_3_inlet_height = 1
heat_exchanger_3_outlet_height = 1.5

# Wärmeübertrager 4 für Wärmeentnahme 
heat_exchanger_4_massflow = 0
heat_exchanger_4_inlet_T = 35
heat_exchanger_4_inlet_height = 1
heat_exchanger_4_outlet_height = 1.5

# Direkte Entladung 1 !!! inlet unter outlet !!!
direct_load_1_massflow = 0                             # Massenstrom vom verbraucher kg/s
direct_load_1_inlet_T = 12                              # Rücklauftemperatur des Verbrauchers in °C
direct_load_1_inlet_height = 0
direct_load_1_outlet_height = 2
#################################################################################################
# Berechnungen der Anzahl der Knoten, die von der Komponente betroffen sind:
heat_exchanger_1_nodes = max(math.ceil((heat_exchanger_1_inlet_height - heat_exchanger_1_outlet_height) / height_node),1)
heat_exchanger_2_nodes = max(math.ceil((heat_exchanger_2_inlet_height - heat_exchanger_2_outlet_height) / height_node),1)
direct_supply_1_nodes = max(math.ceil((direct_supply_1_inlet_height - direct_supply_1_outlet_height) / height_node),1)
heat_exchanger_3_nodes = max(math.ceil((heat_exchanger_3_outlet_height - heat_exchanger_3_inlet_height) / height_node),1)
heat_exchanger_4_nodes = max(math.ceil((heat_exchanger_4_outlet_height - heat_exchanger_4_inlet_height) / height_node),1)
direct_load_1_nodes = max(math.ceil((direct_load_1_outlet_height - direct_load_1_inlet_height) / height_node),1)
# Toleranz für Lokalisierung der Konponenten im DGL
tolerance = height_node
#################################################################################################
# Definition der Funktionen 
def ambient_transfer(U,A_lateral,T,T_ambient):
    return U * A_lateral * (T - T_ambient)
def cond_transfer(A,lam,height,T1,T2):
    return ((A*lam)/height)*(T1-T2)
def conv_transfer(m,c,T1,T2):
    return m*c*(T1-T2)
def hx_heat(m,c,T1,T2,N):
    return (m*c*(T1-T2))/N
# Definition des Differentialgleichungssystems
def differentialgleichungen(T, t):                
    dTdt = np.zeros_like(T) # mithilfe der Funktion wird ein Array erstellt mit gleicher Dimension wie T und die Einträge sind alle 0  
    # Booleans für Lokalisierung von den Komponenten (und ggf Outlet Temperatur initialisieren)
    direct_supply_1_activated = False
    direct_load_1_activated = False
    auxiliary_heater_activated = False
    heat_exchanger_1_activated = False 
    heat_exchanger_1_outlet_T = 0
    heat_exchanger_2_activated = False
    heat_exchanger_2_outlet_T = 0
    heat_exchanger_3_activated = False 
    heat_exchanger_3_outlet_T = 0
    heat_exchanger_4_activated = False
    heat_exchanger_4_outlet_T = 0
    # Laufvariabeln für Lokalisierung von Komponenten
    a = 0 
    b = 0 
    c = 0
    d = 0
    e = 0
    f = 0
    for i in range(n):
        # Bedingung für die Mantelfläche
        if i == 0 or i == n-1:
            A_lateral_i = math.pi * diameter * height_node + A_node
        else:
            A_lateral_i = math.pi * diameter * height_node
        # Bedingungen für Lokalisieren der Schichten, welche von der jeweiligen Komponente Betroffen ist
            
        # Heizstab:            
        if not auxiliary_heater_activated and abs(height - auxiliary_heater_height - ((i-0.5)* height_node)) <= tolerance:
            delta_auxiliary_heater = 1
            auxiliary_heater_activated = True
        else:
            delta_auxiliary_heater = 0

        # Wärmeübertrager 1 Beladung:
        if not heat_exchanger_1_activated and abs(height - heat_exchanger_1_inlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_1_activated = True
            delta_heat_exchanger_1 = 1
            heat_exchanger_1_outlet_T = T[i+heat_exchanger_1_nodes-1]
        elif heat_exchanger_1_activated and a < heat_exchanger_1_nodes-1:
            delta_heat_exchanger_1 = 1
            a += 1
        else:
            delta_heat_exchanger_1 = 0

        # Wärmeübertrager 2 Beladung:
        if not heat_exchanger_2_activated and abs(height - heat_exchanger_2_inlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_2_activated = True
            delta_heat_exchanger_2 = 1
            heat_exchanger_2_outlet_T = T[i+heat_exchanger_2_nodes-1]
        elif heat_exchanger_2_activated and b < heat_exchanger_2_nodes-1:
            delta_heat_exchanger_2 = 1
            b += 1
        else:
            delta_heat_exchanger_2 = 0

        # Wärmeübertrager 3 Entladung:
        if not heat_exchanger_3_activated and abs(height - heat_exchanger_3_outlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_3_activated = True
            delta_heat_exchanger_3 = 1
            heat_exchanger_3_outlet_T = T[i]
        elif heat_exchanger_3_activated and b < heat_exchanger_3_nodes-1:
            delta_heat_exchanger_3 = 1
            c += 1
        else:
            delta_heat_exchanger_3 = 0

        # Wärmeübertrager 4 Entladung:
        if not heat_exchanger_4_activated and abs(height - heat_exchanger_4_outlet_height - ((i-0.5) * height_node)) <= tolerance:
            heat_exchanger_4_activated = True
            delta_heat_exchanger_4 = 1
            heat_exchanger_4_outlet_T = T[i]
        elif heat_exchanger_4_activated and b < heat_exchanger_4_nodes-1:
            delta_heat_exchanger_4 = 1
            d += 1
        else:
            delta_heat_exchanger_4 = 0

        # Direkte Beladung
        if not direct_supply_1_activated and abs(height - direct_supply_1_inlet_height - ((i-0.5) * height_node)) <= tolerance:
            direct_supply_1_activated = True
            delta_direct_supply_1 = 1
            delta_direct_supply_1_down = 0
        elif direct_supply_1_activated and e < direct_supply_1_nodes-1:
            delta_direct_supply_1 = 0
            delta_direct_supply_1_down = 1
            e += 1
        else:
            delta_direct_supply_1 = 0
            delta_direct_supply_1_down = 0

        # direkte Entladung 
        if not direct_load_1_activated and abs(height - direct_load_1_outlet_height - ((i-0.5) * height_node)) <= tolerance:
            direct_load_1_activated = True
            delta_direct_load_1 = 0
            delta_direct_load_1_up = 1
        elif direct_load_1_activated and f < direct_load_1_nodes-1:
            delta_direct_load_1 = 0
            delta_direct_load_1_up = 1
            f += 1
            if f + 1 == direct_load_1_nodes:
                delta_direct_load_1 = 1
                delta_direct_load_1_up = 0
        else:
            delta_direct_load_1 = 0
            delta_direct_load_1_up = 0

        # Oberste Schicht:
        if i == 0:
            if T[i] < T[i+1]:
                lambda_eff_inv = lambda_eff * inversion * abs(T[i] - T[i+1])
            else:
                lambda_eff_inv = lambda_eff
            dTdt[i] = (1 /(m * cw))*(- ambient_transfer(U,A_lateral_i,T[i],T_ambient)  
                                     - cond_transfer(A_node,lambda_eff_inv,height_node,T[i],T[i+1])
                                     + delta_direct_supply_1 * conv_transfer(direct_supply_1_massflow,cw,direct_supply_1_inlet_T,T[i])
                                     + delta_direct_load_1 * conv_transfer(direct_load_1_massflow,cw,direct_load_1_inlet_T,T[i])   
                                     - delta_direct_load_1_up * conv_transfer(direct_load_1_massflow,cw,T[i],T[i+1]) 
                                     + delta_auxiliary_heater * auxiliary_heater_power
                                     + delta_heat_exchanger_1 * hx_heat(heat_exchanger_1_massflow,cw,heat_exchanger_1_inlet_T,heat_exchanger_1_outlet_T,heat_exchanger_1_nodes)                                                     
                                     + delta_heat_exchanger_2 * hx_heat(heat_exchanger_2_massflow,cw,heat_exchanger_2_inlet_T,heat_exchanger_2_outlet_T,heat_exchanger_2_nodes)
                                     - delta_heat_exchanger_3 * hx_heat(heat_exchanger_3_massflow,cw,heat_exchanger_3_outlet_T,heat_exchanger_3_inlet_T,heat_exchanger_3_nodes)  
                                     - delta_heat_exchanger_4 * hx_heat(heat_exchanger_4_massflow,cw,heat_exchanger_4_outlet_T,heat_exchanger_4_inlet_T,heat_exchanger_4_nodes))
        # Unterste Schicht:    
        elif i == n-1:
            if T[i] > T[i-1]:
                lambda_eff_inv = lambda_eff * inversion * abs(T[i] - T[i-1])
            else:
                lambda_eff_inv = lambda_eff
            dTdt[i] = (1 /(m * cw))*(- ambient_transfer(U,A_lateral_i,T[i],T_ambient) 
                                     + cond_transfer(A_node,lambda_eff_inv,height_node,T[i-1],T[i])
                                     + delta_direct_load_1 * conv_transfer(direct_load_1_massflow,cw,direct_load_1_inlet_T,T[i])
                                     + delta_direct_supply_1 * conv_transfer(direct_supply_1_massflow,cw,direct_supply_1_inlet_T,T[i]) 
                                     + delta_direct_supply_1_down * conv_transfer(direct_supply_1_massflow,cw,T[i-1],T[i])
                                     + delta_auxiliary_heater * auxiliary_heater_power
                                     + delta_heat_exchanger_1 * hx_heat(heat_exchanger_1_massflow,cw,heat_exchanger_1_inlet_T,heat_exchanger_1_outlet_T,heat_exchanger_1_nodes)                                                     
                                     + delta_heat_exchanger_2 * hx_heat(heat_exchanger_2_massflow,cw,heat_exchanger_2_inlet_T,heat_exchanger_2_outlet_T,heat_exchanger_2_nodes)
                                     - delta_heat_exchanger_3 * hx_heat(heat_exchanger_3_massflow,cw,heat_exchanger_3_outlet_T,heat_exchanger_3_inlet_T,heat_exchanger_3_nodes)  
                                     - delta_heat_exchanger_4 * hx_heat(heat_exchanger_4_massflow,cw,heat_exchanger_4_outlet_T,heat_exchanger_4_inlet_T,heat_exchanger_4_nodes))                             
        # mittlere Schichten:
        else:
            if T[i] < T[i+1]:
                lambda_eff_inv_1 = lambda_eff * inversion * abs(T[i] - T[i+1])
            else:
                lambda_eff_inv_1 = lambda_eff
            if T[i] > T[i-1]:
                lambda_eff_inv_2 = lambda_eff * inversion * abs(T[i] - T[i-1])
            else:
                lambda_eff_inv_2 = lambda_eff
            dTdt[i] = (1 /(m * cw))*(- ambient_transfer(U,A_lateral_i,T[i],T_ambient)
                                     + cond_transfer(A_node,lambda_eff_inv_2,height_node,T[i-1],T[i])
                                     - cond_transfer(A_node,lambda_eff_inv_1,height_node,T[i],T[i+1])
                                     + delta_direct_supply_1 * conv_transfer(direct_supply_1_massflow,cw,direct_supply_1_inlet_T,T[i])
                                     + delta_direct_load_1 * conv_transfer(direct_load_1_massflow,cw,direct_load_1_inlet_T,T[i])
                                     + delta_direct_supply_1_down * conv_transfer(direct_supply_1_massflow,cw,T[i-1],T[i])
                                     - delta_direct_load_1_up * conv_transfer(direct_load_1_massflow,cw,T[i],T[i+1])
                                     + delta_auxiliary_heater * auxiliary_heater_power   
                                     + delta_heat_exchanger_1 * hx_heat(heat_exchanger_1_massflow,cw,heat_exchanger_1_inlet_T,heat_exchanger_1_outlet_T,heat_exchanger_1_nodes)                                                     
                                     + delta_heat_exchanger_2 * hx_heat(heat_exchanger_2_massflow,cw,heat_exchanger_2_inlet_T,heat_exchanger_2_outlet_T,heat_exchanger_2_nodes)
                                     - delta_heat_exchanger_3 * hx_heat(heat_exchanger_3_massflow,cw,heat_exchanger_3_outlet_T,heat_exchanger_3_inlet_T,heat_exchanger_3_nodes)  
                                     - delta_heat_exchanger_4 * hx_heat(heat_exchanger_4_massflow,cw,heat_exchanger_4_outlet_T,heat_exchanger_4_inlet_T,heat_exchanger_4_nodes))
    return dTdt

# Eine Liste wird mit den Anfangsbedingungen erstellt
T0 = [T_start] * n

# erstellen einer Liste mit Start, Stop, step
t_values = np.arange(0, 10000, 300) 

# odeint löst das System. T_values ist ein array mit den verschiednen temperaturen der Schichten
T_values = odeint(differentialgleichungen, T0, t_values) 

#for i, temp in enumerate(T_values[0]):
#    print(f"Schicht {i}: {temp}")

# Schichtenplot
plt.figure(figsize=(10, 6))
for i in range(n):
    plt.plot(t_values/3600, T_values[:, i], label=f'Schicht {i+1}')
plt.xlabel('Zeit (h)')
plt.ylabel('Temperatur (°C)')
plt.title('Entwicklung der Temperaturen der Schichten über die Zeit')
plt.legend()

# Sprungsschichtplot
plt.figure(figsize=(8, 6))
selected_time_indices = [4, 7, 10, 13]
for index in selected_time_indices:
    plt.plot(T_values[index, :], np.linspace(height, 0, n), label=f'Sprungschicht nach {t_values[index]/60} Min')
plt.xlabel('Temperatur (°C)')
plt.ylabel('Höhe des Tanks (m)')
plt.title(f'Sprungschichten ')
plt.legend(loc='lower right')

plt.show()