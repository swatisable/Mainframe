# CASNCTD1 — Input / Output Mapping

This document maps every major **input** (DB2 tables, case data, individual data, control/lookup
data) to every major **output** (the four extract files), field by field.

> **Legend**
> - **_(spec)_** — given by the CASNCTD1 specification.
> - **_(family)_** — taken from the sibling program `CASNCTD9` and reliable for the whole family.
> - **_(representative)_** — reconstructed from family naming conventions; validate against the
>   real copybook/DCLGEN. Datatypes/lengths for representative rows are typical values and should
>   be confirmed.

Datatypes use platform-neutral names: **CHAR(n)** fixed text, **VARCHAR(n)** variable text,
**DATE** (yyyy-mm-dd), **TIMESTAMP**, **DECIMAL(p,s)** packed/zoned number, **INT** integer.

---

## 1. Input sources (what the program reads)

### 1.1 Control / contract input

| Field | Source | Datatype | Len | Description | Notes |
|-------|--------|----------|----:|-------------|-------|
| Contract number | Context service / control input `CASGETCC` | CHAR | 3 | 3-digit contract that scopes the run (e.g. `320`) **_(family)_** | Drives the whole run |
| Client id | Control input | CHAR | 6 | Sub-selector for multi-context states (NY, FL) **_(family)_** | e.g. `CTSCEN`, `CTSMST` |

### 1.2 DB2 `ARTCASE` — case master (driver table) — prefix `CASE-`

| Column | Field name | Datatype | Len | Description |
|--------|-----------|----------|----:|-------------|
| CONTEXT_CD | `CASE-CONTEXT-CD` | VARCHAR | 16 | Context code identifying state + line of business **_(spec)_** |
| CASE_ID | `CASE-CASE-ID` | CHAR | 12 | Unique case identifier **_(representative)_** |
| ICN_NUM | `CASE-ICN-NUM` | CHAR | 20 | Internal case/claim control number **_(representative)_** |
| CASE_STATUS_CD | `CASE-CASE-STATUS-CD` | CHAR | 2 | Status code → open/closed classification **_(spec)_** |
| INCIDENT_DT | `CASE-INCIDENT-DT` | DATE | 10 | Date of the incident/accident **_(spec)_** |
| OPEN_DT | `CASE-OPEN-DT` | DATE | 10 | Date the case was opened **_(representative)_** |
| CLOSE_DT | `CASE-CLOSE-DT` | DATE | 10 | Date the case was closed (if closed) **_(representative)_** |
| CONTRACT_NUM | `CASE-CONTRACT-NUM` | CHAR | 3 | Owning contract **_(representative)_** |
| STATE_CD | `CASE-STATE-CD` | CHAR | 2 | U.S. state **_(representative)_** |
| CASE_TYPE_CD | `CASE-CASE-TYPE-CD` | CHAR | 3 | Casualty / Estate / Trust / Mass-tort indicator **_(representative)_** |
| CLAIMANT_ID | `CASE-CLAIMANT-ID` | CHAR | 12 | FK to individual/claimant **_(representative)_** |

### 1.3 DB2 `ARTINDV` — individual / claimant — prefix `INDV-`

| Column | Field name | Datatype | Len | Description |
|--------|-----------|----------|----:|-------------|
| CONTEXT_CD | `INDV-CONTEXT-CD` | VARCHAR | 16 | Context code (join key) **_(representative)_** |
| CASE_ID | `INDV-CASE-ID` | CHAR | 12 | Case join key **_(representative)_** |
| INDV_ID | `INDV-INDV-ID` | CHAR | 12 | Individual identifier **_(representative)_** |
| LAST_NM | `INDV-LAST-NM` | VARCHAR | 30 | Claimant last name **_(representative)_** |
| FIRST_NM | `INDV-FIRST-NM` | VARCHAR | 20 | Claimant first name **_(representative)_** |
| MID_INIT | `INDV-MID-INIT` | CHAR | 1 | Middle initial **_(representative)_** |
| SSN | `INDV-SSN` | CHAR | 9 | Social security / national id **_(representative)_** |
| DOB | `INDV-DOB` | DATE | 10 | Date of birth **_(representative)_** |
| GENDER_CD | `INDV-GENDER-CD` | CHAR | 1 | Gender code **_(representative)_** |
| ADDR_LINE | `INDV-ADDR-LINE` | VARCHAR | 30 | Address line **_(representative)_** |
| CITY | `INDV-CITY` | VARCHAR | 20 | City **_(representative)_** |
| STATE | `INDV-STATE` | CHAR | 2 | State **_(representative)_** |
| ZIP | `INDV-ZIP` | CHAR | 9 | ZIP/postal code **_(representative)_** |

### 1.4 DB2 `ARTCCKP` — contract-context checkpoint / control — prefix `CCKP-`

