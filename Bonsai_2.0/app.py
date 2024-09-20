from flask import Flask, render_template, jsonify, request
from plot_utils import generate_volatility_surface, plot_volatility, plot_iv_skew
import json
from websocket import create_connection, WebSocketConnectionClosedException
import time

app = Flask(__name__)

@app.route('/')
def index():
    plot_html = generate_volatility_surface()
    volatility_plot_html = plot_volatility()
    iv_skew_plot_html = plot_iv_skew()  # Add this line
    return render_template('index.html', plot_html=plot_html, volatility_plot_html=volatility_plot_html, iv_skew_plot_html=iv_skew_plot_html)

@app.route('/update_plot', methods=['POST'])
def update_plot():
    plot_html = generate_volatility_surface()
    plot_data = {}  # Replace with actual plot data if needed
    return jsonify({'plot_html': plot_html, 'plot_data': plot_data})

@app.route('/update_volatility_plot', methods=['POST'])
def update_volatility_plot():
    volatility_plot_html = plot_volatility()
    volatility_plot_data = {}  # Replace with actual plot data if needed
    return jsonify({'volatility_plot_html': volatility_plot_html, 'volatility_plot_data': volatility_plot_data})

@app.route('/update_iv_skew_plot', methods=['POST'])  # Add this route
def update_iv_skew_plot():
    iv_skew_plot_html = plot_iv_skew()
    iv_skew_plot_data = {}  # Replace with actual plot data if needed
    return jsonify({'iv_skew_plot_html': iv_skew_plot_html, 'iv_skew_plot_data': iv_skew_plot_data})

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
        time.sleep(1)  # Increase duration if needed
        
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
    app.run(debug=True)