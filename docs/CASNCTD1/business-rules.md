# CASNCTD1 — Business Rules

All rules are stated in plain English and grouped by topic. Each rule has an ID (`BR-nn`) for
cross-referencing. Rules confirmed against the sibling program `CASNCTD9` are marked
**_(family)_**; rules derived from the CASNCTD1 specification are marked **_(spec)_**.

---

## A. Record selection — what qualifies a case

| ID | Rule |
|----|------|
| **BR-01** | A run is **scoped to exactly one contract number** (e.g., `320`). Only cases belonging to the context code(s) derived from that contract are eligible. **_(family)_** |
| **BR-02** | A case is selected from **`ARTCASE`** when its `CONTEXT_CD` matches the resolved context code for the run (plus any status/date predicates configured for the extract). **_(spec)_** |
| **BR-03** | Each selected case is enriched from **`ARTINDV`** using the same `CONTEXT_CD` **and** the case's `CASE_ID`. A missing individual row does **not** reject the case; claimant fields default to spaces. **_(spec)_** |
| **BR-04** | If the input/selection yields **no rows at all**, the job ends with a **"good/no-data" completion** rather than an error (see BR-31). **_(family)_** |

## B. Context-code matching (contract → context)

| ID | Rule |
|----|------|
| **BR-10** | The 3-digit contract number is translated to a context code by a fixed lookup: `320→CTSCASNY`, `313→CTSCASFL`, `326→CTSCASCO`, `341→CTSCASOH`, `535→CTSCASOH`, `319→CTSCASCT`, `317→CTSWRCCA`, `590→CTSCASAL`, `330→CTSCASAR`, `358→CTSCASNV`, `359→CTSCASNM`, `645→CTSCASWV`, `300→CTSCASTST`. **_(family)_** |
| **BR-11** | An **unknown contract number** is a **fatal error** — the program logs "UNKNOWN CONTRACT" and abends (dump code `0999`). It never guesses a context. **_(family)_** |
| **BR-12** | For **New York (320)**, the context is refined by client id: `CTSCEN→CTSCASEX-NY`, `CTSCCN→CTSCASNYC`, `CTSECN→CTSESTNY`, `CTSEEN→CTSESTEX-NY`, `CTSCON→CTSCASNYOP1`, `CTSEON→CTSESTNYOP1`; default `CTSCASNY`. **_(family)_** |
| **BR-13** | For **Florida (313)**, the context is refined by client id: `CTSCAS→CTSCASFL`, `CTSEST→CTSESTFL`, `CTSTRS→CTSTRSFL`, `CTSMST→CTSCASMT-FL`; default `CTSCASFL`. **_(family)_** |
| **BR-14** | When the resolved context code is **longer than the 6-character output slot**, it is **shortened to its significant left-most 6 characters** before being written. Short codes pass through unchanged. **_(family)_** |
| **BR-15** | At the moment the context is resolved, the matching **state audit stamp** is also set (`WNYCDF40` for NY, `WFLCDF40` for FL, `WCOCDF40` for CO, `WOHCDF40`/`WCXCDF40` for OH, `WCTCDF40` for CT, `WCACDF40` for CA, `WALCDF40` for AL, `WARCDF40` for AR, `WNVCDF40` for NV, `WNMCDF40` for NM, `WWVCDF40` for WV). **_(family)_** |

## C. Line-of-business treatment (casualty / estate / trust / mass-tort)

| ID | Rule |
|----|------|
| **BR-20** | **Casualty** cases (context codes starting `CTSCAS…`) produce a **`TCMCASE-RECORD`** in addition to the standard NCTCASE record. **_(spec)_** |
| **BR-21** | **Estate** cases (`CTSEST…`) and **Trust** cases (`CTSTRS…`) produce NCTCASE (and closed/extract when closed) records but **no TCM record**. **_(spec)_** |
| **BR-22** | **Mass-tort** in Florida (`CTSCASMT-FL`) is a **casualty** variant, so it **does** receive a TCM record. **_(family)_** |
| **BR-23** | Colorado and West Virginia additionally process **estate** cases alongside casualty (their contracts were extended to cover estates). **_(family)_** |

## D. Open / closed classification and routing

| ID | Rule |
|----|------|
| **BR-30a** | A case's `CASE-CASE-STATUS-CD` is examined and classified as **OPEN** or **CLOSED**. **_(spec)_** |
| **BR-30b** | **Open** cases are written to **`NCTC-OUT`** only. **_(spec)_** |
| **BR-30c** | **Closed** cases are written to **`NCTC-OUT`**, **`CLSD-OUT`** (full closed record), **and** **`CLSD-EXTR-OUT`** (thin extract of keys + status + close date). **_(spec)_** |
| **BR-30d** | The raw status code is preserved in the output; a **derived `O`/`C` indicator** is added so downstream consumers need not decode every status value. **_(spec)_** |

## E. Date assignment, adjustment, and validation

