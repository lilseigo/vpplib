import pandas as pd
from a_hydrogen_elec_copy_Tim import ElectrolysisMoritz #importieren der klasse

#TODO: wöfür die +40 bei H20

#Import der Eingangsleistung

ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=20)
#ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)
#ts = pd.read_csv('a_wind_energy_cologne.csv',sep=',', decimal='.',nrows=20)



#ts['P_in [KW]'] = round(ts['P_in [KW]']/100,2)
ts['P_ac'] = round(ts['P_ac']/100,2)
#print(ts)
#ts['time']=0


#definieren eines elektrolyseurs mit der Klasse Electrolyzer
electrolyzer = ElectrolysisMoritz(500,"kW",350,15,"m",5,'kg')  #Elektrolyseur-Größe,Einheit Elektrolyseur, bar, dt, Einheit zeit, benötigte Wasserstoffmenge, Einheit Wasserstoffmenge

#Auführen des Elektrolyseurs
electrolyzer.prepare_timeseries(ts)
print(ts)

#CSV-Datei
ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)
#ts.to_csv('a_output.csv', index=False)
#EXCEL-Datei
excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
ts.to_excel(excel_file_path, index=False)

