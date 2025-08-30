# import pandas as pd
# from datetime import datetime, timedelta, time
# import json
# import traceback
# from typing import Dict, Any, List
# from bull_credit_final import (
#     fetch_max_data_zerodha, 
#     generate_signals, 
#     match_signals_with_1min,
#     simulate_trades_with_stoploss_extended,
#     load_expiry_dates_from_csv
# )
# from zip_read import fetch_csv_from_zip, create_symbol_format


# class BacktestService:
#     """Service class to handle backtest execution"""
    
#     def __init__(self):
#         self.default_config = {
#             'ema9': 9, 
#             'ema5': 5, 
#             'ema13': 13, 
#             'ema21': 21,
#             'ema34': 34, 
#             'sma40': 40,
#             'ema40': 40,
#             'sma45': 45,
#             'sma50': 50,
#             'sma100': 100,
#             'sma200': 200,
#             'sma300': 300,
#             'rsi14': 14,
#             'rsi_threshold': 50,
#             'body_ratio': 0.6,
#             'sell_otm': 0,
#             'spread': 200,
#             'lot_size': 50,
#             'max_profit_per_lot': 100,
#             'spot_sl_pct': 0.003,
#             'max_hold': 210,
#             'min_premium': 30,
#             'instrument_token': 256265,  # NIFTY token
#             'timeframe': '15minute'
#         }
    
#     def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
#         """Validate and merge config with defaults"""
#         validated_config = self.default_config.copy()
        
#         # Update with provided config
#         for key, value in config.items():
#             if key in validated_config:
#                 # Validate numeric fields
#                 if key in ['ema9', 'ema5', 'ema13', 'ema21', 'ema34', 'sma40', 'ema40', 
#                           'sma45', 'sma50', 'sma100', 'sma200', 'sma300', 'rsi14', 'lot_size',
#                           'max_profit_per_lot', 'max_hold', 'spread', 'sell_otm', 'min_premium']:
#                     validated_config[key] = int(value) if isinstance(value, (int, float)) else validated_config[key]
#                 elif key in ['rsi_threshold', 'body_ratio', 'spot_sl_pct']:
#                     validated_config[key] = float(value) if isinstance(value, (int, float)) else validated_config[key]
#                 elif key in ['timeframe']:
#                     if value in ['minute', '5minute', '15minute', 'day']:
#                         validated_config[key] = value
#                 else:
#                     validated_config[key] = value
        
#         return validated_config
    
#     def run_backtest(
#         self, 
#         strategy_config: Dict[str, Any], 
#         start_date: str, 
#         end_date: str,
#         progress_callback=None
#     ) -> Dict[str, Any]:
#         """
#         Run backtest with given parameters
        
#         Args:
#             strategy_config: Strategy configuration parameters
#             start_date: Start date in YYYY-MM-DD format
#             end_date: End date in YYYY-MM-DD format
#             progress_callback: Optional callback function for progress updates
            
#         Returns:
#             Dictionary containing backtest results
#         """
#         try:
#             # Validate configuration
#             config = self.validate_config(strategy_config)
            
#             if progress_callback:
#                 progress_callback("Validating configuration", 10)
            
#             # Load expiry dates
#             expiry_dates = load_expiry_dates_from_csv('files/expiry_dates.csv', start_date, end_date)
            
#             if progress_callback:
#                 progress_callback("Loading historical data", 20)
            
#             # Fetch historical data
#             historical_data_min_interval = fetch_max_data_zerodha(
#                 config['instrument_token'], 
#                 start_date, 
#                 end_date, 
#                 config['timeframe']
#             )
            
#             historical_data_1min = fetch_max_data_zerodha(
#                 config['instrument_token'], 
#                 start_date, 
#                 end_date, 
#                 'minute'
#             )
            
#             if progress_callback:
#                 progress_callback("Generating signals", 40)
            
#             # Generate signals
#             df_signals = generate_signals(historical_data_min_interval, config)
            
#             if progress_callback:
#                 progress_callback("Matching signals with 1min data", 60)
            
#             # Match signals with 1min data
#             entries_df = match_signals_with_1min(df_signals)
            
