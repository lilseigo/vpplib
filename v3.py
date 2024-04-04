import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

### Input:
n = 10                                        # Anzahl Schichten
T_ambient = 12                                # Umgebungstemperatur in °C
T = 12                                        # Anfangstemperatur der Schichten in °C

### Geomotrie Tank:
height = 2                                     # Höhe Tank in m
diameter = 0.69                                # Durchmesser Tank in m
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

### Physikalische Größen:
lambda_w = 1                                   # Wasserleitfähigkeit in W/m*K
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K

### Erzeugerdaten
T_s_out = 60                                   # Einspeisetemperatur in °C
m_s = 150 / 3600                               # Massenstrom vom Erzeuger kg/s
### Verbraucherdaten
T_l_out = 0                                    # Rücklauftemperatur des Verbrauchers in °C
m_l     = 0                                    # Massenstrom vom verbraucher kg/s
### Massflow
m_e = m_s - m_l                                # effektiver massflow

### Diese Bedingungen beschreiben ob wie der Fluß im Tank ist für die Bilanzierung
if m_e > 0:
    delta_1 = 1
else:
    delta_1 = 0
    
if m_e < 0:
    delta_2 = 1
else:
    delta_2 = 0

### Definition des Differentialgleichungssystems für die Energiegleichungen. T Temperatur und t die Zeit
def differentialgleichungen(T, t):      
    # dTdt ist die Änderungsrate (Ableitung)
    # mithilfe der Funktion wird ein Array erstellt mit gleicher DImension wie T und die Einträge sind alle 0                  
    dTdt = np.zeros_like(T)
    for i in range(n):
        if i == 0:
            delta_s = 1
        else:
            delta_s = 0

        if i == n-1: 
            delta_l = 1
        else:
            delta_l = 0

        if i == 0 or i == n-1:
            A_lateral_i = math.pi * diameter * height_node + A_node
        else:
            A_lateral_i = math.pi * diameter * height_node
        
        if i == 0:
            dTdt[i] = (1 /(m * cw))*( delta_s * m_s *cw * (T_s_out - T[i])     
                                     - delta_l * m_l *cw * (T[i] - T_l_out)  
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_2 *m_e*cw* (T[i+1] - T[i])         
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i-1]))
            
        elif i == n-1:
            dTdt[i] = (1 /(m * cw))*( delta_s * m_s *cw * (T_s_out - T[i])     
                                     - delta_l * m_l *cw * (T[i] - T_l_out)  
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_1 *m_e*cw* (T[i-1] - T[i])        
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i-1]))

        else:
            dTdt[i] = (1 /(m * cw))*( delta_s * m_s *cw * (T_s_out - T[i])     
                                     - delta_l * m_l *cw * (T[i] - T_l_out)  
                                     - U * A_lateral_i *   (T[i] - T_ambient)   
                                     + delta_1 *m_e*cw* (T[i-1] - T[i])        
                                     + delta_2 *m_e*cw* (T[i+1] - T[i])         
                                     - ((A_node*lambda_w)/height_node)*(T[i] - T[i-1]))

    return dTdt
### Eine Liste wird mit den Anfangsbedingungen erstellt
T0 = [T] * n

### erstellen einer Liste mit Start, Stop, step
t_values = np.arange(0, 36000, 360) 

### odeint löst das System. T_values ist ein array mit den verschiednen temperaturen der Schichten
T_values = odeint(differentialgleichungen, T0, t_values) 

### Plot
for i in range(n):
    plt.plot(t_values/3600, T_values[:, i], label=f'Schicht {i}')
plt.xlabel('Zeit (h)')
plt.ylabel('Temperatur (°C)')
plt.title('Entwicklung der Temperaturen der Schichten über die Zeit')
plt.legend()
plt.show()

### Tabelle für erste Schicht
df = pd.DataFrame({'Zeit': t_values,'Schicht' : T_values[:,0]})
print(df)
print(m_e)