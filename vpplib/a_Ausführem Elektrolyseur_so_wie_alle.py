import pandas as pd
from a_hydrogen_electrolyseur import ElectrolysisMoritz 
import matplotlib.pyplot as plt
from environment import Environment


#Import der Eingangsleistung
ts = pd.read_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_wind_energy_cologne.csv', sep=',', decimal='.',nrows=50)

#Leistungsanpassung
ts['P_ac'] = round(ts['P_ac']/100,2)

# start = "2015-06-01 00:00:00"
# end = "2015-06-01 23:45:00"
# timebase = 15
# timestamp_int = 48
# timestamp_str = "2015-06-01 12:00:00"

# environment = Environment(start=start, end=end, timebase=timebase)
# print(environment)
# ts=environment

timestamp_int=20
timestamp_str="2015-01-01 02:30:00+00:00"

Power_electrolyzer="500"
Unit_Power_electrolyser="KW"
Timestamp="15"
Unit_Timestamp="m"
Pressure_Compression="750"
Hydrogen_Production="1"
Unit_Hydrogen_Production="KG"

electrolyzer = ElectrolysisMoritz(
    Power_electrolyzer,
    Unit_Power_electrolyser,
    Timestamp,
    Unit_Timestamp,
    Pressure_Compression,
    Hydrogen_Production,
    Unit_Hydrogen_Production)  

#Auführen des Elektrolyseurs
electrolyzer.prepare_timeseries(ts)
print(ts)
ts=ts
#CSV-Datei
ts.to_csv(r'C:\Users\Anwender\Documents\Masterprojekt\12345\vpplib\vpplib\a_output.csv', index=False)


def test_value_for_timestamp(ts, timestamp):
    
    timestepvalue = electrolyzer.value_for_timestamp(timestamp)
    print("\nvalue_for_timestamp:\n", timestepvalue)

def test_observations_for_timestamp(ts, timestamp):

    print("observations_for_timestamp:")
    
    observation = electrolyzer.observations_for_timestamp(timestamp)
    print(observation, "\n")


#electrolyzer.prepare_timeseries(ts)
test_value_for_timestamp(ts, timestamp_int)
test_value_for_timestamp(ts, timestamp_str)

test_observations_for_timestamp(ts, timestamp_int)
test_observations_for_timestamp(ts, timestamp_str)



