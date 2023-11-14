import pandas as pd
from a_hydrogen_elec_copy import ElectrolysisMoritz #importieren der klasse
import matplotlib.pyplot as plt

#import windenergy timeseries


#ts=pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\wind.csv', sep=',', decimal='.',nrows=29)#, header=3
#ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=100)
ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)
#ts = pd.read_csv('a_wind_energy_cologne.csv',sep=',', decimal='.',nrows=100)

#ts['P_in [KW]'] = round(ts['P_in [KW]']/100,2)
ts['P_ac'] = round(ts['P_ac']/100,2)
#print(ts)
ts['time']=0


#definieren eines elektrolyseurs mit der Klasse Electrolyzer
electrolyzer = ElectrolysisMoritz(10000,750,15,10)  #kw, bar, t, wie viel zeit für ... kg wasserstoff

#Auführen von Funktionen
#Hier Wasserstoffproduktion

electrolyzer.prepare_timeseries(ts)

print(ts)
#ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)
df = ts.to_csv(r'C:\Users\katri\vpplib\vpplib\a_output.csv', index=False)
excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
#ts.to_excel(excel_file_path, index=False)
#ts.to_csv('a_output.csv', index=False)
#output ist eine timeseries mit zwei neuen Zeilen, Statuscodes und hydrogen production


# Variable mit Status "Produktion"
run = ts[ts['status'] == 'production']

# Visualisieren der Ergebnisse
plt.figure(figsize=(12, 8))

# Subplot 1: Eingangsleistung P_in Hydrogen Production
plt.subplot(2, 1, 1)
plt.plot(run["P_in [kW]"], run["Hydrogen Production [kg/dt]"], marker="o")
plt.title('P_in zu Hydrogen Production')
plt.xlabel("P_in [kW]")
plt.ylabel("Hydrogen Production [kg/dt]")

# Subplot 2: Wasser und Sauerstoff in kg pro erzeugten Wasserstoff in kg
ax2 = plt.subplot(2, 1, 2)
ax1 = ax2.twinx()

ax1.plot(run["Hydrogen Production [kg/dt]"], run["H20 [kg/dt]"], marker="o", label="H2O", color="blue")
ax1.set_ylabel("H2O [kg/dt]", color="blue")
ax1.tick_params(axis='y', labelcolor="blue")

ax2.plot(run["Hydrogen Production [kg/dt]"], run["Oxygen [kg/dt]"], marker="o", label="Oxygen", color="green")
ax2.set_ylabel("Oxygen [kg/dt]", color="green")
ax2.tick_params(axis='y', labelcolor="green")

plt.title("Reactants (Water, Oxygen [kg/dt]) per Produced Hydrogen [kg/dt]")
plt.xlabel("Hydrogen Production [kg/dt]")

plt.tight_layout()
plt.show()