| ID | Rule |
|----|------|
| **BR-40** | `CASE-INCIDENT-DT` is reformatted to the output date mask and placed in `NCTC-INCIDENT-DATE`. **_(spec)_** |
| **BR-41** | Open/close dates are reformatted; **close date is blanked (spaces/zeros) for open cases** to avoid emitting an invalid date. **_(spec)_** |
| **BR-42** | A required date that is missing or invalid is handled per the extract's data-quality policy — either defaulted to low-values or flagged; it does not silently write garbage. **_(spec)_** |
| **BR-43** | An **extract date/timestamp** is stamped from the system clock onto each run's output and recorded as the last-run marker in `ARTCCKP`. **_(family)_** |

## F. State / contract exceptions

| ID | Rule |
|----|------|
| **BR-50** | **Ohio** has **two contracts** that both map to `CTSCASOH`: `341` (standard, stamp `WOHCDF40`) and `535` (CareSource, stamp `WCXCDF40`). They share a context but are distinguished by audit stamp. **_(family)_** |
| **BR-51** | **New York (320)** is the most complex: up to **six** context codes across casualty/estate × city/exchange/option-1 (see BR-12). **_(family)_** |
| **BR-52** | **Florida (313)** carries **four** lines of business — casualty, estate, trust, mass-tort (see BR-13). **_(family)_** |
| **BR-53** | The **`300`** contract is a **test** context (`CTSCASTST`, stamp `WTTCDF40`) and must not be used in production feeds. **_(family)_** |
| **BR-54** | **California (317 → `CTSWRCCA`)** is a **workers'-comp / WRC** context and may follow WRC-specific downstream handling. **_(family)_** |

## G. Output-writing rules

| ID | Rule |
|----|------|
| **BR-60** | Every selected case writes **exactly one** `NCTCASE-RECORD` (fixed **384** bytes). **_(spec)_** |
| **BR-61** | Closed cases additionally write **one** `CLOSED-RECORD` and **one** `CLSD-EXTRACT-RECORD`. **_(spec)_** |
| **BR-62** | Casualty contexts additionally write **one** `TCMCASE-RECORD`. **_(spec)_** |
| **BR-63** | All records are **fixed-length**; unused trailing bytes are space-filled so record boundaries stay aligned for downstream fixed-format readers. **_(spec)_** |

## H. Errors, warnings, and SQL timeout handling

| ID | Rule |
|----|------|
| **BR-70** | **`SQLCODE = 0`** → success; process the row. **_(family)_** |
| **BR-71** | **`SQLCODE = +100`** (not found) → no matching row; handle as empty (e.g., default enrichment, or end-of-data). **_(family)_** |
| **BR-72** | **`SQLCODE = -811`** (more than one row where one expected) → **data-integrity error**; log the offending key and **abend** (`0999`). **_(family)_** |
| **BR-73** | **`SQLCODE = -904 / -911 / -913`** (resource unavailable / deadlock / timeout) → **retry**: increment a timeout counter and re-drive the unit of work **up to 5 times**; if nothing has been committed yet, retry, otherwise abend. Exceeding 5 timeouts ends the run via error exit. **_(family)_** |
| **BR-74** | **Any other negative `SQLCODE`** → log `SQLCODE` and **abend** (`0999`). **_(family)_** |
| **BR-75** | **Commit frequency:** the program issues an implicit **`COMMIT` every 300 processed rows** (and a final commit at end of job) to bound lock duration and enable restart. **_(family)_** |
| **BR-76** | **No-data completion:** if there is nothing to process (empty input / all previously processed), the program ends with dump code **`0998`** — a **deliberate "good/no-data" completion**, not a failure. **_(family)_** |
| **BR-77** | **Abend mechanism:** fatal conditions move a dump code into a field and call the standard abort routine (`ILBOABN0`) so operations sees a distinct code (`0999` error, default `3645`). **_(family)_** |
| **BR-78** | **Context-service failure:** if the contract-retrieval service (`CASGETCC`) returns non-zero, the program logs "RETRIEVE CONTRACT NUMBER" error and abends (`0999`). **_(family)_** |

---

## Decision points (quick reference)

```
1. Contract known?            no  → ABEND 0999                (BR-11)
2. Context resolved & fits?   >6  → shorten to 6 chars        (BR-14)
3. Any rows to process?       no  → good completion 0998      (BR-04, BR-76)
4. Case status?               closed → NCTC + CLSD + EXTRACT  (BR-30c)
                              open   → NCTC only              (BR-30b)
5. Line of business?          casualty → also write TCM       (BR-20, BR-22)
                              estate/trust → no TCM           (BR-21)
6. SQL result?                -811/other → ABEND              (BR-72, BR-74)
                              -904/-911/-913 → retry ≤5       (BR-73)
                              +100 → treat as empty           (BR-71)
7. Rows since last commit ≥300? → COMMIT                      (BR-75)
```

---
*See [process-flow.md](./process-flow.md) for the end-to-end flow and
[glossary.md](./glossary.md) for code definitions.*
