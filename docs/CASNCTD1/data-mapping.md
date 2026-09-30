# CASNCTD1 — Data Mapping (field-level transformations)

This document explains **how source fields become output fields** in plain English, including the
conditional logic (context-code mapping, date handling, contract-specific rules, open/closed
handling, and state-specific rules). Transformations are shown as
`SOURCE → intermediate → TARGET`.

> Notation: `WS-…` denotes a COBOL **working-storage** intermediate (a temporary variable used
> while reformatting). "Move" = copy a value; "translate" = look up/convert a value; "derive" =
> compute a value from one or more inputs.

---

## 1. Context code — the central transformation

The single most important transformation is turning a **contract number** into a **context code**,
then carrying that context code into every output record.

### 1.1 Contract → context (run scoping)

```
CONTRACT-NUM (3 digits)  →  EVALUATE (lookup)  →  WS-CONTEXT-CD
```

| Rule | Example |
|------|---------|
| Look up the 3-digit contract in the family mapping table | `320 → CTSCASNY`, `313 → CTSCASFL`, `326 → CTSCASCO`, `341/535 → CTSCASOH`, `319 → CTSCASCT`, `317 → CTSWRCCA`, `590 → CTSCASAL`, `330 → CTSCASAR`, `358 → CTSCASNV`, `359 → CTSCASNM`, `645 → CTSCASWV`, `300 → CTSCASTST` |
| Unknown contract → **fatal error** (abend) | any other value |
| Also set the **state-specific audit stamp** at the same time | `320 → WNYCDF40`, `313 → WFLCDF40`, … |

### 1.2 Client id → sub-context (multi-context states)

For **New York (320)** and **Florida (313)**, a second lookup on the **client id** refines the
context code, because those states carry multiple lines of business:

```
CLIENT-ID  →  EVALUATE (state sub-lookup)  →  WS-CONTEXT-CD (refined)
```

**New York (320):**

| Client id | Refined context | Meaning (letter decode) |
|-----------|-----------------|-------------------------|
| `CTSCEN` | `CTSCASEX-NY` | **C**asualty · **E**xchange · **N**ew York |
| `CTSCCN` | `CTSCASNYC` | **C**asualty · **C**ity · **N**ew York |
| `CTSECN` | `CTSESTNY` | **E**state · **C**ity · **N**ew York |
| `CTSEEN` | `CTSESTEX-NY` | **E**state · **E**xchange · **N**ew York |
| `CTSCON` | `CTSCASNYOP1` | **C**asualty · **O**ption 1 · **N**ew York |
| `CTSEON` | `CTSESTNYOP1` | Exchange/Estate · **O**ption 1 · **N**ew York |
| *(other)* | `CTSCASNY` | Casualty New York (default) |

**Florida (313):**

| Client id | Refined context | Meaning |
|-----------|-----------------|---------|
| `CTSCAS` | `CTSCASFL` | Casualty |
| `CTSEST` | `CTSESTFL` | Estate |
| `CTSTRS` | `CTSTRSFL` | Trust |
| `CTSMST` | `CTSCASMT-FL` | Mass Tort |
| *(other)* | `CTSCASFL` | Casualty (default) |

### 1.3 Context code → output field (carry-through + shortening)

```
CASE-CONTEXT-CD  →  WS-MOVE  →  NCTC-CONTEXT-CODE
```

- **Plain English:** the case's context code is copied into a work field and then placed into the
  output record's context slot.
- **Why a shortening step exists:** some context codes are **longer than 6 characters**
  (e.g. `CTSCASEX-NY`, `CTSCASNYOP1`, `CTSCASMT-FL`) but a downstream output slot is only **6**
  positions wide. The family handles this by extracting the significant left-most 6 characters
  (via an `UNSTRING`/substring into `WS-CONTEXT-CD6` then `MOVE … (1:6)`), so long codes are
  **normalized/shortened** to fit fixed output while short codes pass through unchanged.
  _(This exact 6-char normalization is documented in the sibling `CASNCTD9`.)_

---

## 2. Dates

```
CASE-INCIDENT-DT  →  (reformat)  →  NCTC-INCIDENT-DATE
CASE-OPEN-DT      →  (reformat)  →  NCTC-OPEN-DATE
CASE-CLOSE-DT     →  (reformat, guarded)  →  NCTC-CLOSE-DATE
system clock      →  (current date)  →  NCTC-EXTRACT-DATE
```

- **Reformat:** DB2 stores dates as `DATE` (yyyy-mm-dd). The output layout may require a compact
  form (e.g. `yyyymmdd` / `ccyymmdd`) or a specific display mask; the value is converted during the
  move.
- **Guarded close date:** if the case is **open**, there is no valid close date, so
  `NCTC-CLOSE-DATE` is written as **spaces/zeros** (a null/low-value guard) rather than a bogus
  date.
- **Validation:** dates are checked for presence/validity; a missing required date is treated per
  the validation rules in [business-rules.md](./business-rules.md).
- **Extract date/timestamp** is stamped from the system clock so downstream systems know when the
  feed was produced; the run's last-run marker is also recorded in `ARTCCKP`.

---

## 3. Open / closed classification

```
CASE-CASE-STATUS-CD  →  (classify)  →  NCTC-OPEN-CLOSED-IND  →  routes to files
```

| Input status | Classification | Output routing |
|--------------|----------------|----------------|
| Status codes meaning "open/active" | **OPEN** (`O`) | `NCTC-OUT` only |
| Status codes meaning "closed/finalized" | **CLOSED** (`C`) | `NCTC-OUT` **and** `CLSD-OUT` **and** `CLSD-EXTR-OUT` |

