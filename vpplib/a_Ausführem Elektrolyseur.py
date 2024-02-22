import pandas as pd
from a_hydrogen_electrolyseur import ElectrolysisMoritz 




#Import der Eingangsleistung

ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=50)
#ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)
#ts = pd.read_csv('a_wind_energy_cologne.csv',sep=',', decimal='.',nrows=20)

#Leistungsanpassung
ts['P_ac'] = round(ts['P_ac']/100,2)


electrolyzer = ElectrolysisMoritz("500","kw","15","M","750","1","kg")  #Elektrolyseur-Größe,Einheit Elektrolyseur,  dt, Einheit zeit, Druck in bar, benötigte Wasserstoffmenge, Einheit Wasserstoffmenge

#Auführen des Elektrolyseurs
electrolyzer.prepare_timeseries(ts)
print(ts)

#CSV-Datei
ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)
#ts.to_csv('a_output.csv', index=False)
#EXCEL-Datei
# excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
# ts.to_excel(excel_file_path, index=False)

timestamp_int=10
timestamp_str="2015-01-01 02:30:00+00:00"

def test_value_for_timestamp(electrolyzer, timestamp):
    
    timestepvalue = electrolyzer.value_for_timestamp(timestamp)
    print("\nvalue_for_timestamp:\n", timestepvalue)

def test_observations_for_timestamp(electrolyzer, timestamp):

    print("observations_for_timestamp:")
    
    observation = electrolyzer.observations_for_timestamp(timestamp)
    print(observation, "\n")



test_value_for_timestamp(electrolyzer, timestamp_int)
test_value_for_timestamp(electrolyzer, timestamp_str)

test_observations_for_timestamp(electrolyzer, timestamp_int)
test_observations_for_timestamp(electrolyzer,timestamp_str)
