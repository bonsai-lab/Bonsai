
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_auth
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State
import numpy as np
import asyncio
import json
from pandas.io.json import json_normalize
import statsmodels.api as sm
import datetime as dt
from scipy import interpolate
import dash_table
#Plotting
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
from dash.exceptions import PreventUpdate


#__________________________________________________


#COLOR SCALE FOR TABLE (VOL)

def discrete_background_color_bins(df, n_bins=7, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = list(reversed(colorlover.scales[str(n_bins+4)]['div']['RdYlGn']))[2:-2][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))



#___

#BARS FOR OI IN TABLE

def data_bars(df, column):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min()
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append({
            'if': {
                'filter_query': (
                    '{{{column}}} >= {min_bound}' +
                    (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                'column_id': column
            },
            'background': (
                """
                    linear-gradient(90deg,
                    #0074D9 0%,
                    #0074D9 {max_bound_percentage}%,
                    #2b2b2b {max_bound_percentage}%,
                    #2b2b2b 100%)
                """.format(max_bound_percentage=max_bound_percentage)
            ),
            'paddingBottom': 2,
            'paddingTop': 2
        })

    return styles


def data_bars_diverging(df, column, color_above='#3D9970', color_below='#FF4136'):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    col_max = df[column].max()
    col_min = df[column].min()
    ranges = [
        ((col_max - col_min) * i) + col_min
        for i in bounds
    ]
    midpoint = (col_max + col_min) / 2.

    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        min_bound_percentage = bounds[i - 1] * 100
        max_bound_percentage = bounds[i] * 100

        style = {
            'if': {
                'filter_query': (
                    '{{{column}}} >= {min_bound}' +
                    (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                'column_id': column
            },
            'paddingBottom': 2,
            'paddingTop': 2
        }
        if max_bound > midpoint:
            background = (
                """
                    linear-gradient(90deg,
                    #2b2b2b 0%,
                    #2b2b2b 50%,
                    {color_above} 50%,
                    {color_above} {max_bound_percentage}%,
                    #2b2b2b {max_bound_percentage}%,
                    #2b2b2b 100%)
                """.format(
                    max_bound_percentage=max_bound_percentage,
                    color_above=color_above
                )
            )
        else:
            background = (
                """
                    linear-gradient(90deg,
                    #2b2b2b 0%,
                    #2b2b2b {min_bound_percentage}%,
                    {color_below} {min_bound_percentage}%,
                    {color_below} 50%,
                    #2b2b2b 50%,
                    #2b2b2b 100%)
                """.format(
                    min_bound_percentage=min_bound_percentage,
                    color_below=color_below
                )
            )
        style['background'] = background
        styles.append(style)

    return styles





#table text = #ffc800;?
#__________GET OPTIONS DATA


def get_all_active_options():
    import urllib.request, json
    url =  "https://deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false"
    with urllib.request.urlopen(url) as url:
        data = json.loads(url.read().decode())
    data = pd.DataFrame(data['result']).set_index('instrument_name')
    data['creation_date'] = pd.to_datetime(data['creation_timestamp'], unit='ms')
    data['expiration_date'] = pd.to_datetime(data['expiration_timestamp'], unit='ms')
    print(f'{data.shape[0]} active options.')
    return data

# Filter options based on data available from 'get_instruments'
def filter_options(price, active_options):
    # price is the current price of BTC

    #Get Put/Call information
    pc = active_options.index.str.strip().str[-1]

    # Set "moneyness"
    active_options['m'] = np.log(active_options['strike']/price)
    active_options.loc[pc=='P','m'] = -active_options['m']
    # Set days until expiration
    active_options['t'] = (active_options['expiration_date']-pd.Timestamp.today()).dt.days

    # Only include options that are less than 30% from the current price and have less than 91 days until expiration
    active_options = active_options.query('m>-.7 & m<.3 & t<90')

    return active_options

# Get Tick data for a given instrument from the Deribit API
def get_tick_data(instrument_name):
    import urllib.request, json
    url =  f"https://deribit.com/api/v2/public/ticker?instrument_name={instrument_name}"
    with urllib.request.urlopen(url) as url:
        data = json.loads(url.read().decode())
    data = pd.json_normalize(data['result'])
    data.index = [instrument_name]
    return data

# Loop through all filtered options to get the current 'ticker' datas
def get_all_option_data():
    option_data = get_tick_data('BTC-PERPETUAL')
    options = filter_options(option_data['last_price'][0], get_all_active_options())
    for o in options.index:
        option_data = option_data.append(get_tick_data(o))
    return option_data

# SORT OPTIONS DATA FOR TABLE
df = get_all_option_data()
df = df[1:]
df_full= df[['instrument_name','mark_price','greeks.delta','greeks.gamma','greeks.vega','greeks.theta','greeks.rho','open_interest','mark_iv']]
df_full.columns = ['Instrument', 'Market Price',  'Delta', 'Gamma', 'Vega', 'Theta', 'Rho','Open Interest','MarkIV']
df_put = df_full[df_full.index.str.contains('-P', case=False)]
df_put = df_put.sort_values(by=['Delta']);
df_call = df_full[df_full.index.str.contains('-C', case=False)]
df_call = df_call.sort_values(by=['Delta']);




#______TAB STYLE__(MOVE)
tabs_styles = {
    'height': '44px',
    'align-items': 'center'
}
tab_style = {
    'borderBottom': '0px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'border-radius': '1px',
    'background-color': '#1c1c1c',
    'box-shadow': '1px 1px 1px 1px grey',
    'color': 'lightgrey'

}

tab_selected_style = {
    'borderTop': '3px solid #d6d6d6',
    'borderBottom': '0px solid #d6d6d6',
    'backgroundColor': '#1c1c1c',
    'color': 'white',
    'padding': '6px',
    'border-radius': '1px',
    'fontWeight': 'bold',
}


#___________ACTUAL APP__


(styles, legend) = discrete_background_color_bins(df_call, columns=['MarkIV'])


app = dash.Dash(__name__)
app.title = 'Bonzai'
#https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/


app.layout = html.Div(children=[

    html.Div([
        dcc.Tabs([
            dcc.Tab(label='Calls', children=[legend,
                #TABLE CALLS
                dash_table.DataTable(
                id='table_call',
                columns=[{"name": i, "id": i}
                for i in df_call.columns],
                data=df_call.to_dict('records'),
                sort_action='native',
                style_data_conditional= styles + data_bars(df_call, 'Open Interest'),
                style_cell=dict(textAlign='left'),
                style_header=dict(backgroundColor="#000000"),
                style_data=dict(backgroundColor='#2b2b2b'))],className= 'block1',style = tab_style, selected_style = tab_selected_style),


            dcc.Tab(label='Puts', children=[
                #TABLE PUTS
                dash_table.DataTable(
                id='table_put',
                columns=[{"name": i, "id": i}
                for i in df_put.columns],
                data=df_put.to_dict('records'),
                style_cell=dict(textAlign='left'),
                style_header=dict(backgroundColor="#000000"),
                style_data=dict(backgroundColor='#2b2b2b'))],className= 'block1',style = tab_style, selected_style = tab_selected_style)
                                            ])], className= 'g-block-1 table-wrapper-scroll-y my-custom-scrollbar'),


    html.Div([
        dcc.Graph(id='vol_surface',
        animate=True,
        animation_options={"frame":{"redraw":True}},
        className='block3'),

        dcc.Graph(id='atm_vol',animate=True,
        className='block4'),

        dcc.Interval(id='interval-component',
        interval=60*1000)], className='g-block-2')])




@app.callback(
    Output('vol_surface', 'figure'),
    [Input('interval-component', 'n_intervals')]
)

def refresh_surface(n):

    option_data = get_all_option_data()

    # Add additional metrics to data
    option_data['t'] = np.nan; option_data['strike'] = np.nan
    # Calculated days until expiration
    option_data.loc[1:,'t'] = (pd.to_datetime(option_data[1:].index.map(lambda x: x.split('-')[1]))-pd.Timestamp.today()).days
    # Pull strike from instrument name
    option_data.loc[1:,'strike'] = option_data[1:].index.map(lambda x: x.split('-')[2]).astype(int)
    # Calculate "moneyness"
    option_data['m'] = np.log(option_data['last_price'][0]/option_data['strike'])

    # Interpolate implied volatility using a cubic spline
    # Then plot the implied volatility surface

    option_data_ = option_data.iloc[1:].sort_values(['t','strike']).query('t>1') #form time inwards out
    x = option_data['last_price'][0]/option_data_['strike']

    y = option_data_['t']
    z = option_data_['mark_iv']

    X,Y = np.meshgrid(np.linspace(0.6,1.4,99),np.linspace(1,np.max(y),100))
    Z = interpolate.griddata(np.array([x,y]).T,np.array(z),(X,Y), method='cubic')

    fig = go.Figure(data=[go.Surface(x=X,y=Y,z=Z, colorscale = [[0, 'green'],[.5, 'yellow'], [1.0, 'red']], name = 'Bitcoin Vol Surface (Refresh Rate = 60s)', opacity=1)]);
    fig.update_layout(legend=dict(yanchor="top",y=0.99,xanchor="left",x=0.01))
    fig.update_traces(showlegend=True, showscale=False);
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0));
    fig.update_layout(template='plotly_dark');

    fig.update_layout(
            scene = {
                "xaxis": {"nticks": 30, 'showgrid': True},
                "zaxis": {"nticks": 30, 'showgrid': True},
                "yaxis": {"nticks": 30, 'showgrid': True},

                "aspectratio": {"x": 1.45, "y": 1.25, "z": .75}
                });

    fig.update_layout(scene = dict(
                        xaxis_title='Moneyness',
                        yaxis_title='Days To Expiration',
                        zaxis_title='IV (%)'));


    fig.update_layout(scene = dict(
                        xaxis = dict(
                             backgroundcolor="rgb(0,0,0)",
                             gridcolor="rgb(64,64,64)",  ##white theme "rgb(211,211,211)"
                             showbackground=False,
                             zerolinecolor="rgb(64,64,64)",),
                        yaxis = dict(
                            backgroundcolor="rgb(0,0,0)",
                            gridcolor="rgb(64,64,64)",
                            showbackground=False,
                            zerolinecolor="rgb(64,64,64)"),
                        zaxis = dict(
                            backgroundcolor="rgb(0,0,0)",
                            gridcolor="rgb(64,64,64)",
                            showbackground=False,
                            zerolinecolor="rgb(64,64,64)")));



    return fig


@app.callback(
    Output('atm_vol', 'figure'),
    [Input('interval-component', 'n_intervals')]
)

def update_atm_vol(n):

    option_data = get_all_option_data()

    #Add additional metrics to data
    option_data['t'] = np.nan; option_data['strike'] = np.nan
    # Calculated days until expiration
    option_data.loc[1:,'t'] = (pd.to_datetime(option_data[1:].index.map(lambda x: x.split('-')[1]))-pd.Timestamp.today()).days
    # Pull strike from instrument name
    option_data.loc[1:,'strike'] = option_data[1:].index.map(lambda x: x.split('-')[2]).astype(int)
    # Calculate "moneyness"
    option_data['m'] = np.log(option_data['last_price'][0]/option_data['strike'])

    # Interpolate implied volatility using a cubic spline
    # Then plot the implied volatility surface

    option_data_ = option_data.iloc[1:].sort_values(['t','strike']).query('t>0') #form time inwards out
    x = option_data['last_price'][0]/option_data_['strike']

    y = option_data_['t']
    z = option_data_['mark_iv']

    X,Y = np.meshgrid(np.linspace(0.6,1.4,99),np.linspace(1,np.max(y),100))
    Z = interpolate.griddata(np.array([x,y]).T,np.array(z),(X,Y), method='cubic')

    xyz = pd.DataFrame({'x':x,'y':y,'z':z})
    xyz = xyz.query('x>.7 & x<1.3')

    #(switch Z to Z2?)
    iv_df = pd.DataFrame(Z, index=np.linspace(1,np.max(y),100), columns=np.linspace(.5,1.5,99))
    iv_df = iv_df[iv_df.columns[::10]]

    fig_lin = px.line(iv_df)
    fig_lin.update_layout(xaxis_title="Days to Expiration",yaxis_title="IV %");
    fig_lin.update_layout(showlegend=False);
    fig_lin.update_layout(template='plotly_dark');

    return fig_lin




@app.callback(Output('table_call', 'data'),
                Input('interval-component', 'n_intervals'))

def update_table(n):
    df = get_all_option_data()
    df = df[1:]
    df_full= df[['instrument_name','mark_price','open_interest','mark_iv','greeks.delta','greeks.gamma','greeks.vega','greeks.theta','greeks.rho',]]
    df_full.columns = ['Instrument', 'Market Price', 'Open Interest', 'MarkIV',  'Delta', 'Gamma', 'Vega', 'Theta', 'Rho']
    df_call = df_full[df_full.index.str.contains('-C', case=False)]
    df_call = df_call.sort_values(by=['Delta']);
    return df_call.to_dict('records')

# @app.callback(Output('vol_surface', 'hoverdata'),
#                 Input('table_call', 'active_cell'))
#
# def showonvol():
#     return


if __name__ == '__main__':
    app.run_server(debug=True)
