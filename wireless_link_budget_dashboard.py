# [Last Edited: 08/28/2014]
# [Author: Vinay Gotnakodlu Hegde - vinay.hegde@verkada.com]
# [Title - Wireless Link Budget Dashboard]


# Import all python modules and dependencies
#---------------------------------------------------------
import pandas as pd     #(version 1.0.0)
import math
import plotly.express as px
import dash             #(version 1.9.1) pip install dash==1.9.1
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, dash_table
from dash.exceptions import PreventUpdate
#--------------------------------------------------------


# Initialize Dash App
#--------------------------------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
#--------------------------------------------------------


# Read device specification file from directory
#--------------------------------------------------------
#df = pd.read_csv('device_specifications_csv.csv')
df = pd.read_csv('https://github.com/VinayGHegde/wireless_link_budget_dashboard/device_specifications_csv.csv')
#--------------------------------------------------------


# Styling 'Tabs' used in Dashboard
#--------------------------------------------------------
tab_alignment = {
                        'height': '50px',
                        'align-items': 'center'
                }


tab_style = {
                    'borderTop': '1px solid black',
                    'borderBottom': '1px solid black',
                    'borderLeft': '1px solid black',
                    'borderRight': '1px solid black',
                    'backgroundColor': '#CDD1D7',
                    'color': 'black',
                    'fontWeight': 'normal',
                    'padding': '4px',
                    'border-radius': '35px',
            }


selected_tab_style = {
                            'borderTop': '1px solid black',
                            'borderBottom': '1px solid black',
                            'borderLeft': '1px solid black',
                            'borderRight': '1px solid black',
                            #'backgroundColor': '#119DFF',
                            'backgroundColor': '#CFEFFB',
                            'color': 'black',
                            'fontWeight': 'bold',
                            #'fontStyle': 'italic',
                            'padding': '8px',
                            'border-radius': '35px',
                    }
#--------------------------------------------------------


# BLE propagation modeling function
# Models used - Free Space Path Loss, ITU Indoor Propagation
#--------------------------------------------------------
def BLE_propagation_models(distance_list, frequency_MHz):
    FSPL = [i for i in range(len(distance_list))]
    ITU_Indoor_PL_BLE = [i for i in range(len(distance_list))]

    i = 0
    for distance_value in distance_list[1:]:    
        i = i+1
        FSPL[i] = 20*math.log10(distance_value) + 20*math.log10(frequency_MHz) - 27.55
        ITU_Indoor_PL_BLE[i] = 20*math.log10(frequency_MHz) + 30*math.log10(distance_value) + 15 - 28

    return FSPL, ITU_Indoor_PL_BLE
#-------------------------------------------------------


# Sub GHz propagation modeling function
# Models used - Free Space Path Loss, ITU Indoor Propagation, Okumura Hata
#-----------------------------------------------------------------------------
def subG_propagation_models(distance_list, frequency_MHz, tx_ant_height, rx_ant_height):
    FSPL = [i for i in range(len(distance_list))]
    ITU_Indoor_PL_subG = [i for i in range(len(distance_list))]
    Okumura_Hata_PL = [i for i in range(len(distance_list))]
    
    
    a_hm = rx_ant_height*1.1*math.log10(frequency_MHz) - 0.7*rx_ant_height - 1.56*math.log10(frequency_MHz) + 0.8

    i = 0
    for distance_value in distance_list[1:]:    
        i = i+1
        FSPL[i] = 20*math.log10(distance_value) + 20*math.log10(frequency_MHz) - 27.55
        ITU_Indoor_PL_subG[i] = 20*math.log10(frequency_MHz) + 33*math.log10(distance_value) + 9 - 28
        # 2-ray_GND_Reflection_PL[i] = 40*math.log10(distance_value) - (tx_ant_efficiency)indB - (rx_ant_efficiency)dB - 20*math.log10(tx_ant_height) - 20*math.log10(rx_ant_height)
        Okumura_Hata_PL[i] = 69.55 + 26.16*math.log10(frequency_MHz) - 13.82*math.log10(tx_ant_height) - a_hm + 44.9*math.log10(distance_value/1000) - 6.55*math.log10(tx_ant_height)*math.log10(distance_value/1000)
        # Okumura_Hata_PL[i] = 69.55 + 26.16*math.log10(frequency_MHz) - 13.82*math.log10(tx_ant_height) - a_hm + 44.9*math.log10(distance_value/1000) - 6.55*math.log10(tx_ant_height)*math.log10(distance_value/1000) - 40.94 -4.78*math.log10(frequency_MHz)*math.log10(frequency_MHz) + 18.33*math.log10(frequency_MHz)
        # COST231_Walfish_Ikegami_PL[i] = 42.6 + 20*math.log10(frequency_MHz) + 26*math.log10(distance_value/1000) #COST231-Walfish-Ikegami LOS Model

    return FSPL, ITU_Indoor_PL_subG, Okumura_Hata_PL
