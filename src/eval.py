from html_parser import HTMLParser
from insert_filings_to_db import DBOperations
import csv


db = DBOperations()

rows = db.retrieve_metrics()

metric2valueMap = {}
for row in rows:
    metricTuple = tuple(row[:3])
    value = row[3]
    if metricTuple in metric2valueMap:
        metric2valueMap[metricTuple] = max(metric2valueMap[metricTuple], value)
    else:
        metric2valueMap[metricTuple] = value

result_map = {}

with open("ground_truth.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ticker = row["ticker"]
        metric = row["metric_name"]
        year = int(row["fiscal_year"])
        expected = float(row["expected_value"])

        label_tuple = (ticker, metric, year)

        if(ticker, metric, year) in metric2valueMap:
            actual_value = metric2valueMap[(ticker, metric, year)]
            actual_value = float(actual_value)
            pct_diff = abs(actual_value - expected) / expected * 100
            result_map[label_tuple] = pct_diff

print(result_map)

db.close()