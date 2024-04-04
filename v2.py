import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

####Parameter
n = 5                                          # Anzahl Schichten
#Geomotrie Tank
height = 2                                     # Höhe Tank in m
diameter = 0.69                                # Durchmesser Tank in m
A_node = math.pi * (diameter/2)**2             # Grundfläche
volume = A_node * height                       # Volumen Tank in m^3
m_tank = volume * 1000                         # masse des Tanks 
height_node = height/n                         # höhe einer Schicht
####eigenschaftern
lambda_w = 1                                   # Wasserleitfähigkeit in W/m*K
cw = 4190                                      # spezifische Wärmekapazität J/kg*K
U = 0.50                                       # Wärmedurchgangskoeffizient der Wand in W/M^2*K
#### Umgebung
T_ambient = 12                                 # Umgebungstemperatur in °C
T = 12                                         # Anfangstemperatur speicher in °C
#### Erzeuger
T_s_out = 60                                   # Einspeisetemperatur in °C
m_s = 150 / 3600                               # Massenstrom vom Erzeuger kg/s
#### Verbraucher
T_l_out = 0                                    # Rücklauftemperatur des Verbrauchers in °C
m_l     = 0                                    # Massenstrom vom verbraucher kg/s

m_e = m_s - m_l                                # effektiver massflow
                                               # Betrachtete Zeit in s
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

### Diese Bedinungen beschreibt ob gerade
if m_e > 0:
    delta_1 = 1
else:
    delta_1 = 0
    
if m_e < 0:
    delta_2 = 1
else:
    delta_2 = 0

### Diese Bedingungen gelten für jede Schicht
# delta_s: suply into top layer und delta_l : load return into bottom layer
i = 1
if i == 1:
    delta_s = 1
else:
    delta_s = 0

if i == n: 
    delta_l = 1
else:
    delta_l = 0
# Man muss eine If schleife für die Mantelfläche des Knoten machen da Knoten 1 und N eine andere haben als die anderen
A_lateral_1 = math.pi * diameter * height_node + A_node 
A_lateral_2 = math.pi * diameter * height_node
A_lateral_3 = math.pi * diameter * height_node + A_node 

# Definition des Differentialgleichungssystems
def differentialgleichungen(u, t):
    x, y, z = u
    dxdt = (1 /(m * cw)) * (delta_s * m_s *cw * (T_s_out - x)       # Wärmezufuhr von Erzeuger 
                         - delta_l * m_l *cw * (x - T_l_out)        # Rücklauf von Last 
                         - U * A_lateral_1*   (x - T_ambient))      # Umgebungsverluste
                       # + delta_1 *m_e*cw* (Ti-1 - Ti)             # Wärmeübertragung durch Massenstrom von Schicht 1
                       # + delta_2 *m_e*cw* (T_i - Ti+1)            # Wärmeübertragung durch Massenstrom von Schicht 3
                       # - ((A_node*lambda_w)/height_node)*(Ti - Ti-1) # Konvektion

    dydt = (1 /(m * cw)) * (#delta_s * m_s *cw * (T_s_out - y)      # Wärmezufuhr von Erzeuger 
                         - delta_s * m_l *cw * (y - T_l_out)        # Rücklauf von Last 
                         - U * A_lateral_2 *   (y - T_ambient)      # Umgebungsverluste
                         + delta_1 *m_e*cw* (x - y)                 # Wärmeübertragung durch Massenstrom von Schicht 1
                         + delta_2 *m_e*cw* (y - z)                 # Wärmeübertragung durch Massenstrom von Schicht 3
                         - ((A_node*lambda_w)/height_node)*(y - x)) # Konvektion

    dzdt = (1 /(m * cw)) * (#delta_s * m_s *cw * (T_s_out - z)      # Wärmezufuhr von Erzeuger 
                         - delta_l * m_l *cw * (z - T_l_out)        # Rücklauf von Last 
                         - U * A_lateral_3*   (z     - T_ambient)  # Umgebungsverluste
                         + delta_1 *m_e*cw* (y - z)                 # Wärmeübertragung durch Massenstrom von Schicht 1
                       # + delta_2 *m_e*cw* (T_i     - Ti+1)        # Wärmeübertragung durch Massenstrom von Schicht 3
                         - ((A_node*lambda_w)/height_node)*(z - y)) # Konvektion

    return [dxdt, dydt, dzdt]


u0 = [T, T, T]


t_values = np.arange(0, 28800, 60)


u_values = odeint(differentialgleichungen, u0, t_values)

x_values, y_values, z_values = u_values.T

# Darstellung der Ergebnisse
plt.plot(t_values, x_values, label='x(t)')
plt.plot(t_values, y_values, label='y(t)')
plt.plot(t_values, z_values, label='z(t)')
plt.xlabel('Zeit (t)')
plt.ylabel('Variablenwerte')
plt.legend()
plt.show()