#-----------------------------------------------------------------------------

# RSSI calculation function
# Common function used for both uplink and downlink
#-----------------------------------------------------------------------------
def RSSI_calc(distance_list, tx_power_dBm, tx_ant_efficiency_dB, rx_ant_efficiency_dB, path_loss_contents_dB):
    rssi_dBm = [i for i in range(len(distance_list))]

    i = 0
    for path_loss_value in path_loss_contents_dB[1:]:    
        i = i+1
        rssi_dBm[i] = tx_power_dBm + tx_ant_efficiency_dB + rx_ant_efficiency_dB - path_loss_value

    return rssi_dBm
#-----------------------------------------------------------------------------


# Dash Layout Definition
#-----------------------------------------------------------------------------
app.layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                                    html.Img(
                                                    # src=app.get_asset_url('Verkada-Logo-Vert-Black.png'),
                                                    #src=app.get_asset_url('verkada-icon-black.png'),
                                                    # className = 'two columns',
                                                    #style = {'height':'8%', 'width': '8%', 'paddingLeft': '15px'}
                                            )
                            ]),
                        ], width=3),
                        
                dbc.Col([
                    html.Div([]),
                        ], width=6),
                
                dbc.Col([
                    html.Div([
                                    html.H1(
                                                    ['VerkPlot'],
                                                    style={'font-weight': 'bold', 'fontFamily': 'calibri', "textAlign":"right", 'padding-right':"15px", 'color':'#030E16'}
                                            )
                            ]),
                        ], width=3),
                    ], 
                    # align='center',
                    # className="h-25"
                    ), 


            dbc.Row([
                dbc.Col([
                    html.Div([
                                    dcc.Tabs(
                                                    id="tabs_inline",
                                                    value = 'tab-1',
                                                    children = [
                                                                dcc.Tab(label = 'LINK BUDGET', value = 'tab-1', style = tab_style, selected_style = selected_tab_style),
                                                                dcc.Tab(label = 'REQUESTS / FEEDBACK', value = 'tab-2', style = tab_style, selected_style = selected_tab_style)
                                                                ],
                                                    style = tab_alignment
                                            ),
                            ]),    
                        ])
                    ]),


            html.Div(id='tabs_content'),


            html.Div([    
                            html.Label(
                                                ['Dashboard created by Verkada Access Control Hardware Team'],
                                                className = 'six columns', style={'color': 'black', 'fontSize': '15px', 'fontWeight': 'bold', 'fontFamily': 'helvetica', "textAlign":"left", 'opacity': '0.5'}
                                        ),

                            html.Label(
                                                ['Dash-Plotly code version v1.0'],
                                                className = 'six columns', style={'color': 'black', 'fontSize': '15px', 'fontStyle': 'italic', 'fontFamily': 'helvetica', "textAlign":"right", 'opacity': '0.5'}
                                        )
                    ],
                    style={'position': 'fixed', 'bottom': 0, 'width': '99%'}
                    ),
                    ], 
                    # style={'backgroundColor':'#FFFFF0'}
                    )       
            )],
            style={'backgroundColor':'#FFFFF0'}
            )




#--------------------------------------------------------------------------------------------------------------------------
@app.callback(Output('tabs_content', 'children'),
              Input('tabs_inline', 'value'))


