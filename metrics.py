import pandas as pd
import numpy as np

def calculate_drawdown(equity_series: pd.Series):
    """
    回撤框架：基于带杠杆和保证金变化的净资产变动
    某点的回撤 = (该点净值 - 该点之前的历史最高净值) / 历史最高净值
    """
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    if max_drawdown == 0.0 or pd.isna(max_drawdown):
        return drawdown, 0.0, None, None
        
    mdd_bottom_idx = drawdown.idxmin()
    mdd_peak_idx = equity_series.loc[:mdd_bottom_idx].idxmax()
    return drawdown, max_drawdown, mdd_peak_idx, mdd_bottom_idx

def get_performance_metrics(df: pd.DataFrame):
    if len(df) <= 1:
        return {}, pd.Series()
    
    equity = df['Equity_Curve']
    pnl = df['Net_Daily_PnL']
    returns = pnl / equity.shift(1).fillna(equity.iloc[0])
    
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    years = len(df) / 242.0
    annual_return = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1
    
    # 波动率
    volatility = returns.std() * np.sqrt(242)
    
    risk_free_rate = 0.02
    daily_rf = risk_free_rate / 242.0
    std_dev = returns.std()
    
    # Sharpe Ratio
    sharpe_ratio = np.sqrt(242) * (returns.mean() - daily_rf) / std_dev if std_dev != 0 and not pd.isna(std_dev) else 0
    
    # Sortino Ratio
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    sortino_ratio = np.sqrt(242) * (returns.mean() - daily_rf) / downside_std if not pd.isna(downside_std) and downside_std != 0 else 0
    
    # Max Drawdown
    drawdown, max_drawdown, peak_dt, bottom_dt = calculate_drawdown(equity)
    
    # Calmar Ratio
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 and not pd.isna(max_drawdown) else 0
    
    # Profit Factor (盈亏比 = 总盈利 / 总亏损)
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    if profit_factor == float('inf'):
        pf_str = "无亏超神"
    else:
        pf_str = f"{profit_factor:.2f}"
    
    # Win Rate
    holding_days = df[df['Position'] != 0.0]
    win_days = holding_days[holding_days['Net_Daily_PnL'] > 0]
    win_rate = len(win_days) / len(holding_days) if len(holding_days) > 0 else 0
    
    # Trades
    trades = max(int(abs(df['Trade']).sum() / 2), 0)
    
    metrics = {
        "累计收益率": f"{total_return:.2%}",
        "年化收益率": f"{annual_return:.2%}",
        "最大回撤": f"{max_drawdown:.2%}",
        "卡玛比率 (Calmar)": f"{calmar_ratio:.2f}",
        "夏普比率 (Sharpe)": f"{sharpe_ratio:.2f}",
        "索提诺比率 (Sortino)": f"{sortino_ratio:.2f}",
        "盈亏比 (Profit Factor)": pf_str,
        "年化波动率": f"{volatility:.2%}",
        "资金胜率": f"{win_rate:.2%}",
        "总交易回合": trades,
        "回撤顶峰日": str(peak_dt.date()) if pd.notna(peak_dt) else "-",
        "回撤深谷日": str(bottom_dt.date()) if pd.notna(bottom_dt) else "-"
    }
    return metrics, drawdown
