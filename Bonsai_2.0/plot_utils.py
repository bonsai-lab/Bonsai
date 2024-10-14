import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime
from scipy import interpolate
import threading
from websocket import create_connection
import time
import sys
import re
from flask import request, jsonify


# Initialize global variables and data structures
option_data_dict = {}  
btc_price = None
volatility_data = None
historical_volatility_data = [] 
data_lock = threading.Lock()
data_collection_complete = False


def ws_listener(channels, callback_dict):
    ws = None
    while True:
        try:
            # Initialize WebSocket connection
            ws = create_connection("wss://www.deribit.com/ws/api/v2")
            
            # Subscribe to multiple channels
            ws.send(json.dumps({
                "method": "public/subscribe",
                "params": {
                    "channels": channels
                },
                "jsonrpc": "2.0",
                "id": 100
            }))
            
            while True:
                result = json.loads(ws.recv())
                if 'params' in result and 'data' in result['params']:
                    channel = result['params']['channel']
                    data = result['params']['data']
                    
                    # Call the appropriate callback function based on the channel
                    if channel in callback_dict:
                        callback_dict[channel](data)
        
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
        
        finally:
            # Ensure the WebSocket is cleanly closed before reconnecting
            if ws:
                ws.close()

            print("Reconnecting after 5 seconds...")
            time.sleep(5)  # Wait before attempting to reconnect


# BTC price callback
def handle_btc_price(data):
    global btc_price
    btc_price = data.get('price')
    print(f"BTC price received: {btc_price}")


# Options data callback
def handle_options_data(data):
    global option_data_dict, data_collection_complete
    if isinstance(data, list):
        with data_lock:
            for option_data in data:
                instrument_name = option_data.get('instrument_name')
                if instrument_name:
                    option_data_dict[instrument_name] = {
                        'mark_price': option_data.get('mark_price'),
                        'iv': option_data.get('iv'),
                        'timestamp': option_data.get('timestamp')
                    }
            if len(option_data_dict) >= 820:
                data_collection_complete = True
            print(f"Option data updated: {len(option_data_dict)} unique entries")


# Volatility data callback
def handle_volatility_data(data):
    global volatility_data, historical_volatility_data
    volatility_data = data
    with data_lock:
        historical_volatility_data.append({
            'volatility': volatility_data.get('volatility'),
            'timestamp': volatility_data.get('timestamp')
        })
    print(f"Volatility data received: {volatility_data}")


# Start WebSocket connections for all channels
def start_data_collection():
    channels = [
        "deribit_price_index.btc_usd",
        "markprice.options.btc_usd",
        "deribit_volatility_index.btc_usd"
    ]
    
    # Dictionary to map channels to their respective callbacks
    callback_dict = {
        "deribit_price_index.btc_usd": handle_btc_price,
        "markprice.options.btc_usd": handle_options_data,
        "deribit_volatility_index.btc_usd": handle_volatility_data
    }
    
    threading.Thread(target=ws_listener, args=(channels, callback_dict), daemon=True).start()



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
        Z2 = interpolate.griddata(np.array([x, y]).T, z, (X2, Y2), method='cubic', rescale=True)

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
            line=dict(color='white', width=3),
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



def extract_strike_price_from_query(query):
    parts = query.split('-')
    if len(parts) >= 3:  # Ensure there are enough parts
        return int(parts[2])  # Convert to integer
    raise ValueError("Invalid format")




