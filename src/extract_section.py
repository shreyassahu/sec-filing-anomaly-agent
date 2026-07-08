from bs4 import BeautifulSoup
from datetime import datetime


def normalize(text):
    """Fold typographic punctuation to ASCII so keyword matching is robust."""
    if not text:
        return ""
    return (
        text.replace("’", "'").replace("‘", "'") 
            .replace("“", '"').replace("”", '"')
            .replace("–", "-").replace("—", "-")
            .lower()
    )


class ExtractSection:
    def __init__(self, filepath):
        with open(filepath) as fp:
            self.soup = BeautifulSoup(fp, 'html.parser')


    def extract_section(self, section_keywords, end_keywords):
        norm_keywords = [normalize(kw) for kw in section_keywords]
        norm_end_keywords = [normalize(kw) for kw in end_keywords]

        candidates = []
        for keyword in norm_keywords:
            candidates.extend(self.soup.find_all(string=lambda text: keyword in normalize(text)))

        best_text = ""

        for candidate in candidates:

            if len(candidate.strip()) > 200:
                continue

               # Filter 2: Skip TOC entries
            # if candidate.find_parent("table"):
            #     continue

            collected_text = ""
            parent = candidate.find_parent()

            for node in parent.find_all_next(string=True):
                text = node.strip()
                if not text:
                    continue

                norm_text = normalize(text)

                # breaks only if end keyword in phrase that is short, i.e, less than 200 characters
                if len(text) < 200 and any(end_kw in norm_text for end_kw in norm_end_keywords):
                    break    

                if node.find_parent("table"):
                    continue
                

                collected_text += text + " "
                
            if len(collected_text) > 5000:
                best_text = collected_text

        return best_text


extractSection = ExtractSection("data/filings/0000789019/msft-20230630.htm")

# section_keywords=[
#         "Management's Discussion and Analysis",
#         "Management's discussion and analysis"
#     ]

# end_keywords=[
#     "ITEM 8",
#     "Item 8",
#     "Financial Statements and Supplementary Data",
#     "Report of Independent Registered Public Accounting Firm",
#     "Management's Report on Internal Control",
#     "Financial statements and supplementary data",
#     "MANAGEMENT’S REPORT ON INTERNAL CONTROL OVER FINANCIAL REPORTING",
#     "FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA"
# ]




# mda_text = extractSection.extract_section(section_keywords, end_keywords)
# print(mda_text)

section_keywords=[
        "Item 1A"
    ]

end_keywords=[
        "Item 1B",
        "ITEM 1B. UNRESOLVED STAFF COMMENTS"
        "Item 2",
        "Unresolved Staff Comments",
        "Properties"
    ]

risk_text = extractSection.extract_section(section_keywords, end_keywords)
print(risk_text)