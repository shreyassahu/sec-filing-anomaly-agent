from src.insert_filings_to_db import DBOperations

from langchain.tools import tool
@tool
def anomaly_detector(ticker: str, fiscal_year: int=None):
    """
    Compare financial metrics for the given fiscal year against the prior year
    for a specific company. Flags any metric with a year-over-year change
    exceeding 15%. Returns flagged anomalies with the metric name, both values,
    percentage change, and severity level.
    """

    db = DBOperations()
    ## Retrieve cik from company ticker
    ciks = db.retrieve_cik_from_company_ticker(ticker)

    cik = ""
    if ciks and len(ciks) >= 1:
        cik = ciks[0][0]

    if len(cik) == 0:
        return {"status": "error", "message": f"No company found for ticker '{ticker}'"}
    

    ## Retrieve financial metrics from company cik

    fiscal_years = []

    if fiscal_year:
        fiscal_years = [fiscal_year - 1, fiscal_year]
    else:
        fiscal_years = None

    rows = db.retrieve_metrics_for_company(cik, fiscal_years)


    results = []

    for row in rows:
        results.append({
            "ticker": row[0],
            "metric_name": row[2],
            "fiscal_year": row[3],
            "value": float(row[4])
    })
        
    metrics_year_value_dict = {}



    for result in results:
        metric_name = result["metric_name"]
        fiscal_year = result["fiscal_year"]
        metric_value = result["value"]

        if metric_name not in metrics_year_value_dict:
            metrics_year_value_dict[metric_name] = {}
        
        metrics_year_value_dict[metric_name][fiscal_year] = metric_value

    
    anomalies = []

    for metric_name, year_values in metrics_year_value_dict.items():
        sorted_years = sorted(year_values.keys())
        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            previous_year = sorted_years[i - 1]
            current_value = year_values[current_year]
            previous_value = year_values[previous_year]

            if previous_value == 0:
                continue

            pct_change = ((current_value - previous_value) / abs(previous_value)) * 100

            if abs(pct_change) > 15:
                if current_year < 2023:
                    continue
                anomalies.append({
                    "metric_name": metric_name,
                    "current_year": current_year,
                    "previous_year": previous_year,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "pct_change": round(pct_change, 2)
            })
                

    if not anomalies:
        return {"status": "success", "message": "No anomalies detected above 15% threshold", "anomalies": []}

    return {"status": "success", "anomalies": anomalies}


if __name__ == "__main__":
    print(anomaly_detector("AAPL"))