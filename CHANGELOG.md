# Changelog

## Day 1 — July 4, 2026

### Done

- Explored 5 raw 10-K filings in DevTools (AAPL, JPM, MSFT, XOM, JNJ)
- Built complete XBRL synonym table for all 5 metrics across 5 companies
- Found that operating income is not tagged for ExxonMobil and JPMorgan
- Wrote scoping doc (docs/scoping.md)
- Set up Postgres 16 via Docker Compose, applied schema, seeded 5 companies

### Blockers

- None

### Notes

- JPMorgan's long-term debt tag includes current maturities — parser needs anti-double-counting logic
- Banks have fundamentally different income statement structure — revenue = net of interest expense