#             if progress_callback:
#                 progress_callback("Running trade simulation", 80)
            
#             # Simulate trades
#             trades_df = simulate_trades_with_stoploss_extended(
#                 entries_df,
#                 historical_data_1min,
#                 expiry_dates,
#                 fetch_option_data_fn=fetch_csv_from_zip,
#                 create_symbol_format_fn=create_symbol_format,
#                 config=config
#             )
            
#             if progress_callback:
#                 progress_callback("Calculating results", 95)
            
#             # Calculate results
#             results = self.calculate_backtest_metrics(trades_df, config)
            
#             if progress_callback:
#                 progress_callback("Complete", 100)
            
#             return results
            
#         except Exception as e:
#             error_msg = f"Backtest execution failed: {str(e)}"
#             traceback.print_exc()
#             return {
#                 'success': False,
#                 'error': error_msg,
#                 'total_trades': 0,
#                 'winning_trades': 0,
#                 'losing_trades': 0,
#                 'win_rate': 0.0,
#                 'total_pnl': 0.0,
#                 'max_drawdown': 0.0,
#                 'sharpe_ratio': 0.0,
#                 'trades': []
#             }
    
#     def calculate_backtest_metrics(self, trades_df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
#         """Calculate backtest performance metrics"""
#         if trades_df.empty:
#             return {
#                 'success': False,
#                 'error': 'No trades generated',
#                 'total_trades': 0,
#                 'winning_trades': 0,
#                 'losing_trades': 0,
#                 'win_rate': 0.0,
#                 'total_pnl': 0.0,
#                 'max_drawdown': 0.0,
#                 'sharpe_ratio': 0.0,
#                 'trades': []
#             }
        
#         # Basic metrics
#         total_trades = len(trades_df)
        
#         # Use net_option_pnl if available, otherwise use pnl
#         pnl_column = 'net_option_pnl' if 'net_option_pnl' in trades_df.columns else 'pnl'
#         trades_df[pnl_column] = pd.to_numeric(trades_df[pnl_column], errors='coerce').fillna(0)
        
#         winning_trades = len(trades_df[trades_df[pnl_column] > 0])
#         losing_trades = len(trades_df[trades_df[pnl_column] < 0])
#         win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
#         # PnL calculations
#         total_pnl = trades_df[pnl_column].sum()
        
#         # Calculate cumulative PnL for drawdown
#         trades_df['cumulative_pnl'] = trades_df[pnl_column].cumsum()
        
#         # Calculate maximum drawdown
#         running_max = trades_df['cumulative_pnl'].cummax()
#         drawdown = trades_df['cumulative_pnl'] - running_max
#         max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0.0
        
#         # Calculate Sharpe ratio (simplified version)
#         if len(trades_df) > 1:
#             returns = trades_df[pnl_column]
#             sharpe_ratio = returns.mean() / returns.std() if returns.std() != 0 else 0.0
#         else:
#             sharpe_ratio = 0.0
        
#         # Prepare trades data for response
#         trades_list = []
#         for _, trade in trades_df.iterrows():
#             trade_dict = {
#                 'signal_time': trade['signal_time'].isoformat() if pd.notna(trade['signal_time']) else None,
#                 'entry_time': trade['entry_time'].isoformat() if pd.notna(trade['entry_time']) else None,
#                 'exit_time': trade['exit_time'].isoformat() if pd.notna(trade['exit_time']) else None,
#                 'entry_price': float(trade['entry_price']) if pd.notna(trade['entry_price']) else 0.0,
#                 'exit_price': float(trade['exit_price']) if pd.notna(trade['exit_price']) else 0.0,
#                 'pnl': float(trade[pnl_column]) if pd.notna(trade[pnl_column]) else 0.0,
#                 'exit_reason': trade['exit_reason'] if pd.notna(trade['exit_reason']) else None,
#                 'buy_leg_strike': int(trade['buy_leg_strike']) if pd.notna(trade['buy_leg_strike']) else 0,
#                 'sell_leg_strike': int(trade['sell_leg_strike']) if pd.notna(trade['sell_leg_strike']) else 0,
#                 'buy_leg_entry_price': float(trade['buy_leg_entry_price']) if pd.notna(trade['buy_leg_entry_price']) else 0.0,
#                 'sell_leg_entry_price': float(trade['sell_leg_entry_price']) if pd.notna(trade['sell_leg_entry_price']) else 0.0,
#                 'buy_leg_exit_price': float(trade['buy_leg_exit_price']) if pd.notna(trade['buy_leg_exit_price']) else 0.0,
#                 'sell_leg_exit_price': float(trade['sell_leg_exit_price']) if pd.notna(trade['sell_leg_exit_price']) else 0.0,
#             }
#             trades_list.append(trade_dict)
        
