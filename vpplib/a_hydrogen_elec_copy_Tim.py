import math
import numpy as np
import scipy
import pandas as pd
from scipy.signal import tf2ss, cont2discrete
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar

class ElectrolysisMoritz:
    
    def __init__(self,P_elektrolyseur,unit_P,p2,dt_1,unit_dt,production_H2):

           
        # Constants
        self.F = 96485.34  # Faraday's constant [C/mol]
        self.R = 8.314  # ideal gas constant [J/(mol*K)]
        self.n = 2  # number of electrons transferred in reaction
        self.gibbs = 237.24e3
        self.E_th_0 = 1.481  # thermoneutral voltage at standard state
        self.M = 2.016  # molecular weight [g/mol]
        self.lhv = 33.33  # lower heating value of H2 [kWh/kg]
        self.hhv = 39.41  # higher heating value of H2 [kWh/kg]
        self.roh_H2 = 0.08988 #Density in kg/m3
        self.roh_O = 1.429 #Density kg/m3
        self.T = 50 # Grad Celsius
        self.p2=p2 #bar compression

        #units
        #units_P W, KW,MW
        self.unit_P =unit_P

        if self.unit_P.lower() =="w":
            P_elektrolyseur =P_elektrolyseur*1000
        elif self.unit_P.lower() =="kw":
           P_elektrolyseur =P_elektrolyseur
        elif self.unit_P.lower() =="mw":
            P_elektrolyseur =P_elektrolyseur/1000
        else:
           raise ValueError("Bitte überprüfen Sie die Einheit des Elektrolyseurs! Derzeit sind die Möglickeiten W,KW,MW") 
        
        #Units_dt S, M,H     
        self.unit_dt=unit_dt
        self.dt_1=dt_1
        if self.unit_dt.lower() =="s": # second
            self.dt=self.dt_1/60
        elif self.unit_dt.lower() =="m": # minute
           self.dt=self.dt_1
        elif self.unit_dt.lower() =="h": # hour
            self.dt=self.dt_1*60
        else:
           raise ValueError("Bitte überprüfen Sie die Einheit der Zeit! Derzeit sind die Möglichkeiten S,M,H") 
        
        
        
        self.P_nominal = P_elektrolyseur    #kW
        self.P_min = self.P_nominal * 0.1   #kW
        self.P_max = self.P_nominal         #kW
        
        # Stack parameters
        self.n_cells = 56  # Number of cells
        self.cell_area = 2500  # [cm^2] Cell active area
        self.max_current_density = 2.1  # [A/cm^2] max. current density #2 * self.cell_area
        self.temperature = 50  # [C] stack temperature
        self.n_stacks = self.P_nominal/self.stack_nominal()

        self.p_atmo = 101325 #2000000  # (Pa) atmospheric pressure / pressure of water
        self.p_anode = self.p_atmo  # (Pa) pressure at anode, assumed atmo
        
        self.production_H2=production_H2
        
    def status_codes(self,df):      #tabelle
      
        long_gap_threshold = math.ceil(60 / self.dt)
        short_gap_threshold = math.ceil(5 / self.dt)
        # create a mask for power values below P_min
        below_threshold_mask = df['P_in [KW]'] < self.P_min

        # find short gaps (up to 4 steps) where power is below P_min
        short_gaps = below_threshold_mask.rolling(window=short_gap_threshold).sum()
        hot_mask = (short_gaps <= math.ceil(4 / self.dt)) & below_threshold_mask
        df.loc[hot_mask, 'status'] = 'hot'

        # find middle gaps (between 5 and 60 steps) where power is below P_min
        middle_gaps = below_threshold_mask.rolling(window=long_gap_threshold).sum()
        hot_standby_mask = ((math.ceil(5 / self.dt) <= middle_gaps) & (middle_gaps < math.ceil(60 / self.dt))) & below_threshold_mask
        df.loc[hot_standby_mask, 'status'] = 'hot standby'
        # find long gaps (over 60 steps) where power is below P_min
        long_gaps = below_threshold_mask.rolling(window=long_gap_threshold).sum()
        cold_standby_mask = (long_gaps >= math.ceil(60 / self.dt)) & below_threshold_mask
        df.loc[cold_standby_mask, 'status'] = 'cold standby'

        # mark production periods (above P_min)
        production_mask = df['P_in [KW]'] >= self.P_min
        df.loc[production_mask, 'status'] = 'production'

        # add status codes
        df['status codes'] = df['status'].replace({
            'cold standby': 0,
            'hot standby': 1,
            'hot': 2,
            'production': 4
        })

        # add 'booting' status
        booting_mask = pd.Series(False, index=df.index)
        # Identify rows where production is True and previous row is hot standby or cold standby
        booting_mask |= (df['status'].eq('production') & df['status'].shift(1).isin(['hot standby', 'cold standby']))

        # Identify rows where production is True and status is cold standby for up to 5 rows before

        booting_mask |= (df['status'].eq('production') & df['status'].shift(math.ceil(30 / self.dt)).eq('cold standby'))

        # Identify rows where production is True and status is hot standby for up to 30 rows before
        for i in range(math.ceil(1 / self.dt), math.ceil(15 / self.dt)):
            booting_mask |= (df['status'].eq('production') & df['status'].shift(i).eq('hot standby'))

        df.loc[booting_mask, 'status'] = 'booting'

        # add status codes
        df['status codes'] = df['status'].replace({
            'cold standby': 0,
            'hot standby': 1,
            'hot': 2,
            'production': 4,
            'booting': 3
        })
        return df
    
    def calc_cell_voltage(self, I, T):         #Einheit: V
        """
        I [Adc]: stack current
        T [degC]: stack temperature
        return :: V_cell [Vdc/cell]: cell voltage
        """
        T_K = T + 273.15

        # Cell reversible voltage:
        E_rev_0 = self.gibbs / (self.n * self.F)  # Reversible cell voltage at standard state

        p_anode = 200000
        p_cathode = 3000000 #pressure/Druck der von den Pumpen aufgebracht wird

        # Arden Buck equation T=C, https://www.omnicalculator.com/chemistry/vapour-pressure-of-water#vapor-pressure-formulas
        p_h2O_sat = (0.61121 * np.exp((18.678 - (T / 234.5)) * (T / (257.14 + T)))) * 1e3  # (Pa)
        p_atmo = 101325
       # General Nernst equation
        E_rev = E_rev_0 + ((self.R * T_K) / (self.n * self.F)) * (
           np.log( ((p_anode - p_h2O_sat) / p_atmo)* np.sqrt((p_cathode - p_h2O_sat) / p_atmo)))

        #E_rev = E_rev_0 - ((E_rev_0* 10**-3 * T_K) + 9.523 * 10**-5 * np.log(T_K) + 9.84*10**-8* T_K**2) #empirical equation


        T_anode = T_K

        T_cathode = T_K

        # anode charge transfer coefficient
        alpha_a = 2

        # cathode charge transfer coefficient
        alpha_c = 0.5

        # anode exchange current density
        i_0_a = 2 * 10 ** (-7)

        # cathode exchange current density
        i_0_c = 10 ** (-3)

        i = I / self.cell_area

        # derived from Butler-Volmer eqs
       # V_act_a = ((self.R * T_anode) / (alpha_a * self.F)) * np.arcsinh(i / (2*i_0_a))
        #V_act_c = ((self.R * T_cathode) / (alpha_c * self.F)) * np.arcsinh(i / (2*i_0_c))
        # alternate equations for Activation overpotential
        # Option 2: Dakota: I believe this may be more accurate, found more
        # frequently in lit review
        # https://www.sciencedirect.com/science/article/pii/S0360319918309017

        z_a = 4 # stoichiometric coefficient of electrons transferred at anode
        z_c = 2 # stoichometric coefficient of electrons transferred at cathode
        i_0_a = 10**(-9) # anode exchange current density TODO: update to be f(T)?
        i_0_c = 10**(-3) # cathode exchange current density TODO: update to be f(T)?

        V_act_a = ((self.R*T_anode)/(alpha_a*z_a*self.F)) * np.log(i/i_0_a)
        V_act_c = ((self.R*T_cathode)/(alpha_c*z_c*self.F)) * np.log(i/i_0_c)

        # pulled from https://www.sciencedirect.com/science/article/pii/S0360319917309278?via%3Dihub
        lambda_nafion = 25
        t_nafion = 0.01  # cm

        sigma_nafion = ((0.005139 * lambda_nafion) - 0.00326) * np.exp(
            1268 * ((1 / 303) - (1 / T_K)))
        R_ohmic_ionic = t_nafion / sigma_nafion

        R_ohmic_elec = 50e-3

        V_ohmic = i * (R_ohmic_elec + R_ohmic_ionic)

        V_cell = E_rev + V_act_a + V_act_c + V_ohmic

        return V_cell

    def create_polarization(self):  
        currents = np.arange(1, 5500, 10)
        voltage = []
        for i in range(len(currents)):
            voltage.append(self.calc_cell_voltage(currents[i],self.T))
        df = pd.DataFrame({"current_A": currents, "voltage_U": voltage})
        df['power_W'] = df["current_A"]*df["voltage_U"]
        #df['current_A'] = df['current_A']/self.cell_area
        return df

    def plot_polarization(self):
        df = self.create_polarization()

        plt.plot((df['current_A']/self.cell_area), df['voltage_U'])

        plt.title('Polarization curve')
        plt.xlabel('Current densitiy [A/cm2]')
        plt.ylabel('Cell Voltage [V]')
        plt.grid(True)

        plt.show()

    def stack_nominal(self):                #Einheit: KW
        '''
        stack nominal in kW
        :return:
        '''
        P_stack_nominal = round((self.create_polarization().iloc[504,0] * self.create_polarization().iloc[504,1]*self.n_cells) /1000) #in kW
        return P_stack_nominal #KW

    def calculate_cell_current(self, P_dc): 
        '''
        P_dc: Power DC in Watt
        P_cell: Power each cell
        return I: Current each cell in Ampere
        '''

        P_cell = ((P_dc/self.n_stacks)/self.n_cells)*1000 #in W
        df = self.create_polarization()
        x = df['power_W'].to_numpy()
        y = df['current_A'].to_numpy()
        f = interp1d(x, y, kind='linear')
        return f(P_cell)
    
    def calc_faradaic_efficiency(self, I):  
        """
            #     I [A]: stack current
            #     return :: eta_F [-]: Faraday's efficiency
            #     Reference: https://res.mdpi.com/d_attachment/energies/energies-13-04792/article_deploy/energies-13-04792-v2.pdf
            #     """
        p = 20 #electrolyze pressure in bar
        i = I/self.cell_area

        a_1 = -0.0034
        a_2 = -0.001711
        b = -1
        c = 1

        eta_f = (a_1*p+a_2)*((i)**b)+c

        return eta_f

    def power_electronics(self, P_nominal, P_ac):               #Einheit: KW
        '''
        P_nominal: Electrolyzer Size in kW
        P_ac: P_in [KW]
        P_electronics: Self-consumption power electronics in kW
        '''
        # Wirkungsgradkurve definieren
        relative_performance = [0.0,0.09,0.12,0.15,0.189,0.209,0.24,0.3,0.4,0.54,0.7,1.001]
        eta = [0.86,0.91,0.928,0.943,0.949,0.95,0.954,0.96,0.965,0.97,0.973,0.977]
        # Interpolationsfunktion erstellen
        f_eta = interp1d(relative_performance, eta)

        # Eigenverbrauch berechnen
        eta_interp = f_eta(P_ac / P_nominal)  # Interpoliere den eta-Wert

        P_electronics = P_ac * (1 - eta_interp)  # Berechne den Eigenverbrauch

        return P_electronics

    def power_dc(self, P_ac):                  #Einheit: KW
        '''
        :param P_ac:
        :return:
        '''
        P_dc = P_ac - self.power_electronics(P_ac, self.stack_nominal()/100)
        #P_dc = P_ac - self.power_electronics(P_ac, self.P_nominal/100)
        return P_dc

    def run(self, P_dc):        #tabelle        #Einheit: kg/dt
        """
        P_in [KW] [kWdc]: stack power input
        return :: H2_mfr [kg/dt]: hydrogen mass flow rate
        """

        I = self.calculate_cell_current(P_dc)   #A
        V = self.calc_cell_voltage(I, self.temperature) #V
        eta_F = self.calc_faradaic_efficiency(I)
        mfr = (eta_F * I * self.M * self.n_cells*self.n_stacks) / (self.n * self.F) #self.n_stacks hinzugefügt
        #power_left -= self.calc_stack_power(I, self.temperature) * 1e3
        H2_mfr = (mfr*60*self.dt)/1000 #kg/dt

        return H2_mfr

    def calc_O_mfr(self, H2_mfr):       #tabelle        #Einheit:kg/dt
        '''
        H2_mfr = massen flow rate H2 in kg/dt
        return: Oxygen flow rate in kg/dt
        '''
        roh_O = 1.429 #density Oxigen kg/m3
        O_mfr_m3 = (H2_mfr/self.roh_H2)/2
        O_mfr = O_mfr_m3*roh_O
        return O_mfr    #kg/dt

    def calc_H2O_mfr(self, H2_mfr):     #tabelle        #Einheit: kg/dt
        '''
        H2_mfr: Hydrogen mass flow in kg
        O_mfr: Oxygen mass flow in kg
        return: needed water mass flow in kg
        '''
        M_H2O = 18.010 #mol/g
        roh_H2O = 997 #kg/m3

        ratio_M = M_H2O/self.M # (mol/g)/(mol/g)
        H2O_mfr = H2_mfr * ratio_M + 40#H2O_mfr in kg
        #H2O_mfr = H2O_mfr_kg / roh_H2O

        return H2O_mfr  #kg/dt

    def gas_drying(self,H2_mfr):    #tabelle        #hier könnte noch ein fehler sein die werte scheinen mir sehr hoch
        '''
        input n_h2: mass flow in kg/dt
        :param n_H2:
        :return:
        '''
        M_H2 = 2.016*10**-3  # kg/mol Molare Masse H2
        nH2 = (H2_mfr/(60*self.dt))/M_H2 #kg/dt in kg/s in mol/s
        cp_H2 = 14300  # J/kg*K Wärmekapazität H2

        X_in = 0.1 #Mol H2O/Mol H2
        X_out = 1 #minimum needed
        n = (X_in/(X_out-X_in))*nH2
        dT=300-20 #Temperaturdifferenz zwischen Adsorbtion und Desorption

        P_hz = cp_H2*M_H2*n*dT

        Q_des = 48600*n #J/s
        #P_gasdrying = (P_hz + Q_des)/1000/H2_mfr #in kW/kg 
        P_gasdrying = (P_hz + Q_des)/1000 #in kW 
        return P_gasdrying  #kw

    def compression(self,p2):       #tabelle
        '''
        :param p2: needed pressure in bar
        :param T: electrolyze temperature
        :return: needed Power for compression in kW/kg
        '''
        #w_isotherm = R * T * Z * ln(p2 / p1)
        #p1=101325 #p atmo in pascal
        T2 = 273.15+30 #k
        p1 = 30 #bar    
        Z = 0.95    
        k = 1.4
        kk = k / (k - 1)
        eta_Ver = 0.75
        w_isentrop = kk * self.R * T2 * Z*(((p2 / p1)**kk) - 1)
        #T2 = T*(p2 / p1) ** kk
        #P_compression = (((w_isentrop/self.M)/1000) * (1/3600)) / eta_Ver  #alt
        #P_compression = ((w_isentrop/(60*self.dt))/eta_Ver)/1000
        #P_compression = ((w_isentrop/self.M)/1000)/eta_Ver 
        P_compression = (((w_isentrop/self.M) / eta_Ver )/1000)/(60*self.dt)   
        return P_compression    #kw

    def heat_cell(self, P_dc):          #tabelle
        '''
        P_dc: in kW
        return: q cell in kW
        '''
        V_th = self.E_th_0
        I = self.calculate_cell_current(P_dc)
        U_cell = self.calc_cell_voltage(I, self.temperature)

        q_cell = (self.n_cells*(U_cell - V_th)*I)/1000
        return q_cell       #kW

    def heat_sys(self, q_cell,H2O_mfr):  #hier könnte noch ein fehler sein 
        '''
        q_cell: in kW
        H20_mfr: in kg/dt
        return: q_loss in kW
                q_H20_fresh in kW
        '''
        #c_pH2O = 0.001162 #kWh/kg*k #alt
        c_pH2O = (0.001162)/(60*self.dt) #kWdt/kg*k
        dt = self.T - 20 #operate temp. - ambient temp.

        q_H2O_fresh = (- (c_pH2O) * H2O_mfr * dt * 1.5) #multyplied with 1.5 for transport water #kw
        q_loss =  (q_cell + q_H2O_fresh) * 0.14   # hier war mal ein minus vor

        return q_loss   #kw

    def calc_mfr_cool(self, q_loss):  #tabelle
        '''
        q_system in kW
        return: mfr cooling water in kg/dt
        '''

        q_system = q_loss/1000#kWh
        c_pH2O = 0.001162/(60*self.dt) #kWh/kg*k
        #operate temperature - should temperature
        mfr_cool = ((q_system)/(c_pH2O*(50-20)))

        return mfr_cool

    def calc_pump(self, H2O_mfr):     #tabelle
        '''
        H2O_mfr: in kg/dt
        P_stack: kw
        P_dc:kw
        pressure: in Pa
        return: kW
        '''
        # Wirkungsgradkurve Kreiselpumpe: https://doi.org/10.1007/978-3-642-40032-2
        relative_performance_pump = [0.0,0.05,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.001]
        eta_pump = [0.627,0.644,0.661,0.677,0.691,0.704,0.715,0.738,0.754,0.769,0.782,0.792,0.797,0.80]
        # Interpolationsfunktion erstellen
        f_eta_pump = interp1d(relative_performance_pump, eta_pump, kind='linear')
        # Wirkungsgrad berechnen für aktuellen
        eta_interp_pump = f_eta_pump(0.9)  # Interpoliere den eta-Wert

        #Druckverlust Leitungen in Pa
        relative_performance_pressure = [0.0, 0.02, 0.07, 0.12, 0.16, 0.2, 0.25, 0.32, 0.36, 0.4, 0.47, 0.54, 0.59,
                                         0.63, 0.67, 0.71, 0.74, 0.77, 0.8, 0.83, 0.86, 0.89, 0.92, 0.95, 0.98, 1.01]
        dt_pressure = [0.0, 330, 1870, 3360, 5210, 8540, 12980, 21850, 27020, 32930, 44000, 59500, 70190, 80520, 90850,
                        100810,110400, 119990, 128840, 138420, 148010, 158330, 169760, 181190, 191890, 200000]
        # Interpolationsfunktion erstellen
        f_dt_pressure = interp1d(relative_performance_pressure, dt_pressure)
        # Eigenverbrauch berechnen
        dt_interp_pressure = f_dt_pressure(0.9)  # Interpoliere den eta-Wert

        vfr_H2O = ((H2O_mfr/(60*self.dt))/997) #mass in volume with 997 kg/m3
        P_pump_fresh =  (vfr_H2O) * (self.p_atmo) * (1-eta_interp_pump)
        P_pump_cool = (vfr_H2O ) * (dt_interp_pressure) * (1 - eta_interp_pump)
        #P_gesamt=(P_pump_fresh+ P_pump_cool)/1000/(60*self.dt) #W in KW   
        #P_gesamt=(P_pump_fresh+ P_pump_cool)/1000/(H2O_mfr)#kw/kg
        P_gesamt=(P_pump_fresh+ P_pump_cool)#kw
        return P_gesamt #kw

    
    
    
    def prepare_timeseries(self, ts):
        #prüft ob der elektrolyseur in der 500 klasse liegt
        if self.P_nominal % 500 != 0:
            raise ValueError("Die Leistung des Elektrolyseurs muss in der 500er Reihe liegen!")
        else:   
            #power_dc 
            ts['P_in [KW]'] = 0.0
            
            for i in range(len(ts.index)):
                if ts.loc[ts.index[i], 'P_ac'] > 0:
                    ts.loc[ts.index[i], 'P_in [KW]'] = round(self.power_dc(ts.loc[ts.index[i], 'P_ac']),2)
                else:
                    
                    ts.loc[ts.index[i], 'P_in [KW]'] = 0  

            #status_codes
            ts = self.status_codes(ts)
            
            
            ts['hydrogen production [Kg/dt]'] = 0.0 #neue Spalte mit hydrogenproduction = 0.0 "platzhalter"
            ts['surplus electricity [kW]'] = 0.0
            ts['H20 [kg/dt]'] = 0.0
            ts['Oxygen [kg/dt]'] = 0.0
            ts['cooling Water [kg/dt]'] = 0.0
            ts['Heat Cell [%]'] = 0.0
            ts['compression [%]'] = 0.0
            ts['gasdrying {%]'] = 0.0
            ts['pump [%]'] = 0.0
            ts['heat system [%]'] = 0.0
            ts['efficiency [%]'] = 0.0
            ts['efficency with compression [%]'] = 0.0
            


            for i in range(len(ts.index)): #Syntax überprüfen! 
                
                
                # komtrolliert ob in der zeile status die zahl 4 steht (production)
                if ts.loc[ts.index[i], 'status'] == 'production':

                    
                    #wenn die Eingangsleistung kleiner als p_eletrolyseur ist
                    if ts.loc[ts.index[i], 'P_in [KW]'] <= self.P_nominal:
                        #----------------------------------------------------------------------------------------------------------------
                        #output
                        
                        #hydrogen kg/dt
                        hydrogen_production=self.run(ts.loc[ts.index[i], 'P_in [KW]'])
                        ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'] = round(hydrogen_production,2)
                        
                        #H20  kg/dt
                        H2O=self.calc_H2O_mfr(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'H20 [kg/dt]'] = round(H2O,2)
                        
                        #oxygen kg/dt
                        Oxygen=self.calc_O_mfr(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'Oxygen [kg/dt]'] = round(Oxygen,2)

                        #cooling_water kg/dt
                        
                        cooling_water=self.calc_mfr_cool(heat_system_KW)
                        ts.loc[ts.index[i], 'cooling Water [kg/dt]']=round(cooling_water,2)
                        #------------------------------------------------------------------------------------------------------------------------------
                        #losses 
                        
                        #gasdrying %
                        gasdrying_KW=self.gas_drying(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'gasdrying {%]'] = round((gasdrying_KW/ts.loc[ts.index[i], 'P_in [KW]'])*100,2)   
                        
                        #pump  #%
                        pump_KW=self.calc_pump(ts.loc[ts.index[i], 'H20 [kg/dt]'])
                        ts.loc[ts.index[i], 'pump [%]'] = round((pump_KW/ts.loc[ts.index[i], 'P_in [KW]'])*100,2)
                        
                        
                        # heat_cell %
                        Heat_Cell_kW=self.heat_cell(ts.loc[ts.index[i], 'P_in [KW]'])
                        ts.loc[ts.index[i], 'Heat Cell [%]'] = round((Heat_Cell_kW/ts.loc[ts.index[i], 'P_in [KW]'])*100,2)
                        
                        # heat system %
                        heat_system_KW=self.heat_sys(Heat_Cell_kW, ts.loc[ts.index[i], 'H20 [kg/dt]'])
                        ts.loc[ts.index[i], 'heat system [%]'] = round((heat_system_KW/ts.loc[ts.index[i], 'P_in [KW]'])*100,2)
                        
                        #compression %
                        compression_KW=self.compression(self.p2)
                        ts.loc[ts.index[i], 'compression [%]'] = round((compression_KW/ts.loc[ts.index[i], 'P_in [KW]'])*100,2)

                        #cooling_water kg/dt
                        cooling_water=self.calc_mfr_cool(heat_system_KW)
                        ts.loc[ts.index[i], 'cooling Water [kg/dt]']=round(cooling_water,2)
                        #---------------------------------------------------------------------------------------------------------------------------------------
                        #efficiency
                        efficiency=100-ts.loc[ts.index[i], 'gasdrying {%]']-ts.loc[ts.index[i], 'pump [%]']-ts.loc[ts.index[i], 'Heat Cell [%]']-ts.loc[ts.index[i], 'heat system [%]']
                        ts.loc[ts.index[i], 'efficiency [%]'] = round(efficiency,2)
                        
                        #efficency with compression
                        efficency_with_compression=100-ts.loc[ts.index[i], 'gasdrying {%]']-ts.loc[ts.index[i], 'pump [%]']-ts.loc[ts.index[i], 'Heat Cell [%]']-ts.loc[ts.index[i], 'heat system [%]']-ts.loc[ts.index[i], 'compression [%]']
                        ts.loc[ts.index[i], 'efficency with compression [%]'] = round(efficency_with_compression,2)
                        #---------------------------------------------------------------------------------------------------------------------------------------------
                    
                    #wenn die Eingangsleistung größer als p_eletrolyseur ist
                    else:
                        #----------------------------------------------------------------------------------------------------------------
                        #output
                        
                        #hydrogen kg/dt
                        hydrogen_production=self.run(self.P_nominal)
                        ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'] = round(hydrogen_production,2)
                        
                        #surplus electricity [kW]
                        surplus_electricity=ts.loc[ts.index[i], 'P_in [KW]'] - self.P_nominal
                        ts.loc[ts.index[i], 'surplus electricity [kW]'] = round(surplus_electricity,2)

                        #H20  kg/dt
                        H2O=self.calc_H2O_mfr(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'H20 [kg/dt]'] = round(H2O,2)
                        
                        #oxygen kg/dt
                        Oxygen=self.calc_O_mfr(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'Oxygen [kg/dt]'] = round(Oxygen,2)

                        #------------------------------------------------------------------------------------------------------------------------------
                        #losses 
                        
                        #gasdrying %
                        gasdrying_KW=self.gas_drying(ts.loc[ts.index[i], 'hydrogen production [Kg/dt]'])
                        ts.loc[ts.index[i], 'gasdrying {%]'] = round((gasdrying_KW/self.P_nominal)*100,2)   
                        
                        #pump  #%
                        pump_KW=self.calc_pump(ts.loc[ts.index[i], 'H20 [kg/dt]'])
                        ts.loc[ts.index[i], 'pump [%]'] = round((pump_KW/self.P_nominal)*100,2)
                        
                        
                        # heat_cell %
                        Heat_Cell_kW=self.heat_cell(self.P_nominal)
                        ts.loc[ts.index[i], 'Heat Cell [%]'] = round((Heat_Cell_kW/self.P_nominal)*100,2)
                        
                        # heat system %
                        heat_system_KW=self.heat_sys(Heat_Cell_kW, ts.loc[ts.index[i], 'H20 [kg/dt]'])
                        ts.loc[ts.index[i], 'heat system [%]'] = round((heat_system_KW/self.P_nominal)*100,2)
                        
                        #compression %
                        compression_KW=self.compression(self.p2)
                        ts.loc[ts.index[i], 'compression [%]'] = round((compression_KW/self.P_nominal)*100,2)

                        #cooling_water kg/dt
                        cooling_water=self.calc_mfr_cool(heat_system_KW)
                        ts.loc[ts.index[i], 'cooling Water [kg/dt]']=round(cooling_water,2)
                        #---------------------------------------------------------------------------------------------------------------------------------------
                        #efficiency
                        efficiency=100-ts.loc[ts.index[i], 'gasdrying {%]']-ts.loc[ts.index[i], 'pump [%]']-ts.loc[ts.index[i], 'Heat Cell [%]']-ts.loc[ts.index[i], 'heat system [%]']
                        ts.loc[ts.index[i], 'efficiency [%]'] = round(efficiency,2)
                        
                        #efficency with compression
                        efficency_with_compression=100-ts.loc[ts.index[i], 'gasdrying {%]']-ts.loc[ts.index[i], 'pump [%]']-ts.loc[ts.index[i], 'Heat Cell [%]']-ts.loc[ts.index[i], 'heat system [%]']-ts.loc[ts.index[i], 'compression [%]']
                        ts.loc[ts.index[i], 'efficency with compression [%]'] = round(efficency_with_compression,2)
                        #---------------------------------------------------------------------------------------------------------------------------------------------
                    
                
                    

                
                #hochfahren
                elif ts.loc[ts.index[i], 'status'] == 'booting':
                    ts.loc[ts.index[i], 'surplus electricity [kW]'] = ts.loc[ts.index[i], 'P_in [KW]'] - 0.0085*self.P_nominal
                else:
                    ts.loc[ts.index[i], 'surplus electricity [kW]'] = ts.loc[ts.index[i], 'P_in [KW]']

            #Wie lange dauert die produktion des Wasserstoffs
            for i in ts.index:
                total_production = 0
                count_additions = 0
                i=0
                # Solange die Gesamtproduktion kleiner als 100 ist, addiere den aktuellen Wert
            while total_production <= self.production_H2:
                #total_production += ts.loc[ts.index[i], 'hydrogen production [Kg/dt]']
                total_production += ts.loc[ts.index[i], 'hydrogen production [Kg/dt]']
                count_additions += 1
                i+=1
                #print(total_production)
            
            print("Die Produktion von {}kg Wasserstoff dauert {} Stunden".format(self.production_H2,(count_additions/(60/self.dt))))
            

           
    
    
            return ts

            