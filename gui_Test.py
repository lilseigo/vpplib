import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash 
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from vpplib.environment import Environment
from vpplib.user_profile import UserProfile
from vpplib.photovoltaic import Photovoltaic
from vpplib.battery_electric_vehicle import BatteryElectricVehicle
from vpplib.heat_pump import HeatPump
from vpplib.electrical_energy_storage import ElectricalEnergyStorage
from vpplib.wind_power import WindPower
from vpplib.virtual_power_plant import VirtualPowerPlant
from vpplib.operator import Operator


#TODO: Add units to input fields (input addons)

#region Input Mask
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  


app.layout = dbc.Container([

dbc.Row([
    dbc.Col([
        html.H1('VPPlib Simulation')
    ],align='middle')
    
    ],style={'margin-top': '20px', 
             'margin-bottom': '20px',
             }),

#Create Tabs    
    dbc.Tabs([
        dbc.Tab(label='Basic Settings', 
                id='tab_grundeinstellungen',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                                html.P('PV Percentage')
                            ], width=3),
                        dbc.Col([
                            dbc.Input(
                                    id='input_pv_percentage',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='%'
                                    )
                            ], width= 3)
                        ],style={'width':'3', 'margin-top': '20px'}),
                        dbc.Row([
                            dbc.Col([
                                    html.P('Storage Percentage')
                                ],width=3),
                            dbc.Col([
                                dbc.Input(
                                    id='input_storage_percentage',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='%'
                                    )
                                ], width=3)
                            ]),
                        dbc.Row([
                            dbc.Col([
                                    html.P('BEV Percentage')
                                ],width=3),
                            dbc.Col([
                                dbc.Input(
                                    id='input_bev_percentage',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='%'
                                    )
                                ], width=3)
                            ]),
                        dbc.Row([
                            dbc.Col([
                                    html.P('Heat Pump Percentage')
                                ],width=3),
                            dbc.Col([
                                dbc.Input(
                                    id='input_hp_percentage',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='%'
                                    )
                                ], width=3)
                            ]),
                        dbc.Row([
                            dbc.Col([
                                    html.P('Wind Percentage')
                                ],width=3),
                            dbc.Col([
                                dbc.Input(
                                    id='input_wind_percentage',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='%'
                                    )
                                ], width=3)
                                
                        ])
                    ]),        
        dbc.Tab(label='Environment', 
                tab_id= 'tab_environment',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                            dbc.Col([
                                    html.P('Date Start'),
                                ], width=3),
                            dbc.Col([
                                dbc.Input(
                                        id='input_date_start',
                                        type='date',
                                        style={'width': 'auto'},
                                        placeholder='YYYY-MM-DD',
                                        ),
                                ], width= 3)
                            ],style={'width':'auto', 'margin-top': '20px'}),
                            dbc.Row([
                                dbc.Col([
                                        html.P('Date End')
                                    ],width=3),
                                dbc.Col([
                                    dbc.Input(
                                        id='input_date_end',
                                        type='date',
                                        style={'width': 'auto'},
                                        placeholder='YYYY-MM-DD'
                                        )
                                    ], width='auto')
                                ]),
                            dbc.Row([
                                dbc.Col([
                                        html.P('Time Zone')
                                    ],width='3'),
                                dbc.Col([
                                    dcc.Dropdown(
                                        [   'Pacific/Kwajalein UTC-12',
                                            'Pacific/Samo UTC-11',
                                            'Pacific/Honolulu UTC-10',
                                            'America/Anchorage UTC-9',
                                            'America/Los_Angeles UTC-8',
                                            'America/Denver UTC-7',
                                            'America/Chicago UTC-6',
                                            'America/New_York UTC-5',
                                            'America/Caracas UTC-4',
                                            'America/St_Johns UTC-3.5',
                                            'America/Argentina/Buenos_Aires UTC-3s',
                                            'Atlantic/Azores UTC-2',
                                            'Atlantic/Cape_Verde UTC-1',
                                            'Europe/London UTC+0',
                                            'Europe/Berlin UTC+1',
                                            'Europe/Helsinki UTC+2 ',
                                            'Europe/Moscow UTC+3',
                                            'Asia/Dubai UTC+4',
                                            'Asia/Kabul UTC+4.5',
                                            'Asia/Karachi UTC+5',
                                            'Asia/Kathmandu UTC+5.75',
                                            'Asia/Dhaka UTC+6',
                                            'Asia/Jakarta UTC+7',
                                            'Asia/Shanghai UTC+8',
                                            'Asia/Tokyo UTC+9 ',
                                            'Australia/Brisbane UTC+10 ',
                                            'Australia/Sydney UTC+11',
                                            'Pacific/Auckland UTC+12'
                                            ],
                                        id='dropdown_timezone',
                                        style={'width': 'auto', 
                                                'color': 'black',
                                                'bgcolor': 'white',
                                                'width': '3'
                                                },
                                        placeholder='Choose a Timezone',
                                        clearable=False
                                        )
                                    ], width='3')
                                ]),
                            dbc.Row([
                                dbc.Col([
                                        html.P('Time Step')
                                    ],width='3'),
                                dbc.Col([
                                    dcc.Dropdown(
                                        [   '1 min',
                                            '15 min',
                                            '60 min',
                                            '1 day'
                                            ],
                                        id='dropdown_time_step',
                                        style={'width': 'auto', 
                                                'color': 'black',
                                                'bgcolor': 'white',
                                                'width': '3'
                                                },
                                        placeholder='Choose a Time Step',
                                        clearable=False
                                        )
                                    ], width='3')
                                ]),
                            dbc.Row([
                                dbc.Col([
                                        html.P('Upload Weather Data')
                                    ],width='3', 
                                    ),
                                dbc.Col([
                                    dcc.Upload(
                                        id='upload_weather_data',
                                        children=dbc.Container([
                                            'Drag and Drop or ',
                                            html.A('Select Files')
                                        ]),
                                        style={
                                            'width': 'auto',
                                            'height': 'auto',
                                            'lineHeight': '60px',
                                            'borderWidth': '1px',
                                            'borderStyle': 'dashed',
                                            'textAlign': 'center',
                                            'margin': '10px'
                                        },
                                    )
                                        
                                    ], width='3')
                                ], align='center'),
                            
                    ]),
        dbc.Tab(label='User Profile', 
                tab_id='tab_userprofile',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                                html.P('Identifier')
                                ], width=4),
                        dbc.Col([
                               dbc.Input(
                                        id='input_identifier',
                                        type='text',
                                        style={'width': 'auto'},
                                        placeholder='bus 1')
                                ], width=3)
                        ],style={'margin-top': '20px'}),      
                    dbc.Row([
                        dbc.Col([
                                html.P('Latitude'),
                                ],width=4),
                        dbc.Col([
                            dbc.Input(
                                    id='input_latitude',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='e.g. 50.7498321')
                            ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([                 
                                html.P('Longitude')
                                ],width=4),
                        dbc.Col([
                                 dbc.Input(
                                    id='input_longitude',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='e.g. 6.473982')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                html.P('Thermal Energy Demand')
                                ], width=4),
                        dbc.Col([
                                dbc.Input(
                                        id='input_thermal_energy_demand',
                                        type='number',
                                        style={'width': 'auto'},
                                        placeholder='e.g. 10000 kWh')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                html.P('Comfort Factor')
                                ],width=4),
                        dbc.Col([
                                dbc.Input(
                                        id='input_comfort_factor',
                                        type='number',
                                        style={'width': 'auto'},
                                        placeholder='e.g. ?')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                html.P('Daily Vehicle Usage')
                                ],width=4),
                        dbc.Col([
                                dbc.Input(
                                        id='input_daily_vehicle_usage',
                                        type='number',
                                        style={'width': 'auto'},
                                        placeholder='e.g. 100 km')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                html.P('Building Type')
                                ], width=4),
                        dbc.Col([
                                dcc.Dropdown( 
                                    ['DE_HEF33', 'DE_HEFXYZ'],
                                    id='dropwdown_building_type',
                                    style={
                                            'color': 'black',
                                            'bgcolor': 'white',
                                            'width': '82%'
                                            },
                                    placeholder='Choose a Building Type')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                html.P('T0'),
                                ], width=4),
                        dbc.Col([
                                dbc.Input(
                                    id='input_t0',
                                    type='number',
                                    style={'width': 'auto'},
                                    placeholder='e.g. 20 °C')
                                ], width=3)
                        ]),
                    dbc.Row([
                        dbc.Col([
                                 html.P('Upload Base Load')   
                                ], width=4),
                        dbc.Col([
                            dcc.Upload(
                                id='upload_base_load',
                                children=dbc.Container([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]),style={
                                    'height': 'auto',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'textAlign': 'center',
                                    'margin': '10px',
                                })
                            ], width=3)
                        ], align='center')
                    ]),
        dbc.Tab(label='BEV', 
                tab_id='tab_bev',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.P('Max. Battery Capacity')
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id='input_bev_max_battery_capacity',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 100 kWh'
                            )
                        ], width=3),
                    ], style={'margin-top': '20px'}),
                    dbc.Row([
                        dbc.Col([
                            html.P('Min. Battery Capacity')
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id='input_bev_min_battery_capacity',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 15 kWh'
                            )
                        ], width=3),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Battery Usage') #TODO: What is this?
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id='input_bev_battery_usage',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. ???'
                            )
                        ], width=3),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Charging Power') 
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id='input_bev_charging_power',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 11 kW'
                            )
                        ], width=3),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Charging Efficiency') 
                        ], width=4),
                        dbc.Col([
                            dbc.Input(
                                id='input_bev_charging_efficiency',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 90%'
                            )
                        ], width=3),
                    ])
                ]),
        dbc.Tab(label='Photovoltaic', #TODO: Fill in the blanks in DropDown Menues
                tab_id='tab_photvoltaic',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.P('Module Library')
                        ], width=3),
                        dbc.Col([
                            dcc.Dropdown(
                                id='dropdown_pv_module_library',
                                clearable=True,
                                style={'width': '82%', 
                                       'color': 'black',
                                        'bg-color':'white' 
                                        },
                                placeholder='e.g. SandiaMod',
                                options=[
                                    {'label': 'SandiaMod', 'value': 'SandiaMod'},
                                    {'label': 'CECMod', 'value': 'CECMod'}
                                ]
                            )
                        ], width=3)
                    ], style={'margin-top': '20px'}),
                    dbc.Row([
                        dbc.Col([
                            html.P('Module')
                        ], width=3),
                        dbc.Col([
                            dcc.Dropdown(
                                id='dropdown_pv_module',
                                clearable=True,
                                style={'width': '82%', 
                                       'color': 'black'},
                                placeholder='e.g. Canadian_Solar_CS5P_220M___2009_'
                            )
                        ], width=3)

                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Inverter Library')
                        ], width=3),
                    dbc.Col([
                        dcc.Dropdown(
                            id='dropdown_pv_inverter_library',
                            clearable=True,
                            style={'width': '82%', 
                                   'color': 'black'},
                            placeholder='e.g. cecinverter'
                        )
                        ], width=3)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Inverter')
                        ], width=3),
                        dbc.Col([
                            dcc.Dropdown(
                                id='dropdown_pv_inverter',
                                clearable=True,
                                style={'width': '82%', 
                                       'color': 'black'},
                                placeholder='e.g. ABB__MICRO_0_25_I_OUTD_US_208__208V_'
                            )
                        ], width=3)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Surface Tilt')
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_pv_surface_tilt',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 20°'
                            )
                        ], width=3)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Surface Azimuth')
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_pv_surface_azimuth',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 200°'
                            )
                        ], width=3)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Modules per String')
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_pv_modules_per_string',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 6'
                            )
                        ], width=3)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Strings per Inverter')
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_pv_strings_per_inverter',
                                type='number',
                                style={'width': 'auto'},
                                placeholder='e.g. 2'
                            )
                        ], width=3)
                    ])
                ]),
        dbc.Tab(label='Wind', 
                tab_id='tab_wind',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader('Wind Turbine Data', 
                                               style={'font-weight': 'bold'}),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Turbine Type')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Input(
                                                id='input_wind_turbine_type',
                                                type='text',
                                                style={'width': 'auto'},
                                                placeholder='e.g. E-126/4200',
                                            )
                                        ]),
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Hub Height')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Input(
                                                id='input_wind_hub_height',
                                                type='number',
                                                style={'width': 'auto'},
                                                placeholder='e.g. 135 m'
                                            )
                                        ])                                    
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Rotor Diameter')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Input(
                                                id='input_wind_rotor_diameter',
                                                type='number',
                                                style={'width': 'auto'},
                                                placeholder='e.g. 127 m'
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Comfort Factor')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Input( #TODO: What is this? Compare with Screeenshot
                                                id='input_wind_comfort_factor',
                                                type='number',
                                                style={'width': 'auto'},
                                                placeholder='e.g. 0.9'
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Data source')
                                        ], width=3),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                ['oedb', 'xyz'],
                                                id='dropdown_wind_data_source',
                                                clearable=True,
                                                style={
                                                       'color': 'black',
                                                       'bgcolor': 'white',
                                                       'width':'70%'
                                                       },
                                                placeholder='e.g. WindTurbines',
                                            )
                                        ])
                                    ])
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader('Wind Power Model Chain Data',
                                               style={'font-weight': 'bold'}),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Wind Speed Model')
                                        ], width = 4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                ['logarithmic', 'hellman', 'interpolation_extrapolation'],
                                                id='dropdown_wind_speed_model',
                                                clearable=True,
                                                style={'width': '82%', 
                                                       'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. logarithmic',
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Density Model')
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                ['barometric', 'ideal gas', 'interpolation_extrapolation'],
                                                id='dropdown_wind_density_model',
                                                clearable=True,
                                                style={'width': '82%', 
                                                       'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. barometric',
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Temperature Model')
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                ['linear gradient', 'interpolation extrapolation'],
                                                id='dropdown_wind_temperature_model',
                                                clearable=True,
                                                style={'width': '82%', 
                                                       'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. linear gradient',
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Power Output Model')
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                ['power curve', 'power coefficient curve'],
                                                id='dropdown_wind_power_output_model',
                                                clearable=True,
                                                style={'width': '82%', 
                                                       'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='power curve',
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Density Correction', style={'margin-top': '10%'})
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='switch_wind_density_correction',
                                                style={'width': 'auto', 'margin-top': '5%'},
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Obstacle Height')
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Input(
                                                id='input_wind_obstacle_height',
                                                type='number',
                                                style={'width': 'auto'},
                                                placeholder='e.g. 0 m'
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Hellmann Exponent')
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Input( 
                                                id='input_hellmann_exponent',
                                                type='text',
                                                style={'width': 'auto'},
                                                placeholder='e.g. 0.2'
                                            )
                                        ])
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Upload Wind Data', style={'margin-top': '15%'})
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Upload(
                                                id='upload_wind_data',
                                                style={'width': 'auto',
                                                    'height': 'auto',
                                                    'lineHeight': '60px',
                                                    'borderWidth': '1px',
                                                    'borderStyle': 'dashed',
                                                    'textAlign': 'center',
                                                    'margin': '10px'
                                                },
                                                children=dbc.Container([
                                                    'Drag and Drop or ',
                                                    html.A('Select Files')
                                                ]),
                                            )
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ], style={'margin-top': '20px'}),
                ]),
        dbc.Tab(label='Heat Pump', 
                tab_id='tab_heatpump',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.P('Type of Heat Pump')
                        ], width=3),
                        dbc.Col([
                            dcc.Dropdown(
                                ['Air', 'Ground'],
                                id='dropdown_heatpump_type',
                                style={'width': '100%',
                                        'color': 'black',
                                        'bgcolor': 'white',
                                        },
                                placeholder='e.g. Air'
                            )
                        ], width=2)
                    ], style={'margin-top': '20px'}),
                    dbc.Row([
                        dbc.Col([
                            html.P('Heat System Temperature')
                        ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_heatpump_system_temperature',
                                type='number',
                                style={'width': '100%'},
                                placeholder='e.g. 20.5 °C'
                            )
                        ], width=2)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Electrical Power')
                            ], width=3),
                        dbc.Col([
                            dbc.Input(
                                id='input_heatpump_electrical_power',
                                type='number',
                                style={'width': '100%'},
                                placeholder='e.g. 5 kW'
                            )
                        ], width=2)
                    ])
                ]),
        dbc.Tab(label='Storage', 
                tab_id='tab_storage',
                active_label_style={'color': 'grey'},
                children=[
                    dbc.Row([
                        dbc.Col([
                            html.P('Charge Efficiency')
                        ], width=3),
                        dbc.Col([
                            dbc.InputGroup([
                            dbc.Input(
                                id='input_storage_charge_efficiency',
                                type='number',
                                style={'width': '70%'},
                                placeholder='e.g. 90%'),
                            dbc.InputGroupText('%')
                        ])
                        ], width=2)
                    ],style={'margin-top':'20px'}),
                    dbc.Row([
                        dbc.Col([
                            html.P('Discharge Efficiency')
                        ], width=3),
                        dbc.Col([
                            dbc.InputGroup([
                            dbc.Input(
                                id='input_storage_discharge_efficiency',
                                type='number',
                                style={'width': '70%'},
                                placeholder='e.g. 90%'),
                            dbc.InputGroupText('%')
                            ])
                        ], width=2)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Max. Power')
                        ], width=3),
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.Input(
                                    id='input_storage_max_power',
                                    type='number',
                                    style={'width': '70%'},
                                    placeholder='e.g. 10 kW'),
                                dbc.InputGroupText('kW')
                            ])
                        ], width=2)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Max. Capacity')
                        ], width=3),
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.Input(
                                    id='input_storage_max_capacity',
                                    type='number',
                                    style={'width': '60%'},
                                    placeholder='e.g. 10 kWh'),
                                dbc.InputGroupText('kWh')
                            ])
                        ], width=2)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.P('Max. C-Rate')
                        ], width=3),
                        dbc.Col([
                                dbc.Input(
                                    id='input_storage_max_crate',
                                    type='number',
                                    style={'width': '100%'},
                                    placeholder='0.5-1.2')
                        ], width=2)
                    ])
                ]),

        dbc.Tab(label='Results', 
                tab_id='tab9',
                active_label_style={'color': 'grey'}
                ),
        ]),
],fluid=True)



#Create Tab Contents

#endregion


#region Results
#Create Results Tab
#endregion
if __name__ == '__main__':
    app.run_server(debug=True)

