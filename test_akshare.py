import akshare as ak

print("Fetching Rebar (RB) main continuous...")
try:
    # 螺纹钢主连 RB0
    # Try using futures_zh_daily_sina which works well for continuous Sina data
    df = ak.futures_zh_daily_sina(symbol="RB0")
    print(df.tail())
except Exception as e:
    print("Error with futures_zh_daily_sina RB0:", e)

print("Fetching Soybean meal (M) main continuous...")
try:
    # 豆粕主连 M0
    df_m = ak.futures_zh_daily_sina(symbol="M0")
    print(df_m.tail())
except Exception as e:
    print("Error with futures_zh_daily_sina M0:", e)
