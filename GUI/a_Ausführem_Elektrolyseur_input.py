import pandas as pd
from a_hydrogen_electrolyseur import ElectrolysisMoritz 
#-------------------------------------------------------------------------------------------------
#test mit input
def simulate_electrolyzer(store_hydrogen, store_environment):
    aa = str(store_hydrogen['Power_Electrolyzer'])+'kW'
    a = ''.join([c for c in aa if c.isnumeric() or c == '.'])
    b = ''.join([c for c in aa if c.isalpha()])

    # ---------------------------------------------------------------------------

    cc = store_environment['Time Step']
    c = ''.join([c for c in cc if c.isnumeric() or c == '.'])
    d = ''.join([c for c in cc if c.isalpha()])

    # ---------------------------------------------------------------------------
    ccc = store_hydrogen['Number of Time Steps']
    try:
        Zeitschritte = int(ccc)
    except ValueError:
        print("Ungültige Eingabe. Bitte geben Sie eine ganze Zahl ein.")
    #-------------------------------------------------------------------------------

    e = store_hydrogen['Pressure_Hydrogen']

    # ---------------------------------------------------------------------------

    ff = str(store_hydrogen['Quantity_Hydrogen'])+'kg'
    if not ff.strip():
        f=""
        g=""
    else:
        f = ''.join([c for c in ff if c.isnumeric() or c == '.'])
        g = ''.join([c for c in ff if c.isalpha()])

    electrolyzer = ElectrolysisMoritz(a,b,c,d,e,f,g)
    #--------------------------------------------------------------------------------------------------------------------------




    #Import der Eingangsleistung
    ts = pd.read_csv(r'GUI/a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=Zeitschritte)
    #ts = pd.read_csv(r"C:\Users\katri\vpplib\vpplib\a_wind_energy_cologne.csv", sep=',', decimal='.',nrows=100)




    #Leistungsanpassung
    ts['P_ac'] = round(ts['P_ac']/100,2)

    electrolyzer.prepare_timeseries(ts)
    print(ts)

    #CSV-Datei
    ts.to_csv(r'GUI/a_hydrogen_time_series.csv', index=False)
    # ts.to_csv('electrolyzer_timeseries.csv', index=True)
    #EXCEL-Datei
    # excel_file_path = r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.xlsx'
    # ts.to_excel(excel_file_path, index=False)


