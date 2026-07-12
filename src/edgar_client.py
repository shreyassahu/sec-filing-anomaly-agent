import requests
import time
import os
from src.utils.format_accession_number import format_accession_number
from src.insert_filings_to_db import DBOperations

HEADERS = {"User-Agent": "sec-filing-anomaly-agent (shreyassahu2208@gmail.com)"}

class EdgarClient:
    def __init__(self):
        self.db = DBOperations()

    def generate_10k_accession_numbers(self, cik_no: str):
        try:
            response = requests.get(
                f"https://data.sec.gov/submissions/CIK{cik_no}.json",
                headers=HEADERS,
                timeout=30
            )

            if response.status_code == 200:
                cik, filings_10k = self.get_10k_filings(response)

                for filing in filings_10k:
                    accession_formatted = format_accession_number(filing['accessionNumber'])
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_formatted}/{filing['primaryDocument']}"

                    filing_html = self.download_filings(filing_url)

                    folder_path = f"data/filings/{cik_no}"
                    os.makedirs(folder_path, exist_ok=True)

                    file_path = f"{folder_path}/{filing['primaryDocument']}"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(filing_html)

                    print(f"Downloaded: {filing['primaryDocument']}")
                    time.sleep(0.15)
            
                self.db.insert_filings_to_db(cik_no, filings_10k, cik)


            else:
                print(f"Error: Received status code {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    # def retrive_cik_from_ticker(self, ticker: str):


    def download_filings(self, filing_url: str):
        response = requests.get(filing_url, headers=HEADERS, timeout=30)
        return response.text

    def get_10k_filings(self, response, num_filings: int = 3):
        data = response.json()
        cik = data['cik']

        # Start with recent filings
        results = self.extract_10k_from_filing_data(data['filings']['recent'])

        # If not enough, fetch overflow files
        if len(results) < num_filings:
            overflow_files = data['filings']['files']
            for file_info in overflow_files:
                if len(results) >= num_filings:
                    break
                time.sleep(0.15)
                overflow_response = requests.get(
                    f"https://data.sec.gov/submissions/{file_info['name']}",
                    headers=HEADERS,
                    timeout=30
                )
                overflow_data = overflow_response.json()
                results.extend(self.extract_10k_from_filing_data(overflow_data))

        return cik, results[:num_filings]



    def extract_10k_from_filing_data(self, filing_data):
        results = []
        forms = filing_data['form']
        for i in range(len(forms)):
            if forms[i] == '10-K':
                results.append({
                    'accessionNumber': filing_data['accessionNumber'][i],
                    'filingDate': filing_data['filingDate'][i],
                    'primaryDocument': filing_data['primaryDocument'][i]
                })
        return results




