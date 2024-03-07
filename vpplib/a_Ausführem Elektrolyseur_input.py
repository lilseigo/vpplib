import pandas as pd
from a_hydrogen_electrolyseur import ElectrolysisMoritz 

#----------------------------------------------------------------------------
# Eingabeparameter: Elektrolyseur-Größe [kW, MW, etc.]
aa = input("Bitte geben Sie die Elektrolyseur-Größe und die Einheit an! (z.B. 10MW) ")
a = ''.join([c for c in aa if c.isnumeric() or c == '.'])
b = ''.join([c for c in aa if c.isalpha()])

#----------------------------------------------------------------------------
# Eingabeparameter: Zeiteinheit [min]
cc = input("Bitte geben Sie die Zeiteinheit an! (z.B. 15m) ")
c = ''.join([c for c in cc if c.isnumeric() or c == '.'])
d = ''.join([c for c in cc if c.isalpha()])

#----------------------------------------------------------------------------
# Eingabeparameter: Zeiteinheit [-]
ccc = input("Wie viele Zeitschritte möchten Sie simulieren? ")
try:
    Zeitschritte = int(ccc)
except ValueError:
    print("Ungültige Eingabe. Bitte geben Sie eine ganze Zahl ein.")

#----------------------------------------------------------------------------

e = input("Bitte geben Sie den Druck an, auf den der Wasserstoff komprimiert werden soll!")

#----------------------------------------------------------------------------
# Eingabeparameter: Wasserstoffproduktion [kg]

ff = input("Bitte geben Sie an, wie viel Wasserstoff produziert werden soll! (z.B. 10kg) ")
if not ff.strip():
    f=""
    g=""
else:
    f = ''.join([c for c in ff if c.isnumeric() or c == '.'])
    g = ''.join([c for c in ff if c.isalpha()])

electrolyzer = ElectrolysisMoritz(a,b,c,d,e,f,g)

#----------------------------------------------------------------------------
# Eine Datenreihe an Eingangsleistungen, bezogen durch eine Windkraftanlage, wird eingelesen. 
#ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=Zeitschritte)
ts = pd.read_csv(r'C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=Zeitschritte)


#Leistungsanpassung
ts['P_ac'] = round(ts['P_ac']/100,2)

electrolyzer.prepare_timeseries(ts)
print(ts)

#CSV-Datei
#ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)
ts.to_csv(r'C:\Users\katri\vpplib\vpplib\a_output.csv', index=False)
#ts.to_csv('a_output.csv', index=False)
#EXCEL-Datei
# excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
# ts.to_excel(excel_file_path, index=False)

# Variable 
timestamp_int=10
# Variable mit Zeitstempel
timestamp_str="2015-01-01 02:30:00+00:00"

# Funktion, 
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
