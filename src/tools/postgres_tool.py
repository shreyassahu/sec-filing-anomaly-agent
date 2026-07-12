from src.insert_filings_to_db import DBOperations


from langchain.tools import tool
@tool
def postgres_query(ticker: str, fiscal_years: list = None, metric_names: list = None):
    """
    Fetch financial metrics from the database for a specific company.
    Returns revenue, net_income, operating_income, total_debt, and stockholders_equity.
    If fiscal_year is provided, returns metrics for that year only.
    If metric_name is provided, returns only that metric across available years.
    If neither is provided, returns all metrics for all available years.
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

    rows = db.retrieve_metrics_for_company(cik, fiscal_years, metric_names)

    results = []
    for row in rows:
        results.append({
            "ticker": row[0],
            "metric_name": row[2],
            "fiscal_year": row[3],
            "value": float(row[4])
    })

    if not rows or len(rows) == 0:
        return {"status": "error", "message": f"No metrics found for the passed input"}
    
    return {"status": "success", "results": results}


    






# if __name__ == "__main__":
#     postgres_query("AAPL", [2024, 2025], ["net_income", "operating_income", "revenue"])