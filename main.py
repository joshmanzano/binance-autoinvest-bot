from binance import Client
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()

api_key = os.getenv('API_KEY').strip()
api_secret = os.getenv('API_SECRET').strip()

client = Client(api_key, api_secret)

try:
    client.ping()
    status = client.get_system_status()
    print("Bot status: Running")
    print("Server status:",status['msg'])
except:
    print('Down!')

def get_account_data():
    busd = client.get_asset_balance(asset='BUSD')['free']
    return float(busd)

def get_data(symbol):
    minQty = client.get_symbol_info(symbol)['filters'][2]['minQty']
    ticker = client.get_ticker(symbol=symbol)
    last_price = ticker['lastPrice']
    price_change = ticker['priceChangePercent']
    min_order = float(minQty) * float(last_price)
    return [float(price_change), symbol, float(last_price), float(min_order)]

def get_price_change(e):
    return e[0]

choices = ['BTC','ETH','BNB','NEXO','ADA','ALGO','XTZ']
data = []
num_choices = len(choices)
lump_sum_limit = 99

balance = get_account_data()
for choice in choices:
    new_data = get_data(choice+'BUSD')
    if new_data[0] < 0:
        new_data[0] = abs(new_data[0])
        data.append(new_data)

data.sort(reverse=True, key=get_price_change)

price_changes = [d[0] for d in data]

if sum(price_changes) > lump_sum_limit:
    oldMax = max(price_changes)
    oldMin = min(price_changes)
    oldRange = (oldMax - oldMin)
    newMin = 1
    newMax = lump_sum_limit / num_choices
    newRange = (newMax - newMin)
    for d in data:
        d[0] = (((d[0] - oldMin) * newRange) / oldRange) + newMin

orders = []

for d in data:
    order_size = balance * (d[0]/100)
    if order_size > 0.99:
        orders.append([d[1], order_size])

for order in orders:
    print(f'Market order for ${round(order[1])} of {order[0]}') 




