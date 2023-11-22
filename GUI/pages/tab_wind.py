from dash import dash, dcc, html, callback, Input, Output, State, callback_context as ctx
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate

layout=dbc.Container([
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
                                                placeholder='e.g. E-126/4200',
                                            )
                                        ], width=4),
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Hub Height')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id='input_wind_hub_height',
                                                    type='number',
                                                    placeholder='e.g. 135 m'
                                                ),
                                                dbc.InputGroupText('m')
                                            ])
                                        ],width=4)                                    
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Rotor Diameter')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id='input_wind_rotor_diameter',
                                                    type='number',
                                                    placeholder='e.g. 127 m'
                                                ),
                                                dbc.InputGroupText('m')
                                            ])
                                        ], width=4)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Comfort Factor')
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Input( #TODO: What is this? Compare with Screeenshot
                                                id='input_wind_comfort_factor',
                                                type='number',
                                                placeholder='e.g. 0.9'
                                            )
                                        ], width=4)
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
                                                       },
                                                placeholder='e.g. WindTurbines',
                                            )
                                        ], width =4)
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
                                                style={'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. logarithmic',
                                            )
                                        ], width=4)
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
                                                style={'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. barometric',
                                            )
                                        ], width=4)
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
                                                style={'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='e.g. linear gradient',
                                            )
                                        ], width=4)
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
                                                style={'color': 'black',
                                                       'bgcolor': 'white',
                                                       },
                                                placeholder='power curve',
                                            )
                                        ], width=4)
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
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id='input_wind_obstacle_height',
                                                    type='number',
                                                    placeholder='e.g. 0 m'
                                                ),
                                                dbc.InputGroupText('m')
                                            ])
                                        ], width=4)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.P('Hellmann Exponent')
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Input( 
                                                id='input_hellmann_exponent',
                                                type='text',
                                                placeholder='e.g. 0.2'
                                            )
                                        ], width=4)
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
                    dbc.Row([
                                dbc.Col([
                                    dbc.Button('Submit Settings',
                                               id='submit_wind_settings',
                                               color='primary')
                                ])
                            ])
               
])

@callback(
    Output('store_wind', 'data'),
    [Input('submit_wind_settings', 'n_clicks')],
    [State('input_wind_turbine_type', 'value'),
     State('input_wind_hub_height', 'value'),
     State('input_wind_rotor_diameter', 'value'),
     State('input_wind_comfort_factor', 'value'),
     State('dropdown_wind_data_source', 'value'),
     State('dropdown_wind_speed_model', 'value'),
     State('dropdown_wind_density_model', 'value'),
     State('dropdown_wind_temperature_model', 'value'),
     State('dropdown_wind_power_output_model', 'value'),
     State('switch_wind_density_correction', 'on'),
     State('input_wind_obstacle_height', 'value'),
     State('input_hellmann_exponent', 'value')]
)
def update_basic_settings_store(n_clicks, turbine_type, hub_height, rotor_diameter,
                                comfort_factor, data_source, speed_model, density_model,
                                temperature_model, power_output_model, density_correction,
                                obstacle_height, hellmann_exponent):
    if 'submit_basic_settings' ==ctx.triggered_id and n_clicks is not None:
        data_basic_settings=pd.DataFrame({'Turbine Type': turbine_type,
                                            'Hub Height': hub_height,
                                            'Rotor Diameter': rotor_diameter,
                                            'Comfort Factor': comfort_factor,
                                            'Data Source': data_source,
                                            'Speed Model': speed_model,
                                            'Density Model': density_model,
                                            'Temperature Model': temperature_model,
                                            'Power Output Model': power_output_model,
                                            'Density Correction': density_correction,
                                            'Obstacle Height': obstacle_height,
                                            'Hellmann Exponent': hellmann_exponent}, index=[0])
        return data_basic_settings.to_dict('records')
    elif n_clicks is None:
        raise PreventUpdate