import requests
import time, os
import sys
import datetime
from pprint import pprint
import base64
import logging
import solders
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
import base64, json
from solders.pubkey import Pubkey
import cloudscraper

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = CustomFormatter()
ch.setFormatter(formatter)
logger.addHandler(ch)   


COPY_ACCOUNTS= [
    'suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK',
    # 'DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj',
    # 'CLf3PUt3be4qiqEBrXcg4U6S4Jjpz7RW8udwvc2NqR8J'
]
COPY_TOKEN_PROGRAM = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
LIVE = True
FEE = 0.002  # SOL fee for each transaction
BALANCE = 500.0
COST_PER_TRADE = 0.05
SOL = "So11111111111111111111111111111111111111112"
AMOUNT = 2_000_000_000 // 1000  # 0.002 SOL in lamports
SCRAPPER = cloudscraper.create_scraper()
ALL_TOKENS = {}
PROGRAMS = [
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
    'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
]
SOL_RPC = os.environ['SOL_RPC']  #https://api.mainnet-beta.solana.com"
MONITOR_START ={}
MONITOR_CHANGES = {}
BOUGHT_AT = {}
ENDED = {}
STARTED = {}
BUY = {}
SELL = {}
START_EPOCH = int(datetime.datetime.now().timestamp())

CLIENT = Client(SOL_RPC) 

def get_keypair():
    with open("keypair.json", "r") as f:
        secret = json.load(f)
    return Keypair.from_bytes(bytes(secret))
    
def send_signed_tx(serialized_tx_b64):
    # Load keypair from bytes (e.g. from keypair.json)
    keypair = get_keypair()
    
     # Step 1: Decode base64 Jupiter TX
    tx_bytes = base64.b64decode(serialized_tx_b64)

    # Step 2: Extract the message to sign
    raw_tx = VersionedTransaction.from_bytes(tx_bytes)

    # Step 3: Sign the message manually
    signature = keypair.sign_message(solders.message.to_bytes_versioned(raw_tx.message))
    
    # Step 4: Attach signature to transaction
    signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])

    # Step 5: Send the signed transaction
    resp = CLIENT.send_raw_transaction(bytes(signed_tx))
    return resp

def get_best_route(input_mint, output_mint, amount):
    url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,         # in lamports (1 SOL = 1_000_000_000)
        "slippageBps": 50,       # = 0.5%
        # "onlyDirectRoutes": True
    }
    res = requests.get(url, params=params).json()
    return res

def build_swap_transaction(route, user_pubkey):
    url = "https://quote-api.jup.ag/v6/swap"
    payload = {
        "quoteResponse": route,
        "userPublicKey": user_pubkey,
        "wrapUnwrapSOL": True,
        "dynamicSlippage": { "maxBps": 300 },
        "dynamicComputeUnitLimit": True,
        "prioritizationFeeLamports": {
            "priorityLevelWithMaxLamports": {
                "maxLamports": 5000,
                "priorityLevel": "veryHigh"
            }
        }
    }
    res = requests.post(url, json=payload)
    return res.json()

def calculate_percentage_change(old_price, new_price):
    if old_price == 0:
        return 0
    return ((new_price - old_price) / old_price) * 100  

def get_token_balance(mint_address):
    global COPY_TOKEN_PROGRAM
    opts =  TokenAccountOpts(program_id=Pubkey.from_string(COPY_TOKEN_PROGRAM))
    tokens = CLIENT.get_token_accounts_by_owner_json_parsed(get_keypair().pubkey(), opts)
    for token in tokens.value:
        info = token.account.data.parsed['info']
        mint = info['mint']
        if mint != mint_address:
            continue
        amount = info['tokenAmount']['amount']
        return int(amount)
    return 0

def is_sellable(token):
    time.sleep(1)  # Rate limit
    logger.info(f"Checking if token is sellable: {token.get('symbol', 'Unknown')}")
    mint = token.get("id")
    quote = get_best_route(mint, SOL, AMOUNT)  # 0.01 SOL
    if not quote or quote.get('error'):
        logger.error(f"Error fetching quote for {token['symbol']} - http://gmgn.ai/sol/token/{mint}:")
        return False
    return quote

