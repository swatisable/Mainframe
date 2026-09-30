# CASNCTD1 — Glossary

Definitions of every code, file, table, and abbreviation used in this documentation set. Values
marked **_(family)_** are confirmed from the sibling program `CASNCTD9`.

---

## 1. Contract codes (3-digit `CONTRACT-NUM`) — _(family)_

| Contract | State | Context code | Notes |
|---------:|-------|--------------|-------|
| `320` | New York | `CTSCASNY` (+ sub-contexts) | Most complex; up to 6 contexts |
| `313` | Florida | `CTSCASFL` (+ sub-contexts) | Casualty/Estate/Trust/Mass-tort |
| `326` | Colorado | `CTSCASCO` | Estate cases also processed |
| `341` | Ohio | `CTSCASOH` | Standard Ohio |
| `535` | Ohio | `CTSCASOH` | CareSource variant (different audit stamp) |
| `319` | Connecticut | `CTSCASCT` | |
| `317` | California | `CTSWRCCA` | Workers'-comp / WRC |
| `590` | Alabama | `CTSCASAL` | |
| `330` | Arkansas | `CTSCASAR` | |
| `358` | Nevada | `CTSCASNV` | |
| `359` | New Mexico | `CTSCASNM` | |
| `645` | West Virginia | `CTSCASWV` | Estates added |
| `300` | (Test) | `CTSCASTST` | Non-production test contract |

## 2. Context codes (`CONTEXT-CD`) — _(family)_

The **context code** is the internal key for *state + line of business*. It drives selection and
is carried into every output record.

### 2.1 Base / casualty contexts

| Context code | Meaning |
|--------------|---------|
| `CTSCASNY` | Casualty — New York |
| `CTSCASFL` | Casualty — Florida |
| `CTSCASCO` | Casualty — Colorado |
| `CTSCASOH` | Casualty — Ohio |
| `CTSCASCT` | Casualty — Connecticut |
| `CTSWRCCA` | Workers'-comp / WRC — California |
| `CTSCASAL` | Casualty — Alabama |
| `CTSCASAR` | Casualty — Arkansas |
| `CTSCASNV` | Casualty — Nevada |
| `CTSCASNM` | Casualty — New Mexico |
| `CTSCASWV` | Casualty — West Virginia |
| `CTSCASTST` | Casualty — Test |

### 2.2 New York sub-contexts (contract 320, by client id)

| Client id | Context code | Letter decode |
|-----------|--------------|---------------|
| `CTSCEN` | `CTSCASEX-NY` | **C**asualty · **E**xchange · **N**ew York |
| `CTSCCN` | `CTSCASNYC` | **C**asualty · **C**ity · **N**ew York |
| `CTSECN` | `CTSESTNY` | **E**state · **C**ity · **N**ew York |
| `CTSEEN` | `CTSESTEX-NY` | **E**state · **E**xchange · **N**ew York |
| `CTSCON` | `CTSCASNYOP1` | **C**asualty · **O**ption 1 · **N**ew York |
| `CTSEON` | `CTSESTNYOP1` | Exchange/Estate · **O**ption 1 · **N**ew York |

### 2.3 Florida sub-contexts (contract 313, by client id)

| Client id | Context code | Meaning |
|-----------|--------------|---------|
| `CTSCAS` | `CTSCASFL` | Casualty |
| `CTSEST` | `CTSESTFL` | Estate |
| `CTSTRS` | `CTSTRSFL` | Trust |
| `CTSMST` | `CTSCASMT-FL` | Mass Tort (treated as casualty) |

### 2.4 Context-code letter conventions

| Fragment | Meaning |
|----------|---------|
| `CTS` | Enterprise context namespace prefix |
| `CAS` | **Cas**ualty line of business |
| `EST` | **Est**ate line of business |
| `TRS` | **Tr**u**s**t line of business |
| `MST` | **M**ass **T**ort |
| `EX` / `EXCHANGE` | Exchange sub-population |
| `NYC` / `C` | New York **C**ity sub-population |
| `OP1` / `O` | **Op**tion **1** sub-population |
| `NY/FL/CO/OH/CT/CA/AL/AR/NV/NM/WV` | U.S. state |

## 3. File names (DDName → record)

| DDName | Record | Length | Meaning |
|--------|--------|-------:|---------|
| `NCTC-OUT` | `NCTCASE-RECORD` | 384 | Primary standardized **case** extract feed |
| `TCM-OUT` | `TCMCASE-RECORD` | _(rep.)_ | **Casualty-only** feed to the TCM subsystem |
| `CLSD-OUT` | `CLOSED-RECORD` | _(rep.)_ | Full record for **closed** cases |
| `CLSD-EXTR-OUT` | `CLSD-EXTRACT-RECORD` | _(rep.)_ | Thin key/status **extract** of closed cases |
| `NCTC-IN` / control | — | — | Contract/context control input (family uses `CASGETCC` service + a small control file) |

