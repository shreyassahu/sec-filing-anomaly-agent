from html_parser import HTMLParser
from insert_filings_to_db import DBOperations
import os

filings_dir = "data/filings"


db = DBOperations()

class ExtractMetrics:

    def __init__(self):
        self.db = DBOperations()


    ## Parses and extracts metrics for a given CIDR file. 
    def parse_documents(self, file_path):
        parser = HTMLParser(file_path)
        return parser.extract_all_metrics()
    

    ## Extracts metrics for all the downloaded filings and stores in DB.
    def extract_metrics(self, filings_dir):

        for cik in os.listdir(filings_dir):
            file_to_id = db.retrieve_filing_ids_from_cik(cik)
            cik_path = os.path.join(filings_dir, cik)
            if os.path.isdir(cik_path):
                for filename in os.listdir(cik_path):
                    if filename.endswith(".htm"):
                        filepath = os.path.join(cik_path, filename)
                        filing_id = file_to_id[filename]
                        metrics_dict = self.parse_documents(filepath)
                        db.insert_metrics_to_db(filing_id, metrics_dict)


        db.close()
                


                



