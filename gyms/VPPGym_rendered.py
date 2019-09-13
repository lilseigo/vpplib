# -*- coding: utf-8 -*-
"""
Created on Thu May  2 12:13:59 2019

@author: patri
"""


import numpy as np
import pandas as pd
from gym import spaces
import gym
from collections import deque
from model.VPPPhotovoltaic import VPPPhotovoltaic
from model.VPPEnergyStorage import VPPEnergyStorage
from model.VPPHousehold import VPPHousehold
import pyglet
from gym.envs.classic_control import rendering
import utils.rendering_sprites as img
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

class ems(gym.Env):
               
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 30
    }
    """
        Info
        ----
        The ems-class is the training environment for the DDQN-Agent. 
        
        Parameters
        ----------
        Under __init__ 
        ...
        	
        Attributes
        ----------
        
        ...
        
        Notes
        -----
        The offset variable takes into account that there are nearly no days with more PV-production than electricity demand. 
        ...
        
        References
        ----------
        
        ...
        
        Returns
        -------
        
        ...
        
    """

    def __init__(self, EP_LEN):
        super(ems, self).__init__()
        self.LOG_EVENTS = False
        self.EP_LEN = EP_LEN
        self.obs = 3
        self.offset = 24 * 4 * 7 * 13 
        self.observation_space = spaces.Box(low = -5, high = 5, shape = (self.obs,), dtype=np.float32)
        self.action_space = spaces.Box(low = -1, high = 1, shape = (2,), dtype = np.float32)#spaces.Continuous(3)
        self.time = 0 + self.offset
        self.residual = 0
        self.max_pv = 0
        self.r = 0
        self.log = deque(maxlen=self.EP_LEN)
        self.pv = self.prepareTimeSeriesPV()
        self.loadprofile = VPPHousehold(15, None, None)
        self.loadprofile.data *= 0.5
        self.day_ind = self.day_sin()
        self.max_lp = max(self.loadprofile.data)
        self.viewer = None
        self.render_vars = [np.zeros(self.obs),0]
        self.plot = np.zeros(5)
        
    def prepareTimeSeriesPV(self):
        """
        Info
        ----
        This method initializes the PV-Lib module with its necessary parameters.
        
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
        A DataFrame Object with the 
        ...
        
        """
        latitude = 50.941357
        longitude = 6.958307
        name = 'Cologne'
        
        weather_data = pd.read_csv("./Input_House/PV/2017_irradiation_15min.csv")
        weather_data.set_index("index", inplace = True)
        
        pv = VPPPhotovoltaic(timebase=1, identifier=name, latitude=latitude, longitude=longitude, modules_per_string=5, strings_per_inverter=1)
        pv.prepareTimeSeries(weather_data)
        return pv
        
    def reset(self):
        """
        Info
        ----
        This method resets all necessary parameters for a new episode of the training.
        
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
        The starting state is an array of zeros, as the first observation for the agent.
        ...
        
        """
        self.rand_start = int(np.random.rand()*25000)+self.offset
        state = np.array(np.zeros(self.obs))
        self.time = self.rand_start
        self.residual = 0       
        self.el_storage = VPPEnergyStorage(15, 35, 0.9, 0.9, 15, 1)
        self.el_storage.prepareTimeSeries()
        self.soc = []
        return state
    
    def day_sin(self):
        day_sin = []
        for i in range(24*4*366):
            sin_day = np.sin(2*np.pi*i/(24*4))
            cos_day = np.cos(2*np.pi*i/(24*4))
            day_sin.append([sin_day, cos_day])
        return day_sin
    
    def size_of_charge(self, action_size):
        #This function ensures that an action of 0.8 is the maximum charge multiplier. Higher multipliers need significantly higher input values in the neural network, thus reducing learning efficiency. 
        if action_size > 0.8: action_size = 0.8
        return abs(self.residual)*1.25*action_size
    
    def get_charge_reward(self, charge_size):
        is_valid_action = False
        #Action 0: Nichts
        #if selected_action == 0: r, is_valid_action = 0, True
        if charge_size < 0.05 and charge_size > -0.05: charge_reward, is_valid_action = 0, True
        #Action 1: Laden
        elif self.residual < 0 and charge_size > 0.05 :
            charge_reward = abs(charge_size)*3
            is_valid_action = self.el_storage.charge(abs(self.residual)*abs(charge_size), 15, self.time)
        #Action 2: Entladen
        elif self.residual > 0 and charge_size < -0.05:
            charge_reward = abs(charge_size)*3
            is_valid_action = self.el_storage.discharge(abs(self.residual)*abs(charge_size), 15, self.time)        
        #Fehler- und Rewardüberprüfung
        if not is_valid_action: charge_reward = -1
        return charge_reward
    
    def get_control_reward(self, control_size):
        control_reward = abs(self.residual - control_size)
        return np.clip(-control_reward, -1, 0)
    
    def step(self, action):
    #Actions:
    # 0 = nichts
    # 1 = Laden
    # 2 = Entladen   
        done = False
        res_bool, info = 0, 0
        #selected_action = np.argmax(action)
        charge_size = self.size_of_charge(action[0]) * self.el_storage.maxPower
        control_size = self.size_of_charge(action[1]) * self.max_lp
        charge_reward = self.get_charge_reward(charge_size)
        control_reward = self.get_control_reward(control_size)
        #Bereite den nächsten state vor
        lp = self.loadprofile.valueForTimestamp(self.time) 
        pv = self.pv.valueForTimestamp(self.time)*3
        self.residual = lp - pv
        if self.pv.valueForTimestamp(self.time) > self.max_pv: self.max_pv = self.pv.valueForTimestamp(self.time)

        res_bool = self.residual > 0     
        state = np.array([self.el_storage.stateOfCharge/self.el_storage.capacity, self.residual/self.max_lp, res_bool])
        
        self.time += 1
        self.soc.append(self.el_storage.stateOfCharge)
        timer_done = self.time >= self.rand_start + self.EP_LEN
        control_done = False#control_reward < -0.2 
        reward = control_reward + charge_reward
        if control_done:
            reward = -3
        if any([timer_done, control_done]) == True:         
            done = True
            info = pd.DataFrame(self.soc)
        self.render_vars = [state, control_reward]
            
        return state, reward, done, info
    
    def create_plot(self):
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.gca()        
        ax.text(0.0,0.0,"Test", fontsize=45)
        ax.axis('off')        
        canvas.draw()       # draw the canvas, cache the renderer       
        image = np.fromstring(canvas.tostring_rgb(), dtype='uint8')*255
        return image
        
    def render(self, mode = "human", close = False):
        screen_width = 600
        screen_height = 400
        
        if self.viewer == None:         
            
            self.viewer = rendering.Viewer(screen_width, screen_height)
            charge_state_border = rendering.make_polyline([(200,200), (200,250), (210,250), (210,200)])
            self.viewer.add_geom(charge_state_border)
            
            residual_state_border = rendering.make_polyline([(150,150), (150,250), (160,250), (160,150), (150,150)])
            self.viewer.add_geom(residual_state_border)  
    
            control_state_border = rendering.make_polyline([(250,150), (250,200), (260,200), (260,150), (250,150)])
            self.viewer.add_geom(control_state_border) 
            
            battery_icon = rendering.Image("./utils/rendering_sprites/battery.png", 30, 30)
            battery_icon.add_attr(rendering.Transform(translation=(205,275)))

            demand_icon = rendering.Image("./utils/rendering_sprites/demand.png", 30, 30)
            demand_icon.add_attr(rendering.Transform(translation=(155,275)))

            pv_icon = rendering.Image("./utils/rendering_sprites/pv.png", 30, 30)
            pv_icon.add_attr(rendering.Transform(translation=(155, 125)))
        
            control_icon = rendering.Image("./utils/rendering_sprites/control.png", 30, 30)
            control_icon.add_attr(rendering.Transform(translation=(255,275)))
            
