# import warnings
# warnings.simplefilter(action='ignore', category=Warning)
# import pandas as pd
# from datetime import datetime,timedelta,time
# from kiteconnect import KiteConnect
# import pandas_ta as ta
# from zip_read import fetch_csv_from_zip,create_symbol_format
# import traceback,os

# kite = KiteConnect(api_key='e2rljmvjeg7v53ku', access_token='2ppvDvHXCFFCfhXZomPZSlxP9maYeFpC')
# ema = 92121200

# year = '2024'
# # timeframe = '15minute'

# # ---- Dates ----
# start_date = f'{year}-01-01'
# end_date = f'{year}-12-31'


# config = {
#     'ema9': 9, 
#     'ema5': 5, 
#     'ema13': 13, 
#     'ema21': 21,
#     'ema34': 34, 
#     'sma40': 40,
#     'ema40': 40,
#     'sma45': 45,
#     'sma50': 50,
#     'sma100': 100,
#     'sma200': 200,
#     'sma300': 300,
#     'rsi14': 14,
#     'rsi_threshold': 50,
#     'body_ratio': 0.6,
#     # 'sell_otm': 100,
#     'sell_otm': 0,
#     'spread': 200,
#     'lot_size': 50,
#     'max_profit_per_lot': 100,
#     'spot_sl_pct': 0.003,
#     # 'spot_sl_pct': 0.001,
#     'max_hold': 210,
#     'min_premium': 30 
# } 


# def load_expiry_dates_from_csv(csv_path, start_date, end_date):
#     # 1) Read the CSV (expects a column named “expiry_date” in YYYY-MM-DD form)
#     expiry_df = pd.read_csv(csv_path, parse_dates=['expiry_date'])
    
#     # 2) Filter to your date window
#     mask = (
#         (expiry_df['expiry_date'] >= pd.to_datetime(start_date)) &
#         (expiry_df['expiry_date'] <= pd.to_datetime(end_date))
#     )
#     filtered = expiry_df.loc[mask]
    
#     # 3) Sort ascending and reset index
#     filtered = filtered.sort_values('expiry_date').reset_index(drop=True)

#     filtered['expiry_date'] = filtered['expiry_date'].dt.date  # so comparisons work with .date()
    
#     return filtered
    
# expiry_dates = load_expiry_dates_from_csv('files/expiry_dates.csv', start_date, end_date)

# # ---- Fetch Zerodha Data ----
# def fetch_max_data_zerodha(token, start_date, end_date, time_data,
#                            trading_dates_csv='files/trading_dates.csv'):
#     # 1) Read the CSV of trading dates
#     trading_df = pd.read_csv(trading_dates_csv, parse_dates=['date'])
    
#     # 2) Filter to your requested window
#     mask = (trading_df['date'] >= pd.to_datetime(start_date)) & \
#            (trading_df['date'] <= pd.to_datetime(end_date))
#     trading_df = trading_df.loc[mask]
    
#     # 3) Build a DESC–sorted list of date strings
#     trading_dates = trading_df['date'] \
#         .dt.strftime('%Y-%m-%d') \
#         .sort_values(ascending=False) \
#         .tolist()

#     # 4) Chunk into 30‐day slices
#     chunks = [trading_dates[i:i+30] for i in range(0, len(trading_dates), 30)]
    
#     # 5) Pull history in batches and concatenate
#     df = pd.DataFrame()
#     for chunk in chunks:
#         # chunk[-1] is the earliest, chunk[0] the latest in that slice
#         temp = pd.DataFrame(
#             kite.historical_data(token, chunk[-1], chunk[0], time_data)
#         )
#         df = pd.concat([df, temp], ignore_index=True)
    
#     # 6) Final cleanup
#     df['date'] = pd.to_datetime(df['date'])
#     df = df.sort_values('date').reset_index(drop=True)
#     return df