# Function to plot IV skew
def plot_iv_skew(strike_price=None, expiration_raw=None, combine_put_call=True):
    global option_data_dict, btc_price, data_collection_complete
    try:
        if not data_collection_complete:
            return "<p>Waiting for complete data...</p>"

        if btc_price is None:
            return "<p>No BTC price available</p>"

        # Create DataFrame from option data
        df = pd.DataFrame.from_dict(option_data_dict, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'instrument_name'}, inplace=True)

        if df.empty or 'instrument_name' not in df or 'mark_price' not in df or 'iv' not in df:
            return "<p>Invalid or insufficient option data available</p>"

        # Parse expiration dates and calculate time to expiration
        df['expiration_timestamp'] = df['instrument_name'].apply(parse_expiration_date)
        df['current_timestamp'] = pd.Timestamp.now().value // 10**6  # Ensure this is in milliseconds
        df['t'] = (df['expiration_timestamp'] - df['current_timestamp']) / (1000 * 60 * 60 * 24)
        df['strike_price'] = df['instrument_name'].apply(extract_strike_price)

        # Add a column to differentiate between calls and puts
        df['option_type'] = df['instrument_name'].apply(lambda x: 'call' if 'C' in x else 'put')

        # Filter DataFrame for valid options
        df = df[(df['t'] > 0) & (df['mark_price'] > 0) & (df['iv'] > 0)]

        # Filtering based on BTC price bounds
        lower_bound = btc_price * 0.25
        upper_bound = btc_price * 1.75
        df = df[(df['strike_price'] >= lower_bound) & (df['strike_price'] <= upper_bound)]

        # Initialize the figure
        fig = go.Figure()

        # Parse expiration date using parse_expiration_date function
        expiration_timestamp = None
        if expiration_raw is not None:
            try:
                expiration_timestamp = parse_expiration_date(expiration_raw)
                expiration_df = df[df['expiration_timestamp'] == expiration_timestamp]
                
                if expiration_df.empty:
                    print(f"No data available for expiration: {expiration_raw}")
                else:
                    # Option to combine IVs for puts and calls or keep them separate
                    if combine_put_call:
                        # Average IV for puts and calls at the same strike
                        grouped_df = expiration_df.groupby('strike_price').agg(
                            avg_iv=('iv', 'mean')).reset_index()
                        connected_df = grouped_df.sort_values(by='strike_price')
                    else:
                        # Keep calls and puts separate
                        connected_df = expiration_df.sort_values(by='strike_price')

                    fig.add_trace(go.Scatter(
                        x=connected_df['strike_price'],
                        y=connected_df['iv'] if not combine_put_call else connected_df['avg_iv'],
                        mode='lines+markers',
                        line=dict(color='white', width=3),
                    ))
            except Exception as e:
                print(f"Error parsing expiration date: {e}")

        # Highlight specific strike price if given
        if strike_price is not None:
            highlighted_df = df[np.isclose(df['strike_price'], strike_price)]

            if expiration_timestamp is not None:
                intersection_df = df[
                    np.isclose(df['strike_price'], strike_price) &
                    (df['expiration_timestamp'] == expiration_timestamp)
                ]
                if intersection_df.empty:
                    print(f"No data for strike price {strike_price} and expiration {expiration_raw}")
                else:
                    fig.add_trace(go.Scatter(
                        x=intersection_df['strike_price'],
                        y=intersection_df['iv'],
                        mode='markers',
                        marker=dict(size=15, color='red', symbol='diamond'),
                    ))
            elif not highlighted_df.empty:
                fig.add_trace(go.Scatter(
                    x=highlighted_df['strike_price'],
                    y=highlighted_df['iv'],
                    mode='markers',
                    marker=dict(size=15, color='red'),
                ))
            else:
                print(f"No data for strike price {strike_price}")

        # Always plot all valid options
        fig.add_trace(go.Scatter(
            x=df['strike_price'],
            y=df['iv'],
            mode='markers',
            marker=dict(size=6, color=df['iv'], colorscale=[[0, 'green'], [0.5, 'yellow'], [1.0, 'red']], showscale=False),
        ))

        fig.update_layout(
            xaxis_title='Strike Price',
            yaxis_title='Implied Volatility (%)',
            template='plotly_dark',
            font=dict(family="Roboto Mono", size=9),
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0),
            showlegend=False
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        print(f"Error generating IV skew plot: {e}")
        return "<p>Error generating the plot. Please check server logs.</p>"



