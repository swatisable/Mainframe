# CASNCTD1 — Overview

## 1. Program name and purpose

| Attribute | Value |
|-----------|-------|
| **Program name** | `CASNCTD1` |
| **Type** | Mainframe COBOL **batch extract** program (DB2 → flat files) |
| **Family** | `CASNCTDx` case/claims subrogation programs (siblings: `CASNCTD2`, `CASNCTD7`, `CASNCTD9`, …) |
| **Direction** | **Outbound** — reads case data from DB2 and produces sequential output files |
| **Primary purpose** | Extract insurance **case** records for a given **contract**, translate the contract into its **context code(s)**, pull the matching cases (and related individual / control data) from DB2, and write them out in the standardized **NCTCASE** layout plus specialized **closed-case**, **closed-case extract**, and **TCM** files for downstream systems. |

**In one sentence:** *CASNCTD1 turns "give me the cases for this contract" into a set of
downstream-ready files, applying the correct state- and product-specific context codes and
splitting the results into open, closed, and casualty-specific outputs.*

## 2. High-level business process

The program supports the **claims / casualty subrogation** business. Insurers and government
health programs need to identify cases (accidents, injuries, estates, trusts, mass-tort matters)
where a **third party** may be liable, so that paid medical claims can be recovered.

At a high level, for one run CASNCTD1:

1. Determines **which contract** it is running for (a 3-digit contract number such as `320` = New York).
2. Translates that contract into one or more **context codes** — the internal keys that identify
   a *state + line of business* (e.g., `CTSCASNY` = Casualty / New York, `CTSESTFL` = Estate / Florida).
3. Reads all **matching cases** from the DB2 case tables for those context codes.
4. **Formats** each case into the fixed-length **NCTCASE** output record (384 bytes).
5. **Classifies** each case as **open** or **closed** and routes closed cases to the closed-case
   file and a slimmer closed-case **extract** file.
6. For **casualty** contracts, additionally writes a **TCM** record.
7. Applies **state-specific and product-specific exceptions** throughout (New York, Florida,
   Colorado, Ohio, Connecticut, California, Alabama, Arkansas, Nevada, New Mexico, West Virginia).

## 3. Files used and generated

### Inputs

| Logical name | Kind | Description |
|--------------|------|-------------|
| Contract / context control input | Parameter or control file | Supplies the **contract number** (and, for multi-context states, the client id) that scopes the run. In the family this is retrieved via a context service call (see `CASGETCC` in the glossary) and/or a small control file. |
| DB2 case data | DB2 tables | The real source of records — see §4. |

### Outputs

| DDName / logical file | Record name | Length | Description |
|-----------------------|-------------|--------|-------------|
| `NCTC-OUT` | `NCTCASE-RECORD` | **384** | Primary standardized case extract; **one record per selected case** (open and, depending on configuration, closed). |
| `TCM-OUT` | `TCMCASE-RECORD` | _(representative)_ | **Casualty-only** companion record for the TCM downstream system. |
| `CLSD-OUT` | `CLOSED-RECORD` | _(representative)_ | Full record for cases classified as **closed**. |
| `CLSD-EXTR-OUT` | `CLSD-EXTRACT-RECORD` | _(representative)_ | Slimmer **extract** of closed cases (keys + status/date) for reconciliation downstream. |

> Record lengths marked _(representative)_ are not given by the specification and should be
> confirmed against the real copybooks; only `NCTCASE-RECORD = 384` is specified.

## 4. DB2 tables accessed

| Table | Host-variable prefix | Role in CASNCTD1 | Access |
|-------|----------------------|------------------|--------|
| **ARTCASE** | `CASE-` | **Case master** — the driving table. One row per case: context code, case id, incident/status dates, status code, contract/state. | Read (cursor/select) |
| **ARTINDV** | `INDV-` | **Individual / claimant** detail associated with a case (names, identifiers, demographics). | Read (lookup by case) |
| **ARTCCKP** | `CCKP-` | **Contract-context checkpoint / control** — process control point, last-run markers, and per-context bookkeeping. | Read (and control) |

> Prefix convention comes from the family: in `CASNCTD9`, `ARTCCLM`→`CCLM-`, `ARTCTPK`→`CTPK-`,
> `ARTCLKP`→`CLKP-`. CASNCTD1 follows the same pattern with `ARTCASE`→`CASE-`, `ARTINDV`→`INDV-`,
> `ARTCCKP`→`CCKP-`.

## 5. Data-flow summary

```
Contract number (e.g. 320)
        │
        ▼
Contract → Context-code mapping   (320 → CTSCASNY, 313 → CTSCASFL, …)
        │   (+ client-id sub-mapping for multi-context states: NY, FL)
        ▼
DB2 read:  ARTCASE  (driver)  ──join──►  ARTINDV (claimant)  +  ARTCCKP (control)
        │
        ▼
For each case row:
   • Move/translate fields into NCTCASE layout (384 bytes)
   • Derive OPEN vs CLOSED from CASE-CASE-STATUS-CD
   • Normalize/validate dates (incident, open, close)
        │
        ├─► NCTC-OUT        (NCTCASE-RECORD, all selected cases)
        ├─► CLSD-OUT        (CLOSED-RECORD, closed cases)
        ├─► CLSD-EXTR-OUT   (CLSD-EXTRACT-RECORD, closed keys/status)
        └─► TCM-OUT         (TCMCASE-RECORD, casualty contracts only)
        │
        ▼
Commit / checkpoint periodically; end-of-job return code
```

