from flask import Flask, render_template, jsonify, request
from plot_utils import generate_volatility_surface, plot_volatility, plot_iv_skew, plot_iv_term_structure
import json
from websocket import create_connection, WebSocketConnectionClosedException
import time
from flask_socketio import SocketIO, emit
import threading


app = Flask(__name__)

@app.route('/')
def index():
    plot_html = generate_volatility_surface()
    volatility_plot_html = plot_volatility()
    iv_skew_plot_html = plot_iv_skew()
    iv_term_structure_plot_html = plot_iv_term_structure()
    return render_template('index.html', plot_html=plot_html, volatility_plot_html=volatility_plot_html, iv_skew_plot_html=iv_skew_plot_html)

@app.route('/update_plot', methods=['POST'])
def update_plot():
    plot_html = generate_volatility_surface()
    plot_data = {}  
    return jsonify({'plot_html': plot_html, 'plot_data': plot_data})

@app.route('/update_volatility_plot', methods=['POST'])
def update_volatility_plot():
    volatility_plot_html = plot_volatility()
    volatility_plot_data = {}  #
    return jsonify({'volatility_plot_html': volatility_plot_html, 'volatility_plot_data': volatility_plot_data})


@app.route('/update_iv_skew_plot', methods=['POST'])
def update_iv_skew_plot():
    search_query = request.form.get('search', None)
    strike_price = None
    expiration = None

    if search_query:
        try:
            # Extract strike price
            strike_price = int(search_query.split('-')[2])
            print(f"Extracted strike price: {strike_price}")
            
            # Pass the whole query to the plot function
            expiration = search_query
            print(f"Raw expiration input: {expiration}")

        except (IndexError, ValueError) as e:
            return jsonify({'error': 'Invalid search query format', 'details': str(e)}), 400

    iv_skew_plot_html = plot_iv_skew(strike_price, expiration)
    iv_skew_plot_data = {}

    return jsonify({'iv_skew_plot_html': iv_skew_plot_html, 'iv_skew_plot_data': iv_skew_plot_data})


# @app.route('/update_iv_term_structure_plot', methods=['POST'])
# def update_iv_term_structure_plot():
#     iv_term_structure_plot_html = plot_iv_term_structure()  
#     iv_term_structure_plot_data = {}  
#     return jsonify({'iv_term_structure_plot_html': iv_term_structure_plot_html, 'iv_term_structure_plot_data': iv_term_structure_plot_data})


@app.route('/update_iv_term_structure_plot', methods=['POST'])
def update_iv_term_structure_plot():
    search_query = request.form.get('search', None)
    strike_price = None
    expiration = None

    if search_query:
        try:
            # Extract strike price
            strike_price = int(search_query.split('-')[2])
            print(f"Extracted strike price: {strike_price}")
            
            # Pass the whole query to the plot function
            expiration = search_query
            print(f"Raw expiration input: {expiration}")

        except (IndexError, ValueError) as e:
            return jsonify({'error': 'Invalid search query format', 'details': str(e)}), 400

    # Call the modified plot function for term structure
    iv_term_structure_plot_html = plot_iv_term_structure(strike_price, expiration)
    iv_term_structure_plot_data = {}

    return jsonify({'iv_term_structure_plot_html': iv_term_structure_plot_html, 'iv_term_structure_plot_data': iv_term_structure_plot_data})


def option_sheet_listener(search_query):
    try:
        # Create WebSocket connection
        ws = create_connection("wss://www.deribit.com/ws/api/v2")
        
        # Subscribe to the WebSocket channel
        subscription_request = {
            "method": "public/subscribe",
            "params": {
                "channels": [f"incremental_ticker.{search_query}"]
            },
            "jsonrpc": "2.0",
            "id": 6
        }
        ws.send(json.dumps(subscription_request))
        
        # Wait a bit to ensure we get some data
        time.sleep(1) 
        
        # Receive subscription confirmation
        subscription_response = ws.recv()
        print("Subscription confirmation:", subscription_response)
        
        # Receive actual data
        response = ws.recv()
        print("Raw WebSocket response:", response)
        
        ws.close()
        
        # Parse and return the response data
        try:
            response_json = json.loads(response)
            print("Parsed WebSocket response:", response_json)
            
            if 'params' in response_json and 'data' in response_json['params']:
                return response_json['params']['data']
            else:
                return {"error": "No data found in response"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}
    
    except WebSocketConnectionClosedException:
        return {"error": "WebSocket connection closed unexpectedly"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search')
    if not search_query:
        return jsonify({"error": "No search query provided"})
    
    print("Search Query:", search_query)
    response_data = option_sheet_listener(search_query)
    return jsonify({
        "search_query": search_query,
        "result": response_data
    })



if __name__ == "__main__":
    app.run(debug=False)