def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
                    dbc.Row([
                        dbc.Col(
                                    [],
                                    width = 1
                                ),

                        dbc.Col(
                            html.Div([
                                            html.Br(),
                                            html.Label(
                                                            ['Wireless Technology'],
                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "center"}
                                                        ),
                                
                                            dcc.Dropdown(
                                                                id='tech_filter',
                                                                options=[{'label': 'Bluetooth LE (2440MHz)', 'value': 'BLE'}, {'label': 'Sub GHz (915MHz)', 'value': 'Sub GHz'}, {'label': 'WiFi (not supported)', 'value': 'wifi'}],
                                                                value='NA',
                                                                multi=False,
                                                                disabled=False,
                                                                clearable=False,
                                                                searchable=True,
                                                                placeholder='Choose Technology...',
                                                                style={'width':"100%"},
                                                                persistence='string',
                                                                persistence_type='session'
                                                        ),
                                    ],
                                    # className = "six columns",
                                    style={'marginLeft':'90px', 'marginRight':'90px', 'text-align':'center'}
                                    ),
                                    width = 10
                                ),

                        dbc.Col(
                                    [],
                                    width = 1
                                ),
                                    
                        # html.Hr(),
                        html.Div(id='output_div'),
                        ])

                    ])
    

    elif tab == 'tab-2':
        return html.Div([
                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),

                        dcc.Markdown(['''
                                    ###### **_VerkPlot_** is built to visualize communication link margins for various wireless technologies and devices in a simple and straightforward way. Therefore, any feedback to make this tool better is always welcome.

                                    ###### If you come across any bugs with the tool or have any feature requests, please email - [vinay.hegde@verkada.com](https://outlook.office365.com/mail/) or send a message on [Slack](https://fb.workplace.com/chat/t/100056117707070).
                                    '''], 
                                    style={'color': 'black', 'font-weight': 'normal', "text-align": "center"}),

                        html.Br(),
                        html.Br(),
                        html.Br(),
                        html.Br(),

                        dcc.Markdown(['''
                                    ###### **Notes from the developer**

                                    ###### **_VerkPlot_** is only a data visualization tool and requires that the input file be in a certain format.

                                    ###### You can find all the device specification files in the below link. I will ensure that the latest version of the files are available for your use.
                                      
                                    ###### The following path loss models are used in the tool.
                                    '''], style={'color': 'black', 'font-weight': 'normal', "text-align": "center"}),

                        html.Br(),          
                        ], 
                        # className = "twelve columns",
                        style={'marginLeft':'90px', 'marginRight':'90px', 'text-align':'center'}
                        )
#--------------------------------------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------------------------------------
@app.callback(Output('output_div', 'children'),
            Input('tech_filter', 'value'))