# # ---- Indicators ----
# def generate_signals(interval_df, config):
#     df = interval_df.copy()

#     df['ema_5'] = ta.ema(df['close'], length=config['ema5'])
#     df['ema_9'] = ta.ema(df['close'], length=config['ema9'])
#     df['ema_13'] = ta.ema(df['close'], length=config['ema13'])
#     df['ema_21'] = ta.ema(df['close'], length=config['ema21'])
#     df['ema_34'] = ta.ema(df['close'], length=config['ema34'])
#     df['sma_40'] = ta.sma(df['close'], length=config['sma40'])
#     df['ema_40'] = ta.ema(df['close'], length=config['ema40'])
#     df['sma_45'] = ta.sma(df['close'], length=config['sma45'])
#     df['sma_50'] = ta.sma(df['close'], length=config['sma50'])
#     df['sma_100'] = ta.sma(df['close'], length=config['sma100'])
#     df['sma_200'] = ta.sma(df['close'], length=config['sma200'])
#     df['sma_300'] = ta.sma(df['close'], length=config['sma300'])
#     df['rsi_14'] = ta.rsi(df['close'], length=config['rsi14'])
#     df.dropna(inplace=True)
#     body_size = (df['close'] - df['open'])
#     wick_size = df['high'] - df['low']
#     df['body_condition'] = body_size >= config['body_ratio'] * wick_size

#     df['long_signal'] = (
#         (df['ema_9'] > df['ema_21']) &
#         (df['ema_21'] > df['sma_200']) &
#         (df['rsi_14'] > config['rsi_threshold']) &
#         df['body_condition']
#     )

#     df.to_csv('signaltest.csv')
#     return df[['date','open', 'close', 'long_signal']]

# # # ---- Match with 1-min data ----
# # def match_signals_with_1min(df_signals, df_1min):
# #     entries = []
# #     for _, row in df_signals[df_signals['long_signal']].iterrows():
# #         signal_time = row['date']
# #         future_candle = df_1min[df_1min['date'] > signal_time].head(1)
# #         if not future_candle.empty:
# #             c = future_candle.iloc[0]
# #             entries.append({
# #                 'signal_time': signal_time,
# #                 'signal_close': row['close'],
# #                 'execution_time': c['date'],
# #                 'execution_open': c['open'],
# #                 'execution_high': c['high'],
# #                 'execution_low': c['low'],
# #                 'execution_close': c['close']
# #             })
# #     return pd.DataFrame(entries)

# # def match_signals_with_1min(df_signals, df_1min):
# #     # print(df_signals, df_1min)
# #     entries = []
    
# #     signal_indices = df_signals[df_signals['long_signal']].index.tolist()
    
# #     for i, idx in enumerate(signal_indices):
# #         row = df_signals.loc[idx]
# #         row['date'] = df_signals.loc[idx+1]['date']
# #         # print (row)
                
# #         signal_time = row['date']
# #         future_candle = df_1min[df_1min['date'] > signal_time].head(1)
# #         if not future_candle.empty:
# #             c = future_candle.iloc[0]
# #             # print (c)
# #             # exit(0)
# #             entries.append({
# #                 'signal_time'    : signal_time,
# #                 'signal_close'   : row['close'],
# #                 'execution_time' : c['date'],
# #                 'execution_open' : c['open'],
# #                 'execution_high' : c['high'],
# #                 'execution_low'  : c['low'],
# #                 'execution_close': c['close']
# #             })
# #     return pd.DataFrame(entries)


# def match_signals_with_1min(df_signals):
#     # print(df_signals, df_1min)
#     entries = []
#     signal_indices = df_signals[df_signals['long_signal']].index.tolist()
    
#     for i, idx in enumerate(signal_indices):
#         row = df_signals.loc[idx]
#         # row['date'] = df_signals.loc[idx+1]['date']
#         next_row = df_signals.loc[idx+1]
                
