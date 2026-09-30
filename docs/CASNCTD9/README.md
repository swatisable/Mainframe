# CASNCTD9 — Documentation Index

Technology-agnostic documentation for the mainframe program **`CASNCTD9`**, generated from the source in this repository.

## ⚠️ Source discrepancy (please read first)

The analysis task requested program **`CASNCTD1`**. **`CASNCTD1` does not exist in this repository** — it is not in the working tree or anywhere in git history: *Not present in provided source — requires further input.*

The **only** mainframe program available is **`CASNCTD9`**, a COBOL/DB2 batch program recovered from the `CASNCTD9_Version2.txt` blob in git history (the file had been deleted on the default branch). All documents below describe `CASNCTD9`.

**Partial source note:** the program body is complete, but its copybooks (`NCTCLMS9`), DB2 DCLGENs (`ARTCCLM`, `ARTCLKP`, `CARTCTPK`, `ARTSPRF`, `PMONITOR`), called subprograms (`CASGETCC`, `DSNTIAR`, `ILBOABN0`), and JCL are **not included** and are labeled *External dependency not analyzed in provided source*.

## Documents

| File | Contents |
|------|----------|
| [overview.md](overview.md) | Program identity, purpose, high-level flow, paragraphs, inputs/outputs, dependencies. |
| [input-output-mapping.md](input-output-mapping.md) | Input/output source & target tables, field mappings, parameters, linkage areas. |
| [data-mapping.md](data-mapping.md) | Source→target field transformations, decision tables, date/diagnosis/null logic. |
| [business-rules.md](business-rules.md) | Numbered business rules, validations, SQLCODE handling, return/dump codes. |
| [process-flow.md](process-flow.md) | Mermaid flowchart + numbered process description. |
| [glossary.md](glossary.md) | Terms, tables, columns, context codes, flags, status/return codes, abbreviations. |
| [technical-to-business-summary.md](technical-to-business-summary.md) | Plain-English business summary. |
| [modernization-notes.md](modernization-notes.md) | Modernization strategy and legacy→modern equivalents. |

*All statements are grounded in the provided source; unknowns are explicitly labeled.*