def render_layout(filtering):
    if filtering == 'BLE':
        return html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                                html.Br(),
                                                html.Br(),
                                                # html.Br(),
                                                html.Div([
                                                                html.Label(
                                                                                ['Transmit Device'], 
                                                                                style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                            ),

                                                                dcc.Dropdown(
                                                                                    # df.Device.unique(),
                                                                                    id = 'transmitter_dropdown',
                                                                                    options=[{'label': str(x), 'value': x} for x in sorted(df['Device'])],
                                                                                    value='NA',
                                                                                    optionHeight = 25,
                                                                                    #maxHeight = 300,
                                                                                    disabled = False,
                                                                                    multi = False,
                                                                                    searchable = True,
                                                                                    # search_value = '',
                                                                                    placeholder = 'Please select your transmitter',
                                                                                    clearable = True,
                                                                                    # style={'width':"55%", 'padding-left':"15px"},
                                                                                    #className = 'select_box',
                                                                                    #persistence = 'True',
                                                                                    #persistence_type = 'memory'
                                                                            )
                                                        ],
                                                        # className = "six columns"
                                                        ),

                                                html.Br(),
                                                html.Div([
                                                                html.Label(
                                                                                ['Receive Device'], 
                                                                                style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                            ),
                                
                                                                dcc.Dropdown(
                                                                                    # df.Device.unique(),
                                                                                    id = 'receiver_dropdown',
                                                                                    options=[{'label': str(x), 'value': x} for x in sorted(df['Device'].unique())],
                                                                                    value='NA',
                                                                                    optionHeight = 25,
                                                                                    #maxHeight = 300,
                                                                                    disabled = False,
                                                                                    multi = False,
                                                                                    searchable = True,
                                                                                    # search_value = '',
                                                                                    placeholder = 'Please select your receiver',
                                                                                    clearable = True,
                                                                                    # style={'width':"55%", 'padding-left':"15px"},
                                                                                    # className = 'select_box',
                                                                                    #persistence = 'True',
                                                                                    #persistence_type = 'memory'
                                                                            )
                                                        ],
                                                        # className = "six columns"
                                                        ),
                                        ], 
                                        style={'marginLeft':'80px', 'marginRight':'200px', 'padding-left':"200px"}
                                        )
                                    ], 
                                    width={'size': 3,  "offset": 0}
                                    ),

                            dbc.Col([
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                                html.Label(
                                                                ['Device Specifications'], 
                                                                style={'color': 'black', 'font-weight': 'bold', "text-align": "center"}
                                                            ),
                                                html.Hr(),
                                                html.Div(id='specification_table'),
                                                
                                    ], 
                                    width=4),

                            dbc.Col([
                                            html.Br(),
                                            dcc.Graph(id='path_loss_graph'),
                                    ], 
                                    width=4),

                            dbc.Col([
                                            html.Br(),
                                    ], 
                                    width=1),
                        ]),


                        html.Br(),


                        dbc.Row([
                            dbc.Col([
                                            # drawFigure()
                                    ], 
                                    width=3),

                            dbc.Col([
                                            dcc.Graph(id='uplink_graph'),
                            ], width=4,
                            # style = {
                            #         'border-right': '2px solid black',
                            #         'border-left': '2px solid black',
                            #         'border-top': '2px solid black',
                            #         'border-bottom': '2px solid grey',
                            #         # 'border-radius': '20px',
                            #         # 'border rounded': '5px solid black',
                            #         # 'margin': 'auto'
                            #         }
                                    ),

                            dbc.Col([
                                            dcc.Graph(id='downlink_graph'), 
                            ], width=4,
                            # style = {
                            #         'border-right': '2px solid black',
                            #         'border-left': '2px solid black',
                            #         'border-top': '2px solid black',
                            #         'border-bottom': '2px solid grey',
                            #         # 'border-radius': '20px',
                            #         # 'border rounded': '5px solid black',
                            #         # 'margin': 'auto'
                            #         }
                                    ),

                            dbc.Col([
                                            # drawFigure() 
                            ], width=1),
                        ], 
                        align='center'), 
                        html.Br(),
                        ])


    elif filtering == 'Sub GHz':
        return html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                            html.Br(),
                                            html.Br(),
                                            html.Div([
                                                            html.Label(
                                                                            ['Transmit Device'], 
                                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                        ),

                                                            dcc.Dropdown(
                                                                                # df.Device.unique(),
                                                                                id = 'transmitter_dropdown',
                                                                                options=[{'label': str(x), 'value': x} for x in sorted(df['Device'])],
                                                                                value='NA',
                                                                                optionHeight = 25,
                                                                                #maxHeight = 300,
                                                                                disabled = False,
                                                                                multi = False,
                                                                                searchable = True,
                                                                                # search_value = '',
                                                                                placeholder = 'Please select your transmitter',
                                                                                clearable = True,
                                                                                # style={'width':"55%", 'padding-left':"15px"},
                                                                                #className = 'select_box',
                                                                                #persistence = 'True',
                                                                                #persistence_type = 'memory'
                                                                        )
                                                    ],
                                                    # className = "six columns"
                                                    ),

                                            html.Br(),
                                            html.Div([
                                                            html.Label(
                                                                            ['Receive Device'], 
                                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                        ),
                            
                                                            dcc.Dropdown(
                                                                                # df.Device.unique(),
                                                                                id = 'receiver_dropdown',
                                                                                options=[{'label': str(x), 'value': x} for x in sorted(df['Device'].unique())],
                                                                                value='NA',
                                                                                optionHeight = 25,
                                                                                #maxHeight = 300,
                                                                                disabled = False,
                                                                                multi = False,
                                                                                searchable = True,
                                                                                # search_value = '',
                                                                                placeholder = 'Please select your receiver',
                                                                                clearable = True,
                                                                                # style={'width':"55%", 'padding-left':"15px"},
                                                                                # className = 'select_box',
                                                                                #persistence = 'True',
                                                                                #persistence_type = 'memory'
                                                                        )
                                                    ],
                                                    # className = "six columns"
                                                    ),

                                            html.Br(),
                                            html.Div([
                                                            html.Label(
                                                                            ['Transmit Antenna Height (in m)'], 
                                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                        ),

                                                            dcc.Dropdown(
                                                                                # df.Device.unique(),
                                                                                id = 'transmitter_antenna_height',
                                                                                optionHeight = 25,
                                                                                #maxHeight = 300,
                                                                                disabled = True,
                                                                                multi = False,
                                                                                searchable = True,
                                                                                search_value = '',
                                                                                placeholder = 'Please select your receiver',
                                                                                clearable = True,
                                                                                # style={'width':"55%", 'padding-left':"15px"},
                                                                                # className = 'select_box',
                                                                                #persistence = 'True',
                                                                                #persistence_type = 'memory'
                                                                        )
                                                    ],
                                                    # className = "six columns"
                                                    ),

                                            html.Br(),
                                            html.Div([
                                                            html.Label(
                                                                            ['Receive Antenna Height (in m)'], 
                                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "left", 'padding-left':"15px"}
                                                                        ),

                                                            dcc.Dropdown(
                                                                                # df.Device.unique(),
                                                                                id = 'receiver_antenna_height',
                                                                                optionHeight = 25,
                                                                                #maxHeight = 300,
                                                                                disabled = True,
                                                                                multi = False,
                                                                                searchable = True,
                                                                                search_value = '',
                                                                                placeholder = 'Please select your receiver',
                                                                                clearable = True,
                                                                                # style={'width':"55%", 'padding-left':"15px"},
                                                                                # className = 'select_box',
                                                                                #persistence = 'True',
                                                                                #persistence_type = 'memory'
                                                                        )
                                                    ],
                                                    # className = "six columns"
                                                    ),
                                    ], 
                                    style={'marginLeft':'80px', 'marginRight':'200px', 'padding-left':"200px"}
                                    )
                                ], 
                                width={'size': 3,  "offset": 0}
                                ),

                            dbc.Col([
                                            html.Br(),
                                            html.Br(),
                                            html.Br(),
                                            html.Br(),
                                            html.Br(),
                                            html.Label(
                                                            ['Device Specifications'], 
                                                            style={'color': 'black', 'font-weight': 'bold', "text-align": "center"}
                                                        ),
                                            html.Hr(),
                                            html.Div(id='specification_table'),
                                            
                                ], 
                                width=4),

                            dbc.Col([
                                            html.Br(),
                                            dcc.Graph(id='path_loss_graph'),
                                    ], 
                                    width=4),

                            dbc.Col([
                                            html.Br(),
                                    ], 
                                    width=1),
                        ]),


                        html.Br(),


                        dbc.Row([
                            dbc.Col([
                                            # drawFigure()
                                    ], 
                                    width=3),

                            dbc.Col([
                                            dcc.Graph(id='uplink_graph'),
                            ], width=4),

                            dbc.Col([
                                            dcc.Graph(id='downlink_graph'), 
                            ], width=4),

                            dbc.Col([
                                            # drawFigure() 
                            ], width=1),
                        ], 
                        align='center'), 
                        html.Br(),
                        ])
    

    elif filtering == 'wifi':
        return html.Div([
                                html.Br(),
                                html.Br(),
                                html.Div(
                                                ['WiFi link budget is currently not supported'], 
                                                style={'color': 'black', 'font-weight': 'bold', "text-align": "center"}
                                        ),
                                html.Div(
                                                ['VerkPlot team is happy to integrate it depending on user feedback'], 
                                                style={'color': 'black', 'font-weight': 'bold', "text-align": "center"}
                                        )
                        ])
