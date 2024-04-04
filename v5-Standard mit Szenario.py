import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

### Input:
n = 10                                         # Anzahl Schichten
T_ambient = 12                                 # Umgebungstemperatur in °C
T = 12                                         # Anfangstemperatur der Schichten in °C

### Geomotrie Tank:
height = 2                                     # Höhe Tank in m
diameter = 0.69                                # Durchmesser Tank in m
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

### Physikalische Größen:
lambda_w = 0.6                                 # Wasserleitfähigkeit in W/m*K
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K

### Erzeugerdaten
T_s = 60                                       # Einspeisetemperatur in °C
massenstrom_wärmepumpe = 300/3600              # Massenstrom vom Erzeuger kg/s
### Verbraucherdaten
T_l = 40                                       # Rücklauftemperatur des Verbrauchers in °C
massenstrom_heizung = 500/3600                 # Massenstrom vom verbraucher kg/s

t_0 = 0
t_1 = 3 * 3600
t_2 = 5 * 3600
t_3 = 7 * 3600
t_4 = 9 * 3600

def get_mass_flow(t):
    if t_0 <= t < t_1:
        m_s = massenstrom_wärmepumpe
        m_l = 0
    elif t_1 <= t < t_2:
        m_s = 0
        m_l = massenstrom_heizung
    elif t_2 <= t < t_3:
        m_s = 0
        m_l = massenstrom_heizung
    elif t_3 <= t < t_4:
        m_s = massenstrom_wärmepumpe
        m_l = massenstrom_heizung
    else:
        m_s = 0
        m_l = 0
    ### effektiver Massflow
    m_e = m_s - m_l
    ### Befüllen -> delta_1 = 1 und delta_2 = 0
    ### Entladen -> delta_1 = 0 und delta_2 = 1
    if m_e > 0:
        delta_1 = 1
    else:
        delta_1 = 0
    if m_e < 0:
        delta_2 = 1
    else:
        delta_2 = 0
    return m_s, m_l, m_e, delta_1, delta_2

### Definition des Differentialgleichungssystems für die Energiegleichungen. T Temperatur und t die Zeit
def differentialgleichungen(T, t):      
    # dTdt ist die Änderungsrate (Ableitung)
    # mithilfe der Funktion wird ein Array erstellt mit gleicher Dimension wie T und die Einträge sind alle 0                  
    dTdt = np.zeros_like(T)
    
    for i in range(n):
        # Bedingung für die Mantelfläche
        if i == 0 or i == n-1:
            A_lateral_i = math.pi * diameter * height_node + A_node
        else:
            A_lateral_i = math.pi * diameter * height_node
        m_s, m_l, m_e, delta_1, delta_2 = get_mass_flow(t)
        # Oberste Schicht:
        if i == 0:
            dTdt[i] = (1 /(m * cw))*(+ m_s *cw * (T_s - T[i])      
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_2 *m_e*cw* (T[i] - T[i+1])         
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i+1]))
        # Unterste Schicht:    
        elif i == n-1:
            dTdt[i] = (1 /(m * cw))*(+ m_l *cw * (T_l - T[i])  
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_1 *m_e*cw* (T[i-1] - T[i])        
                                     + ((A_node*lambda_w)/height_node)*(T[i-1] - T[i]))
        # mittlere Schichten:
        else:
            dTdt[i] = (1 /(m * cw))*(- U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_1 *m_e*cw* (T[i-1] - T[i])        
                                     + delta_2 *m_e*cw* (T[i] - T[i+1])         
                                     + ((A_node*lambda_w)/height_node)*(T[i-1] - T[i])
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i+1]))
    return dTdt

### Eine Liste wird mit den Anfangsbedingungen erstellt
T0 = [T] * n

### erstellen einer Liste mit Start, Stop, step
t_values = np.arange(0, 40000, 360) 

### odeint löst das System. T_values ist ein array mit den verschiednen temperaturen der Schichten
T_values = odeint(differentialgleichungen, T0, t_values) 

### Plot
for i in range(n):
    plt.plot(t_values/3600, T_values[:, i], label=f'Schicht {i+1}')
plt.xlabel('Zeit (h)')
plt.ylabel('Temperatur (°C)')
plt.title('Entwicklung der Temperaturen der Schichten über die Zeit')
plt.legend()
plt.show()

### Tabelle für erste Schicht
#df = pd.DataFrame({'Zeit': t_values, 'Schicht 1' : T_values[:,0], 'Schicht 2' : T_values[:,1]})
#print(df)
#print(m_e)
#print(T_values[1])