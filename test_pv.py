# -*- coding: utf-8 -*-
"""
Info
----
In this testfile the basic functionalities of the Photovoltaic class are tested.
Run each time you make changes on an existing function.
Adjust if a new function is added or
parameters in an existing function are changed.

"""

import matplotlib.pyplot as plt

from vpplib.environment import Environment
from vpplib.user_profile import UserProfile
from vpplib.photovoltaic import Photovoltaic
import datetime
import zoneinfo

zoneinfo.available_timezones()


latitude = 51.4
longitude = 6.97
identifier = "Cologne"
timestamp_int = 48
"""CSV
timestamp_str = "2015-11-09 12:00:00"
environment = Environment(start="2015-01-01 00:00:00", end="2015-12-31 23:45:00")
environment.get_pv_data(file="./input/pv/dwd_pv_data_2015.csv")
"""

"""OBSERVATION:
timestamp_str = "2015-11-09 12:00:00"
environment = Environment(start="2015-01-01 00:00:00", end="2015-12-31 23:45:00")
environment.get_dwd_pv_data(lat=latitude, lon=longitude)
"""

"""MOSMIX:"""
time_now = Environment().get_time_from_dwd().replace(tzinfo=None)
#timestamp_str = "2023-12-07 12:00:00"
timestamp_str = str((time_now + datetime.timedelta(days = 5)).replace(minute = 0, second = 0))
environment = Environment(start=str(time_now), end=str(time_now + datetime.timedelta(hours = 240)))
environment.get_dwd_pv_data(lat=latitude, lon=longitude)


user_profile = UserProfile(
    identifier=identifier, latitude=latitude, longitude=longitude
)

pv = Photovoltaic(
    unit="kW",
    identifier=identifier,
    environment=environment,
    user_profile=user_profile,
    module_lib="SandiaMod",
    module="Canadian_Solar_CS5P_220M___2009_",
    inverter_lib="cecinverter",
    inverter="ABB__MICRO_0_25_I_OUTD_US_208__208V_",
    surface_tilt=20,
    surface_azimuth=200,
    modules_per_string=2,
    strings_per_inverter=2,
    temp_lib='sapm',
    temp_model='open_rack_glass_glass'
)


def test_prepare_time_series(pv):

    pv.prepare_time_series()
    print("prepare_time_series:")
    print(pv.timeseries.head())
    pv.timeseries.plot(figsize=(16, 9))
    plt.show()


def test_value_for_timestamp(pv, timestamp):

    timestepvalue = pv.value_for_timestamp(timestamp)
    print("\nvalue_for_timestamp:\n", timestepvalue)


def observations_for_timestamp(pv, timestamp):

    print("observations_for_timestamp:")
    observation = pv.observations_for_timestamp(timestamp)
    print(observation, "\n")


test_prepare_time_series(pv)
test_value_for_timestamp(pv, timestamp_int)
test_value_for_timestamp(pv, timestamp_str)

observations_for_timestamp(pv, timestamp_int)
observations_for_timestamp(pv, timestamp_str)
