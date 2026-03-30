import pandas as pd
import numpy as np

class BaseStrategy:
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

class DualMovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window=20, long_window=60):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data['SMA_Short'] = data['Close'].rolling(window=self.short_window).mean()
        data['SMA_Long'] = data['Close'].rolling(window=self.long_window).mean()
        
        data['Signal'] = 0.0
        valid_idx = self.long_window
        
        diff = data['SMA_Short'].iloc[valid_idx:] - data['SMA_Long'].iloc[valid_idx:]
        signal_array = np.where(diff > 0, 1.0, np.where(diff < 0, -1.0, 0.0))
        data.loc[data.index[valid_idx:], 'Signal'] = signal_array
        
        data['Position'] = data['Signal'].shift(1).fillna(0)
        return data

class RsiMeanReversionStrategy(BaseStrategy):
    def __init__(self, rsi_period=14, rsi_ob=70, rsi_os=30, bb_period=20, bb_std=2.0):
        self.rsi_period = rsi_period
        self.rsi_ob = rsi_ob
        self.rsi_os = rsi_os
        self.bb_period = bb_period
        self.bb_std = bb_std
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        data['BB_MA'] = data['Close'].rolling(window=self.bb_period).mean()
        data['BB_Std'] = data['Close'].rolling(window=self.bb_period).std()
        data['BB_Upper'] = data['BB_MA'] + (data['BB_Std'] * self.bb_std)
        data['BB_Lower'] = data['BB_MA'] - (data['BB_Std'] * self.bb_std)
        
        buy_cond = (data['RSI'] < self.rsi_os) & (data['Close'] < data['BB_Lower'])
        sell_cond = (data['RSI'] > self.rsi_ob) & (data['Close'] > data['BB_Upper'])
        
        positions = np.zeros(len(data))
        current_pos = 0
        
        for i in range(len(data)):
            if buy_cond.iloc[i]:
                current_pos = 1
            elif sell_cond.iloc[i]:
                current_pos = -1
            positions[i] = current_pos
            
        data['Signal'] = positions
        data['Position'] = data['Signal'].shift(1).fillna(0)
        return data

class TurtleTradingStrategy(BaseStrategy):
    """
    海龟交易法则 (Turtle Trading System 1 核心版)：
    主要利用唐奇安通道（Donchian Channel）的 N 日高低点进行破位突破验证。
    多头长线入场：当价格突破过去 20 日的最高点，建立多头头寸。
    空头短线入场：当价格跌破过去 20 日的最低点，建立空头头寸。
    做多止盈离场：当价格跌破过去 10 日的最低点，多头平仓。
    做空止盈离场：当价格突破过去 10 日的最高点，空头平仓。
    """
    def __init__(self, entry_window=20, exit_window=10):
        self.entry_window = entry_window
        self.exit_window = exit_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        # 避免未来数据：用 shift(1) 寻找过去的最高/最低点
        data['Highest_20'] = data['High'].shift(1).rolling(window=self.entry_window).max()
        data['Lowest_20'] = data['Low'].shift(1).rolling(window=self.entry_window).min()
        
        data['Highest_10'] = data['High'].shift(1).rolling(window=self.exit_window).max()
        data['Lowest_10'] = data['Low'].shift(1).rolling(window=self.exit_window).min()
        
        positions = np.zeros(len(data))
        current_pos = 0
        
        close = data['Close'].values
        h20 = data['Highest_20'].values
        l20 = data['Lowest_20'].values
        h10 = data['Highest_10'].values
        l10 = data['Lowest_10'].values
        
        for i in range(len(data)):
            if pd.isna(h20[i]) or pd.isna(l20[i]):
                positions[i] = 0
                continue
                
            # 入场逻辑
            if current_pos == 0:
                if close[i] > h20[i]:
                    current_pos = 1
                elif close[i] < l20[i]:
                    current_pos = -1
                    
            # 持有多头逻辑
            elif current_pos == 1:
                if close[i] < l10[i]:
                    current_pos = 0   # 多头离场
                if close[i] < l20[i]:
                    current_pos = -1  # 反转极弱势，甚至反手空头
                    
            # 持有空头逻辑
            elif current_pos == -1:
                if close[i] > h10[i]:
                    current_pos = 0   # 空头离场
                if close[i] > h20[i]:
                    current_pos = 1   # 反转极强势，反手多头
                    
            positions[i] = current_pos
            
        data['Signal'] = positions
        data['Position'] = data['Signal'].shift(1).fillna(0)
        return data