## 4. DB2 table names

| Table | Meaning | Prefix |
|-------|---------|--------|
| `ARTCASE` | **Case master** — driving table for the extract | `CASE-` |
| `ARTINDV` | **Individual / claimant** detail | `INDV-` |
| `ARTCCKP` | **Contract-context checkpoint / control** | `CCKP-` |
| `ARTCCLM`* | Claim table (used by sibling `CASNCTD9`) | `CCLM-` |
| `ARTCTPK`* | Primary-key / context-key table (sibling) | `CTPK-` |
| `ARTCLKP`* | Claim lookup table (sibling) | `CLKP-` |
| `ARTSPRF`* | Preferences table (sibling; exclusion settings) | — |

*Starred tables belong to the sibling program and are listed to explain the `ARTxxxx` family
naming; CASNCTD1 uses `ARTCASE`, `ARTINDV`, `ARTCCKP`.

## 5. Output record meanings

| Record | Purpose |
|--------|---------|
| `NCTCASE-RECORD` | One standardized row per selected case for the downstream case/claims system |
| `TCMCASE-RECORD` | Casualty companion row for the TCM recovery subsystem |
| `CLOSED-RECORD` | Full detail of a closed case for closed-case downstream processing |
| `CLSD-EXTRACT-RECORD` | Minimal keys + status + close date for closure reconciliation |

## 6. Status / return codes

| Code | Type | Meaning |
|------|------|---------|
| `CASE-CASE-STATUS-CD` | Input | Raw case status; classified to open/closed |
| `O` / `C` | Derived | Open / Closed indicator on output |
| `SQLCODE 0` | DB2 | Success |
| `SQLCODE +100` | DB2 | Row not found / end of data |
| `SQLCODE -811` | DB2 | More than one row where one expected (data error) |
| `SQLCODE -904` | DB2 | Resource unavailable |
| `SQLCODE -911` | DB2 | Deadlock/timeout, unit-of-work rolled back |
| `SQLCODE -913` | DB2 | Deadlock/timeout, no automatic rollback |
| RC `0000` | Job | Normal completion |
| RC `0998` | Job | **Good** completion, no data to process |
| RC `0999` | Job | Error / abend |
| `3645` | Job | Default dump-code baseline |

## 7. Short names / COBOL abbreviations

| Token | Expansion |
|-------|-----------|
| `WS-` | **W**orking-**S**torage temporary field |
| `WS-MOVE` | Generic working-storage move/staging field |
| `CASE-` | Host-variable prefix for `ARTCASE` columns |
| `INDV-` | Host-variable prefix for `ARTINDV` columns |
| `CCKP-` | Host-variable prefix for `ARTCCKP` columns |
| `NCTC-` | Field prefix for the `NCTCASE-RECORD` output |
| `TCM-` | Field prefix for the `TCMCASE-RECORD` output |
| `CLSD-` | Field prefix for the closed / extract outputs |
| `CONTEXT-CD` | Context code |
| `CONTRACT-NUM` / `HMS-3BYTE-CONTRACT-NUM` | 3-digit contract number |
| `CLIENT-ID` / `HMS-CLIENT-ID` | Client identifier used to refine multi-context states |
| `ICN-NUM` | Internal case/claim control number |
| `DT` | Date (suffix) |
| `CD` | Code (suffix) |
| `NM` | Name (suffix) |
| `IND` | Indicator (suffix) |
| `CTR` | Counter |
| `EOF` | End-of-file flag |
| `CSR` | Cursor |
| `LUW` | Logical Unit of Work (between commits) |
| `COMMIT-FREQ` | Number of rows between DB2 commits (300) |
| `CASGETCC` | Called service that returns the contract/context (**CAS** **GET** **C**ontext **C**ode) |
| `ILBOABN0` | Standard COBOL abend/abort routine |
| `WxxCDF40` | State audit/update stamp (e.g. `WNYCDF40` = NY) |
| `GDG` | Generation Data Group (versioned mainframe dataset) |
| `DCLGEN` | DB2 **DCL**aration **GEN**erator (host-variable copybook) |
| `SQLCA` | SQL Communication Area (holds `SQLCODE`) |
| `FD` | File Description (COBOL file definition) |
| `TCM` | Downstream casualty recovery subsystem feed |
| `NCT` / `NCTCASE` | Standard case extract layout name |
| `HMS` | Installation/system identifier seen in the family code |

---
*See [overview.md](./overview.md) for how these pieces fit together and
[business-rules.md](./business-rules.md) for how the codes drive behavior.*