#         entries.append({
#             'signal_time'     : row['date'],
#             'execution_time'  : next_row['date'],
#             'execution_open'  : next_row['open'],
#         })
#     return pd.DataFrame(entries)



# # ---- Get ATM, Sell PE, Buy PE ----
# def get_option_strikes(spot_price, config):
#     atm = round(spot_price / 50) * 50
#     sell_pe = atm - config['sell_otm']
#     buy_pe = sell_pe - config['spread']
#     return {'atm': atm, 'sell_pe': sell_pe, 'buy_pe': buy_pe}

# # ---- Simulate Trades (Updated Inline) ----
# def calculate_max_profit_loss_per_leg(option_data, entry_time, entry_price, lot_size, leg_type):
#     """
#     Calculate max profit and max loss for an option leg after the entry time.
#     leg_type: 'buy' or 'sell'
#     """
#     option_data = option_data[option_data['time'] > entry_time.time()]
#     if option_data.empty:
#         return 0.0, 0.0

#     ltp_values = option_data['LTP']
#     if leg_type == 'buy':
#         max_profit = (ltp_values.max() - entry_price) * lot_size
#         max_loss = (entry_price - ltp_values.min()) * lot_size
#     elif leg_type == 'sell':
#         max_profit = (entry_price - ltp_values.min()) * lot_size
#         max_loss = (ltp_values.max() - entry_price) * lot_size
#     else:
#         raise ValueError("Invalid leg_type: Must be 'buy' or 'sell'")
    
#     return round(max_profit, 2), round(max_loss, 2)

# def simulate_trades_with_stoploss_extended(entries_df, df_1min, expiry_dates,fetch_option_data_fn, create_symbol_format_fn, config):
#     print("--- Starting Trade Simulation ---")
#     trades = []
#     next_trade_start_time = None

#     for index, row in entries_df.iterrows():
#         print(f"[Entry {index+1}] Signal Time: {row['signal_time']} | Spot: {row['execution_open']:.2f}")
#         signal_time = row['execution_time']
#         if next_trade_start_time and signal_time <= next_trade_start_time:
#             continue
#         if signal_time.time() >= time(15, 0):
#             continue

#         entry_time = signal_time
#         entry_price = row['execution_open']
#         sl_price = entry_price * (1 - config['spot_sl_pct'])
#         target_pnl = config['max_profit_per_lot'] * config['lot_size']

#         execution_date = entry_time.date()
#         print(f"Entry Time: {entry_time} | Calculated SL: {sl_price:.2f} ")
#         try:
#             base_expiry_idx = expiry_dates[expiry_dates['expiry_date'] >= pd.to_datetime(execution_date).date()].index[0]
#             base_expiry = expiry_dates.iloc[base_expiry_idx]['expiry_date']
#             next_expiry = expiry_dates.iloc[base_expiry_idx + 1]['expiry_date'] if base_expiry_idx + 1 < len(expiry_dates) else base_expiry

#             # Get ATM-based strikes
#             strikes = get_option_strikes(entry_price, config)

#             # Prepare 100pt OTM PE sell strike for premium check
#             test_expiry = base_expiry
#             test_sell_leg = {
#                 'name': 'NIFTY',
#                 'expiry': str(test_expiry),
#                 'strike': strikes['sell_pe'],
#                 'instrument_type': 'PE'
#             }
#             test_sell_symbol, test_sell_date, test_sell_name = create_symbol_format_fn(test_sell_leg, str(execution_date))
#             test_sell_data = fetch_option_data_fn(test_sell_symbol, test_sell_date, test_sell_name)
#             test_sell_data['time'] = pd.to_datetime(test_sell_data['time'], format='%H:%M:%S').dt.time
#             test_sell_data = test_sell_data[test_sell_data['time'] > entry_time.time()]
#             test_sell_price = test_sell_data.iloc[3]['LTP']