## 6. Core responsibilities of the program

1. **Contract resolution** — establish the contract number the run is for.
2. **Context-code mapping** — translate contract (and client id) into one or more context codes,
   including state- and product-specific variants (casualty, estate, trust, mass tort).
3. **Case selection** — read the matching cases from `ARTCASE`, enriched from `ARTINDV` and
   controlled via `ARTCCKP`.
4. **Record formatting** — populate the fixed 384-byte `NCTCASE-RECORD` from source columns.
5. **Open/closed classification** — split records by case status and produce closed-case and
   closed-extract files.
6. **Casualty TCM generation** — emit `TCMCASE-RECORD` for casualty contracts.
7. **State/contract exception handling** — apply per-state rules and audit stamps.
8. **Operational controls** — periodic DB2 commit/checkpoint, SQL error/timeout handling,
   and meaningful end-of-job return codes (including a *good* return when there is simply no data).

## 7. Assumptions and limitations

- **Single-contract-per-run (by design of the family).** Each execution is scoped to one contract
  number; running for all states means running the job (or the job stream) once per contract.
- **Context codes are the pivot.** All selection and output keying is by *context code*, not by a
  human-readable state name. A missing or unknown contract→context mapping is a **fatal error**.
- **Fixed-length output.** Downstream systems expect exact record lengths (NCTCASE = 384). Field
  offsets are contractually fixed; any change is a downstream-breaking change.
- **DB2 availability and locking.** The program is designed to tolerate transient DB2
  timeouts/deadlocks with limited retries; sustained contention aborts the run.
- **Representative field layouts.** Because `CASNCTD1.txt` is not in the repository, exact column
  lists and record offsets below §4/§3 marked _(representative)_ are reconstructed from family
  conventions and must be validated against the real copybooks/DCLGEN.

## 8. State-specific contract handling summary

The family maps each **3-digit contract** to a **context code**. The table below is taken
directly from the sibling `CASNCTD9` and applies to the whole family _(from CASNCTD9 / family)_:

| Contract # | Context code | State / meaning | Audit/update stamp |
|-----------:|--------------|-----------------|--------------------|
| `320` | `CTSCASNY` | **New York** — Casualty (multi-context, see below) | `WNYCDF40` |
| `313` | `CTSCASFL` | **Florida** — Casualty (multi-context, see below) | `WFLCDF40` |
| `326` | `CTSCASCO` | **Colorado** — Casualty (Estate cases also processed) | `WCOCDF40` |
| `341` | `CTSCASOH` | **Ohio** — Casualty | `WOHCDF40` |
| `535` | `CTSCASOH` | **Ohio** — CareSource variant | `WCXCDF40` |
| `319` | `CTSCASCT` | **Connecticut** — Casualty | `WCTCDF40` |
| `317` | `CTSWRCCA` | **California** — Workers'-comp / WRC | `WCACDF40` |
| `590` | `CTSCASAL` | **Alabama** — Casualty | `WALCDF40` |
| `330` | `CTSCASAR` | **Arkansas** — Casualty | `WARCDF40` |
| `358` | `CTSCASNV` | **Nevada** — Casualty | `WNVCDF40` |
| `359` | `CTSCASNM` | **New Mexico** — Casualty | `WNMCDF40` |
| `645` | `CTSCASWV` | **West Virginia** — Casualty (Estates added) | `WWVCDF40` |
| `300` | `CTSCASTST` | **Test** contract | `WTTCDF40` |

**Multi-context states** resolve a *sub-context* from the client id:

- **New York (320):** `CTSCEN`→`CTSCASEX-NY` (Casualty/Exchange), `CTSCCN`→`CTSCASNYC`
  (Casualty/City), `CTSECN`→`CTSESTNY` (Estate/City), `CTSEEN`→`CTSESTEX-NY` (Estate/Exchange),
  `CTSCON`→`CTSCASNYOP1` (Casualty/Option 1), `CTSEON`→`CTSESTNYOP1` (Exchange/Option 1);
  default `CTSCASNY`.
- **Florida (313):** `CTSCAS`→`CTSCASFL` (Casualty), `CTSEST`→`CTSESTFL` (Estate),
  `CTSTRS`→`CTSTRSFL` (Trust), `CTSMST`→`CTSCASMT-FL` (Mass Tort); default `CTSCASFL`.

> **Why state logic matters:** each U.S. state has different subrogation/recovery statutes, data
> obligations, and product lines (casualty vs estate vs trust vs mass tort). The context code is
> how the program encodes "this record belongs to *this state + this line of business*," which
> determines both **which cases are selected** and **how downstream systems must treat them**.

---
*See [input-output-mapping.md](./input-output-mapping.md) for field-level mappings,
[business-rules.md](./business-rules.md) for the full rule catalog, and
[technical-to-business-summary.md](./technical-to-business-summary.md) for the modernization notes.*
