# -*- coding: utf-8 -*-
"""
Info
----
This file contains the basic functionalities of the HeatPump class.

"""

import pandas as pd
from .component import Component


class HeatPump(Component):
    def __init__(
        self,
        heat_pump_type,
        heat_sys_temp,
        el_power,
        th_power,
        ramp_up_time,
        ramp_down_time,
        min_runtime,
        min_stop_time,
        unit,
        identifier=None,
        environment=None,
        user_profile=None,
        cost=None,
    ):

        """
        Info
        ----
        ...

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """

        # Call to super class
        super(HeatPump, self).__init__(unit, environment, user_profile, cost)

        # Configure attributes
        self.identifier = identifier

        # heatpump parameters
        self.cop = pd.DataFrame()
        self.heat_pump_type = heat_pump_type
        self.el_power = el_power
        self.th_power = th_power
        self.limit = 1
        #self.heat_source = "environment"
        #self.storage = storage

        # Ramp parameters
        self.ramp_up_time = ramp_up_time
        self.ramp_down_time = ramp_down_time
        self.min_runtime = min_runtime
        self.min_stop_time = min_stop_time
        self.last_ramp_up = self.user_profile.thermal_energy_demand.index[0]
        self.last_ramp_down = self.user_profile.thermal_energy_demand.index[0]

        self.timeseries_year = pd.DataFrame(
            columns=["thermal_energy_output", "cop", "el_demand"],
            index=self.user_profile.thermal_energy_demand.index,
        )
        self.timeseries = pd.DataFrame(
            columns=["thermal_energy_output", "cop", "el_demand"],
            index=pd.date_range(
                start=self.environment.start,
                end=self.environment.end,
                freq=self.environment.time_freq,
                name="time",
            ),
        )

        self.heat_sys_temp = heat_sys_temp

        self.is_running = False

    def set_heat_source(self, heat_source):
        if heat_source not in ["environment", "solar_thermal", "lts"]:
            raise ValueError(
                "heat source needs to be 'environment', 'solar_thermal' or 'lts'.")
        self.heat_source = heat_source

    def get_cop(self):
        """
        Info
        ----
        Calculate COP of heatpump according to heatpump type

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """
        if len(self.environment.mean_temp_hours) == 0:
            self.environment.get_mean_temp_hours()

        if len(self.environment.mean_ground_temp_hours) == 0:
            self.environment.get_mean_ground_temp_hours()

        cop_lst = []

        if self.heat_pump_type == "Air":
            for i, tmp in self.environment.mean_temp_hours.iterrows():
                cop = (
                    6.81
                    - 0.121 * (self.heat_sys_temp - tmp)
                    + 0.00063 * (self.heat_sys_temp - tmp) ** 2
                )
                cop_lst.append(cop)

        elif self.heat_pump_type == "Ground":
            for i, tmp in self.environment.mean_ground_temp_hours.iterrows():
                cop = (8.77 - 0.15 * (self.heat_sys_temp - tmp)
                       + 0.000734 * (self.heat_sys_temp - tmp)**2)
                cop_lst.append(cop)

        else:
            raise ValueError("Heatpump type is not defined!")

        self.cop = pd.DataFrame(
            data=cop_lst,
            index=pd.date_range(
                self.environment.year, periods=8760, freq="H", name="time"
            ),
        )
        self.cop.columns = ["cop"]

        return self.cop

    def get_current_cop(self, tmp):
        """
        Info
        ----
        Calculate COP of heatpump according to heatpump type

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """

        if self.heat_pump_type == "Air":
            cop = (
                6.81
                - 0.121 * (self.heat_sys_temp - tmp)
                + 0.00063 * (self.heat_sys_temp - tmp) ** 2
            )

        elif self.heat_pump_type == "Ground":
            cop = (
                8.77
                - 0.15 * (self.heat_sys_temp - tmp)
                + 0.000734 * (self.heat_sys_temp - tmp) ** 2
            )

        else:
            print("Heatpump type is not defined")
            return -9999

        return cop

    # from VPPComponents
    def prepare_time_series(self):

        if len(self.cop) == 0:
            self.get_cop()

        if (
            pd.isna(
                next(
                    iter(
                        self.user_profile.thermal_energy_demand.thermal_energy_demand
                    )
                )
            )
            == True
        ):
            self.user_profile.get_thermal_energy_demand()

        if (
            pd.isna(next(iter(self.timeseries_year.thermal_energy_output)))
            == True
        ):
            self.get_timeseries_year()

        self.timeseries = self.timeseries_year.loc[
            self.environment.start : self.environment.end
        ]

        return self.timeseries

    def get_timeseries_year(self):

        self.timeseries_year[
            "thermal_energy_output"
        ] = self.user_profile.thermal_energy_demand
        self.timeseries_year["cop"] = self.cop
        self.timeseries_year.cop.interpolate(inplace=True)
        self.timeseries_year["el_demand"] = (
            self.timeseries_year.thermal_energy_output
            / self.timeseries_year.cop
        )

        return self.timeseries_year

    def reset_time_series(self):

        self.timeseries = pd.DataFrame(
            columns=["thermal_energy_output", "cop", "el_demand"],
            index=pd.date_range(
                start=self.environment.start,
                end=self.environment.end,
                freq=self.environment.time_freq,
                name="time",
            ),
        )
        return self.timeseries

    # =========================================================================
    # Controlling functions
    # =========================================================================
    def limit_power_to(self, limit):
        """
        Info
        ----
        This function limits the power of the heatpump to the given percentage.
        It cuts the current power production down to the peak power multiplied
        by the limit (Float [0;1]).

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """

        # Validate input parameter
        if limit >= 0 and limit <= 1:

            # Parameter is valid
            self.limit = limit

        else:

            # Parameter is invalid

            raise ValueError("Limit-parameter is not valid")

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
            raise ValueError(
                "timestamp needs to be of type int or string. "
                + "Stringformat: YYYY-MM-DD hh:mm:ss"
            )

    def observations_for_timestamp(self, timestamp):
        """
        Info
        ----
        This function takes a timestamp as the parameter and returns a
        dictionary with key (String) value (Any) pairs.
        Depending on the type of component, different status parameters of the
        respective component can be queried.

        For example, a power store can report its "State of Charge".
        Returns an empty dictionary since this function needs to be
        implemented by child classes.

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """
        if type(timestamp) == int:

            if pd.isna(next(iter(self.timeseries.iloc[timestamp]))) == False:

                thermal_energy_output, cop, el_demand = self.timeseries.iloc[
                    timestamp
                ]

            else:

                if self.is_running:
                    el_demand = self.el_power
                    temp = self.user_profile.mean_temp_quarter_hours.temperature.iloc[
                        timestamp
                    ]
                    cop = self.get_current_cop(temp)
                    thermal_energy_output = el_demand * cop
                else:
                    el_demand, cop, thermal_energy_output = 0, 0, 0

        elif type(timestamp) == str:

            if pd.isna(next(iter(self.timeseries.loc[timestamp]))) == False:

                thermal_energy_output, cop, el_demand = self.timeseries.loc[
                    timestamp
                ]
            else:

                if self.is_running:
                    el_demand = self.el_power
                    temp = self.user_profile.mean_temp_quarter_hours.temperature.loc[
                        timestamp
                    ]
                    cop = self.get_current_cop(temp)
                    thermal_energy_output = el_demand * cop
                else:
                    el_demand, cop, thermal_energy_output = 0, 0, 0

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:

            if (
                pd.isna(next(iter(self.timeseries.loc[str(timestamp)])))
                == False
            ):

                thermal_energy_output, cop, el_demand = self.timeseries.loc[
                    str(timestamp)
                ]

            else:

                if self.is_running:
                    el_demand = self.el_power
                    temp = self.user_profile.mean_temp_quarter_hours.temperature.loc[
                        str(timestamp)
                    ]
                    cop = self.get_current_cop(temp)
                    thermal_energy_output = el_demand * cop
                else:
                    el_demand, cop, thermal_energy_output = 0, 0, 0

        else:
            raise ValueError(
                "timestamp needs to be of type int, "
                + "string (Stringformat: YYYY-MM-DD hh:mm:ss)"
                + " or pd._libs.tslibs.timestamps.Timestamp"
            )

        observations = {
            "thermal_energy_output": thermal_energy_output,
            "cop": cop,
            "el_demand": el_demand,
        }

        return observations

    def log_observation(self, observation, timestamp):

        self.timeseries.thermal_energy_output.loc[timestamp] = observation[
            "thermal_energy_output"
        ]
        self.timeseries.cop.loc[timestamp] = observation["cop"]
        self.timeseries.el_demand.loc[timestamp] = observation["el_demand"]

        return self.timeseries
    # %% ramping functions

    def is_valid_ramp_up(self, timestamp):

        if type(timestamp) == int:
            if timestamp - self.last_ramp_down > self.min_stop_time:
                self.is_running = True
            else:
                self.is_running = False

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:
            if (
                self.last_ramp_down + self.min_stop_time * timestamp.freq
                < timestamp
            ):
                self.is_running = True
            else:
                self.is_running = False

        else:
            raise ValueError(
                "timestamp needs to be of type int or "
                + "pandas._libs.tslibs.timestamps.Timestamp"
            )

    def is_valid_ramp_down(self, timestamp):

        if type(timestamp) == int:
            if timestamp - self.last_ramp_up > self.min_runtime:
                self.is_running = False
            else:
                self.is_running = True

        elif type(timestamp) == pd._libs.tslibs.timestamps.Timestamp:
            if (
                self.last_ramp_up + self.min_runtime * timestamp.freq
                < timestamp
            ):
                self.is_running = False
            else:
                self.is_running = True

        else:
            raise ValueError(
                "timestamp needs to be of type int or "
                + "pandas._libs.tslibs.timestamps.Timestamp"
            )

    def ramp_up(self, timestamp):

        """
        Info
        ----
        This function ramps up the combined heat and power plant. The timestamp is neccessary to calculate
        if the combined heat and power plant is running in later iterations of balancing. The possible
        return values are:
            - None:       Ramp up has no effect since the combined heat and power plant is already running
            - True:       Ramp up was successful
            - False:      Ramp up was not successful (due to constraints for minimum running and stop times)

        Parameters
        ----------

        ...

        Attributes
        ----------

        ...

        Notes
        -----

        ...

        References
        ----------

        ...

        Returns
        -------

        ...

        """
        if self.is_running:
            return None
        else:
            if self.is_valid_ramp_up(timestamp):
                self.is_running = True
                return True
            else:
                return False

    def ramp_down(self, timestamp):
        """.

        Info
        ----
        This function ramps down the combined heat and power plant.
        The timestamp is neccessary to calculate if the combined heat and
        power plant is running in later iterations of balancing. The possible
        return values are:
            - None:       Ramp down has no effect since the combined heat and
                            power plant is not running
            - True:       Ramp down was successful
            - False:      Ramp down was not successful
                        (due to constraints for minimum running and stop times)

        Parameters
        ----------
        ...

        Attributes
        ----------
        ...

        Notes
        -----
        ...

        References
        ----------
        ...

        Returns
        -------
        ...

        """
        if not self.is_running:
            return None
        else:
            if self.is_valid_ramp_down(timestamp):
                self.is_running = False
                return True
            else:
                return False