#         return {
#             'success': True,
#             'total_trades': int(total_trades),
#             'winning_trades': int(winning_trades),
#             'losing_trades': int(losing_trades),
#             'win_rate': round(win_rate, 2),
#             'total_pnl': round(total_pnl, 2),
#             'max_drawdown': round(max_drawdown, 2),
#             'sharpe_ratio': round(sharpe_ratio, 3),
#             'average_profit': round(trades_df[trades_df[pnl_column] > 0][pnl_column].mean(), 2) if winning_trades > 0 else 0.0,
#             'average_loss': round(trades_df[trades_df[pnl_column] < 0][pnl_column].mean(), 2) if losing_trades > 0 else 0.0,
#             'max_profit': round(trades_df[pnl_column].max(), 2),
#             'max_loss': round(trades_df[pnl_column].min(), 2),
#             'profit_factor': round(
#                 abs(trades_df[trades_df[pnl_column] > 0][pnl_column].sum() / 
#                     trades_df[trades_df[pnl_column] < 0][pnl_column].sum()), 2
#             ) if losing_trades > 0 and trades_df[trades_df[pnl_column] < 0][pnl_column].sum() != 0 else 0.0,
#             'trades': trades_list[:100]  # Limit to first 100 trades for API response
#         }
    
#     def get_default_strategy_templates(self) -> List[Dict[str, Any]]:
#         """Get predefined strategy templates"""
#         templates = [
#             {
#                 'name': 'Conservative Bull Credit Spread',
#                 'description': 'Conservative bull credit spread with tight stop loss',
#                 'config': {
#                     'ema9': 9,
#                     'ema21': 21,
#                     'sma200': 200,
#                     'rsi14': 14,
#                     'rsi_threshold': 55,
#                     'body_ratio': 0.7,
#                     'sell_otm': 50,
#                     'spread': 150,
#                     'lot_size': 25,
#                     'max_profit_per_lot': 75,
#                     'spot_sl_pct': 0.002,
#                     'max_hold': 120,
#                     'min_premium': 25,
#                     'timeframe': '15minute'
#                 }
#             },
#             {
#                 'name': 'Aggressive Bull Credit Spread',
#                 'description': 'Aggressive strategy with wider spreads and higher risk',
#                 'config': {
#                     'ema9': 9,
#                     'ema21': 21,
#                     'sma200': 200,
#                     'rsi14': 14,
#                     'rsi_threshold': 45,
#                     'body_ratio': 0.5,
#                     'sell_otm': 0,
#                     'spread': 250,
#                     'lot_size': 75,
#                     'max_profit_per_lot': 150,
#                     'spot_sl_pct': 0.005,
#                     'max_hold': 300,
#                     'min_premium': 35,
#                     'timeframe': '15minute'
#                 }
#             },
#             {
#                 'name': 'Intraday Scalping',
#                 'description': 'Quick intraday trades with tight parameters',
#                 'config': {
#                     'ema9': 5,
#                     'ema21': 13,
#                     'sma200': 100,
#                     'rsi14': 14,
#                     'rsi_threshold': 60,
#                     'body_ratio': 0.8,
#                     'sell_otm': 25,
#                     'spread': 100,
#                     'lot_size': 50,
#                     'max_profit_per_lot': 50,
#                     'spot_sl_pct': 0.001,
#                     'max_hold': 60,
#                     'min_premium': 20,
#                     'timeframe': '5minute'
#                 }
#             }
#         ]
        
#         return templates


# # Global service instance
# backtest_service = BacktestService()
