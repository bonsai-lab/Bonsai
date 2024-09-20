import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime
from scipy import interpolate
import threading
from websocket import create_connection

# Initialize global variables and data structures
option_data_dict = {}  # Dictionary to store option data with instrument_name as key
btc_price = None
volatility_data = None
historical_volatility_data = []  # Initialize as an empty list
data_lock = threading.Lock()
data_collection_complete = False

def btc_price_ws_listener():
    global btc_price
    ws = create_connection("wss://www.deribit.com/ws/api/v2")
    ws.send(json.dumps({
        "method": "public/subscribe",
        "params": {
            "channels": ["deribit_price_index.btc_usd"]
        },
        "jsonrpc": "2.0",
        "id": 36
    }))
    
    while True:
        try:
            result = json.loads(ws.recv())
            if 'params' in result and 'data' in result['params']:
                btc_price = result['params']['data']['price']
                print(f"BTC price received: {btc_price}")
        except Exception as e:
            print(f"Error in BTC price WebSocket listener: {e}")




def options_data_ws_listener():
    global option_data_dict, data_collection_complete
    ws = create_connection("wss://www.deribit.com/ws/api/v2")
    ws.send(json.dumps({
        "method": "public/subscribe",
        "params": {
            "channels": ["markprice.options.btc_usd"]
        },
        "jsonrpc": "2.0",
        "id": 42
    }))
    
    while True:
        try:
            result = json.loads(ws.recv())
            if 'params' in result and 'data' in result['params']:
                option_data_chunk = result['params']['data']
                if isinstance(option_data_chunk, list):
                    with data_lock:
                        for option_data in option_data_chunk:
                            instrument_name = option_data.get('instrument_name')
                            if instrument_name:
                                option_data_dict[instrument_name] = {
                                    'mark_price': option_data.get('mark_price'),
                                    'iv': option_data.get('iv'),
                                    'timestamp': option_data.get('timestamp')
                                }
                    # Check if we have received data for all unique options
                    if len(option_data_dict) >= 900:
                        data_collection_complete = True
                    print(f"Option data updated: {len(option_data_dict)} unique entries")
        except Exception as e:
            print(f"Error in options data WebSocket listener: {e}")

def volatility_data_ws_listener():
    global volatility_data, historical_volatility_data
    ws = create_connection("wss://www.deribit.com/ws/api/v2")
    ws.send(json.dumps({
        "method": "public/subscribe",
        "params": {
            "channels": ["deribit_volatility_index.btc_usd"]
        },
        "jsonrpc": "2.0",
        "id": 43
    }))

    while True:
        try:
            result = json.loads(ws.recv())
            if 'params' in result and 'data' in result['params']:
                volatility_data = result['params']['data']
                with data_lock:
                    historical_volatility_data.append({
                        'volatility': volatility_data.get('volatility'),
                        'timestamp': volatility_data.get('timestamp')
                    })
                print(f"Volatility data received: {volatility_data}")
        except Exception as e:
            print(f"Error in volatility data WebSocket listener: {e}")



def parse_expiration_date(instrument_name):
    try:
        date_str = instrument_name.split('-')[1]
        expiration_date = datetime.strptime(date_str, '%d%b%y')
        return int(expiration_date.timestamp() * 1000)  # Convert to milliseconds
    except Exception as e:
        print(f"Error parsing expiration date: {e}")
        return None

def extract_strike_price(instrument_name):
    try:
        strike_price_str = instrument_name.split('-')[2]
        return float(strike_price_str.replace(',', ''))
    except Exception as e:
        print(f"Error extracting strike price: {e}")
        return None

