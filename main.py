import ccxt
import time
import requests
from threading import Thread
from dotenv import load_dotenv
import os


load_dotenv()


binance_api_key = os.getenv('BINANCE_API_KEY')
binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Telegram API URL
telegram_api_url = f'https://api.telegram.org/bot{telegram_bot_token}/'

def send_telegram_message(chat_id, message):
    url = telegram_api_url + 'sendMessage'
    params = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print('Failed to send Telegram message:', response.text)

def get_chat_id(message):
    chat_id = message['chat']['id']
    return chat_id

def process_telegram_message(update, chat_ids):
    message = update['message']
    chat_id = get_chat_id(message)
    text = message.get('text', '')

    # Process the received message and send a response
    if text == '/start':
        send_telegram_message(chat_id, 'Welcome to the trading bot!')
    elif text == '/help':
        send_telegram_message(chat_id, 'This is a trading bot. Use /buy to buy and /sell to sell.')
    elif text == '/buy':
        send_telegram_message(chat_id, 'Buy Bitcoin')
    elif text == '/sell':
        send_telegram_message(chat_id, 'Sell Bitcoin')
    elif text.lower() == 'hi':
        send_telegram_message(chat_id, 'Да еба и пичути ви да еба')
        chat_ids[chat_id] = {'last_price': None, 'active': True}
    elif text.lower() == 'stop':
        send_telegram_message(chat_id, 'Stopping price updates.')
        chat_ids[chat_id]['active'] = False
        chat_ids[chat_id]['last_price'] = None
    else:
        send_telegram_message(chat_id, 'Sorry, I cannot understand your message.')

def check_telegram_messages(chat_ids):
    last_update_id = 0

    while True:
        # Check for new messages
        url = telegram_api_url + 'getUpdates'
        params = {
            'offset': last_update_id + 1
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                for update in data['result']:
                    process_telegram_message(update, chat_ids)
                    last_update_id = update['update_id']

        time.sleep(1)

def run_trading_strategy():
    binance = ccxt.binance({
        'apiKey': binance_api_key,
        'secret': binance_secret_key
    })

    symbol = 'BTC/USDT'

    # Create a dictionary to store chat_ids and stop status
    chat_ids = {}

    # Start the thread for checking Telegram messages
    thread = Thread(target=check_telegram_messages, args=(chat_ids,))
    thread.start()

    while True:
        # Get the latest ticker information
        ticker = binance.fetch_ticker(symbol)

        # Get the current price
        current_price = ticker['last']

        # Send the current price to chat_ids with "Hi" messages
        for chat_id, data in chat_ids.items():
            if data['active']:
                last_price = data['last_price']
                if last_price is not None:
                    if current_price > last_price:
                        send_telegram_message(chat_id, f"BTC Price: {current_price}\nBuy Bitcoin")
                    elif current_price < last_price:
                        send_telegram_message(chat_id, f"BTC Price: {current_price}\nSell Bitcoin")

        # Update the last_price for chat_ids with "Hi" messages
        for chat_id, data in chat_ids.items():
            if data['active']:
                chat_ids[chat_id]['last_price'] = current_price

        # Wait for 2 seconds before checking again
        time.sleep(2)

run_trading_strategy()
