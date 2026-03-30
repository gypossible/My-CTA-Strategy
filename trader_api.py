"""
实盘与模拟交易 API 基础接口 (Live Trading Paper Engine)
此层作为独立于历史回测系统的标准化发单流程接口，旨在为您策略后续上云或直接连接国内 CTP / VNPY 提供统一标准架构封装。
"""

class LiveTrader:
    def __init__(self, broker_name):
        self.broker = broker_name
        self.connected = False
        
    def connect(self):
        """连接行情或交易服务器"""
        pass
        
    def buy(self, symbol, price, volume):
        raise NotImplementedError
        
    def sell(self, symbol, price, volume):
        raise NotImplementedError


class SimulatedPaperTrader(LiveTrader):
    """
    轻量化的纸面模拟交易层（Paper Trading Engine）
    主要用于将回测产出的策略在本地实务环境以模拟撮合的方式运行发单。
    并记录一切下限资金（Capital）及流水。
    """
    def __init__(self, initial_capital=1000000.0):
        super().__init__("Simulated_Paper")
        self.capital = initial_capital
        self.positions = {}
        self.trade_logs = []
        
    def connect(self):
        self.connected = True
        print("[System API] Simulated Paper Trader 挂载连接已就绪。")
        
    def _execute(self, action, symbol, price, volume, msg=""):
        if not self.connected:
            raise Exception("致命错误: 在发送订单前，请首先调用 connect() ! ")
            
        cost = price * volume
        # 对模拟盘可用资金变动的简略结算 (不含保证金冻结测算)
        if action in ["BUY", "COVER"]:
            self.capital -= cost
        else:
            self.capital += cost
            
        log = f"{action} | {symbol} | 手数: {volume} | 成交价: {price} | 可用余资: ￥{self.capital:.2f} | {msg}"
        self.trade_logs.append(log)
        print(f"[{symbol} 订单引擎拦截] {log}")
        
    def buy(self, symbol, price, volume=1):
        """实务：买入开仓 (Take Long Entry)"""
        self._execute("BUY", symbol, price, volume, "建立多头底仓")
        self.positions[symbol] = self.positions.get(symbol, 0) + volume
        
    def sell(self, symbol, price, volume=1):
        """实务：卖出平仓 (Long Exit/StopLoss)"""
        if self.positions.get(symbol, 0) < volume:
            print(f"!! [风控拒单] 您在 {symbol} 上的多头持仓不足以平 {volume} 手")
            return
        self._execute("SELL", symbol, price, volume, "多头平仓落袋")
        self.positions[symbol] -= volume
        
    def short(self, symbol, price, volume=1):
        """实务：卖出开仓 (Take Short Entry)"""
        self._execute("SHORT", symbol, price, volume, "建立空单头寸")
        self.positions[symbol] = self.positions.get(symbol, 0) - volume
        
    def cover(self, symbol, price, volume=1):
        """实务：买入平仓 (Short Exit/StopLoss)"""
        if self.positions.get(symbol, 0) > -volume:
            print(f"!! [风控拒单] 您在 {symbol} 上的空头持仓极其不足以被 {volume} 手所掩盖")
            return
        self._execute("COVER", symbol, price, volume, "空单平仓落袋")
        self.positions[symbol] += volume
        
    def get_positions(self):
        return self.positions

    def get_trade_history(self):
        return self.trade_logs