#             # Premium condition check
#             if test_sell_price < config['min_premium']:
#                 print(f"Premium {test_sell_price:.2f} < {config['min_premium']} — Switching to next expiry.")
#                 valid_expiry = next_expiry
#             else:
#                 valid_expiry = base_expiry

#             strikes['valid_expiry'] = str(valid_expiry)

#             # Final legs with valid expiry
#             otm_buy = {'name': 'NIFTY', 'expiry': str(valid_expiry), 'strike': strikes['buy_pe'], 'instrument_type': 'PE'}
#             otm_sell = {'name': 'NIFTY', 'expiry': str(valid_expiry), 'strike': strikes['sell_pe'], 'instrument_type': 'PE'}
#             otm_buy_symbol, otm_buy_date, otm_buy_name = create_symbol_format_fn(otm_buy, str(execution_date))
#             otm_sell_symbol, otm_sell_date, otm_sell_name = create_symbol_format_fn(otm_sell, str(execution_date))

#             otm_buy_data = fetch_option_data_fn(otm_buy_symbol, otm_buy_date, otm_buy_name)
#             otm_sell_data = fetch_option_data_fn(otm_sell_symbol, otm_sell_date, otm_sell_name)

#             otm_buy_data['time'] = pd.to_datetime(otm_buy_data['time'], format='%H:%M:%S').dt.time
#             otm_sell_data['time'] = pd.to_datetime(otm_sell_data['time'], format='%H:%M:%S').dt.time
#             otm_buy_data = otm_buy_data[otm_buy_data['time'] > entry_time.time()]
#             otm_sell_data = otm_sell_data[otm_sell_data['time'] > entry_time.time()]

#             # Entry LTPs (3rd tick to simulate slippage)
#             buy_leg_entry_price = otm_buy_data.iloc[3]['LTP']
#             print(f"Buy PE Strike: {strikes['buy_pe']} | Entry Price: {buy_leg_entry_price:.2f}")
#             sell_leg_entry_price = otm_sell_data.iloc[3]['LTP']
#             print(f"Sell PE Strike: {strikes['sell_pe']} | Entry Price: {sell_leg_entry_price:.2f}")

            
#             future_data = df_1min[df_1min['date'] >= entry_time].head(1).copy()

#             minute_counter = 0
#             exit_time = exit_price = exit_reason = buy_leg_exit_price = sell_leg_exit_price = None

#             for _, candle in future_data.iterrows():
#                 print("======= candle =========",candle)
#                 if candle['date'].time() >= time(15, 30):
#                     continue
                
#                 spot = candle['close']

#                 # buy_row = otm_buy_data[otm_buy_data['time'] == candle['date'].time()]
#                 # sell_row = otm_sell_data[otm_sell_data['time'] == candle['date'].time()]

#                 buy_row = otm_buy_data[otm_buy_data['time'] >= candle['date'].time()].head(1)
#                 sell_row = otm_sell_data[otm_sell_data['time'] >= candle['date'].time()].head(1)


#                 if not buy_row.empty and not sell_row.empty:
#                     buy_ltp = buy_row.iloc[0]['LTP']
#                     sell_ltp = sell_row.iloc[0]['LTP']
#                     pnl = (sell_leg_entry_price - sell_ltp) - (buy_leg_entry_price - buy_ltp)
#                     pnl *= config['lot_size']
                    
                    
#                     if pnl >= target_pnl:
#                         print(f"[Exit - Target] Time: {candle['date']} | Spot: {spot:.2f} | PnL: {pnl:.2f}")
#                         exit_time, exit_price, exit_reason = candle['date'], spot, 'target_hit'
#                         buy_leg_exit_price, sell_leg_exit_price = buy_ltp, sell_ltp
#                         break
                    