- **Plain English:** the raw case status code is examined; if it represents a closed/finalized
  case, the record is additionally written to the full closed-case file **and** the thin
  closed-extract file. Open cases go only to the primary NCTCASE feed.
- The raw `CASE-CASE-STATUS-CD` is still copied verbatim into `NCTC-STATUS-CODE`; the derived
  `O/C` indicator is an **additional** normalized field so downstream systems don't need to know
  every status code.

---

## 4. Casualty vs Estate vs Trust vs Mass-tort (product routing)

The **line of business** is encoded in the context code and drives the `TCM-OUT` file:

| Context pattern | Line of business | TCM record? |
|-----------------|------------------|-------------|
| `CTSCAS…` (e.g. `CTSCASNY`, `CTSCASFL`, `CTSCASEX-NY`, `CTSCASMT-FL`) | **Casualty** (incl. mass-tort casualty) | **Yes** — write `TCMCASE-RECORD` |
| `CTSEST…` (e.g. `CTSESTNY`, `CTSESTFL`) | **Estate** | No |
| `CTSTRS…` (e.g. `CTSTRSFL`) | **Trust** | No |

- **Plain English:** if the resolved context code is a **casualty** code, the program emits an
  extra `TCM` record for the casualty subsystem. Estate and trust cases still produce NCTCASE
  (and closed/extract) records but **no** TCM record.
- Mass-tort in Florida (`CTSCASMT-FL`) is treated as a **casualty** variant, so it **does** get a
  TCM record.

---

## 5. Claimant enrichment (ARTINDV join)

```
ARTCASE row  →  (join on CONTEXT_CD + CASE_ID)  →  ARTINDV row  →  claimant fields
```

| Target | Source | Transformation |
|--------|--------|----------------|
| `NCTC-CLMNT-LAST-NM` | `INDV-LAST-NM` | Move, trimmed/space-padded to fixed width |
| `NCTC-CLMNT-FIRST-NM` | `INDV-FIRST-NM` | Move, trimmed/space-padded |
| `NCTC-CLMNT-SSN` | `INDV-SSN` | Move as-is (digits only) |
| `NCTC-CLMNT-DOB` | `INDV-DOB` | Reformat to output date form |
| `TCM-CLMNT-NAME` | `INDV-LAST-NM` + `INDV-FIRST-NM` | **Concatenate** last + first into a single name field |

- If no matching `ARTINDV` row exists, claimant fields are written as **spaces/defaults** and the
  case is still output (see validation rules).

---

## 6. Field-by-field transformation catalog (NCTCASE)

| # | Source → Target | Transformation in plain English |
|---|-----------------|--------------------------------|
| 1 | `CASE-CONTEXT-CD → WS-MOVE → NCTC-CONTEXT-CODE` | Copy context code into work field; **shorten to 6 chars** if longer than the output slot |
| 2 | `CASE-CASE-ID → NCTC-CASE-ID` | Copy case id verbatim |
| 3 | `CASE-ICN-NUM → NCTC-ICN-NUM` | Copy control number verbatim |
| 4 | `CASE-INCIDENT-DT → NCTC-INCIDENT-DATE` | Reformat DB2 date to output date mask |
| 5 | `CASE-OPEN-DT → NCTC-OPEN-DATE` | Reformat date |
| 6 | `CASE-CLOSE-DT → NCTC-CLOSE-DATE` | Reformat date; **blank if open** |
| 7 | `CASE-CASE-STATUS-CD → NCTC-STATUS-CODE` | Copy raw status |
| 8 | `CASE-CASE-STATUS-CD → NCTC-OPEN-CLOSED-IND` | **Derive** `O`/`C` from status |
| 9 | `CASE-STATE-CD → NCTC-STATE-CODE` | Copy state |
| 10 | `CASE-CASE-TYPE-CD → NCTC-CASE-TYPE` | Copy line-of-business type |
| 11 | `INDV-LAST-NM → NCTC-CLMNT-LAST-NM` | Copy, space-pad |
| 12 | `INDV-FIRST-NM → NCTC-CLMNT-FIRST-NM` | Copy, space-pad |
| 13 | `INDV-SSN → NCTC-CLMNT-SSN` | Copy digits |
| 14 | `INDV-DOB → NCTC-CLMNT-DOB` | Reformat date |
| 15 | `CASE-CONTRACT-NUM → NCTC-CONTRACT-NUM` | Copy contract |
| 16 | `system clock → NCTC-EXTRACT-DATE` | Stamp current date |
| 17 | `spaces → NCTC-FILLER` | Pad to 384 bytes |

> Rows 1, 4, 7, 8 are **specified**; the rest are **representative** decompositions of the
> 384-byte record and should be reconciled with the real copybook.

---

## 7. Redefinitions, normalizations, and shortenings — and why

| Item | What happens | Why |
|------|--------------|-----|
| **Context code shortening (16 → 6)** | Long context codes are trimmed to their significant left-most 6 characters via `UNSTRING`/substring | The fixed output slot is only 6 wide; long codes like `CTSCASEX-NY` must fit without corrupting neighboring fields |
| **Date reformatting (DATE → ccyymmdd)** | DB2 `DATE` converted to compact numeric/text | Downstream fixed-format files expect a specific date mask, not the DB2 ISO form |
| **Open/closed derivation** | A 1-char `O/C` flag is added alongside the raw status | Downstream consumers should not need to know every internal status code |
| **Name concatenation (TCM)** | Last + First merged into one field | The TCM layout carries a single name field, not separate parts |
| **Close-date guard** | Blank/zero when case is open | Avoids emitting an invalid or misleading close date |
| **Space padding / FILLER** | Unused trailing bytes set to spaces | Fixed-length records must always be exactly 384 bytes |

---
*See [business-rules.md](./business-rules.md) for the decision rules that decide selection,
classification, and file routing.*