#--------------------------------------------------------------------------------------------------------------------------



#--------------------------------------------------------------------------------------------------------------------------
@app.callback(
    Output('path_loss_graph', 'figure'),
    Output('uplink_graph', 'figure'),
    Output('downlink_graph', 'figure'),
    Output('specification_table', 'children'),
    [Input('transmitter_dropdown', 'value'),
     Input('receiver_dropdown', 'value'),
     Input('tech_filter', 'value')
    ]
)


def update_datatable(tx_dropdown, rx_dropdown, technology_sel):
            if tx_dropdown and rx_dropdown:
                # #Transmitter parameters filtered
                df_transmitter = df[df['Device'] == tx_dropdown]
                df_transmitter.reset_index(drop=True, inplace=True)

                tx_power_transmitter = df_transmitter.loc[:, 'Transmit Power (dBm)'].tolist()
                ant_efficiency_transmitter = df_transmitter.loc[:, 'Antenna Efficiency (dB)'].tolist()
                rx_sensitivity_transmitter = df_transmitter.loc[:, 'Receive Sensitivity (dBm)'].tolist()

                # #Receiver parameters filtered
                df_receiver = df[df['Device'] == rx_dropdown]
                df_receiver.reset_index(drop=True, inplace=True)
                tx_power_receiver = df_receiver.loc[:,'Transmit Power (dBm)'].tolist()
                ant_efficiency_receiver = df_receiver.loc[:,'Antenna Efficiency (dB)'].tolist()
                rx_sensitivity_receiver = df_receiver.loc[:,'Receive Sensitivity (dBm)'].tolist()

                # ======================== Plotly Table
                df_merge = pd.concat([df_transmitter, df_receiver], axis=0)
                df_merge.reset_index(drop=True, inplace=True)

                tx_device_parameters = {'tx_power' : tx_power_transmitter, 'ant_efficiency': ant_efficiency_transmitter, 'rx_sensitivity': rx_sensitivity_transmitter}
                rx_device_parameters = {'tx_power' : tx_power_receiver, 'ant_efficiency': ant_efficiency_receiver, 'rx_sensitivity': rx_sensitivity_receiver}

                distance_meter = 100
                # frequency_MHz = 915
                height_TX = 1
                height_RX = 2.9
                distance_target = 100

                distance_list = []
                for i in range(0,distance_target+100, 1):
                    distance_list.append(i)

