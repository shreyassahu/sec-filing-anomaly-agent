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

## Day 2 — July 5, 2026

### Done

## Day 3 - July 6, 2026

- But you should also log it in your CHANGELOG.md and eventually in docs/postmortem.md with the specifics: "JPMorgan and ExxonMobil don't tag us-gaap:OperatingIncomeLoss. Banks have a fundamentally different income statement structure without a standard operating income line. Parser returns NULL for these companies."