def generate_volatility_surface():
    global option_data_dict, btc_price, data_collection_complete
    try:
        if not data_collection_complete:
            return "<p>Waiting for complete data...</p>"

        if btc_price is None:
            return "<p>No BTC price available</p>"

        df = pd.DataFrame.from_dict(option_data_dict, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'instrument_name'}, inplace=True)

        if df.empty or 'instrument_name' not in df or 'mark_price' not in df or 'iv' not in df:
            return "<p>Invalid or insufficient option data available</p>"

        df['expiration_timestamp'] = df['instrument_name'].apply(parse_expiration_date)
        df['current_timestamp'] = pd.Timestamp.now().value // 10**6
        df['t'] = (df['expiration_timestamp'] - df['current_timestamp']) / (1000 * 60 * 60 * 24)

        df['strike_price'] = df['instrument_name'].apply(extract_strike_price)
        df = df[(df['t'] > 0) & (df['mark_price'] > 0) & (df['iv'] > 0) & (df['strike_price'].notnull())]

        lower_bound = btc_price * 0.75
        upper_bound = btc_price * 1.25
        df = df[(df['strike_price'] >= lower_bound) & (df['strike_price'] <= upper_bound)]
        df = df[df['t'] > 5]

        print("Data used for interpolation:")
        print(df[['strike_price', 't', 'iv']].describe())

        x = df['strike_price']
        y = df['t']
        z = df['iv']

        if x.empty or y.empty or z.empty:
            return "<p>Insufficient data for plotting.</p>"

        X2, Y2 = np.meshgrid(
            np.linspace(x.min(), x.max(), 300),
            np.linspace(y.min(), y.max(), 300)
        )
        Z2 = interpolate.griddata(np.array([x, y]).T, z, (X2, Y2), method='cubic', rescale=False)

        Z2[np.isnan(Z2)] = None

        def now_utc():
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        fig = go.Figure()
        custom_color = [[0, 'green'], [0.5, 'yellow'], [1.0, 'red']]
        fig.add_surface(x=X2, y=Y2, z=Z2, colorscale=custom_color, showscale=True)
        fig.update_layout(scene_camera_eye=dict(x=-1, y=-2, z=0.5))
        fig.update_layout(title=f" <br>Updated: {now_utc()} | Source: Bonsai Lab, Deribit.com")
        fig.update_layout(font=dict(family="Roboto Mono", size=9))
        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            template='plotly_dark',
            font_color="lightgrey",
            scene=dict(
                xaxis_title='Strike Price',
                yaxis_title='Days To Expiration',
                zaxis_title='Implied Volatility (%)',
                aspectratio=dict(x=1, y=1, z=0.6),
                xaxis=dict(gridcolor="rgb(64,64,64)", zerolinecolor="rgb(64,64,64)"),
                yaxis=dict(gridcolor="rgb(64,64,64)", zerolinecolor="rgb(64,64,64)"),
                zaxis=dict(gridcolor="rgb(64,64,64)", zerolinecolor="rgb(64,64,64)")
            ),
            autosize=True
        )

        print("Plot generated successfully.")
        return fig.to_html(full_html=False)

    except Exception as e:
        print(f"Error generating plot: {e}")
        return f"<p>Error generating plot: {e}</p>"

def plot_volatility():
    global historical_volatility_data
    try:
        if not historical_volatility_data:
            return "<p>No volatility data available</p>"

        timestamps = [datetime.fromtimestamp(data['timestamp'] / 1000) for data in historical_volatility_data]
        volatilities = [data['volatility'] for data in historical_volatility_data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=volatilities,
            mode='lines',
        ))
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Volatility (%)',
            template='plotly_dark',
            font=dict(family="Roboto Mono", size=9),
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0)
        )

        print("Volatility plot generated successfully.")
        return fig.to_html(full_html=False)

    except Exception as e:
        print(f"Error generating volatility plot: {e}")
        return f"<p>Error generating volatility plot: {e}</p>"



def plot_iv_skew():
    global option_data_dict, btc_price, data_collection_complete
    try:
        if not data_collection_complete:
            return "<p>Waiting for complete data...</p>"

        if btc_price is None:
            return "<p>No BTC price available</p>"

        df = pd.DataFrame.from_dict(option_data_dict, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'instrument_name'}, inplace=True)

        if df.empty or 'instrument_name' not in df or 'mark_price' not in df or 'iv' not in df:
            return "<p>Invalid or insufficient option data available</p>"

        df['expiration_timestamp'] = df['instrument_name'].apply(parse_expiration_date)
        df['current_timestamp'] = pd.Timestamp.now().value // 10**6
        df['t'] = (df['expiration_timestamp'] - df['current_timestamp']) / (1000 * 60 * 60 * 24)

        df['strike_price'] = df['instrument_name'].apply(extract_strike_price)
        df = df[(df['t'] > 0) & (df['mark_price'] > 0) & (df['iv'] > 0) & (df['strike_price'].notnull())]

        lower_bound = btc_price * 0.75
        upper_bound = btc_price * 1.25
        df = df[(df['strike_price'] >= lower_bound) & (df['strike_price'] <= upper_bound)]
        df = df[df['t'] > 5]

        print("Data used for IV skew plotting:")
        print(df[['strike_price', 'iv']].describe())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['strike_price'],
            y=df['iv'],
            mode='markers',
            marker=dict(size=6, color=df['iv'], colorscale='Viridis',showscale=False, colorbar=dict(title='IV (%)'))
        ))
        fig.update_layout(
            xaxis_title='Strike Price',
            yaxis_title='Implied Volatility (%)',
            template='plotly_dark',
            font=dict(family="Roboto Mono", size=9),
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0)
        )
        
        print("IV skew plot generated successfully.")
        return fig.to_html(full_html=False)

    except Exception as e:
        print(f"Error generating IV skew plot: {e}")
        return f"<p>Error generating IV skew plot: {e}</p>"





def start_data_collection():
    threading.Thread(target=btc_price_ws_listener, daemon=True).start()
    threading.Thread(target=options_data_ws_listener, daemon=True).start()
    threading.Thread(target=volatility_data_ws_listener, daemon=True).start()

# Start data collection
start_data_collection()