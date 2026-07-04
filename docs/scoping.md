# SEC Filing Anomaly Agent — Scoping Document

## Customer

A mid-market PE fund analyst evaluating public companies for potential investment. Today, this analyst manually opens SEC 10-K filings in a browser, scrolls through 200+ pages of HTML to find financial tables, copies numbers into a spreadsheet, then opens prior year filings to compare year-over-year changes. For each company, they also read the MD&A and Risk Factors sections to understand why the numbers changed. This process takes approximately 5-6 hours per company. A typical quarterly review covers 10-20 companies.

## Problem

SEC 10-K filings are unstructured HTML documents with no standard formatting. Every company uses different table layouts, different row labels ("Net sales" vs "Revenue" vs "Total revenues and other income"), and different XBRL tag names for the same financial concept. Revenue alone has 3 different XBRL names across just 5 companies. Debt is even worse — short-term debt has 4 variants, and some companies bundle current maturities into long-term debt while others separate them.

An analyst can read one filing manually. They cannot efficiently compare 15 companies across 3 years of filings. The data extraction is mechanical, repetitive, and error-prone. The contextual analysis (connecting numbers to narrative explanations) is where the analyst adds value — but they spend most of their time on extraction instead.

## Solution

An AI agent that:
1. Pulls 10-K filings from SEC EDGAR via API
2. Parses financial tables using inline XBRL tags (primary) with table heuristic fallback
3. Extracts 5 core financial metrics and stores them in Postgres
4. Detects year-over-year anomalies (>15% change threshold)
5. Retrieves narrative context from MD&A and Risk Factors sections via RAG to explain detected anomalies
6. Responds to natural language queries like "Pull Apple's key financials for FY2025 and flag anything unusual"

## Target Metrics (5)

| Metric | Purpose | XBRL Variants Found |
|---|---|---|
| Revenue | Business scale and growth | 3 variants across 5 companies |
| Net Income | Bottom-line profitability | 1 variant (consistent across all 5) |
| Operating Income | Core business profitability, excluding financing/taxes | 1 variant (available for 3/5 companies; skipped for banks and energy) |
| Total Debt | Financial leverage (sum of short-term + long-term debt) | 4 short-term variants, 3 long-term variants |
| Stockholders' Equity | Book value; used with debt for debt-to-equity ratio | 2 variants |

## Success Criteria

- Extraction accuracy >90% across all extractable metrics (compared against hand-labeled ground truth from Yahoo Finance / Macrotrends)
- Anomaly detection precision >80% (flagged anomalies are real, not noise)
- Agent answers end-to-end queries with correct metrics and relevant narrative context
- Deployed and accessible on AWS EC2 via Docker Compose

## Test Companies (5 across sectors)

| Company | Ticker | CIK | Sector | Known Edge Cases |
|---|---|---|---|---|
| Apple | AAPL | 0000320193 | Technology | Fiscal year ends September; high debt-to-equity by design (capital return strategy) |
| JPMorgan Chase | JPM | 0000019617 | Financial Services | Bank income statement is structurally different; no operating income; revenue = net of interest expense |
| Microsoft | MSFT | 0000789019 | Technology | Fiscal year ends June; has both short-term debt and current portion of long-term debt as separate lines |
| ExxonMobil | XOM | 0000034088 | Energy | Revenue mixes operating and non-operating income; no operating income tag; long-term debt includes capital lease obligations |
| Johnson & Johnson | JNJ | 0000200406 | Healthcare | No explicit operating income row (must calculate); equity tag includes noncontrolling interest; recent Kenvue spinoff creates one-time items |

## Out of Scope

- 10-Q (quarterly) filings — annual only for this sprint
- Real-time filing monitoring / streaming
- Non-US filers
- Full XBRL taxonomy coverage (only 5 metrics, not full financial statement extraction)
- Frontend UI (API endpoint only)
- Custom calculation logic for operating income when not tagged (logged as NULL instead)

## Key Findings from Data Exploration

1. XBRL-first parsing works. Inline `<ix:nonFraction>` tags with `name` attributes provide structured, machine-readable data embedded in the HTML. Every metric except operating income (for some companies) is directly extractable via XBRL tag lookup.

2. Synonym lists are essential. The same financial concept uses different XBRL names across companies. The parser must search a list of known synonyms for each metric, not a single tag name.

3. Debt requires anti-double-counting logic. JPMorgan's long-term debt tag includes current maturities. If the parser also finds a current portion tag, it would double-count. Logic: if "IncludingCurrentMaturities" tag found, skip current portion tags for that filing.

4. Scale and decimals are consistent (6 / -6) across all 5 test companies, but the parser should read these from the tag attributes rather than hardcoding, since smaller companies may report in thousands.

5. Banks break non-bank assumptions. JPMorgan has no standard revenue line, no operating income, and a fundamentally different income statement structure. The parser handles this via sector-specific tag lists rather than trying to force bank data into a non-bank template.

## Tech Stack

| Component | Tool |
|---|---|
| Agent framework | LangGraph |
| LLM | Claude Sonnet (via API) |
| Vector store | ChromaDB |
| Database | PostgreSQL 16 |
| Embedding model | sentence-transformers (all-MiniLM-L6-v2) |
| External API | SEC EDGAR |
| Web framework | FastAPI |
| Deployment | Docker Compose → AWS EC2 |