# Uplink calculations
#--------------------------------------------------------------------------------------------------------------------------
                if technology_sel == 'Sub GHz':
                    frequency_MHz = 915
                    FSPL_uplink, ITU_Indoor_PL_subG_uplink, Okumura_Hata_PL_uplink = subG_propagation_models(distance_list, frequency_MHz, height_TX, height_RX)
                    rssi_FSPL_uplink = RSSI_calc(distance_list, tx_device_parameters['tx_power'][0], tx_device_parameters['ant_efficiency'][0], rx_device_parameters['ant_efficiency'][0], FSPL_uplink)
                    rssi_ITU_Indoor_PL_subG_uplink = RSSI_calc(distance_list, tx_device_parameters['tx_power'][0], tx_device_parameters['ant_efficiency'][0], rx_device_parameters['ant_efficiency'][0], ITU_Indoor_PL_subG_uplink)
                    rssi_Okumura_Hata_PL_uplink = RSSI_calc(distance_list, tx_device_parameters['tx_power'][0], tx_device_parameters['ant_efficiency'][0], rx_device_parameters['ant_efficiency'][0], Okumura_Hata_PL_uplink)
                    # print('subG Propagation Model Uplink')
                    # print(FSPL_uplink, ITU_Indoor_PL_subG_uplink, Okumura_Hata_PL_uplink)

                elif technology_sel == 'BLE':
                    frequency_MHz = 2440
                    FSPL_uplink, ITU_Indoor_PL_BLE_uplink  = BLE_propagation_models(distance_list, frequency_MHz)
                    rssi_FSPL_uplink = RSSI_calc(distance_list, tx_device_parameters['tx_power'][0], tx_device_parameters['ant_efficiency'][0], rx_device_parameters['ant_efficiency'][0], FSPL_uplink)
                    rssi_ITU_Indoor_PL_BLE_uplink = RSSI_calc(distance_list, tx_device_parameters['tx_power'][0], tx_device_parameters['ant_efficiency'][0], rx_device_parameters['ant_efficiency'][0], ITU_Indoor_PL_BLE_uplink)
                    # print('WiFi Propagation Model Downlink')
                    # print(FSPL_uplink, ITU_Indoor_PL_BLE_uplink)

                else:
                    pass
#--------------------------------------------------------------------------------------------------------------------------

