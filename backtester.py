import pandas as pd
import numpy as np

class FuturesVectorBacktester:
    def __init__(self, initial_capital=100000.0, multiplier=10.0, margin_rate=0.1, commission_rate=0.0001, slippage=1.0):
        self.initial_capital = initial_capital
        self.multiplier = multiplier
        self.margin_rate = margin_rate
        self.commission_rate = commission_rate
        self.slippage = slippage
        
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        data['Price_Diff'] = data['Close'].diff().fillna(0)
        
        data['Daily_PnL'] = data['Position'] * data['Price_Diff'] * self.multiplier
        
        data['Trade'] = data['Position'].diff().fillna(0)
        
        data['Commission'] = np.abs(data['Trade']) * data['Close'] * self.multiplier * self.commission_rate
        data['Slippage'] = np.abs(data['Trade']) * self.slippage * self.multiplier
        
        data['Net_Daily_PnL'] = data['Daily_PnL'] - data['Commission'] - data['Slippage']
        
        data['Equity_Curve'] = self.initial_capital + data['Net_Daily_PnL'].cumsum()
        
        data['Market_PnL'] = data['Price_Diff'] * self.multiplier
        data['Market_Equity_Curve'] = self.initial_capital + data['Market_PnL'].cumsum()
        
        return data
