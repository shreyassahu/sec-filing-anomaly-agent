from src.insert_filings_to_db import DBOperations
from src.ingest import IngestPipeline

import requests


HEADERS = {"User-Agent": "sec-filing-anomaly-agent (shreyassahu2208@gmail.com)"}

from langchain.tools import tool
@tool
def edgar_api(ticker: str):
    """
    Fetch and ingest the latest 3 years of 10-K filings from SEC EDGAR for a company
    not yet in the database. Takes a stock ticker (e.g., 'TSLA'), resolves it to a CIK,
    downloads filings, parses financial metrics, and stores them in the database.
    Only use this when postgres_query returns no data for the requested company.
    """

    db = DBOperations()
    ingest = IngestPipeline()

    ## Check if company already exists — return early instead of nesting
    ciks = db.retrieve_cik_from_company_ticker(ticker)

    cik = ""
    if ciks and len(ciks) >= 1:
        cik = ciks[0][0]

    if cik:
        return {"status": "success", "message": f"{ticker} already exists in database (CIK: {cik})"}

    try:
        response = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            return {"status": "error", "message": f"Failed to fetch company tickers: status {response.status_code}"}

        data = response.json()
        match = next((v for v in data.values() if v["ticker"].upper() == ticker.upper()), None)

        if not match:
            return {"status": "error", "message": f"Couldn't find CIK for ticker: {ticker}."}

        cik = str(match["cik_str"]).zfill(10)
        name = match["title"]
        ticker = match["ticker"]
        sic = ""
        sector = ""

        sic_response = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=HEADERS,
            timeout=30
        )

        if sic_response.status_code == 200:
            sic_data = sic_response.json()
            if sic_data:
                sic = sic_data.get("sic", "")
                sector = sic_data.get("sicDescription", "")

        db.seed_company(cik, name, ticker, sector, sic)
        ingest.run([cik], True)

        return {"status": "success", "message": f"Ingested filings for {ticker} (CIK: {cik}, {name})"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Ingestion failed: {str(e)}"}

if __name__ == "__main__":
    edgar_api("TSLA")
