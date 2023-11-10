import pandas as pd
from a_hydrogen_elec_copy import ElectrolysisMoritz #importieren der klasse


#import windenergy timeseries


#ts=pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\wind.csv', sep=',', decimal='.',nrows=29)#, header=3
ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=100)
#ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)
#ts = pd.read_csv('a_wind_energy_cologne.csv',sep=',', decimal='.',nrows=100)

#ts['P_in [KW]'] = round(ts['P_in [KW]']/100,2)
ts['P_ac'] = round(ts['P_ac']/100,2)
#print(ts)
ts['time']=0



#definieren eines elektrolyseurs mit der Klasse Electrolyzer
electrolyzer = ElectrolysisMoritz(500,750,15)

#Auführen von Funktionen
#Hier Wasserstoffproduktion

electrolyzer.prepare_timeseries(ts)

print(ts)
ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)

excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
ts.to_excel(excel_file_path, index=False)
#ts.to_csv('a_output.csv', index=False)
#output ist eine timeseries mit zwei neuen Zeilen, Statuscodes und hydrogen production