# Downlink calculations
#--------------------------------------------------------------------------------------------------------------------------
                if technology_sel == 'Sub GHz':
                    frequency_MHz = 915
                    FSPL_downlink, ITU_Indoor_PL_subG_downlink, Okumura_Hata_PL_downlink = subG_propagation_models(distance_list, frequency_MHz, height_RX, height_TX)
                    rssi_FSPL_downlink = RSSI_calc(distance_list, rx_device_parameters['tx_power'][0], rx_device_parameters['ant_efficiency'][0], tx_device_parameters['ant_efficiency'][0], FSPL_downlink)
                    rssi_ITU_Indoor_PL_subG_downlink = RSSI_calc(distance_list, rx_device_parameters['tx_power'][0], rx_device_parameters['ant_efficiency'][0], tx_device_parameters['ant_efficiency'][0], ITU_Indoor_PL_subG_downlink)
                    rssi_Okumura_Hata_PL_downlink = RSSI_calc(distance_list, rx_device_parameters['tx_power'][0], rx_device_parameters['ant_efficiency'][0], tx_device_parameters['ant_efficiency'][0], Okumura_Hata_PL_downlink)
                    # print('subG Propagation Model Downlink')
                    # print(FSPL_downlink, ITU_Indoor_PL_subG_downlink, Okumura_Hata_PL_downlink)

                elif technology_sel == 'BLE':
                    frequency_MHz = 2440
                    FSPL_downlink, ITU_Indoor_PL_BLE_downlink  = BLE_propagation_models(distance_list, frequency_MHz)
                    rssi_FSPL_downlink = RSSI_calc(distance_list, rx_device_parameters['tx_power'][0], rx_device_parameters['ant_efficiency'][0], tx_device_parameters['ant_efficiency'][0], FSPL_downlink)
                    rssi_ITU_Indoor_PL_BLE_downlink = RSSI_calc(distance_list, rx_device_parameters['tx_power'][0], rx_device_parameters['ant_efficiency'][0], tx_device_parameters['ant_efficiency'][0], ITU_Indoor_PL_BLE_downlink)
                    # print('WiFi Propagation Model Downlink')
                    # print(FSPL_downlink, ITU_Indoor_PL_BLE_downlink)

                else:
                    pass
#--------------------------------------------------------------------------------------------------------------------------