#            plot_icon = rendering.Image("./utils/rendering_sprites/control.png", 200, 200)
#            plot_icon.img = pyglet.image.ImageData(100, 100, "L", self.create_plot().data.__str__())
#            plot_icon.add_attr(rendering.Transform(translation=(100,100)))

            #battery_icon.Transform()
            self.viewer.add_geom(battery_icon)
            self.viewer.add_geom(demand_icon)
            self.viewer.add_geom(pv_icon)
            self.viewer.add_geom(control_icon)
#            self.viewer.add_geom(plot_icon)
#        @self.viewer.window.event        
#        def on_flip(self):
#            label.draw()
#        
#        label = pyglet.text.Label("yehaa", x = 120, y = 180)
        charge_state = rendering.FilledPolygon([(200,200), (200,200+50*self.render_vars[0][0]), (210,200+50*self.render_vars[0][0]), (210,200)])
        self.viewer.add_onetime(charge_state)
        
        residual_state = rendering.FilledPolygon([(150,200), (150,200+50*self.render_vars[0][1]), (160,200+50*self.render_vars[0][1]), (160,200)])
        self.viewer.add_onetime(residual_state)  

        control_state = rendering.FilledPolygon([(250,200), (250,200+50*self.render_vars[1]), (260,200+50*self.render_vars[1]), (260,200)])
        self.viewer.add_onetime(control_state) 

        return self.viewer.render(return_rgb_array = mode=='rgb_array')
    
    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None        