#                 if candle['low'] <= sl_price:
#                     print(f"[Exit - Stop Loss] Time: {candle['date']} | Spot: {spot:.2f} <= SL: {sl_price:.2f}")
#                     exit_time, exit_price, exit_reason = candle['date'], sl_price, 'stop_loss'
#                     buy_leg_exit_price = buy_ltp if 'buy_ltp' in locals() else None
#                     sell_leg_exit_price = sell_ltp if 'sell_ltp' in locals() else None
#                     break
                
#                 minute_counter += 1
#                 if minute_counter >= config['max_hold']:
#                     print(f"[Exit - Max Hold] Time: {candle['date']} | Total Minutes: {minute_counter}")
#                     exit_time, exit_price, exit_reason = candle['date'], candle['close'], 'time_exit'
#                     buy_leg_exit_price = buy_ltp if 'buy_ltp' in locals() else None
#                     sell_leg_exit_price = sell_ltp if 'sell_ltp' in locals() else None
#                     break

#             trades.append({
#                 'signal_time': row['signal_time'],
#                 'entry_time': entry_time,
#                 'entry_price': entry_price,
#                 'exit_time': exit_time,
#                 'exit_price': exit_price,
#                 'exit_reason': exit_reason,
#                 'sl_price': sl_price,
#                 'pnl': pnl if 'pnl' in locals() else (exit_price - entry_price) * config['lot_size'],
#                 'expiry':str(valid_expiry),
#                 'opttype':'PE',
#                 'buy_leg_strike': strikes['buy_pe'],
#                 'sell_leg_strike': strikes['sell_pe'],
#                 'buy_leg_entry_price': buy_leg_entry_price,
#                 'sell_leg_entry_price': sell_leg_entry_price,
#                 'buy_leg_exit_price': buy_leg_exit_price,
#                 'sell_leg_exit_price': sell_leg_exit_price,
#                 'net_option_pnl': ((sell_leg_entry_price - sell_leg_exit_price) - (buy_leg_entry_price - buy_leg_exit_price)) * config['lot_size'] if buy_leg_exit_price is not None and sell_leg_exit_price is not None else None,
#             })
#             next_trade_start_time = exit_time + timedelta(minutes=1)

#         except Exception as e:
#             print("Error:", e)
#             continue

#     return pd.DataFrame(trades)





# # ---- Run Backtest ----
# historical_data_min_interval = fetch_max_data_zerodha(256265, start_date, end_date, timeframe)
# historical_data_1min = fetch_max_data_zerodha(256265, start_date, end_date, 'minute')
# df_signals = generate_signals(historical_data_min_interval, config)
# # print (df_signals.to_string())
# entries_df = match_signals_with_1min(df_signals)

# trades_df = simulate_trades_with_stoploss_extended(
#     entries_df,
#     historical_data_1min,
#     expiry_dates,
#     fetch_option_data_fn=fetch_csv_from_zip,
#     create_symbol_format_fn=create_symbol_format,
#     config=config
# )



# # Ensure "data" folder exists
# os.makedirs("data", exist_ok=True)
# # ---- Export ----
# fileName = f"""bull_credit_{timeframe}_ema_{ema}_rsi_threshold_{config['rsi_threshold']}_body_ratio_{config['body_ratio']}_spread_{config['spread']}_SL_{config['spot_sl_pct']}_maxhold_{config['max_hold']}_backtest_{year}.csv"""

# # Save file inside "data" folder
# file_path = os.path.join("data", fileName)
# trades_df.to_csv(file_path, index=False)

# print("--- Trade Simulation Complete ---",fileName)
# # print(trades_df[['signal_time', 'entry_time', 'exit_time', 'exit_reason', 'entry_price', 'exit_price', 'pnl','buy_leg_entry_price', 'sell_leg_entry_price', 'buy_leg_exit_price', 'sell_leg_exit_price', 'net_option_pnl']])


# # historical_data_1min = pd.DataFrame(
# #             kite.historical_data(256265, '2025-08-22', '2025-08-22', 'minute')
# #         )
# # historical_data_1min.to_csv('fridaydata.csv')
# # print(historical_data_1min)