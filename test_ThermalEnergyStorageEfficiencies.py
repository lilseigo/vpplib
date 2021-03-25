# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:38:38 2020

@author: andre
"""

from vpplib.user_profile import UserProfile
from vpplib.environment import Environment
from vpplib.thermal_energy_storage import ThermalEnergyStorageEfficiencies
from vpplib.heat_pump import HeatPump
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

figsize = (10, 6)
# Values for environment
start = "2015-01-01 00:00:00"
# bis 2015-02-04 geht es gut, dann sinkt die Temperatur wieder zu tief! :(
end = "2015-03-31 23:45:00"
year = "2015"
timebase = 15

# Values for user_profile
yearly_thermal_energy_demand = 10000  # kWh
building_type = "DE_HEF33"
t_0 = 40  # °C

# Values for Thermal Storage
target_temperature = 60  # °C
hysteresis = 5  # °K
mass_of_storage = 500  # kg
cp = 4.2
efficiency_class = "A+"

# Values for Heatpump
ramp_up_time = 1 / 15  # timesteps
ramp_down_time = 1 / 15  # timesteps
min_runtime = 1  # timesteps
min_stop_time = 2  # timesteps
heat_pump_type = "Air"
heat_sys_temp = 60

environment = Environment(timebase=timebase, start=start, end=end, year=year)

user_profile = UserProfile(
    identifier=None,
    latitude=None,
    longitude=None,
    thermal_energy_demand_yearly=yearly_thermal_energy_demand,
    building_type=building_type,
    comfort_factor=None,
    t_0=t_0,
)


def test_get_thermal_energy_demand(user_profile):

    user_profile.get_thermal_energy_demand()
    user_profile.thermal_energy_demand.plot()
    plt.show()


test_get_thermal_energy_demand(user_profile)

tes = ThermalEnergyStorageEfficiencies(
    environment=environment,
    user_profile=user_profile,
    unit="kWh",
    cp=cp,
    mass=mass_of_storage,
    hysteresis=hysteresis,
    target_temperature=target_temperature,
    efficiency_class=efficiency_class
)

hp = HeatPump(
    identifier="hp1",
    unit="kW",
    environment=environment,
    user_profile=user_profile,
    ramp_up_time=ramp_up_time,
    ramp_down_time=ramp_down_time,
    min_runtime=min_runtime,
    min_stop_time=min_stop_time,
    heat_pump_type=heat_pump_type,
    heat_sys_temp=heat_sys_temp,
)

mode = "overcome shutdown"
# layout tes and hp
tes.optimize_tes_hp(hp, mode)


print("mass of tes: " + str(tes.mass) + " [kg]")
print("electrical power of hp: " + str(hp.el_power) + " [kW]")

for i in tqdm(tes.user_profile.thermal_energy_demand.loc[start:end].index):
    tes.operate_storage(i, hp)


print(hp.timeseries)
print(tes.timeseries)
hp.timeseries.plot()
tes.timeseries.plot()

min_dem = hp.timeseries.el_demand.min()
max_dem = hp.timeseries.el_demand.max()
mean_dem = hp.timeseries.el_demand.mean()
sum_dem = hp.timeseries.el_demand.sum() / 4

min_cop = hp.timeseries.cop.min()
max_cop = hp.timeseries.cop.max()
mean_cop = hp.timeseries.cop.mean()

max_output = hp.timeseries.thermal_energy_output.max()
sum_output = hp.timeseries.thermal_energy_output.sum() / 4
scop = sum_output / sum_dem

hrs = hp.timeseries.el_demand > 0
hrs_count = 0
for i in hrs:
    if i:
        hrs_count += 1

hours_active = hrs_count / 4

print("min el dem: " + str(min_dem))
print("max el dem: " + str(max_dem))
print("mean el dem: " + str(mean_dem))
print("sum el dem: " + str(sum_dem))
print("hours active: " + str(hours_active))
print("max th output: " + str(max_output))
print("sum th output: " + str(sum_output))
print("mean cop: " + str(mean_cop))
print("scop: " + str(scop))

df_complete = pd.concat([hp.timeseries, tes.timeseries], axis=1)
print(df_complete)
