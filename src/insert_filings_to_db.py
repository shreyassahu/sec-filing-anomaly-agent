import psycopg2
from utils.format_accession_number import format_accession_number


class DBOperations:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5433,
            dbname="sec_agent",
            user="agent",
            password="changeme"
        )

    def retrieve_filing_ids_from_cik(self, cik_no):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, raw_url FROM filings WHERE cik = %s
        """, (cik_no,))
        rows = cursor.fetchall()
        file_to_id = {}
        for row in rows:
            url_filename = row[1].split("/")[-1]
            file_to_id[url_filename] = row[0]
        cursor.close()
        return file_to_id

    def insert_filings_to_db(self, cik_no, filings_10k, cik):
        cursor = self.conn.cursor()
        for filing in filings_10k:
            accession_formatted = format_accession_number(filing['accessionNumber'])
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_formatted}/{filing['primaryDocument']}"
            cursor.execute("""
                INSERT INTO filings (cik, accession_number, filing_type, filed_date, raw_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (accession_number) DO NOTHING
            """, (
                cik_no,
                filing['accessionNumber'],
                '10-K',
                filing['filingDate'],
                filing_url
            ))
        self.conn.commit()
        cursor.close()

    def insert_metrics_to_db(self, filing_id, metrics):
        cursor = self.conn.cursor()
        for metric_name, year_values in metrics.items():
            for year, value in year_values.items():
                cursor.execute("""
                    INSERT INTO financial_metrics (filing_id, metric_name, metric_value, fiscal_year)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (filing_id, metric_name, fiscal_year) DO NOTHING
                """, (filing_id, metric_name, value, int(year)))
        self.conn.commit()
        cursor.close()

    
    def retrieve_metrics(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT DISTINCT c.ticker, fm.metric_name, fm.fiscal_year, fm.metric_value
        FROM financial_metrics fm
        JOIN filings f ON fm.filing_id = f.id
        JOIN companies c ON f.cik = c.cik
        ORDER BY c.ticker, fm.metric_name, fm.fiscal_year;
        """)
        rows = cursor.fetchall()

        self.conn.commit()
        cursor.close()

        return rows

    def close(self):
        self.conn.close()