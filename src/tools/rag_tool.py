
from src.rag_pipeline import RAGPipeline

from langchain.tools import tool
@tool
def rag_retrieval(query_text: str, cik: str = None, fiscal_year: int = None, section_name: str = None):
    """
    Search narrative sections of SEC 10-K filings for relevant context.
    Sections available: 'mda' (Management's Discussion and Analysis) and 'risk_factors'.
    Use this to find explanations for financial changes, risk discussions, and management commentary.
    Filters by company (cik), fiscal year, and section name if provided.

    Important: Chunks are tagged by the fiscal year of the filing, not the year being discussed.
    A 10-K filing for FY2023 discusses both 2023 and 2022 performance.
    To find context for a year-over-year change in year N, search fiscal_year N or N+1.
    If no results are found for a given year, retry with the adjacent year.
    """

    rag = RAGPipeline()

    where = {}
    conditions = []
    if cik:
        conditions.append({"cik": cik})
    if fiscal_year:
        conditions.append({"fiscal_year": fiscal_year})
    if section_name:
        conditions.append({"section_name": section_name})

    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}
    else:
        where = None

    results = rag.query(query_text, where=where, n_results=3)
    chunks = results["documents"][0] if results["documents"][0] else []

    if not chunks:
        return {"status": "error", "message": "No relevant context found"}

    return {"status": "success", "chunks": chunks}

if __name__ == "__main__":
    rag_retrieval("What caused revenue decline?", cik="0000320193", fiscal_year=2023, section_name="mda")

    


