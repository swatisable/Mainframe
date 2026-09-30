# CASNCTD1 — Program Documentation Index

Technology-agnostic documentation for the mainframe COBOL batch program **CASNCTD1**.
The goal of this documentation set is to let a developer working in **Java, .NET, Python,
Node.js, or any other stack** understand the program's business purpose, data flow, and
rules **without reading COBOL**, and to support **mapping, re-platforming, and modernization**.

## Documents in this set

| # | Document | What it covers |
|---|----------|----------------|
| 1 | [overview.md](./overview.md) | Purpose, high-level process, files, DB2 tables, data-flow summary, responsibilities, assumptions, state handling |
| 2 | [input-output-mapping.md](./input-output-mapping.md) | Field-level mapping tables for every input and output, plus source/destination summaries |
| 3 | [data-mapping.md](./data-mapping.md) | Field-level transformation logic, conditional rules, redefinitions and normalizations |
| 4 | [business-rules.md](./business-rules.md) | Every business rule, validation, and context-code rule in plain English |
| 5 | [process-flow.md](./process-flow.md) | Mermaid flowchart + numbered step-by-step process description |
| 6 | [glossary.md](./glossary.md) | Contract codes, context codes, file names, table names, status codes, abbreviations |
| 7 | [technical-to-business-summary.md](./technical-to-business-summary.md) | Business-level narrative **and** the *Implementation Notes for Modernization* section |

## How to read this set

- **Business / product reader** → start with [overview.md](./overview.md) then [technical-to-business-summary.md](./technical-to-business-summary.md).
- **Modernization / architecture reader** → read [overview.md](./overview.md), [process-flow.md](./process-flow.md), then the *Implementation Notes for Modernization* at the end of [technical-to-business-summary.md](./technical-to-business-summary.md).
- **Developer building the replacement** → use [input-output-mapping.md](./input-output-mapping.md), [data-mapping.md](./data-mapping.md), and [business-rules.md](./business-rules.md) as the specification.

---

## Documentation basis & scope (please read)

- **Program under analysis:** `CASNCTD1` — a batch **extract / outbound** program that reads
  case data from DB2 and writes flat files for downstream systems.
- **Source availability:** The file `CASNCTD1.txt` is **not present** in this repository. This
  documentation is therefore built from two grounded sources:
  1. The **detailed program specification** provided in the task (file names, record lengths,
     DB2 tables, and the main logic steps for `CASNCTD1`). This is treated as **authoritative**
     for CASNCTD1's structure.
  2. **Real domain knowledge mined from the sibling program `CASNCTD9`** (`CASNCTD9_Version2.txt`,
     recovered from this repository's git history). `CASNCTD9` belongs to the same `CASNCTDx`
     program family and shares the exact **context codes, contract codes, state-specific logic,
     `ARTCxxx` table conventions, casualty/estate/trust/mass-tort concepts, SQL error handling,
     and return-code conventions**. These real values are reused here because the family is
     internally consistent (e.g., `CASNCTD9` documents itself as *"CLONED FROM CASNCTD7"* and a
     *"CLONE OF CASNCTD2"*).
- **How inferred content is marked:** Where a specific field layout is not given by the task and
  is reconstructed from family naming conventions, it is labelled **_(representative layout)_**.
  Values labelled **_(from CASNCTD9 / family)_** are taken directly from the sibling program and
  are highly reliable. Treat representative layouts as *shape and intent*, and confirm exact
  offsets/pictures against the real `CASNCTD1` copybooks when they become available.

> **Relationship to CASNCTD9:** `CASNCTD9` is the **inbound** side (reads a claims file, updates
> DB2 case/claim tables). `CASNCTD1` is the **outbound** side (reads DB2 case tables, writes
> extract files). Together they form the round-trip between the case database and external
> claims/casualty subrogation partners.