# %% further functions

    def determine_optimum_thermal_power(self):
        """.

        Function to determine optimum thermal power of the heat pump according
        to a given heat demand

        Returns
        -------
        None.

        """
        th_demand = self.user_profile.thermal_energy_demand
        temps = pd.read_csv("./input/thermal/dwd_temp_15min_2015.csv",
                            index_col="time")

        dataframe = pd.concat([th_demand, temps], axis=1)
        dataframe.sort_values(
            by=['thermal_energy_demand'], ascending=False, inplace=True)

        self.th_power = round(float(dataframe['thermal_energy_demand'][0]), 1)
        self.el_power = round(
            float(self.th_power
                  / self.get_current_cop(dataframe['temperature'][0])), 1)

    def optimize_bivalent(self, heating_rod, mode, norm_temp):
        """.

        Parameters
        ----------
        heating_rod : TYPE
            DESCRIPTION.
        mode : TYPE
            DESCRIPTION.
        norm_temp : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if mode not in ["parallel", "alternative"]:
            print("error: mode needs to be \"parallel\" or \"alternative\"")

    # =============================================================================
    #     if type(heat_pump) != HeatPump:
    #         print("error: heat_pump needs to be of type HeatPump")
    #
    #     if type(heating_rod) != HeatingRod:
    #         print("error: heating_rod needs to be of type HeatingRod")
    # =============================================================================

    # =============================================================================
    #     if user_profile.thermal_energy_demand == None:
    #         user_profile.get_thermal_energy_demand()
    # =============================================================================

        if norm_temp <= -16:
            biv_temp = -4
        elif (norm_temp > -16) & (norm_temp <= -10):
            biv_temp = -3
        elif norm_temp > -10:
            biv_temp = -2

        heat_demand = self.user_profile.get_thermal_energy_demand()
        temperature = pd.read_csv(
            "./input/thermal/dwd_temp_15min_2015.csv", index_col="time")

        # get point p0 (lowest temperature and corresponding (highest) heat demand)
        T_p0 = round(float(temperature['temperature'].min()), 1)
        P_p0 = round(float(heat_demand['thermal_energy_demand'].max()), 1)

        # get point p1 (heatstop temperature (20°C) and corrsponding (0kW) heat demand)
        T_p1 = 20   # choose reasonable value
        P_p1 = round(float(heat_demand['thermal_energy_demand'].min()), 1)

        # assume linear function P(T)=a*T+b between p0 and p1
        # calculate parameter a: gradient triangle
        a = (P_p1 - P_p0) / (T_p1 - T_p0)

        # calculate parameter b: b=P(T)-a*T
        b = 0 - a * 20  # Annahme bei 20 Grad keine Energie für Raumwärme notwendig

        # bivalence temerature (determine with tabels in Vaillant hand book)
        T_biv = biv_temp

        # calculate corresponding heat demand (equals thermal power of heat pump)
        P_biv = a * T_biv + b
        # print(str(P_biv))
        self.th_power = round(float(P_biv), 1)  # * 1.3

        self.el_power = self.th_power / self.get_current_cop(T_biv)
        th_power_hp_coldest = self.el_power * self.get_current_cop(norm_temp)

        if mode == "parallel":
            heating_rod.el_power = round(
                float((P_p0 - th_power_hp_coldest)
                      / heating_rod.efficiency), 1)

        else:
            heating_rod.el_power = round(
                float(P_p0 / heating_rod.efficiency), 1)

    def run_hp_hr(self, hr, mode, norm_temp):

        # determine bivalence temperature according to norm_temperature
        if norm_temp <= -16:
            biv_temp = -4
        elif (norm_temp > -16) & (norm_temp <= -10):
            biv_temp = -3
        elif norm_temp > -10:
            biv_temp = -2

        temp_air = pd.read_csv("./input/thermal/dwd_temp_15min_2015.csv",
                               index_col="time")

        # temperature and heat demand over time
        heat_demand = self.user_profile.thermal_energy_demand
        if self.heat_pump_type == "Air":
            temperature = temp_air
            dataframe = pd.concat([heat_demand, temperature], axis=1)
        if self.heat_pump_type == "Ground":
            temperature = pd.read_csv("./input/thermal/pik_temp_15min_ground_2015.csv",
                                      index_col="time")
            dataframe = pd.concat([heat_demand, temperature, temp_air], axis=1)

        # times where actual temp is below bivalence temp
        filter_temp = dataframe['temperature'] < biv_temp
        bools_temp = filter_temp.values
        filter_temp = pd.DataFrame(data=bools_temp, columns=['t below t_biv'],
                                   index=dataframe.index)

        dataframe = pd.concat([dataframe, filter_temp], axis=1)

        output_hp = []
        demand_hp = []

        output_hr = []
        demand_hr = []

        cops_hp = []

        hp_capable = []
        hr_working = []

        # to iterate over
        th_energy_demand = dataframe['thermal_energy_demand'].values
        if self.heat_pump_type == "Ground":
            temperature = dataframe['ground_temperature'].values
        if self.heat_pump_type == "Air":
            temperature = dataframe['temperature'].values

        # parallel mode
        if mode == "parallel":
            for i in range(len(dataframe)):
                # thermal output hp
                curr_th_power_hp = self.el_power * \
                    self.get_current_cop(temperature[i])
                if th_energy_demand[i] <= curr_th_power_hp:
                    output_hp.append(th_energy_demand[i])
                    hp_capable.append(True)
                else:
                    output_hp.append(curr_th_power_hp)
                    hp_capable.append(False)

            for i in range(len(dataframe)):
                # thermal output hr
                if bools_temp[i] or not hp_capable[i]:
                    diff = th_energy_demand[i] - output_hp[i]
                    if diff <= hr.el_power * hr.efficiency:
                        output_hr.append(diff)
                    else:
                        output_hr.append(hr.el_power * hr.efficiency)
                else:
                    output_hr.append(0)

        # alternative mode
        if mode == "alternative":
            # determine heat pump thermal output
            # (heat pump running if t >= t_biv)
            for i in range(len(dataframe)):
                if bools_temp[i] is False:
                    curr_th_power_hp = self.el_power * \
                        self.get_current_cop(temperature[i])
                    if th_energy_demand[i] <= curr_th_power_hp:
                        output_hp.append(th_energy_demand[i])
                        hp_capable.append(True)
                    else:
                        # hp.el_power * hp.get_current_cop(temperature[i]))
                        output_hp.append(curr_th_power_hp)
                        hp_capable.append(False)
                else:
                    output_hp.append(0)
                    hp_capable.append(False)

            # determine heating rod thermal output
            for i in range(len(dataframe)):
                if bools_temp[i]:
                    if th_energy_demand[i] <= hr.el_power * hr.efficiency:
                        output_hr.append(th_energy_demand[i])
                        hr_working.append(True)
                    else:
                        output_hr.append(hr.el_power * hr.efficiency)
                        hr_working.append(True)
                else:
                    output_hr.append(0)
                    hr_working.append(False)

            for i in range(len(dataframe)):
                if not hp_capable[i] or not hr_working[i]:
                    diff = th_energy_demand[i] - output_hp[i]
                    if diff <= hr.el_power * hr.efficiency:
                        output_hr[i] = diff
                    else:
                        output_hr[i] = hr.el_power * hr.efficiency

        th_output_hp = pd.DataFrame(data=output_hp, columns=['th_output_hp'],
                                    index=dataframe.index)

        th_output_hr = pd.DataFrame(data=output_hr, columns=['th_output_hr'],
                                    index=dataframe.index)

        dataframe = pd.concat([dataframe, th_output_hp, th_output_hr], axis=1)

        # determine electrical demand of heat pump and heating rod
        for i in range(len(dataframe)):
            demand_hp.append(
                output_hp[i] / self.get_current_cop(temperature[i]))
            demand_hr.append(output_hr[i] / hr.efficiency)

        el_demand_hp = pd.DataFrame(data=demand_hp, columns=['el_demand_hp'],
                                    index=dataframe.index)

        el_demand_hr = pd.DataFrame(data=demand_hr, columns=['el_demand_hr'],
                                    index=dataframe.index)

        for i in range(len(dataframe)):
            cops_hp.append(self.get_current_cop(temperature[i]))

        cops = pd.DataFrame(data=cops_hp, columns=[
                            'cop'], index=dataframe.index)

        dataframe = pd.concat(
            [dataframe, el_demand_hp, el_demand_hr, cops], axis=1)

        return dataframe
