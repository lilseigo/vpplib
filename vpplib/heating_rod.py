"""
Info
----
This file contains the basic functionalities of the VPPHeatPump class.

"""

import pandas as pd
from .component import Component


class HeatingRod(Component):

    def __init__(self, unit="kW", identifier=None,
                 environment=None, user_profile=None,
                 cost=None, el_power=None,
                 rampUpTime=0, rampDownTime=0,
                 min_runtime=0, min_stop_time=0, efficiency=1):

        # Call to super class
        super(HeatingRod, self).__init__(unit, environment, user_profile, cost)

        # Configure attributes
        self.identifier = identifier

        # heatinrod parameters
        self.efficiency = efficiency
        self.el_power = el_power
        self.limit = 1

        # Ramp parameters
        self.rampUpTime = rampUpTime
        self.rampDownTime = rampDownTime
        self.min_runtime = min_runtime
        self.min_stop_time = min_stop_time
        self.lastRampUp = self.user_profile.thermal_energy_demand.index[0]
        self.lastRampDown = self.user_profile.thermal_energy_demand.index[0]

        self.timeseries_year = pd.DataFrame(
            columns=["thermal_energy_output", "efficiency", "el_demand"],
            index=self.user_profile.thermal_energy_demand.index)
        self.timeseries = pd.DataFrame(
            columns=["thermal_energy_output", "efficiency", "el_demand"],
            index=pd.date_range(start=self.environment.start,
                                end=self.environment.end,
                                freq=self.environment.time_freq,
                                name="time"))

