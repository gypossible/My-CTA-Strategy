import os
import time
from data import fetch_futures_data
from strategy import DualEmaStrategy, RsiMeanReversionStrategy, TurtleTradingStrategy
from backtester import FuturesVectorBacktester
from metrics import get_performance_metrics
from reporter import generate_report

# 中国大陆主力连续合约乘数映射 (Multiplier Map)
MULTIPLIER_MAP = {
    "RB0": 10,   # 螺纹钢
    "I0": 100,   # 铁矿石
    "CU0": 5,    # 沪铜
    "TA0": 5,    # PTA
    "FG0": 20,   # 玻璃
    "M0": 10,    # 豆粕
    "SR0": 10,   # 白糖
    "MA0": 10,   # 甲醇
    "RM0": 10,   # 菜粕
    "AL0": 5,    # 沪铝
    "JM0": 60,   # 焦煤
    "C0": 10,    # 玉米
    "SA0": 20,   # 纯碱
    "HC0": 10,   # 热卷
    "Y0": 10,    # 豆油
    "P0": 10,    # 棕榈油
    "V0": 5,     # PVC
    "PP0": 5,    # 聚丙烯
    "AU0": 1000, # 沪金
    "AG0": 15    # 沪银
}

COMMODITY_NAMES = {
    "RB0": "工业品-螺纹钢",
    "I0": "黑色系-铁矿石",
    "CU0": "有色金属-沪铜",
    "TA0": "化工品-PTA",
    "FG0": "建材-玻璃",
    "M0": "农产品-豆粕",
    "SR0": "软商品-白糖",
    "MA0": "化工品-甲醇",
    "RM0": "农产品-菜粕",
    "AL0": "有色金属-沪铝",
    "JM0": "黑色系-焦煤",
    "C0": "农产品-玉米",
    "SA0": "化工品-纯碱",
    "HC0": "黑色系-热卷",
    "Y0": "油脂类-豆油",
    "P0": "油脂类-棕榈油",
    "V0": "化工品-PVC",
    "PP0": "化工品-PP",
    "AU0": "贵金属-沪金",
    "AG0": "贵金属-沪银"
}

def main():
    print("初始化 CNQuant 商品期货量化回测评估引擎 (V4)...")
    
    # 全局测试时间范围：横跨最新的 2026 年大波动期
    START_DATE = "2020-01-01"
    END_DATE = "2026-02-28"
    
    combinations = []
    symbols_to_test = list(MULTIPLIER_MAP.keys())
    
    for sym in symbols_to_test:
        mult = MULTIPLIER_MAP[sym]
        cname = COMMODITY_NAMES[sym]
        
        # 策略 1: 趋势跟随 (EMA升级版)
        combinations.append({
            "name": f"{cname}({sym}) - 趋势跟随", 
            "symbol": sym, 
            "strategy": DualEmaStrategy(short_window=10, long_window=30), 
            "multiplier": mult
        })
        # 策略 2: 震荡反转 (中轨保护优化版)
        combinations.append({
            "name": f"{cname}({sym}) - 震荡反转", 
            "symbol": sym, 
            "strategy": RsiMeanReversionStrategy(rsi_period=14, rsi_ob=70, rsi_os=30, bb_period=20, bb_std=2.0), 
            "multiplier": mult
        })
        # 策略 3: 海龟交易法则 (长趋势突破过滤版)
        combinations.append({
            "name": f"{cname}({sym}) - 海龟交易法则", 
            "symbol": sym, 
            "strategy": TurtleTradingStrategy(entry_window=20, exit_window=10, trend_filter_window=60), 
            "multiplier": mult
        })
    
    results = {}
    data_cache = {}
    
    for combo in combinations:
        sym = combo["symbol"]
        if sym not in data_cache:
            try:
                time.sleep(1)
                df_raw = fetch_futures_data(symbol=sym, start_date=START_DATE, end_date=END_DATE)
                data_cache[sym] = df_raw
            except Exception as e:
                print(f"[{sym}] 数据从 {START_DATE} 至 {END_DATE} 拉取失败，跳过: {e}")
                continue
                
        print(f"▶ 正在回测: {combo['name']} ... (应用合约乘数: {combo['multiplier']})")
        df_data = data_cache[sym].copy()
        
        strat = combo["strategy"]
        df_signals = strat.generate_signals(df_data)
        
        # 初始资金100万，佣金单边万一，滑点设置为1点损失
        bt = FuturesVectorBacktester(initial_capital=1000000.0, multiplier=combo["multiplier"], commission_rate=0.0001, slippage=1.0)
        df_result = bt.run(df_signals)
        
        metrics, drawdown = get_performance_metrics(df_result)
        
        results[combo["name"]] = {
            "df": df_result,
            "metrics": metrics,
            "drawdown": drawdown
        }
        
    print("\n✅ 回测引擎 (包含21组交叉对比) 执行完毕，正在生成全中文量化报告...")
    report_path = os.path.join(os.getcwd(), "reports", "backtest_report.html")
    generate_report(results, report_path)
    
    print(f"\n大功告成！报告位置请在浏览器中打开: file://{report_path}")

if __name__ == "__main__":
    main()