| Column | Field name | Datatype | Len | Description |
|--------|-----------|----------|----:|-------------|
| CONTEXT_CD | `CCKP-CONTEXT-CD` | VARCHAR | 16 | Context code the checkpoint belongs to **_(representative)_** |
| CONTRACT_NUM | `CCKP-CONTRACT-NUM` | CHAR | 3 | Owning contract **_(representative)_** |
| LAST_RUN_DT | `CCKP-LAST-RUN-DT` | DATE | 10 | Last successful extract date **_(representative)_** |
| LAST_RUN_TS | `CCKP-LAST-RUN-TS` | TIMESTAMP | 26 | Last successful extract timestamp **_(representative)_** |
| HIGH_KEY | `CCKP-HIGH-KEY` | CHAR | 20 | Last/high key processed (restart marker) **_(representative)_** |
| STATUS_TXT | `CCKP-STATUS-TXT` | CHAR | 8 | Last-run status (e.g. `SUCCESS`) **_(family)_** |

---

## 2. Output files and records

### 2.1 `NCTC-OUT` → `NCTCASE-RECORD` (length **384** _(spec)_) — prefix `NCTC-`

| Output field | Datatype | Len | Source table.column | Source field | Description / logic |
|--------------|----------|----:|---------------------|--------------|---------------------|
| `NCTC-CONTEXT-CODE` | CHAR | 6/16 | ARTCASE.CONTEXT_CD | `CASE-CONTEXT-CD` | Context code, moved via work field; **may be shortened to 6 chars** for the output slot (see data-mapping) **_(spec)_** |
| `NCTC-CASE-ID` | CHAR | 12 | ARTCASE.CASE_ID | `CASE-CASE-ID` | Case identifier, moved as-is **_(representative)_** |
| `NCTC-ICN-NUM` | CHAR | 20 | ARTCASE.ICN_NUM | `CASE-ICN-NUM` | Case/claim control number **_(representative)_** |
| `NCTC-INCIDENT-DATE` | DATE | 8/10 | ARTCASE.INCIDENT_DT | `CASE-INCIDENT-DT` | Incident date, reformatted to output date format **_(spec)_** |
| `NCTC-OPEN-DATE` | DATE | 8/10 | ARTCASE.OPEN_DT | `CASE-OPEN-DT` | Case open date **_(representative)_** |
| `NCTC-CLOSE-DATE` | DATE | 8/10 | ARTCASE.CLOSE_DT | `CASE-CLOSE-DT` | Case close date (spaces/zeros if open) **_(representative)_** |
| `NCTC-STATUS-CODE` | CHAR | 2 | ARTCASE.CASE_STATUS_CD | `CASE-CASE-STATUS-CD` | Raw status code **_(spec)_** |
| `NCTC-OPEN-CLOSED-IND` | CHAR | 1 | *derived* | from `CASE-CASE-STATUS-CD` | `O`=open / `C`=closed classification **_(spec logic)_** |
| `NCTC-STATE-CODE` | CHAR | 2 | ARTCASE.STATE_CD | `CASE-STATE-CD` | State **_(representative)_** |
| `NCTC-CASE-TYPE` | CHAR | 3 | ARTCASE.CASE_TYPE_CD | `CASE-CASE-TYPE-CD` | Casualty/Estate/Trust/Mass-tort **_(representative)_** |
| `NCTC-CLMNT-LAST-NM` | VARCHAR | 30 | ARTINDV.LAST_NM | `INDV-LAST-NM` | Claimant last name **_(representative)_** |
| `NCTC-CLMNT-FIRST-NM` | VARCHAR | 20 | ARTINDV.FIRST_NM | `INDV-FIRST-NM` | Claimant first name **_(representative)_** |
| `NCTC-CLMNT-SSN` | CHAR | 9 | ARTINDV.SSN | `INDV-SSN` | Claimant SSN/national id **_(representative)_** |
| `NCTC-CLMNT-DOB` | DATE | 8/10 | ARTINDV.DOB | `INDV-DOB` | Claimant date of birth **_(representative)_** |
| `NCTC-CONTRACT-NUM` | CHAR | 3 | ARTCASE.CONTRACT_NUM | `CASE-CONTRACT-NUM` | Owning contract **_(representative)_** |
| `NCTC-EXTRACT-DATE` | DATE | 8/10 | *system clock* | current date | Date the extract was produced **_(representative)_** |
| `NCTC-FILLER` | CHAR | * | — | — | Reserved spaces to pad the record to **384** bytes **_(representative)_** |

> The columns above are a **representative decomposition** of the 384-byte record. Only
> `NCTC-CONTEXT-CODE`, `NCTC-INCIDENT-DATE`, `NCTC-STATUS-CODE`, and the open/closed derivation are
> named by the specification; the remaining slots illustrate the intent and typical content and
> must be reconciled with the real copybook offsets.

### 2.2 `CLSD-OUT` → `CLOSED-RECORD` — prefix `CLSD-`

