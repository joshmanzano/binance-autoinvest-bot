from binance import Client
from binance.helpers import round_step_size
from dotenv import load_dotenv
import os
import schedule
import time
from decimal import Decimal, Context
from tqdm import tqdm

load_dotenv()

api_key = os.getenv('API_KEY').strip()
api_secret = os.getenv('API_SECRET').strip()

client = Client(api_key, api_secret)

choices = ['BTC','ETH','BNB','NEXO','ADA','XTZ','ALGO']

print('Starting bot...')
try:
    client.ping()
    status = client.get_system_status()
    print("Server status:",status['msg'])
except:
    print('Server is down!')

def get_account_data():
    busd = client.get_asset_balance(asset='BUSD')['free']
    return float(busd)

def get_data(symbol):
    info = client.get_symbol_info(symbol)
    minQty = info['filters'][2]['minQty']
    tick_size = info['filters'][2]['stepSize']
    min_notional = info['filters'][3]['minNotional']
    ticker = client.get_ticker(symbol=symbol)
    last_price = ticker['lastPrice']
    price_change = ticker['priceChangePercent']
    min_order = float(minQty) * float(last_price)
    return [float(price_change), symbol, float(last_price), float(min_order), float(tick_size), float(min_notional)]

def get_price_change(e):
    return e[0]

def order_cycle():

    print('Starting order cycle..')
    try:
        client.ping()
        status = client.get_system_status()
        print("Server status:",status['msg'])
    except:
        print('Server is down!')
        return

    data = []
    num_choices = len(choices)
    lump_sum_limit = 99

    balance = get_account_data()
    for choice in tqdm(choices):
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
        quantity = order_size/d[2] 
        tick_size = d[4]
        min_notional = d[5]
        if order_size > 0.99:
            orders.append([d[1], order_size, quantity, tick_size, d[2], min_notional])

    for order in orders:
        c = Context(prec=8)
        amount = c.create_decimal(order[2])
        tick_size = order[3]
        last_price = order[4]
        min_notional = order[5]
        quantity = round_step_size(amount, tick_size)
        notional_value = quantity * last_price
        if notional_value >= min_notional:
            try:
                order_result = client.order_market_buy(symbol=order[0],quantity=quantity)
                print('Market order for %.2f %s, $%.2f' % (quantity, order[0], quantity * last_price)) 
            except:
                print('Failed Market order %s' % order[0])
        else:
            balance = get_account_data()
            if balance > min_notional + 1:
                amount = ((min_notional + 1) / last_price)
                quantity = round_step_size(amount, tick_size)
                try:
                    order_result = client.order_market_buy(symbol=order[0],quantity=quantity)
                    print('Market order for %.2f %s, $%.2f' % (quantity, order[0], quantity * last_price)) 
                except:
                    print('Failed Market order %s' % order[0])
            else:
                print("Size order too low")
    
schedule.every(24).hours.do(order_cycle)

print('Bot is now running!')
order_cycle()

while True:
    schedule.run_pending()
    time.sleep(1)
