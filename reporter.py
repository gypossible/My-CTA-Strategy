import os
import json
from jinja2 import Environment, FileSystemLoader

def generate_report(results, output_path="reports/backtest_report.html"):
    """
    results: dict of { "Identifier": { "df": df, "metrics": metrics, "drawdown": drawdown } }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report.html")
    
    chart_data = {
        "dates": [],
        "strategies": {}
    }
    
    first_key = list(results.keys())[0]
    chart_data["dates"] = list(results[first_key]["df"].index.strftime("%Y-%m-%d"))
    
    for name, data_pkg in results.items():
        df = data_pkg["df"]
        drawdown_pct = data_pkg["drawdown"].fillna(0) * 100
        
        chart_data["strategies"][name] = {
            "equity": list(df["Equity_Curve"].fillna(0).round(2)),
            "market": list(df["Market_Equity_Curve"].fillna(0).round(2)),
            "drawdown": list(drawdown_pct.round(2)),
            "metrics": data_pkg["metrics"],
            "title": name
        }
        
    html_content = template.render(chart_data=json.dumps(chart_data), keys=list(results.keys()))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Report successfully generated at {output_path}")