#        self.heat_sys_temp = heat_sys_temp

        self.is_running = False

    # from VPPComponents

    def prepareTimeSeries(self):

        if pd.isna(next(iter(self.user_profile.thermal_energy_demand.thermal_energy_demand))) == True:
            self.user_profile.get_thermal_energy_demand()

        if pd.isna(next(iter(self.timeseries_year.thermal_energy_output))) == True:
            self.get_timeseries_year()

        self.timeseries = self.timeseries_year.loc[self.environment.start:self.environment.end]

        return self.timeseries

    def get_timeseries_year(self):

        self.timeseries_year["thermal_energy_output"] = self.user_profile.thermal_energy_demand
        self.timeseries_year["el_demand"] = (self.timeseries_year.thermal_energy_output /
                                             self.efficiency)

        return self.timeseries_year

    # =========================================================================
    # Controlling functions
    # =========================================================================
    def limitPowerTo(self, limit):

        # Validate input parameter
        if limit >= 0 and limit <= 1:

            # Parameter is valid
            self.limit = limit

        else:

            # Paramter is invalid
            return

    # =========================================================================
    # Balancing Functions
    # =========================================================================

    # Override balancing function from super class.
    def value_for_timestamp(self, timestamp):

        if type(timestamp) == int:

            return self.timeseries.el_demand.iloc[timestamp] * self.limit

        elif type(timestamp) == str:

            return self.timeseries.el_demand.loc[timestamp] * self.limit

        else:
            raise ValueError("timestamp needs to be of type int or string. " +
                             "Stringformat: YYYY-MM-DD hh:mm:ss")

    def observations_for_timestamp(self, timestamp):

        if type(timestamp) == int:

            if pd.isna(next(iter(self.timeseries.iloc[timestamp]))) == False:

                thermal_energy_output, efficiency, el_demand = self.timeseries.iloc[timestamp]

            else:

                if self.is_running:
                    el_demand = self.el_power
                    #temp = self.user_profile.mean_temp_quarter_hours.temperature.iloc[timestamp]
                    efficiency = self.efficiency
                    thermal_energy_output = el_demand * efficiency
                else:
                    el_demand, thermal_energy_output = 0, 0

        elif type(timestamp) == str:

            if pd.isna(next(iter(self.timeseries.loc[timestamp]))) == False:

                thermal_energy_output, efficiency, el_demand = self.timeseries.loc[timestamp]
            else:

                if self.is_running:
                    el_demand = self.el_power
                    #temp = self.user_profile.mean_temp_quarter_hours.temperature.loc[timestamp]
                    efficiency = self.efficiency
                    thermal_energy_output = el_demand * efficiency
                else:
                    el_demand, thermal_energy_output = 0, 0

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:

            if pd.isna(next(iter(self.timeseries.loc[str(timestamp)]))) == False:

                thermal_energy_output, efficiency, el_demand = self.timeseries.loc[str(
                    timestamp)]

            else:

                if self.is_running:
                    el_demand = self.el_power
                    #temp = self.user_profile.mean_temp_quarter_hours.temperature.loc[str(timestamp)]
                    efficiency = self.efficiency
                    thermal_energy_output = el_demand * efficiency
                else:
                    el_demand, thermal_energy_output = 0, 0

        else:
            raise ValueError("timestamp needs to be of type int, " +
                             "string (Stringformat: YYYY-MM-DD hh:mm:ss)" +
                             " or pd._libs.tslibs.timestamps.Timestamp")

        observations = {
            'thermal_energy_output': thermal_energy_output, 'el_demand': el_demand}

        return observations

    def log_observation(self, observation, timestamp):

        self.timeseries.thermal_energy_output.loc[timestamp] = observation["thermal_energy_output"]
        self.timeseries.el_demand.loc[timestamp] = observation["el_demand"]

        return self.timeseries
    # %% ramping functions

    def isLegitRampUp(self, timestamp):

        if type(timestamp) == int:
            if timestamp - self.lastRampDown > self.min_stop_time:
                self.is_running = True
            else:
                self.is_running = False

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:
            if self.lastRampDown + self.min_stop_time * timestamp.freq < timestamp:
                self.is_running = True
            else:
                self.is_running = False

        else:
            raise ValueError("timestamp needs to be of type int or " +
                             "pandas._libs.tslibs.timestamps.Timestamp")

    def isLegitRampDown(self, timestamp):

        if type(timestamp) == int:
            if timestamp - self.lastRampUp > self.min_runtime:
                self.is_running = False
            else:
                self.is_running = True

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:
            if self.lastRampUp + self.min_runtime * timestamp.freq < timestamp:
                self.is_running = False
            else:
                self.is_running = True

        else:
            raise ValueError("timestamp needs to be of type int or " +
                             "pandas._libs.tslibs.timestamps.Timestamp")

    def ramp_up(self, timestamp):

        if self.is_running:
            return None
        else:
            if self.isLegitRampUp(timestamp):
                self.is_running = True
                return True
            else:
                return False

    def ramp_down(self, timestamp):

        if not self.is_running:
            return None
        else:
            if self.isLegitRampDown(timestamp):
                self.is_running = False
                return True
            else:
                return False

# %%

    def determin_heating_ratio(self, dataframe):
        """.

        function to determin the heating ratio.
        heating ratio = amount of energy output by hr / yearly heating demand
        argument passed is the dataframe wich is returned from
        HeatPump.run_hp_hr()

        Parameters
        ----------
        dataframe : TYPE
            DESCRIPTION.

        Returns
        -------
        heating_ratio : TYPE
            DESCRIPTION.

        """
        heating_demand = dataframe['thermal_energy_demand'].values
        sum_energy = 0
        for i in range(len(dataframe)):
            sum_energy += heating_demand[i]
        # divide by 4 (because time steps are 1/4 hour)
        # for correct result in [kWh]
        sum_energy = sum_energy / 4

        output_hr = dataframe['th_output_hr'].values
        sum_output = 0
        for i in range(len(dataframe)):
            sum_output += output_hr[i]
        # divide by 4 for correct result in [kWh]
        sum_output = sum_output / 4

        heating_ratio = sum_output / sum_energy

        return heating_ratio
