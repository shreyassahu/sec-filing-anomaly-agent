import os

from insert_filings_to_db import DBOperations
from rag_pipeline import RAGPipeline
from html_parser import HTMLParser
from extract_section import ExtractSection
from edgar_client import EdgarClient


FILINGS_DIR = "data/filings"

# CLAUDE.md target companies
COMPANY_CIKS = [
    "0000320193",  # AAPL
    "0000019617",  # JPM
    "0000789019",  # MSFT
    "0000034088",  # XOM
    "0000200406",  # JNJ
]

SECTIONS = ["mda", "risk_factors"]


class IngestPipeline:
    def __init__(self):
        self.db = DBOperations()
        self.rag = RAGPipeline()
        self.sections = ExtractSection()
        self.edgar_client = EdgarClient()

    def download_filings(self, cik_list):
        for company_cik in cik_list:
            self.edgar_client.generate_10k_accession_numbers(company_cik)

    def _primary_fiscal_year(self, metrics):
        """A filing's reporting year = the most recent year across its metrics.

        period_of_report is not stored, so derive it from the parsed XBRL years.
        Prefer income-statement metrics (3 years) over balance-sheet ones.
        """
        for metric_name in ("revenue", "net_income", "operating_income", "stockholders_equity", "total_debt"):
            years = metrics.get(metric_name)
            if years:
                return max(int(y) for y in years)
        return None

    def _extract_section_text(self, section_name, file_path):
        if section_name == "mda":
            return self.sections.extract_md_a(file_path)
        return self.sections.extract_risk_factors(file_path)

    def run(self, cik_list, download=True):
        if download:
            self.download_filings(cik_list)

        for cik in sorted(os.listdir(FILINGS_DIR)):
            cik_path = os.path.join(FILINGS_DIR, cik)
            if not os.path.isdir(cik_path):
                continue

            file_to_id = self.db.retrieve_filing_ids_from_cik(cik)

            for filename in sorted(os.listdir(cik_path)):
                if not filename.endswith(".htm"):
                    continue

                file_path = os.path.join(cik_path, filename)
                filing_id = file_to_id.get(filename)
                if filing_id is None:
                    print(f"[skip] no filing_id for {cik}/{filename} (not in DB)")
                    continue

                print(f"[filing] {cik}/{filename} (id={filing_id})")

                # 1. Metrics -> Postgres
                parser = HTMLParser(file_path)
                metrics = parser.extract_all_metrics()
                self.db.insert_metrics_to_db(filing_id, metrics)

                fiscal_year = self._primary_fiscal_year(metrics)
                if fiscal_year is None:
                    print(f"  [warn] no fiscal year derivable; skipping RAG for {filename}")
                    continue

                # 2. Narrative sections -> ChromaDB
                for section_name in SECTIONS:
                    text = self._extract_section_text(section_name, file_path)
                    self.rag.ingest_section(cik, fiscal_year, section_name, text, filing_id)

        self.db.close()
        print(f"[done] ChromaDB now holds {self.rag.collectionMda.count()} chunks")


if __name__ == "__main__":
    pipeline = IngestPipeline()
    # Filings are already downloaded and filing rows are in Postgres,
    # so default to download=False for a fast metrics + RAG re-ingest.
    # pipeline.run(COMPANY_CIKS, download=False)

    print(pipeline.rag.query("What drove Apple's revenue growth in 2023?", 
                       where={"$and": [{"cik": "0000320193"}, {"fiscal_year": 2023}]}))