| Output field | Datatype | Len | Source | Description / logic |
|--------------|----------|----:|--------|---------------------|
| `CLSD-CONTEXT-CODE` | CHAR | 6/16 | `CASE-CONTEXT-CD` | Context code **_(representative)_** |
| `CLSD-CASE-ID` | CHAR | 12 | `CASE-CASE-ID` | Case id **_(representative)_** |
| `CLSD-STATUS-CODE` | CHAR | 2 | `CASE-CASE-STATUS-CD` | Closed status code **_(representative)_** |
| `CLSD-CLOSE-DATE` | DATE | 8/10 | `CASE-CLOSE-DT` | Close date **_(representative)_** |
| `CLSD-…` (mirrors NCTCASE) | — | — | ARTCASE/ARTINDV | Same body as NCTCASE for closed cases **_(representative)_** |

Written **only when** the case classifies as **closed** (see business-rules §Open/Closed).

### 2.3 `CLSD-EXTR-OUT` → `CLSD-EXTRACT-RECORD` — prefix `CLSD-` (extract)

| Output field | Datatype | Len | Source | Description / logic |
|--------------|----------|----:|--------|---------------------|
| `CLSD-EXT-CONTEXT-CODE` | CHAR | 6/16 | `CASE-CONTEXT-CD` | Context code key **_(representative)_** |
| `CLSD-EXT-CASE-ID` | CHAR | 12 | `CASE-CASE-ID` | Case id key **_(representative)_** |
| `CLSD-EXT-STATUS-CODE` | CHAR | 2 | `CASE-CASE-STATUS-CD` | Closed status **_(representative)_** |
| `CLSD-EXT-CLOSE-DATE` | DATE | 8/10 | `CASE-CLOSE-DT` | Close date **_(representative)_** |

A **thin, key-only** version of the closed file used by downstream reconciliation. Written with
(or immediately after) each `CLOSED-RECORD`.

### 2.4 `TCM-OUT` → `TCMCASE-RECORD` — prefix `TCM-`

| Output field | Datatype | Len | Source | Description / logic |
|--------------|----------|----:|--------|---------------------|
| `TCM-CONTEXT-CODE` | CHAR | 6/16 | `CASE-CONTEXT-CD` | Context code **_(representative)_** |
| `TCM-CASE-ID` | CHAR | 12 | `CASE-CASE-ID` | Case id **_(representative)_** |
| `TCM-INCIDENT-DATE` | DATE | 8/10 | `CASE-INCIDENT-DT` | Incident date **_(representative)_** |
| `TCM-CLMNT-NAME` | VARCHAR | 50 | `INDV-LAST-NM` + `INDV-FIRST-NM` | Concatenated claimant name **_(representative)_** |
| `TCM-STATE-CODE` | CHAR | 2 | `CASE-STATE-CD` | State **_(representative)_** |

Written **only for casualty contracts** (context codes beginning `CTSCAS…` / casualty lines).

---

## 3. Input file sources (summary)

| Source | Kind | Selected by | Feeds |
|--------|------|-------------|-------|
| Contract/context control (`CASGETCC`) | Parameter/service | JCL / job parameter | Context-code mapping |
| `ARTCASE` | DB2 table | `CONTEXT_CD` (+ status/date predicates) | Driver rows for all outputs |
| `ARTINDV` | DB2 table | `CONTEXT_CD` + `CASE_ID` | Claimant enrichment on every output |
| `ARTCCKP` | DB2 table | `CONTEXT_CD` (+ contract) | Restart/checkpoint control, last-run markers |

## 4. Output file destinations (summary)

| File (DDName) | Record | Consumer intent | When written |
|---------------|--------|-----------------|--------------|
| `NCTC-OUT` | `NCTCASE-RECORD` (384) | Primary case feed to downstream case/claims systems | Every selected case |
| `CLSD-OUT` | `CLOSED-RECORD` | Downstream **closed-case** processing | Case classified closed |
| `CLSD-EXTR-OUT` | `CLSD-EXTRACT-RECORD` | Downstream **reconciliation** of closures | Case classified closed |
| `TCM-OUT` | `TCMCASE-RECORD` | **TCM** casualty subsystem | Casualty contracts only |

## 5. DB2 source-to-output mapping summary

| Source table | Primary output(s) | Key relationship |
|--------------|-------------------|------------------|
| `ARTCASE` | `NCTCASE-RECORD`, `CLOSED-RECORD`, `CLSD-EXTRACT-RECORD`, `TCMCASE-RECORD` | Driver: 1 case row → 1 NCTCASE row (+ closed/extract/TCM as applicable) |
| `ARTINDV` | Enriches `NCTCASE-RECORD`, `CLOSED-RECORD`, `TCMCASE-RECORD` | `ARTINDV.CONTEXT_CD = ARTCASE.CONTEXT_CD` **AND** `ARTINDV.CASE_ID = ARTCASE.CASE_ID` |
| `ARTCCKP` | No direct output columns; governs **restart/commit/last-run** | Keyed by `CONTEXT_CD` (+ contract) |

**Cardinality:** one `ARTCASE` row is the unit of work. It always yields one `NCTCASE-RECORD`;
it additionally yields a `CLOSED-RECORD` + `CLSD-EXTRACT-RECORD` when closed, and a
`TCMCASE-RECORD` when the contract/context is casualty.

---
*Continue to [data-mapping.md](./data-mapping.md) for the transformation logic behind each field.*
