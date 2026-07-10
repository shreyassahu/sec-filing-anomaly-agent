from bs4 import BeautifulSoup
import os


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

def is_bold(candidate):
    parent = candidate.find_parent("span")
    if parent and parent.get("style"):
        style = parent["style"].lower()
        if "font-weight:700" in style or "font-weight:bold" in style:
            return True
    return False


class ExtractSection:

    def extract_md_a(self, file_path):

        section_keywords = [
            "management's discussion and analysis"
        ]

        end_keywords = [
            "item 8.",
            "report of independent registered public accounting firm",
            "management's report on internal control"
        ]

        return self.extract_section(file_path, section_keywords, end_keywords)
    

    def extract_risk_factors(self, file_path):

        section_keywords = [
            "item 1a"
        ]

        end_keywords = [
            "item 1b.",
            "item 2.",
            "unresolved staff comments"
        ]

        return self.extract_section(file_path, section_keywords, end_keywords)

    def _collect_text(self, candidate, norm_end_keywords):
        collected_text = ""
        parent = candidate.find_parent()
        for node in parent.find_all_next(string=True):
            text = node.strip()
            if not text:
                continue
            norm_text = normalize(text)
            if len(text) < 200:
                for end_kw in norm_end_keywords:
                    if end_kw in norm_text:
                        print(f"End keyword '{end_kw}' hit: {text[:150]}")
                        return collected_text
            if node.find_parent("table"):
                continue
            collected_text += text + " "
        return collected_text

    def extract_section(self, file_path, section_keywords, end_keywords):
        with open(file_path) as fp:
            soup = BeautifulSoup(fp, 'html.parser')

        norm_keywords = [normalize(kw) for kw in section_keywords]
        norm_end_keywords = [normalize(kw) for kw in end_keywords]

        candidates = []
        for keyword in norm_keywords:
            candidates.extend(soup.find_all(string=lambda text: keyword in normalize(text)))

        # First pass: bold candidates only
        for candidate in candidates:
            if len(candidate.strip()) > 200:
                continue
            if not is_bold(candidate):
                continue
            collected_text = self._collect_text(candidate, norm_end_keywords)
            if len(collected_text) > 5000:
                return collected_text
        # Second pass: all candidates (fallback for JPM-style filings)
        for candidate in candidates:
            if len(candidate.strip()) > 200:
                continue
            collected_text = self._collect_text(candidate, norm_end_keywords)
            if len(collected_text) > 5000:
                return collected_text

        return ""
    
    
if __name__ == "__main__":
    companies = {
        "0000320193": "AAPL",
        "0000019617": "JPM",
        "0000789019": "MSFT",
        "0000034088": "XOM",
        "0000200406": "JNJ",
    }

    # companies = {
    #     "0000789019": "MSFT"
    # }  


    extractor = ExtractSection()

    for cik, ticker in companies.items():
        folder = f"data/filings/{cik}"
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".htm"):
                continue
            filepath = os.path.join(folder, filename)
            print(f"\n{'='*60}")
            print(f"{ticker} — {filename}")
            print(f"{'='*60}")

            text = extractor.extract_md_a(filepath)
            print(f"\n--- MD&A ({len(text)} chars) ---")
            print("BEGIN:", text[:500])
            print("END:", text[-500:])

            rf = extractor.extract_risk_factors(filepath)
            print(f"\n--- Risk Factors ({len(rf)} chars) ---")
            print("BEGIN:", rf[:500])
            print("END:", rf[-500:])