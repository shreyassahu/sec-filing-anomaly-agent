from bs4 import BeautifulSoup
from datetime import datetime


file_path = "data/filings/0000019617/jpm-20241231.htm"

REVENUE_TAGS = [
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:RevenuesNetOfInterestExpense",
    "us-gaap:Revenues"
]

NET_INCOME_TAGS = [
    "us-gaap:NetIncomeLoss",
]

OPERATING_INCOME_TAGS = [
    "us-gaap:OperatingIncomeLoss",
]

LONG_TERM_DEBT_TAGS = [
    "us-gaap:LongTermDebtNoncurrent",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
]

SHORT_TERM_DEBT_TAGS = [
   "us-gaap:ShortTermBorrowings",
    "us-gaap:DebtCurrent",
    "us-gaap:LongTermDebtCurrent",
    "us-gaap:CommercialPaper",
]

STOCKHOLDERS_EQUITY_TAGS = [
    "us-gaap:StockholdersEquity",
    "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
]

class HTMLParser:
    def __init__(self, filepath):
        with open(filepath) as fp:
            self.soup = BeautifulSoup(fp, 'html.parser')
        self.context_map = self.build_context_map()

    def build_context_map(self):
        matches = self.soup.find_all("xbrli:context")
        context_map = {}
        for match in matches:
            if not match.find("xbrli:segment"):
                period = match.find('xbrli:period')
                if not period:
                    continue
                instant = period.find('xbrli:instant')
                enddate = period.find('xbrli:enddate')
                startdate = period.find('xbrli:startdate')
                if instant:
                    context_map[match['id']] = self.get_fiscal_year(instant.text)
                elif enddate and startdate:
                    start = datetime.strptime(startdate.text, "%Y-%m-%d")
                    end = datetime.strptime(enddate.text, "%Y-%m-%d")
                    if (end - start).days > 300:
                        context_map[match['id']] = self.get_fiscal_year(enddate.text)
        # print(context_map)
        return context_map
    
    def get_fiscal_year(self, date_str):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date.month == 1 and date.day <= 10:
            return str(date.year - 1)
        return str(date.year)

    def get_year_to_value(self, synonym_tags):
        res = {}
        for tag_name in synonym_tags:
            matches = self.soup.find_all("ix:nonfraction", attrs={"name": tag_name})
            if matches:
                for tag in matches:
                    context_ref = tag['contextref']
                    if context_ref in self.context_map:
                        year = self.context_map[context_ref]
                        if year not in res:
                            value_text = tag.text.replace(',', '')
                            value = float(value_text) * 10 ** int(tag['scale'])
                            if tag.get('sign') == '-':
                                value = -value
                            res[year] = value
                if res:
                    if synonym_tags[0] == "us-gaap:LongTermDebtCurrent":
                        print(matches)
                    break
        return res

    def get_total_debt(self):
        long_term = self.get_year_to_value(LONG_TERM_DEBT_TAGS)

        # print(long_term)

        # Check if long-term tag includes current maturities
        has_including_current = False
        for tag_name in LONG_TERM_DEBT_TAGS:
            if "IncludingCurrentMaturities" in tag_name:
                matches = self.soup.find_all("ix:nonfraction", attrs={"name": tag_name})
                if matches:
                    has_including_current = True
                    break

        if has_including_current:
            return long_term

        short_term = self.get_year_to_value(SHORT_TERM_DEBT_TAGS)

        # print(short_term)

        total = {}
        all_years = set(list(long_term.keys()) + list(short_term.keys()))
        for year in all_years:
            total[year] = long_term.get(year, 0) + short_term.get(year, 0)
        return total

    def extract_all_metrics(self):
        metrics = {}
        metrics['revenue'] = self.get_year_to_value(REVENUE_TAGS)
        metrics['net_income'] = self.get_year_to_value(NET_INCOME_TAGS)
        metrics['operating_income'] = self.get_year_to_value(OPERATING_INCOME_TAGS)
        metrics['total_debt'] = self.get_total_debt()
        metrics['stockholders_equity'] = self.get_year_to_value(STOCKHOLDERS_EQUITY_TAGS)

        return metrics