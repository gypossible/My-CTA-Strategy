import akshare as ak
import pandas as pd
import sys

def fetch_futures_data(symbol="RB0", start_date="2020-01-01", end_date="2023-12-31") -> pd.DataFrame:
    """Fetch daily continuous futures data using AkShare."""
    print(f"Fetching futures data for '{symbol}'...")
    try:
        df = ak.futures_zh_daily_sina(symbol=symbol)
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        df.sort_index(inplace=True)
        mask = (df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))
        df = df.loc[mask]
        
        if df.empty:
            raise ValueError(f"No data fetched for {symbol} within date range")
            
        print(f"Successfully fetched {len(df)} records for {symbol}.")
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        sys.exit(1)