# Function to plot IV term structure based on same strike price across all expirations
def plot_iv_term_structure(strike_price=None, expiration_raw=None):
    global option_data_dict, btc_price, data_collection_complete
    try:
        if not data_collection_complete:
            return "<p>Waiting for complete data...</p>"

        if btc_price is None:
            return "<p>No BTC price available</p>"

        # Create DataFrame from option data
        df = pd.DataFrame.from_dict(option_data_dict, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'instrument_name'}, inplace=True)

        if df.empty or 'instrument_name' not in df or 'mark_price' not in df or 'iv' not in df:
            return "<p>Invalid or insufficient option data available</p>"

        # Parse expiration dates and calculate time to expiration
        df['expiration_timestamp'] = df['instrument_name'].apply(parse_expiration_date)
        df['current_timestamp'] = pd.Timestamp.now().value // 10**6  # Ensure this is in milliseconds
        df['t'] = (df['expiration_timestamp'] - df['current_timestamp']) / (1000 * 60 * 60 * 24)  # Days to expiration
        df['strike_price'] = df['instrument_name'].apply(extract_strike_price)

        # Filter DataFrame for valid options
        df = df[(df['t'] > 0) & (df['mark_price'] > 0) & (df['iv'] > 0)]
        # df = df[df['t'] > 0]  # Optional: You can adjust this threshold as needed
        

        # Initialize the figure
        fig = go.Figure()

        # Plot all options for reference
        for strike in df['strike_price'].unique():
            strike_df = df[df['strike_price'] == strike].sort_values(by='t')
            if not strike_df.empty:
                fig.add_trace(go.Scatter(
                    x=strike_df['t'],  # Days to expiration
                    y=strike_df['iv'],  # Implied volatility
                    mode='markers',  # Using markers for reference points
                    line=dict(width=2),  # Just keeping the width for better visibility
                ))

        # Highlight the term structure for a specific strike price if provided
        if strike_price is not None:
            highlighted_df = df[df['strike_price'] == strike_price].sort_values(by='t')
            if not highlighted_df.empty:
                fig.add_trace(go.Scatter(
                    x=highlighted_df['t'],  # Days to expiration
                    y=highlighted_df['iv'],  # Implied volatility
                    mode='lines+markers',
                    line=dict(color='white', width=3),  # Highlight in blue
                    name=f'Highlighted Term Structure for Strike {strike_price}'  # Label for the highlighted line
                ))

            # Highlight the specific implied volatility for the parsed expiration
            if expiration_raw is not None:
                # Attempt to parse the expiration from raw input to get timestamp
                expiration_timestamp = parse_expiration_date(expiration_raw)

                # Calculate the specific days to expiration
                current_timestamp = pd.Timestamp.now().value // 10**6  # Current time in milliseconds
                days_to_expiration = (expiration_timestamp - current_timestamp) / (1000 * 60 * 60 * 24)

                # Filter to find the IV corresponding to the highlighted strike price and calculated days to expiration
                specific_iv_df = highlighted_df[highlighted_df['t'] == days_to_expiration]

                if not specific_iv_df.empty:
                    fig.add_trace(go.Scatter(
                        x=[days_to_expiration],  # X value for days to expiration
                        y=specific_iv_df['iv'],  # Y value for the specific implied volatility
                        mode='markers',
                        marker=dict(size=15, color='red', symbol='diamond'),  # Highlight in red
                        name=f'Highlighted IV at {round(days_to_expiration)} Days to Expiration'  # Label for the highlighted point
                    ))
                else:
                    # Attempt to find the nearest available data point if the exact match is not found
                    closest_iv_df = highlighted_df.loc[(highlighted_df['t'] - days_to_expiration).abs().idxmin()]
                    fig.add_trace(go.Scatter(
                        x=[closest_iv_df['t']],  # Nearest available days to expiration
                        y=[closest_iv_df['iv']],  # Corresponding implied volatility
                        mode='markers',
                        marker=dict(size=15, color='red', symbol='diamond', opacity=0.7),  # Highlight in red
                        name='Closest IV Highlighted'  # Label for the highlighted point
                    ))

        # Always plot all valid options for reference
        fig.add_trace(go.Scatter(
            x=df['t'],
            y=df['iv'],
            mode='markers',
            marker=dict(size=6, color=df['iv'], colorscale=[[0, 'green'], [0.5, 'yellow'], [1.0, 'red']], showscale=False),
            name='IV Data'
        ))

        # Update layout of the plot
        fig.update_layout(
            xaxis_title='Days to Expiration',
            yaxis_title='Implied Volatility (%)',
            template='plotly_dark',
            font=dict(family="Roboto Mono", size=9),
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0),
            showlegend=False  # Show legend to differentiate between strike prices and highlights
        )

        return fig.to_html(full_html=False)

    except Exception as e:
        print(f"Error generating IV term structure plot: {e}")
        return "<p>Error generating the plot. Please check server logs.</p>"



# Start data collection
start_data_collection()