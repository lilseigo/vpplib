import math
import pandas as pd

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

t = 60                                        # Betrachtete Zeit in s
m = m_tank / n                                 # masse einer einzelnen Schicht in kg

# delta_1 und delta_2 werden eingeführt um später in der Bilanz der Schichten die Terme zu aktivieren
if m_e > 0:
    delta_1 = 1
else:
    delta_1 = 0
    
if m_e < 0:
    delta_2 = 1
else:
    delta_2 = 0

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


# Die Anfangstemperatur der Schicht 1 ist gleich der Anfangstemperatur des Speichers
T_1 = T
T_2 = T
# Die Temperatur der Schicht i ist am anfang auch der der Anfangstemperatur des speichers
T_i = T

# Man muss eine If schleife für die Mantelfläche des Knoten machen da Knoten 1 und N eine andere haben als die anderen
A_lateral_1 = math.pi * diameter * height_node + A_node 
A_lateral_2 = math.pi * diameter * height_node

# Berechnung Temperaturanstieg von Knoten 1 nach 60 Sekunden
delta_T_1 = (t /(m * cw))   * (delta_s *m_s*cw* (T_s_out - T_1)        # Wärmezufuhr von Erzeuger in Schicht 1
                             - delta_l *m_l*cw* (T_1     - T_l_out)    # Rücklauf von Last --> 0
                             - U*A_lateral_1*   (T_1     - T_ambient)) # Umgebungsverluste
                           # + delta_1 *m_e*cw* (T_i-1   - T_i)        # Wärmeübertragung durch Massenstrom(ist in Schicht 1=0)
                           # + delta_2 *m_e*cw* (T_i     - T_i+1)      # Wärmeübertragung durch Massenstrom(ist in Schicht 1=0)
                                                                       # desweiteren fehlt hier die Wärmeleitung gleichung
T_1_new = T_1 + delta_T_1

delta_T_2 = (t /(m * cw))  * (#delta_l*m_s*cw)* (T_s_out - T_2)        # 0 da wir in Schicht 2 sind
                             - delta_s *m_l*cw* (T_2     - T_l_out)    # Rücklauf von Last --> 0
                             - U*A_lateral_2*   (T_2     - T_ambient)  # Umgebungsverluste aber mit lateral_2
                             + delta_1 *m_e*cw* (T_1_new - T_2)        # Wärmeübertragung durch Massenstrom von Schicht 1
                           # + delta_2 *m_e*cw* (T_i     - T_i+1)      # Wärmeübertragung durch Massenstrom von Schicht 3, ->0
                             - ((A_node*lambda_w)/height_node)*(T_2 - T_1_new)) # Konvektion
T_2_new = T_2 + delta_T_2

timestampe1 = [T_1_new,T_2_new]

df = pd.DataFrame({t: timestampe1})

print(df)