def sell_token(token, parent_quote=None, percentage=1):
    global COST_PER_TRADE
    if not LIVE:
        logger.info(f"🤖 Simulating sell for token: {token['symbol']} - {token['address']}")
        return True
    
    mint = token.get("address")
    balance = get_token_balance(mint)
    if balance == 0:
        logger.warning(f"No balance for token: {token['symbol']} - {mint}")
        return True
    quote = parent_quote or get_best_route(mint, SOL, int(balance*percentage))  # 0.01 SOL
    if not quote or quote.get('error'):
        logger.error(f"Error fetching quote for {token['symbol']} - http://gmgn.ai/sol/token/{mint}: {balance}")
        return False
    bst = build_swap_transaction(quote, str(get_keypair().pubkey()))
    # print("Best route:", quote)
    
    stx = send_signed_tx(bst['swapTransaction'])   
    logger.info(f"Transaction sent: {stx}")
    logger.info(f"Sold token: {token['symbol']} - {mint}")
    return True

def buy_token(token, parent_quote=None):
    if not LIVE:
        logger.info(f"🤖 Simulating buy for token: {token['symbol']} - {token['address']}")
        return True

    mint = token.get("address")
    quote = get_best_route(SOL, mint, AMOUNT)  # 0.01 SOL
    bst = build_swap_transaction(quote, str(get_keypair().pubkey()))
    # print("Best route:", quote)
    stx = send_signed_tx(bst['swapTransaction'])   
    logger.info(f"Transaction sent: {stx}")
    logger.info(f"Bought token: {token['symbol']} - {mint}")
    token['bought_at'] = datetime.datetime.now()
    return True

def try_sell_token(token, percentage=1):
    try:
        if sell_token(token, percentage):
            logger.info(f"Successfully sold token: {token['symbol']} - {token['address']}")
            return True
        else:
            logger.warning(f"Failed to sell token: {token['symbol']} - {token['address']}")
    except Exception as e:
        logger.error(f"Error selling token {token['symbol']} - {token['address']}: {e}")
        
    return False

def try_buy_token(token):
    try:
        if buy_token(token):
            logger.info(f"Successfully bought token: {token['symbol']} - {token['address']}")
            return True
        else:
            logger.warning(f"Failed to buy token: {token['symbol']} - {token['address']}")
    except Exception as e:
        logger.error(f"Error buying token {token['symbol']} - {token['address']}: {e}")
    return False

def get_users_activities(wallet, atype='buy'):
    url = f"https://gmgn.ai/vas/api/v1/wallet_activity/sol?type={atype}&os=android&wallet={wallet}&limit=10&cost=10"
    response = SCRAPPER.get(url, )
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {}).get('activities', [])
    else:
        print(f"Error fetching tokens: {atype} {response.status_code}, {response.text}")
        return []


def get_tokens_to_sell():
    global MONITOR_CHANGES, BALANCE, SELL
    for acc in COPY_ACCOUNTS:
        for activity in get_users_activities(acc,'sell'):
            timestamp = activity['timestamp']
            if timestamp <= START_EPOCH:
                continue
            
            mint = activity['token']['address']
            symbol = activity['token']['symbol']
            
            if not SELL.get((timestamp,mint)) and MONITOR_CHANGES[acc].get(mint):
                
                change = calculate_percentage_change(float(MONITOR_CHANGES[acc][mint]['price']), float(activity['price']))
                logger.info(f"Sold Token Found: {symbol} for {calculate_percentage_change(float(MONITOR_CHANGES[acc][mint]['price']), float(activity['price'])):.2f}% at {datetime.datetime.now()}")            
                
                
                # sell here
                if LIVE:
                    if try_sell_token(activity['token']):
                        SELL[(timestamp,mint)] = True
                        del MONITOR_CHANGES[acc][mint]
                else:
                    BALANCE += COST_PER_TRADE * (1 + (change / 100))
                    logger.info(f"Balance: {BALANCE}")

        
    return 0


def get_tokens_to_buy():
    global MONITOR_CHANGES, BALANCE, BUY, START_EPOCH
    for acc in COPY_ACCOUNTS:
        if acc not in MONITOR_CHANGES:
            MONITOR_CHANGES[acc] = {}
            
        for activity in get_users_activities(acc):
            timestamp = activity['timestamp']

            if timestamp <= START_EPOCH:
                continue
                        
            mint = activity['token']['address']
            symbol = activity['token']['symbol']
            
            if not BUY.get((timestamp,mint)):
                
                MONITOR_CHANGES[acc][mint] = activity
                logger.info(f"New Token Found: {symbol} priced at {float(activity['price'])} at {datetime.datetime.now()}")
                
                # buy here
                if LIVE:
                    if try_buy_token(activity['token']):
                        BUY[(timestamp,mint)] = True
                else:
                    BALANCE -= COST_PER_TRADE + FEE
                    logger.info(f"Balance: {BALANCE}")

def start():
    logger.info("Starting token monitor bot...")
    while True:
        try:
            get_tokens_to_buy()
            get_tokens_to_sell()
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("Stopping token trading bot.")
            break

