import pandas as pd
import numpy as np

class BaseStrategy:
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

class DualEmaStrategy(BaseStrategy):
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        # Use EMA for faster response instead of SMA
        data['EMA_Short'] = data['Close'].ewm(span=self.short_window, adjust=False).mean()
        data['EMA_Long'] = data['Close'].ewm(span=self.long_window, adjust=False).mean()
        
        data['Signal'] = 0.0
        diff = data['EMA_Short'] - data['EMA_Long']
        
        # When diff > 0, EMA_Short is above EMA_Long -> Long signal
        # When diff < 0, EMA_Short is below EMA_Long -> Short signal
        signal_array = np.where(diff > 0, 1.0, np.where(diff < 0, -1.0, 0.0))
        data['Signal'] = signal_array
        
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
        
        # Mean Reversion touch exit protection (止盈逻辑：碰均线即离场)
        exit_long_cond = data['Close'] >= data['BB_MA']
        exit_short_cond = data['Close'] <= data['BB_MA']
        
        positions = np.zeros(len(data))
        current_pos = 0
        
        for i in range(len(data)):
            # Entry and Exit logic evaluated chronologically
            if current_pos == 0:
                if buy_cond.iloc[i]:
                    current_pos = 1
                elif sell_cond.iloc[i]:
                    current_pos = -1
            elif current_pos == 1:
                # If we hit sell conditions or our moving average exit for mean reversion
                if sell_cond.iloc[i]:
                    current_pos = -1
                elif exit_long_cond.iloc[i]:
                    current_pos = 0
            elif current_pos == -1:
                # If we hit buy conditions or our moving average exit
                if buy_cond.iloc[i]:
                    current_pos = 1
                elif exit_short_cond.iloc[i]:
                    current_pos = 0
                    
            positions[i] = current_pos
            
        data['Signal'] = positions
        data['Position'] = data['Signal'].shift(1).fillna(0)
        return data

class TurtleTradingStrategy(BaseStrategy):
    """
    海龟交易法则 (强化优化版)：
    新增长期均线趋势过滤器 (Trend Filter)。
    只有当价格高于长线SMA时才允许做多；只有低于长线SMA时才允许做空。这有效阻止了逆势做单引发的假突破。
    """
    def __init__(self, entry_window=20, exit_window=10, trend_filter_window=60):
        self.entry_window = entry_window
        self.exit_window = exit_window
        self.trend_filter_window = trend_filter_window
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        
        data['Highest_20'] = data['High'].shift(1).rolling(window=self.entry_window).max()
        data['Lowest_20'] = data['Low'].shift(1).rolling(window=self.entry_window).min()
        
        data['Highest_10'] = data['High'].shift(1).rolling(window=self.exit_window).max()
        data['Lowest_10'] = data['Low'].shift(1).rolling(window=self.exit_window).min()
        
        # 趋势过滤器 Trend Filter
        data['Trend_SMA'] = data['Close'].shift(1).rolling(window=self.trend_filter_window).mean()
        
        positions = np.zeros(len(data))
        current_pos = 0
        
        close = data['Close'].values
        h20 = data['Highest_20'].values
        l20 = data['Lowest_20'].values
        h10 = data['Highest_10'].values
        l10 = data['Lowest_10'].values
        trend_sma = data['Trend_SMA'].values
        
        for i in range(len(data)):
            if pd.isna(h20[i]) or pd.isna(l20[i]) or pd.isna(trend_sma[i]):
                positions[i] = 0
                continue
                
            # 入场逻辑 (具备趋势过滤)
            if current_pos == 0:
                if close[i] > h20[i] and close[i] > trend_sma[i]:
                    current_pos = 1
                elif close[i] < l20[i] and close[i] < trend_sma[i]:
                    current_pos = -1
                    
            # 持有多头逻辑
            elif current_pos == 1:
                if close[i] < l10[i]:
                    current_pos = 0   # 多头止盈/止损离场
                if close[i] < l20[i] and close[i] < trend_sma[i]:
                    current_pos = -1  # 反转极弱势，反手空头 (附带空头趋势确认)
                    
            # 持有空头逻辑
            elif current_pos == -1:
                if close[i] > h10[i]:
                    current_pos = 0   # 空头止盈/止损离场
                if close[i] > h20[i] and close[i] > trend_sma[i]:
                    current_pos = 1   # 反转极强势，反手多头 (附带多头趋势确认)
                    
            positions[i] = current_pos
            
        data['Signal'] = positions
        data['Position'] = data['Signal'].shift(1).fillna(0)
        return data
