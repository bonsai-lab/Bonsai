import numpy as np
import pandas as pd
import plotly.express as px
import datetime
import time
pd.set_option("display.max_rows", None, "display.max_columns", None)


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

print(get_all_active_options())

    all = get_all_active_options()

all = all.sort_values(['expiration_timestamp', 'strike'])
all_sorted_call = all[all['option_type'].str.contains("put")==False]
all_sorted_put = all[all['option_type'].str.contains("call")==False]


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
    active_options = active_options.query('m>-1 & m<2 & t<251')

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

df = get_all_option_data()




#option_data = get_all_option_data()

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

option_data_ = option_data.iloc[1:].sort_values(['t','strike']).query('t>0')

option_data_

x = option_data['last_price'][0]/option_data_['strike']

y = option_data_['t']
z = option_data_['mark_iv']

option_data_


z_c = z[z.index.str.contains('-C', case=False)]

a_c = pd.DataFrame(z_c)



b_c = z_c.index.str[4:11]

a_c['date'] = b_c

test_c = a_c;


isodate = pd.DataFrame(test['date'].drop_duplicates())
isodate = isodate['date'].values

d = {}
for i in isodate:
    d[i] = a.loc[a.date == i][['mark_iv', 'date']]


list(d.keys())[0]
d[list(d.keys())[0]]

def plotline(x):
    fig_new = px.line(d[list(d.keys())[x]].drop('date', axis = 1))
    fig_new.update_layout(template='plotly_dark');
    fig_new.show()





plotline(0)



df = px.data.gapminder().query("continent=='Oceania'")

df

new = a.loc[a.date == strike][['mark_iv', 'date']]



start = time.time() - (60*60*24)
end = time.time()
