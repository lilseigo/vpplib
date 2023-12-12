import pandas as pd
from a_hydrogen_elec_copy_Tim import ElectrolysisMoritz 

#-------------------------------------------------------------------------------------------------
#test mit input
aa = input("Bitte geben Sie die Elektrolyseur-Größe und die Einheit an! (z.B. 10MW) ")
a = ''.join([c for c in aa if c.isnumeric() or c == '.'])
b = ''.join([c for c in aa if c.isalpha()])

# ---------------------------------------------------------------------------

cc = input("Bitte geben Sie die Zeiteinheit an! (z.B. 15m) ")
c = ''.join([c for c in cc if c.isnumeric() or c == '.'])
d = ''.join([c for c in cc if c.isalpha()])

# ---------------------------------------------------------------------------
ccc = input("Wie viele Zeitschritte möchten Sie simulieren? ")
try:
    Zeitschritte = int(ccc)
except ValueError:
    print("Ungültige Eingabe. Bitte geben Sie eine ganze Zahl ein.")
#-------------------------------------------------------------------------------

e = input("Bitte geben Sie den Druck an, auf den der Wasserstoff komprimiert werden soll!")

# ---------------------------------------------------------------------------

ff = input("Bitte geben Sie an, wie viel Wasserstoff produziert werden muss! (z.B. 10kg) ")
if not ff.strip():
    f=""
    g=""
else:
    f = ''.join([c for c in ff if c.isnumeric() or c == '.'])
    g = ''.join([c for c in ff if c.isalpha()])

electrolyzer = ElectrolysisMoritz(a,b,c,d,e,f,g)
#--------------------------------------------------------------------------------------------------------------------------




#Import der Eingangsleistung
ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=Zeitschritte)
#ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=50)
#ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)
#ts = pd.read_csv('a_wind_energy_cologne.csv',sep=',', decimal='.',nrows=20)



#Leistungsanpassung
ts['P_ac'] = round(ts['P_ac']/100,2)



#electrolyzer = ElectrolysisMoritz("500","kw","15","M","750","1","kg")  #Elektrolyseur-Größe,Einheit Elektrolyseur,  dt, Einheit zeit, Druck in bar, benötigte Wasserstoffmenge, Einheit Wasserstoffmenge

#Auführen des Elektrolyseurs
electrolyzer.prepare_timeseries(ts)
print(ts)

#CSV-Datei
ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)
#ts.to_csv('a_output.csv', index=False)
#EXCEL-Datei
excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
ts.to_excel(excel_file_path, index=False)