# Path loss, uplink and downlink RSSI plots
#--------------------------------------------------------------------------------------------------------------------------
                if technology_sel == 'Sub GHz':


                    df_propagation_values = pd.DataFrame({
                                                        'distance':distance_list,
                                                        'FSPL_uplink':FSPL_uplink,
                                                        'FSPL_downlink':FSPL_downlink,
                                                        'ITU_Indoor_PL_subG_uplink':ITU_Indoor_PL_subG_uplink,
                                                        'ITU_Indoor_PL_subG_downlink':ITU_Indoor_PL_subG_downlink,
                                                        'Okumura_Hata_PL_uplink':Okumura_Hata_PL_uplink,
                                                        'Okumura_Hata_PL_downlink':Okumura_Hata_PL_downlink,
                                                        'rssi_FSPL_uplink':rssi_FSPL_uplink,
                                                        'rssi_FSPL_downlink':rssi_FSPL_downlink,
                                                        'rssi_ITU_Indoor_PL_subG_uplink':rssi_ITU_Indoor_PL_subG_uplink,
                                                        'rssi_ITU_Indoor_PL_subG_downlink':rssi_ITU_Indoor_PL_subG_downlink,
                                                        'rssi_Okumura_Hata_PL_uplink':rssi_Okumura_Hata_PL_uplink,
                                                        'rssi_Okumura_Hata_PL_downlink':rssi_Okumura_Hata_PL_downlink
                                                        })
                    fig1 = px.line(df_propagation_values, x='distance', y=['FSPL_uplink', 'ITU_Indoor_PL_subG_uplink', 'Okumura_Hata_PL_uplink', 'FSPL_downlink', 'ITU_Indoor_PL_subG_downlink', 'Okumura_Hata_PL_downlink'], title="Path Loss - subG")
                    # fig1 = px.line(df_propagation_values, x='distance', y=['FSPL_uplink', 'FSPL_downlink'], title="Path Loss - subG")
                    fig2 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_uplink', 'rssi_ITU_Indoor_PL_subG_uplink', 'rssi_Okumura_Hata_PL_uplink'], title="RSSI uplink - subG")
                    fig3 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_downlink', 'rssi_ITU_Indoor_PL_subG_downlink', 'rssi_Okumura_Hata_PL_downlink'], title="RSSI downlink - subG")

                elif technology_sel == 'BLE':
                    df_propagation_values = pd.DataFrame({
                                                        'distance':distance_list,
                                                        'FSPL_uplink':FSPL_uplink,
                                                        'FSPL_downlink':FSPL_downlink,
                                                        'ITU_Indoor_PL_BLE_uplink':ITU_Indoor_PL_BLE_uplink,
                                                        'ITU_Indoor_PL_BLE_downlink':ITU_Indoor_PL_BLE_downlink,
                                                        'rssi_FSPL_uplink':rssi_FSPL_uplink,
                                                        'rssi_FSPL_downlink':rssi_FSPL_downlink,
                                                        'rssi_ITU_Indoor_PL_BLE_uplink':rssi_ITU_Indoor_PL_BLE_uplink,
                                                        'rssi_ITU_Indoor_PL_BLE_downlink':rssi_ITU_Indoor_PL_BLE_downlink
                                                        })
                    
                    # if df_propagation_values.empty:
                    #     raise PreventUpdate
                    
                    fig1 = px.line(df_propagation_values, x='distance', y=['FSPL_uplink', 'ITU_Indoor_PL_BLE_uplink', 'FSPL_downlink', 'ITU_Indoor_PL_BLE_downlink'], title="Path Loss - BLE")
                    # fig1 = px.line(df_propagation_values, x='distance', y=['FSPL_uplink', 'FSPL_downlink'], title="Path Loss - BLE")
                    fig2 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_uplink', 'rssi_ITU_Indoor_PL_BLE_uplink'], title="RSSI uplink- BLE")
                    # fig2 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_uplink'], title="RSSI uplink- BLE")
                    fig3 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_downlink', 'rssi_ITU_Indoor_PL_BLE_downlink'], title="RSSI downlink - BLE")
                    # fig3 = px.line(df_propagation_values, x='distance', y=['rssi_FSPL_downlink'], title="RSSI downlink - BLE")


                # fig1.add_hline(y=rx_sensitivity_receiver[0], line_dash='dash', annotation_text="Device Sensitivity Spec", annotation_position="top right") #, line_color='Red')
                fig1.add_vline(x=distance_target, line_dash='dash', annotation_text="Target Distance = {} m".format(distance_target), annotation_position="bottom right", annotation_font = {'size' : 15})
                fig1.update_xaxes(title = 'Distance (m)')
                fig1.update_yaxes(title = 'Path Loss (dB)')
                # fig1.update_layout(legend=dict(
                #     orientation="h",
                #     # entrywidth=70,
                #     yanchor="bottom",
                #     y=1.02,
                #     xanchor="right",
                #     x=1
                #     ))


                return (fig1), (fig2), (fig3), [
                    dash_table.DataTable(
                                                        id='datatable-interactivity',
                                                        columns=[
                                                                    # {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
                                                                    {"name": i, "id": i} for i in df.columns
                                                                ],
                                                        data=df_merge.to_dict('records'),  # the contents of the table
                                                    #     # editable=True,              # allow editing of data inside all cells
                                                    #     filter_action="native",     # allow filtering of data by user ('native') or not ('none')
                                                    #     sort_action="native",       # enables data to be sorted per-column by user or not ('none')
                                                    #     sort_mode="single",         # sort across 'multi' or 'single' columns
                                                    #     # column_selectable="multi",  # allow users to select 'multi' or 'single' columns
                                                    #     # row_selectable="multi",     # allow users to select 'multi' or 'single' rows
                                                    #     # row_deletable=True,         # choose if user can delete a row (True) or not (False)
                                                    #     selected_columns=[],        # ids of columns that user selects
                                                    #     selected_rows=[],           # indices of rows that user selects
                                                    #     # page_action="native",       # all data is passed to the table up-front or not ('none')
                                                    #     # page_current=0,             # page number that user is on
                                                    #     # page_size=6,                # number of rows visible per page
                                                        # style_cell={                # ensure adequate header width when text is shorter than cell's text
                                                        #     'minWidth': 100, 'maxWidth': 100, 'width': 100,
                                                        #     'textAlign': 'center'
                                                        # },
                                                        style_cell={'textAlign': 'center'},
                                                        style_header = {'fontWeight': 'bold', 'backgroundColor': 'rgb(230, 230, 230)', 'border': '1px solid black'},
                                                        style_data={'border': '1px solid black'},
                                                    #     style_data={                # overflow cells' content into multiple lines
                                                    #         'whiteSpace': 'normal',
                                                    #         'height': 'auto'
                                                    #     }
                                                    ),
        ]  
                
                       
            elif not tx_dropdown or not rx_dropdown:
                return {}, {}, {}, {}
#--------------------------------------------------------------------------------------------------------------------------  

# Run App
#--------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=False)
#--------------------------------------------------------------------------------------------------------------------------
