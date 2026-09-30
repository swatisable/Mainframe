# CASNCTD9 — Reverse-Engineering / Transformation Specification

> Source program: **CASNCTD9** (COBOL / DB2, batch).
> Author `JXZ`, Installation `HMS`, Date-Written `10/19/2020`.
> Cloned from `CASNCTD7` "for NY only". Latest change markers in source: **0027**
> (populate `RX_WRITTEN_DT` for NY contexts) and **0028** (exclude NY encounter RX
> claims via the `CTSPROD.SEC.ARTSPRF` preferences table).
>
> **Scope note on exhaustiveness.** The output requirement asks that *every field in the
> copybook/table* appear in the field mapping. The record copybook `NCTCLMS9` and all
> DB2 `DCLGEN` copybooks (`CARTCTPK`, `ARTCCLM`, `ARTCLKP`, `ARTSPRF`, `PMONITOR`) are
> **not present in this repository**. Consequently the inventories below are exhaustive
> for **every field the program actually references**, and exact `PIC` clauses / lengths
> for copybook-owned fields are marked **"copybook not available"**. See
> [Section 8 — Assumptions & Gaps](#8-assumptions--gaps).

---

## 1. Program Overview

`CASNCTD9` is a mainframe batch program that loads/updates DB2 "Case Tracking System"
(CTS) claim tables from a sequential PCFCASE claims extract file (the *current GDG* of
the `NCTCLMS1 300` file). For each input claim it decides whether a matching claim row
already exists and then either **updates** it or **inserts** a brand-new claim (allocating
a primary key from a per-context key table and writing a claim-to-case lookup row).

Key behaviours:

- **Restartable / re-runnable.** A control file (`DB2CNTLO`) records how many records have
  already been committed so a re-run skips previously-processed records.
- **Multi-state / multi-context.** A caller-supplied 3-byte HMS contract number selects a
  base *context code* and an 8-char *last-update name*; some contracts further refine the
  context from the claim's client-id (NY `320`, FL `313`, and the "6-char overlay" clients).
- **Commit management.** Work is committed every `SQL-COMMIT-FREQ` (= **300**) DB2 changes,
  with the control record rewritten at each commit for restart accounting.
- **Contention tolerant.** DB2 lock/timeout SQLCODES (`-904/-911/-913`) are retried at the
  record level up to 5 times before abending.
- **Process monitoring.** On completion (success or failure) it updates `MISC.P_MONITOR`
  rows per client/context.
- **NY RX encounter exclusion (mod 0028).** At start-up it reads `CTSPROD.SEC.ARTSPRF` and,
  for the configured contexts, *skips inserts* of RX claims (`CLM-CLAIM-TYPE = '12'`).

Program result codes surfaced via `DUMP-CODE` / `ILBOABN0`:

| Dump / RC | Meaning |
|---|---|
| `+0998` | "Good completion" — input empty, or all records already processed previously (mod 0011). |
| `+0999` | Fatal setup error — contract-number retrieval failed, or unknown contract number. |
| `+3645` | Default `DUMP-CODE` used by `Z9999-ERROR-EXIT` for a DB2/logic abend. |

---

## 2. Inputs, Outputs & External Interfaces

### 2.1 Files

| Logical name | DDNAME | Mode | Record | Layout | Purpose |
|---|---|---|---|---|---|
| `NCTC-IN` | `NCTCLMI` | INPUT, `RECORDING MODE F`, `RECORD CONTAINS 316` | `NCTCLAIM-RECORD` | `COPY NCTCLMS9 REPLACING ==(PREFIX)== BY ==CLM==` | PCFCASE claims extract; one claim per record. |
| `CNTL-IO` | `DB2CNTLO` | INPUT then OUTPUT (re-opened), `F` | `CNTL-RECORD PIC X(38)` | `WS-CONTROL-RECORD` | Restart/control file: read at start to compute a skip count, written at each commit. |

`WS-CONTROL-RECORD` layout (38 bytes):

| Field | PIC | Notes |
|---|---|---|
| `CNTL-PROC-FLAG` | `X(01)` | `'-'` = process/accumulate; `'N'` = bypass control processing. |
| `NUM-REC-OUT` | `ZZZ,ZZZ,ZZ9` | Edited running total of committed records. |
| `FILLER` | `X(02)` | Constant `'++'`. |
| `WS-CURRENT-TIMESTAMP` | `X(26)` | Timestamp of the commit. |

### 2.2 DB2 tables

| Table | DCLGEN INCLUDE | Host-var prefix | Access | Role |
|---|---|---|---|---|
| `DB2AR01.ARTCTPK` | `CARTCTPK` (→ `DCLARTCTPK`) | `CTPK-` | SELECT / UPDATE / INSERT | Per-context primary-key generator (`PK_NEXT_NUM`). |
| `ARTCCLM` | `ARTCCLM` (→ `DCLARTCCLM`) | `CCLM-` | SELECT / UPDATE / INSERT | Claim table (the main target). |
| `ARTCLKP` | `ARTCLKP` (→ `DCLARTCLKP`) | `CLKP-` | SELECT (join) / INSERT | Claim-to-case lookup table. |
| `CTSPROD.SEC.ARTSPRF` | `ARTSPRF` | `NAME-CD`,`VALUE-TXT`,`CONTEXT-CD` | SELECT via `ARTSPRF-CSR` | Preferences; drives NY RX-encounter exclusion (mod 0028). |
| `MISC.P_MONITOR` | `PMONITOR` | `PMONITOR-` | UPDATE | Process-monitor duration/status rows. |
| `SYSIBM.SYSDUMMY1` | — | — | SELECT | Source of `CURRENT TIMESTAMP` for the control record. |

### 2.3 Called subprograms

| Program | Via | Purpose | Failure handling |
|---|---|---|---|
| `CASGETCC` | `CALL WS-CASGETCC USING CASGETCC-CALLING-AREA` | Returns `HMS-3BYTE-CONTRACT-NUM` + `CASGETCC-RETURN-CODE`. | RC ≠ `'0'` → `DUMP-CODE 0999`, `Z9999-ERROR-EXIT`. |
| `DSNTIAR` | `CALL 'DSNTIAR' USING SQLCA ERROR-MESSAGE ERROR-LINE-LENGTH` | Formats DB2 error text (7×80). | Only in `Z9999-ERROR-EXIT`. |
| `ILBOABN0` | `CALL 'ILBOABN0' USING DUMP-CODE` | Forces an abend with a user dump code. | Terminal. |
| `DPSGTCON` | *commented out* | Former contract retrieval (replaced by `CASGETCC`, mod 0007). | N/A |

### 2.4 Copybooks / INCLUDEs

`NCTCLMS9` (record layout, `COPY … REPLACING (PREFIX) BY CLM`), plus `EXEC SQL INCLUDE`
of `SQLCA`, `CARTCTPK`, `ARTCCLM`, `ARTCLKP`, `ARTSPRF`, `PMONITOR`. **None are in the repo.**

---

## 3. Field Mapping (Source → Target)

Legend for the **Transformation** column: *Direct* = value copied unchanged; *UNSTRING* =
`UNSTRING … DELIMITED BY ALL SPACES` (strips trailing spaces and sets the VARCHAR length);
*De-edit* = moved through numeric `WS-DE-EDIT PIC S9(07)V99`; *Date-format* = `YYYYMMDD`
→ `YYYY-MM-DD`; *Derived* = computed (see [Section 7](#7-derived--computed-fields)).

Because the copybooks are unavailable, **all source `CLM-*` PICs and all target column
datatypes are "copybook not available"** unless the program itself fixes a length/format
(those inferred values are stated explicitly, e.g. dates = `CHAR(10)`, `CLMST_RF` length 1).

### 3.1 `ARTCCLM` (claim table) — target of UPDATE (`1100`) and INSERT (`1200`)

| # | Source field (`NCTCLMS9`/derived) | Target column (`ARTCCLM`) | Host var | Transformation | Conditional? |
|---|---|---|---|---|---|
| 1 | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | `CCLM-CONTEXT-CD` | UNSTRING (space-trim) | Yes — context derivation, DT-A/B/C/D |
| 2 | *derived* `PK_NEXT_NUM − 1` | `CLAIM_ID` | `CCLM-CLAIM-ID` | Derived (INSERT); WHERE key (UPDATE) | Insert path only |
| 3 | `CLM-ICN` | `ICN_NUM` | `CCLM-ICN-NUM` | UNSTRING | No |
| 4 | `CLM-FORMER-ICN` | `PREV_ICN_NUM` | `CCLM-PREV-ICN-NUM` | UNSTRING | No |
| 5 | `CLM-RECIPIENT-ID-NUM` | `RECIP_MA_NUM` | `CCLM-RECIP-MA-NUM` | UNSTRING | No |
| 6 | `CLM-PROVIDER-NUM` | `PROVIDER_ID` | `CCLM-PROVIDER-ID` | UNSTRING | No |
| 7 | `CLM-CLAIM-STATUS` | `CLMST_RF` | `CCLM-CLMST-RF` | Direct, length forced to **1** | No |
| 8 | `CLM-TRANSACTION-TYPE` | `TRNTP_RF` | `CCLM-TRNTP-RF` | Direct, length forced to **1** | No |
| 9 | `CLM-CLAIM-TYPE` | `CLMTP_RF` | `CCLM-CLMTP-RF` | UNSTRING | No (also a *switch*, DT-F/K) |
| 10 | `CLM-UNITS-OF-SERVICE` | `UNITS_NUM` | `CCLM-UNITS-NUM` | UNSTRING | No |
| 11 | `CLM-CHARGE-AMT` | `CHARGE_AMT` | `CCLM-CHARGE-AMT` | De-edit `S9(07)V99` | No |
| 12 | `CLM-PAID-AMT` | `PAID_AMT` | `CCLM-PAID-AMT` | De-edit `S9(07)V99` | No |
| 13 | `CLM-DOR-A` | `REMIT_DT` | `CCLM-REMIT-DT` | Date-format → `CHAR(10)` | No |
| 14 | `CLM-SERVICE-DATE-FROM-A` | `SERVICE_FROM_DT` | `CCLM-SERVICE-FROM-DT` | Date-format → `CHAR(10)` | No |
| 15 | `CLM-SERVICE-DATE-TO-A` | `SERVICE_TO_DT` | `CCLM-SERVICE-TO-DT` | Date-format → `CHAR(10)` | No |
| 16 | `CLM-SVC-CODE` | `ICD9P_RF` | `CCLM-ICD9P-RF` | UNSTRING, **truncate len to 10** | **Yes** — only when `CLM-CLAIM-TYPE ≠ '12'` (DT-F) |
| 17 | `CLM-PRIMARY-DIAG-CODE` | `ICD9D_RF` | `CCLM-ICD9D-RF` | Derived (decimal reformat) | **Yes** — DT-G |
| 18 | `CLM-SECOND-DIAG-CODE` | `ICD9D_2ND_RF` | `CCLM-ICD9D-2ND-RF` | Derived (decimal reformat) | **Yes** — DT-G |
| 19 | `CLM-SVC-CODE` | `NDCCD_RF` | `CCLM-NDCCD-RF` | UNSTRING | **Yes** — only when `CLM-CLAIM-TYPE = '12'` (DT-F) |
| 20 | `WS-LAST-UPDATE-NM` (derived) | `LAST_UPDATE_NM` | `CCLM-LAST-UPDATE-NM` | Direct, length **8** | Yes — from contract (DT-A) |
| 21 | *system* `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | — | System | No |
| 22 | `CLM-CREATE-SOURCE` | `CREATE_SOURCE_NM` | `CCLM-CREATE-SOURCE-NM` | Code→text lookup | **Yes** — DT-H |
| 23 | `CLM-CDE-ICD-VERSION` | `ICD_VERSION` | `CCLM-ICD-VERSION` | UNSTRING | No |
| 24 | *literal* `'535'` / `SPACES` | `ALT_CLIENT_CD` | `CCLM-ALT-CLIENT-CD` | Derived | **Yes** — DT-I |
| 25 | `CLM-AGENCY-CODE` | `AGENCY_CD` | `CCLM-AGENCY-CD` | UNSTRING | No |
| 26 | `CLM-COUNTY-CD` | `COUNTY_CD` | `CCLM-COUNTY-CD` | Direct | No |
| 27 | `CLM-RX-WRITTEN-DATE` | `RX_WRITTEN_DT` | `RX-WRITTEN-DT-VALUE` (+ indicator) | Direct w/ NULL indicator | **Yes** — DT-J |

Columns `CREATE_NM` / `CREATE_DTM` are present in the DCLGEN but their INSERT/MOVE lines are
**commented out** (change marker `00XX`, "installed at a later time") → **Not Mapped**
(see Section 8).

### 3.2 `ARTCLKP` (claim-to-case lookup) — target of INSERT (`1200`)

| # | Source | Target column (`ARTCLKP`) | Host var | Transformation | Conditional? |
|---|---|---|---|---|---|
| 1 | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | `CLKP-CONTEXT-CD` | UNSTRING (space-trim) | Yes (context derivation) |
| 2 | `CLM-HMS-CASE-KEY` | `CASE_ID` | `CLKP-CASE-ID` | Direct | No |
| 3 | *derived* `PK_NEXT_NUM − 1` | `CLAIM_ID` | `CLKP-CLAIM-ID` | Derived | No |
| 4 | *literal* `'0'` | `RELATE_IND` | — | Constant | No |
| 5 | `WS-LAST-UPDATE-NM` (derived) | `LAST_UPDATE_NM` | `CLKP-LAST-UPDATE-NM` | Direct, length **8** | Yes (from contract) |
| 6 | *system* `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | — | System | No |
| 7 | *literal* `'N'` | `IS_AUTO_CHECKED` | — | Constant (mod 0019) | No |

`CREATE_NM` / `CREATE_DTM` — **Not Mapped** (commented out, `00XX`).

### 3.3 `ARTCTPK` (primary-key generator) — UPDATE (`1200`) / INSERT (`1210`)

| # | Source | Target column (`ARTCTPK`) | Host var | Transformation | When |
|---|---|---|---|---|---|
| 1 | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | `CTPK-CONTEXT-CD` | UNSTRING | UPDATE & INSERT (key) |
| 2 | *literal* `'CLM'` | `PK_TYPE_CD` | — | Constant | UPDATE key / INSERT value |
| 3 | *expression* `PK_NEXT_NUM + 1` | `PK_NEXT_NUM` | — | Increment | UPDATE |
| 4 | *literal* `+2` | `PK_NEXT_NUM` | — | Seed for a new context | INSERT (`1210`) |
| 5 | *literal* `'CASE TRACKING SYSTEM CLAIM'` | `PK_DSC` | — | Constant | INSERT (`1210`) |
| 6 | `CTPK-PK-MASK-TXT` | `PK_MASK_TXT` | `CTPK-PK-MASK-TXT` | Direct (DCLGEN host var) | INSERT (`1210`) |
| 7 | `WS-LAST-UPDATE-NM` (derived) | `LAST_UPDATE_NM` | `CTPK-LAST-UPDATE-NM` | Direct, length **8** | UPDATE & INSERT |
| 8 | *system* `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | — | System | UPDATE & INSERT |

`ARTCTPK` is also **read** (`SELECT PK_NEXT_NUM − 1, LAST_UPDATE_NM, LAST_UPDATE_DTM`) to
obtain the allocated claim id and to detect concurrent updates (see Section 4 / DT-M).

### 3.4 `MISC.P_MONITOR` — UPDATE (`8000`)

| Column | Source | Notes |
|---|---|---|
| `END_DTM` | `CURRENT TIMESTAMP` | System. |
| `TASK_STEP_TXT` | literal `'LOAD'` | Constant. |
| `STATUS_TXT` | `WS-STATUS-TXT` → `PMONITOR-STATUS-TXT` | `'SUCCESS'` (normal) or `'FAILURE'` (abend path). |
| `DATA_CNT` | `WS-CONTEXT-CD-n-CNT` | Per-context committed-insert count (0 on the "header" update). |
| *(WHERE)* `CLIENT_CD` | `HMS-3BYTE-CONTRACT-NUM` | Predicate. |
| *(WHERE)* `CONTEXT_CD` | `WS-CONTEXT-CD-n` | Predicate (per distinct context). |
| *(WHERE)* `PROCESS_NM` | `LIKE 'CLKP_LOAD_DURATION_%'` | Predicate. |

### 3.5 `CTSPROD.SEC.ARTSPRF` — SELECT (`0600`, cursor)

| Column | Direction | Bound to | Notes |
|---|---|---|---|
| `NAME_CD` | input | `NAME-CD` = `'NY_RX_ENCOUNTER_EXCLUSION'` (len 25) | Predicate. |
| `VALUE_TXT` | input | `UPPER(VALUE_TXT) = 'TRUE'` | Predicate. |
| `CONTEXT_CD` | output | `CONTEXT-CD` → `WS-RX-EXCL-CONTEXT-CD(n)` | Stored space-padded to 16 for later compare. |

### 3.6 Source fields referenced but **not stored** in a target column

| Source field | Role |
|---|---|
| `CLM-HMS-CLIENT-ID` | Drives context refinement for contracts `320/313/326/590/359/645` (DT-B/C/D). Not written directly. |
| `CLM-CLAIM-TYPE` | Written to `CLMTP_RF`, **and** used as a switch for SVC-CODE routing (DT-F) and RX exclusion (DT-K). |

### 3.7 Per-field plain-English & conditional-logic notes

- **`CONTEXT_CD` (all three tables)** — *Plain English:* the "which client/line-of-business
  bucket this claim belongs to" code. *Conditional:* first set from the 3-byte contract
  number (DT-A); for the 6-char-overlay contracts it is partly overwritten from the claim's
  client-id (DT-B); for NY (`320`) and FL (`313`) it is fully re-derived from the client-id
  (DT-C, DT-D). Then trailing spaces are stripped and the VARCHAR length recorded.
- **`CLAIM_ID`** — *Plain English:* the unique claim number. *Conditional:* on the **insert**
  path it is the next value from the per-context key table (`PK_NEXT_NUM − 1`, allocated by
  incrementing `ARTCTPK`); on the **update** path the existing id from the initial SELECT is
  reused as a WHERE key.
- **`CLMST_RF` / `TRNTP_RF`** — single-character reference codes; the program hard-sets the
  VARCHAR length to `1` regardless of the source field width.
- **`ICD9P_RF` vs `NDCCD_RF`** — *Plain English:* the service code lands in the *procedure*
  column for medical claims but in the *national drug code* column for pharmacy claims.
  *Conditional:* `CLM-CLAIM-TYPE = '12'` (RX) → `NDCCD_RF`; otherwise → `ICD9P_RF` and, if
  the resulting length exceeds 10, it is truncated to 10 (mod 0020). See DT-F.
- **`ICD9D_RF` / `ICD9D_2ND_RF`** — *Plain English:* the primary/secondary diagnosis codes,
  normalised to remove an embedded decimal point. *Conditional:* see DT-G.
- **`CHARGE_AMT` / `PAID_AMT`** — passed through a signed numeric work field
  (`S9(07)V99`) to strip any display editing before storing.
- **`REMIT_DT` / `SERVICE_FROM_DT` / `SERVICE_TO_DT`** — reformatted `YYYYMMDD` → `YYYY-MM-DD`
  (see Section 6). No validation is performed.
- **`CREATE_SOURCE_NM`** — decoded from `CLM-CREATE-SOURCE` (`'00'`/`'01'`); any other value
  leaves the field unchanged (DT-H).
- **`ALT_CLIENT_CD`** — `'535'` only for contract `535` (an OH CareSource variant), else spaces
  (DT-I).
- **`RX_WRITTEN_DT`** — pharmacy "written" date; stored as SQL `NULL` (indicator `-1`) when the
  source is spaces/zeros/low-values, else the 10-char value with indicator `+1` (DT-J, mod 0027).
- **`LAST_UPDATE_NM`** — the 8-char batch user-id derived from the contract (DT-A); reused for
  all three tables and for the `ARTCTPK` concurrency check.

---

## 4. Program Flow & Paragraph Structure

| Paragraph | Responsibility |
|---|---|
| `0000-MAIN` | Driver: compile banner → `CASGETCC` → contract→context (DT-A) → load RX exclusions → compute skip count → skip already-processed input → main loop → final commit → P-Monitor SUCCESS → termination. |
| `0500-CREATE-INFILE-CRP` | Read control file, compute how many records to skip on a re-run (DT-T). |
| `0600-LOAD-RX-EXCLUSIONS` | Read `ARTSPRF` into `WS-RX-EXCL-TABLE` (≤ 50 contexts) for NY RX-encounter exclusion (DT-Q). |
| `1000-MAINLINE` | Per record: refine context (DT-B/C/D) → build all host vars → initial SELECT (DT-E) → UPDATE or INSERT → commit-if-due → READ next. |
| `1100-UPDATE-ARTCCLM` | RX-date NULL handling (DT-J) → `UPDATE ARTCCLM` (DT-R). |
| `1200-INSERT-ARTCCLM` | RX-exclusion skip (DT-K) → bump `ARTCTPK` key (DT-L) → read allocated id + concurrency check (DT-M) → RX-date NULL (DT-J) → `INSERT ARTCCLM` + counters (DT-N/U) → `INSERT ARTCLKP` (DT-O). |
| `1210-INSERT-ARTCTPK` | First-time seed of a context key row, `PK_NEXT_NUM = +2` (DT-P). |
| `1900-IMPLICIT-COMMIT` | `COMMIT`, fetch timestamp (SYSDUMMY1, fallback `CURRENT-DATE`), rewrite control record, roll counters. |
| `8000-P-MONITOR` | Update `MISC.P_MONITOR` per distinct context (DT-S/V). |
| `9000-TERMINATION` / `9100-DISPLAY-COUNTERS` | Print end-of-run counters. |
| `Z9999-ERROR-EXIT` | `DSNTIAR` message → `ROLLBACK` → counters → P-Monitor FAILURE → `ILBOABN0` abend (`DUMP-CODE`). |

**Main-loop control** (`0000-MAIN`): `PERFORM 1000-MAINLINE UNTIL CLM-EOF OR TIME-OUT-CTR >= 5`.
After the loop, `TIME-OUT-CTR >= 5` ⇒ `Z9999-ERROR-EXIT`; any residual uncommitted work ⇒ final
`1900-IMPLICIT-COMMIT`.

**Commit trigger** (`1000-MAINLINE`): after each record `ADD +1 TO SQL-NOT-COMMITED-YET-CTR`; when
that counter `>= SQL-COMMIT-FREQ` (**300**) ⇒ `1900-IMPLICIT-COMMIT`.

---

## 5. Decision Tables

> **Shared DB2 contention handler (SC-H).** Referenced by the SQLCODE tables below for
> `-904` (resource unavailable), `-911` (deadlock/timeout, DB2 already rolled back the LUW),
> and `-913` (deadlock/timeout, no automatic rollback):
>
> | Condition | Action |
> |---|---|
> | `SQL-NOT-COMMITED-YET-CTR = 0` (no pending work in the current LUW) | `ADD 1 TO TIME-OUT-CTR`; display attempt; **[ROLLBACK if `TIME-OUT-CTR < 5`]** *(only the variants noted)*; `GO TO 1000-MAINLINE-EXIT` — the current record is **retried** (the `READ` is skipped). The main loop ends once `TIME-OUT-CTR >= 5`, then `Z9999-ERROR-EXIT`. |
> | `SQL-NOT-COMMITED-YET-CTR ≠ 0` (uncommitted work exists) | `GO TO Z9999-ERROR-EXIT` (abend + `ROLLBACK`) to avoid double-applying. |

### DT-A — Contract number → context code & last-update name (`EVALUATE HMS-3BYTE-CONTRACT-NUM`)

| Condition | Input | `WS-CONTEXT-CD` | `WS-LAST-UPDATE-NM` | Notes |
|---|---|---|---|---|
| `= '320'` | `320` | `CTSCASNY` | `WNYCDF40` | New York (further refined by DT-C). |
| `= '300'` | `300` | `CTSCASTST` | `WTTCDF40` | Test contract. |
| `= '326'` | `326` | `CTSCASCO` | `WCOCDF40` | Colorado (6-char overlay, DT-B). |
| `= '341'` | `341` | `CTSCASOH` | `WOHCDF40` | Ohio. |
| `= '535'` | `535` | `CTSCASOH` | `WCXCDF40` | Ohio CareSource; also sets `ALT_CLIENT_CD` (DT-I). |
| `= '313'` | `313` | `CTSCASFL` | `WFLCDF40` | Florida (further refined by DT-D). |
| `= '319'` | `319` | `CTSCASCT` | `WCTCDF40` | Connecticut. |
| `= '317'` | `317` | `CTSWRCCA` | `WCACDF40` | California. |
| `= '590'` | `590` | `CTSCASAL` | `WALCDF40` | Alabama (6-char overlay, DT-B). |
| `= '330'` | `330` | `CTSCASAR` | `WARCDF40` | Arkansas. |
| `= '358'` | `358` | `CTSCASNV` | `WNVCDF40` | Nevada. |
| `= '359'` | `359` | `CTSCASNM` | `WNMCDF40` | New Mexico (6-char overlay, DT-B). |
| `= '645'` | `645` | `CTSCASWV` | `WWVCDF40` | West Virginia (6-char overlay, DT-B). |
| `WHEN OTHER` | any other | *(unchanged)* | *(unchanged)* | **Default:** display "UNKNOWN…", `DUMP-CODE = 0999`, `Z9999-ERROR-EXIT`. |

### DT-B — 6-char client-id overlay (`IF HMS-3BYTE-CONTRACT-NUM = 326/590/359/645`)

| Condition | Action | Notes |
|---|---|---|
| contract ∈ {`326`,`590`,`359`,`645`} | `MOVE CLM-HMS-CLIENT-ID → WS-CONTEXT-CD6 (X6) → WS-CONTEXT-CD(1:6)` | Overlays the first 6 bytes of the context with the claim's client-id. |
| otherwise | *no action* | `313` was formerly in this list but is **commented out** (now handled by DT-D). |

### DT-C — NY refinement (`IF contract = 320`, `EVALUATE CLM-HMS-CLIENT-ID`)

| Input `CLM-HMS-CLIENT-ID` | `WS-CONTEXT-CD` | Meaning (per source comments) |
|---|---|---|
| `CTSCEN` | `CTSCASEX-NY` | Casualty / Exchange / NY. |
| `CTSCCN` | `CTSCASNYC` | Casualty / City / NY. |
| `CTSECN` | `CTSESTNY` | Estate / City / NY. |
| `CTSEEN` | `CTSESTEX-NY` | Estate / Exchange / NY. |
| `CTSCON` | `CTSCASNYOP1` | Casualty / Option 1 / NY (mod 0026). |
| `CTSEON` | `CTSESTNYOP1` | Exchange / Option 1 / NY (mod 0026). |
| `WHEN OTHER` | `CTSCASNY` | **Default** = Casualty NY. |

### DT-D — FL refinement (`IF contract = 313`, `EVALUATE CLM-HMS-CLIENT-ID`)

| Input `CLM-HMS-CLIENT-ID` | `WS-CONTEXT-CD` | Meaning |
|---|---|---|
| `CTSCAS` | `CTSCASFL` | Casualty. |
| `CTSEST` | `CTSESTFL` | Estate. |
| `CTSTRS` | `CTSTRSFL` | Trust. |
| `CTSMST` | `CTSCASMT-FL` | Mass Tort (mod 0023). |
| `WHEN OTHER` | `CTSCASFL` | **Default** = Casualty FL. |

### DT-E — Initial SELECT on `ARTCCLM`/`ARTCLKP` → update vs insert (`EVALUATE SQLCODE`)

| SQLCODE | Output / action | Notes |
|---|---|---|
| `+0` | `PERFORM 1100-UPDATE-ARTCCLM` | Claim already exists. |
| `+100` | `PERFORM 1200-INSERT-ARTCCLM` | New claim. |
| `-811` | Display "MULTIPLE CLAIM_ID…"; `Z9999-ERROR-EXIT` | More than one row for the ICN — data error. |
| `-904` / `-911` / `-913` | **SC-H** (no ROLLBACK variant) | Lock/timeout retry. |
| `WHEN OTHER` | Display error; `Z9999-ERROR-EXIT` | — |

### DT-F — Service-code routing (`IF CLM-CLAIM-TYPE = '12'`)

| Condition | Target | Extra rule |
|---|---|---|
| `CLM-CLAIM-TYPE = '12'` (pharmacy/RX) | `CLM-SVC-CODE` → `NDCCD_RF` (UNSTRING) | — |
| else (medical) | `CLM-SVC-CODE` → `ICD9P_RF` (UNSTRING) | If resulting length `> 10`, force length `= 10` (mod 0020). |

### DT-G — Diagnosis-code decimal normalisation (`CLM-PRIMARY-DIAG-CODE`, `CLM-SECOND-DIAG-CODE`)

`COUNT-M` = number of characters **before the first `'.'`** (`INSPECT … TALLYING … BEFORE INITIAL '.'`).

| Condition (`COUNT-M`) | Transformation | Result → target |
|---|---|---|
| `= 3` | Take chars 1-3 (`WS-DIAG-CODE-41`) + chars 5-7 (`WS-DIAG-CODE-42`), i.e. drop the `'.'` at position 4, concatenated as 6 bytes; UNSTRING (space-trim). | `ICD9D_RF` / `ICD9D_2ND_RF` |
| `> 0` and `≠ 3`, **and** first byte = space | Shift the code left by one (`(2:6) → (1:6)`, blank pos 7), then UNSTRING. | `ICD9D_RF` / `ICD9D_2ND_RF` |
| `> 0` and `≠ 3`, first byte ≠ space | UNSTRING as-is. | `ICD9D_RF` / `ICD9D_2ND_RF` |
| `= 0` (no digits before a `'.'`, e.g. blank/low) | UNSTRING as-is (length may be 0). | `ICD9D_RF` / `ICD9D_2ND_RF` |

### DT-H — Create-source decode (`EVALUATE CLM-CREATE-SOURCE`, mod 0005)

| Input | Output `CREATE_SOURCE_NM` | Notes |
|---|---|---|
| `'00'` | `STANDARD MEDICAID` | — |
| `'01'` | `DSS` | — |
| *(no `WHEN OTHER`)* | *(field left unchanged / spaces)* | **Fall-through:** any other value produces no move — see Section 8. |

### DT-I — Alternate client code (`IF HMS-3BYTE-CONTRACT-NUM = 535`, mod 0016)

| Condition | `ALT_CLIENT_CD` |
|---|---|
| contract `= '535'` | `'535'` |
| else | `SPACES` |

### DT-J — RX-written-date NULL handling (mod 0027; in both `1100` and `1200`)

| Condition | `RX-WRITTEN-DT-VALUE` | Indicator | Stored as |
|---|---|---|---|
| `CLM-RX-WRITTEN-DATE` = SPACES **or** ZEROS **or** LOW-VALUES | `SPACES` | `-1` | SQL `NULL` |
| otherwise | `CLM-RX-WRITTEN-DATE` (10 bytes) | `+1` | the value |

### DT-K — NY RX-encounter exclusion skip (`1200-INSERT-ARTCCLM`, mod 0028)

| Condition | Action |
|---|---|
| `CLM-CLAIM-TYPE = '12'` **AND** `WS-RX-EXCL-CNT > 0` **AND** `WS-CONTEXT-CD` found in `WS-RX-EXCL-TABLE` | `ADD 1 TO WS-RX-EXCL-SKIP-CTR`; `GO TO 1200-INSERT-EXIT` (skip both inserts). |
| otherwise | Proceed with the normal insert path. |

### DT-L — `UPDATE ARTCTPK` (`EVALUATE SQLCODE`, `1200`)

| SQLCODE | Action |
|---|---|
| `+0` | `CONTINUE`. |
| `+100` | `PERFORM 1210-INSERT-ARTCTPK` (first key row for this context). |
| `-904`/`-911`/`-913` | **SC-H** (no ROLLBACK variant). |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

### DT-M — `SELECT … FROM ARTCTPK` (`1200`) + concurrency guard

| SQLCODE | Action |
|---|---|
| `+0` | `CONTINUE`. |
| `-904`/`-911`/`-913` | **SC-H** *with* `ROLLBACK` when `TIME-OUT-CTR < 5`. |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

Follow-on guard: if `CTPK-LAST-UPDATE-NM-TEXT(1:len) ≠ WS-LAST-UPDATE-NM` ⇒ "UNCOMMITTED
INTERVENTION TO ARTCTPK" ⇒ `Z9999-ERROR-EXIT` (another job changed the key row mid-LUW).

### DT-N — `INSERT INTO ARTCCLM` (`EVALUATE SQLCODE`, `1200`)

| SQLCODE | Action |
|---|---|
| `+0` | `ADD 1 TO SQL-INSERT-CTR`; run context-counter cascade (DT-U). |
| `-904`/`-911`/`-913` | **SC-H** *with* `ROLLBACK` when `TIME-OUT-CTR < 5`. |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

### DT-O — `INSERT INTO ARTCLKP` (`EVALUATE SQLCODE`, `1200`)

| SQLCODE | Action |
|---|---|
| `+0` | `CONTINUE`. |
| `-904`/`-911`/`-913` | **SC-H** *with* `ROLLBACK` when `TIME-OUT-CTR < 5`. |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

### DT-P — `INSERT INTO ARTCTPK` (`EVALUATE SQLCODE`, `1210`)

| SQLCODE | Action |
|---|---|
| `+0` | Display "NEW PK_TYPE_CD = 'CLM' INSERTED". |
| `-904`/`-911`/`-913` | **SC-H** (no ROLLBACK variant). |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

### DT-Q — `FETCH ARTSPRF-CSR` loop (`EVALUATE SQLCODE`, `0600`)

| SQLCODE | Action |
|---|---|
| `+0` | If `WS-RX-EXCL-CNT < 50`: store `CONTEXT-CD` (space-padded to 16); else display "TABLE FULL" warning and ignore. |
| `+100` | `SET CSR-EOF TO TRUE` (end the loop). |
| `WHEN OTHER` | Display error; `Z9999-ERROR-EXIT`. |

*(Cursor OPEN/CLOSE also check SQLCODE: OPEN ≠ 0 ⇒ error exit; CLOSE ≠ 0 ⇒ warning only.)*

### DT-R — `UPDATE ARTCCLM` (`EVALUATE SQLCODE`, `1100`)

| SQLCODE | Action |
|---|---|
| `+0` | `ADD 1 TO SQL-UPDATE-CTR`. |
| `-904`/`-911`/`-913` | **SC-H** (no ROLLBACK variant). |
| `WHEN OTHER` | `Z9999-ERROR-EXIT`. |

### DT-S — `UPDATE MISC.P_MONITOR` (`EVALUATE SQLCODE`, `8000`)

| SQLCODE | Action | Notes |
|---|---|---|
| `+0` | Display "UPDATED P-MONITOR"; `COMMIT`. | — |
| `+100` | Display "P-MONITOR ROW NON-EXISTANT" advisory. | **No abend** — completion is not blocked. |
| `WHEN OTHER` | Display error; `MOVE 0 TO SQLCODE` (swallowed); continue. | The `GO TO Z9999-ERROR-EXIT` is **commented out** — monitor failures are non-fatal. |

### DT-T — Control-file skip accounting (`0500`, `IF CNTL-PROC-FLAG`)

| Condition (per control record) | Action |
|---|---|
| `CNTL-PROC-FLAG = '-'` and `WS-CNTL-RECS-OUT > WS-CNTL-RECS-OUT-HOLD` | New high-water mark: `HOLD = OUT`. |
| `CNTL-PROC-FLAG = '-'` and `WS-CNTL-RECS-OUT ≤ HOLD` | Close a run: `TOT += HOLD`; `HOLD = OUT`. |
| after EOF | `TOT += HOLD` → `WS-CNTL-RECS-OUT-TOT` = records to skip. |
| `CNTL-PROC-FLAG = 'N'` | Display "BYPASS DB2 CONTROL FILE PROCESSING". |

### DT-U — Distinct-context counter cascade (`1200`, on insert `+0`)

Step 1 (seed): for slot *n* = 1..7, `IF WS-CONTEXT-CD-n-CNT = 0 THEN WS-CONTEXT-CD-n = WS-CONTEXT-CD`.
Step 2 (count): first matching slot wins.

| Condition | Action |
|---|---|
| `WS-CONTEXT-CD = WS-CONTEXT-CD-1` | `ADD 1 TO WS-CONTEXT-CD-1-CNT` |
| else `= WS-CONTEXT-CD-2` | `ADD 1 TO WS-CONTEXT-CD-2-CNT` |
| else `= WS-CONTEXT-CD-3` | `ADD 1 TO WS-CONTEXT-CD-3-CNT` |
| else `= WS-CONTEXT-CD-4` | `ADD 1 TO WS-CONTEXT-CD-4-CNT` |
| else `= WS-CONTEXT-CD-5` | `ADD 1 TO WS-CONTEXT-CD-5-CNT` |
| else `= WS-CONTEXT-CD-6` | `ADD 1 TO WS-CONTEXT-CD-6-CNT` (mod 0026) |
| else `= WS-CONTEXT-CD-7` | `ADD 1 TO WS-CONTEXT-CD-7-CNT` (mod 0026) |

Supports up to **7 distinct contexts** per run (a job may span several contexts, e.g. NY DT-C).

### DT-V — Per-context `P_MONITOR` updates (`8000`)

| Slot | Condition to issue the UPDATE |
|---|---|
| 1 | `WS-CONTEXT-CD-1 ≠ SPACES` |
| 2..7 | `WS-CONTEXT-CD-n ≠ SPACES` **AND** `WS-CONTEXT-CD-n ≠ WS-CONTEXT-CD-(n-1)` |

The adjacent-inequality guard suppresses duplicate/empty context updates.

### DT-W — Initial skip-read outcome (`0000-MAIN`, `READ … AT END`)

| Condition at AT END | Action |
|---|---|
| `REC-READ-CTR = 0` | Display "PCFCASE CLAIMS FILE IS EMPTY". |
| `REC-READ-CTR ≠ 0` | Display "ALL n INPUT RECORDS HAVE BEEN PROCESSED PREVIOUSLY". |
| either | `DUMP-CODE = 0998`; `Z9999-ERROR-EXIT` (good completion). |
| NOT AT END | `ADD 1 TO REC-READ-CTR` (count the skipped record). |

---

## 6. Date Handling & Data Validation

### 6.1 Date validation
The program performs **no explicit date validation** — no format checks, range checks, or
leap-year handling on the claim dates. `CLM-DOR-A`, `CLM-SERVICE-DATE-FROM-A`,
`CLM-SERVICE-DATE-TO-A` are treated as valid `YYYYMMDD` and only *reformatted*. An invalid
inbound value is passed to DB2 and, if the target column is a `DATE`, would fail there
(surfaced through the `WHEN OTHER` SQLCODE branches). **Invalid-date default:** none in-program.

### 6.2 Date conversion

| Source | Target | Rule |
|---|---|---|
| `CLM-DOR-A` (`YYYYMMDD`) | `CCLM-REMIT-DT` | Insert `'-'` at positions 5 and 8 → `YYYY-MM-DD` (`CHAR(10)`). |
| `CLM-SERVICE-DATE-FROM-A` | `CCLM-SERVICE-FROM-DT` | Same `YYYYMMDD → YYYY-MM-DD`. |
| `CLM-SERVICE-DATE-TO-A` | `CCLM-SERVICE-TO-DT` | Same `YYYYMMDD → YYYY-MM-DD`. |
| `FUNCTION WHEN-COMPILED` (26-char) | `WS-WHEN-COMPILED-DISP` | Cosmetic display re-order to `MM/DD/YY HH:MM` (`MM=(5:2)`, `DD=(7:2)`, `YY=(3:2)`, `HH=(9:2)`, `MI=(11:2)`). |

No Julian↔Gregorian conversion exists.

### 6.3 Normalization / windowing / timezone
- **Century windowing:** not applicable to claim dates (source carries a full 4-digit year).
  The only 2-digit year is the **cosmetic** compile-date display (`WS-COMP-YY`); it is never
  stored. No 2-digit-year expansion logic exists.
- **Timezone:** none. All stored timestamps use DB2 `CURRENT TIMESTAMP` (server local time).
- **`RX_WRITTEN_DT` (mod 0027):** passed through as a 10-byte value assumed already `YYYY-MM-DD`;
  **not** reformatted or validated. Only spaces/zeros/low-values are normalised to SQL `NULL`
  (DT-J).
- **Control-record timestamp:** `SELECT DISTINCT(CURRENT TIMESTAMP) FROM SYSIBM.SYSDUMMY1`
  → `WS-CURRENT-TIMESTAMP`; on any non-zero SQLCODE it falls back to `FUNCTION CURRENT-DATE`.

### 6.4 Numeric validation
- **Amounts:** `CLM-CHARGE-AMT` / `CLM-PAID-AMT` are moved through `WS-DE-EDIT PIC S9(07)V99`
  to strip any display editing before storing into `CHARGE_AMT` / `PAID_AMT`. There is no
  explicit sign normalisation or zero/blank defaulting beyond standard COBOL `MOVE` semantics.
  **Capacity:** values ≥ 10,000,000.00 overflow the 7-integer-digit work field and lose
  high-order digits (see Section 8).
- **Lengths:** `ICD9P_RF` VARCHAR length is capped at **10** (mod 0020). `CLMST_RF` / `TRNTP_RF`
  lengths are hard-set to **1**.
- **COMP / COMP-3:** all internal counters are `COMP`/`COMP-3`; the program does not convert
  packed input fields itself (the copybook governs their storage).

### 6.5 String validation
- **Trailing-space trim + VARCHAR length:** most host variables are produced with
  `UNSTRING … DELIMITED BY ALL SPACES … COUNT IN …`, giving the trimmed text and its length
  (context, ICN, former-ICN, recipient, provider, claim-type, units, svc-code, ICD version,
  agency code, diag codes).
- **Context space-strip:** `WS-CONTEXT-CD` (X16) is UNSTRING-trimmed before being applied to
  all three tables.
- **RX-exclusion compare:** stored context values are **space-padded to 16** so the equality
  test against `WS-CONTEXT-CD` is consistent (DT-K/Q).
- **Diagnosis codes:** embedded `'.'` removed or a leading space shifted out (DT-G).
- **Case normalisation:** only in SQL — `UPPER(VALUE_TXT) = 'TRUE'` in the `ARTSPRF` predicate.
  No case folding of data fields.

---

## 7. Derived / Computed Fields

| Derived field | Formula / Logic | Source field(s) | Notes |
|---|---|---|---|
| `WS-CONTEXT-CD` | Contract→base code, then client-id refinement/overlay | `HMS-3BYTE-CONTRACT-NUM`, `CLM-HMS-CLIENT-ID` | DT-A/B/C/D. |
| `WS-LAST-UPDATE-NM` | Contract→8-char user-id | `HMS-3BYTE-CONTRACT-NUM` | DT-A; feeds all 3 tables + concurrency check. |
| `CCLM-CLAIM-ID` / `CLKP-CLAIM-ID` | `PK_NEXT_NUM − 1` (after `UPDATE ARTCTPK SET PK_NEXT_NUM = PK_NEXT_NUM + 1`) | `ARTCTPK.PK_NEXT_NUM` | Insert path only; allocates a new key. |
| `CCLM-CHARGE-AMT` / `CCLM-PAID-AMT` | De-edit through `S9(07)V99` | `CLM-CHARGE-AMT` / `CLM-PAID-AMT` | Strips editing; 2 implied decimals. |
| `CCLM-REMIT-DT` / `SERVICE-FROM-DT` / `SERVICE-TO-DT` | `YYYYMMDD → YYYY-MM-DD` | `CLM-DOR-A` / `…FROM-A` / `…TO-A` | `CHAR(10)`. |
| `CCLM-ICD9D-RF` / `ICD9D-2ND-RF` | Remove `'.'` (COUNT-M = 3) or left-shift leading space | `CLM-PRIMARY-DIAG-CODE` / `CLM-SECOND-DIAG-CODE` | DT-G. |
| `CCLM-ICD9P-RF` **or** `CCLM-NDCCD-RF` | Route by claim type; ICD9P length ≤ 10 | `CLM-SVC-CODE`, `CLM-CLAIM-TYPE` | DT-F. |
| `CCLM-CREATE-SOURCE-NM` | Code → descriptive text | `CLM-CREATE-SOURCE` | DT-H. |
| `CCLM-ALT-CLIENT-CD` | `'535'` when contract 535, else spaces | `HMS-3BYTE-CONTRACT-NUM` | DT-I. |
| `RX-WRITTEN-DT-VALUE` + `RX-WRITTEN-DT-INDICATOR` | NULL vs value | `CLM-RX-WRITTEN-DATE` | DT-J. |
| `WS-CNTL-RECS-OUT-TOT` | Rolling accumulation of prior committed counts | Control file `NUM-REC-OUT` | DT-T; = records to skip. |
| `CRP-IN` | `WS-CNTL-RECS-OUT-TOT + 1` | (above) | Number of skip-reads to perform. |
| `WS-CONTEXT-CD-n-CNT` (n = 1..7) | Per-context committed-insert tally | `WS-CONTEXT-CD` | DT-U; feeds P-Monitor + counters. |
| `SQL-INSERT-COMMITTED-CTR` / `SQL-UPDATE-COMMITTED-CTR` / `SQL-TOT-COMMITTED-CTR` | Running sums applied at each commit | `SQL-INSERT-CTR`, `SQL-UPDATE-CTR` | `1900-IMPLICIT-COMMIT`. |
| `WS-WHEN-COMPILED-DISP` | Re-ordered compile timestamp | `FUNCTION WHEN-COMPILED` | Cosmetic. |
| `WS-CURRENT-TIMESTAMP` | `SYSDUMMY1` timestamp or `FUNCTION CURRENT-DATE` | DB2 / system | Control record. |
| Constants on INSERT | `RELATE_IND='0'`, `IS_AUTO_CHECKED='N'`, `PK_TYPE_CD='CLM'`, `PK_DSC='CASE TRACKING SYSTEM CLAIM'`, seed `PK_NEXT_NUM=+2` | literals | Not source-driven. |

---

## 8. Assumptions & Gaps

**Missing source artefacts (cannot be resolved from the provided source):**

- **`NCTCLMS9` record copybook is absent.** Exact `PIC` clauses, lengths, and byte offsets of
  every `CLM-*` field are **unknown**, and the full 316-byte record layout cannot be listed.
  Any copybook field that the program does **not** reference cannot be enumerated. → *Needs
  clarification (provide `NCTCLMS9`).*
- **DCLGEN copybooks absent** (`CARTCTPK`, `ARTCCLM`, `ARTCLKP`, `ARTSPRF`, `PMONITOR`). Target
  column datatypes/lengths are **inferred from usage only** (e.g. dates `CHAR(10)`;
  `CLMST_RF`/`TRNTP_RF` length 1; `LAST_UPDATE_NM` length 8; context ≤ 16; VARCHAR text/length
  split). → *Needs clarification for authoritative column definitions.*
- **`CASGETCC` is a black box.** How the 3-byte HMS contract number is derived is external;
  only its output + return code are consumed.

**Intentionally deferred / not mapped:**

- `ARTCCLM.CREATE_NM` / `CREATE_DTM` and `ARTCLKP.CREATE_NM` / `CREATE_DTM` — **Not Mapped**;
  the populating code is commented out under change marker `00XX` ("this change will be
  installed at a later time").

**Behavioural ambiguities to confirm with the business:**

- **DT-H has no `WHEN OTHER`.** A `CLM-CREATE-SOURCE` other than `'00'`/`'01'` performs no move.
  In practice `1000-MAINLINE` starts with `INITIALIZE DCLARTCCLM`, so `CREATE_SOURCE_NM` is
  spaces for unrecognised codes — but this relies on the initialise and is not an explicit
  default. → *Confirm intended default.*
- **Amount capacity.** `WS-DE-EDIT` is `S9(07)V99`; charge/paid amounts ≥ 10,000,000.00 would
  lose high-order digits. → *Confirm maximum expected amount.*
- **Date trust.** Claim dates are reformatted without validation; the process assumes upstream
  data is clean. Malformed dates abend at DB2. → *Confirm upstream validation guarantees.*
- **`RX_WRITTEN_DT` format.** Assumed already `YYYY-MM-DD`; not validated/reformatted.
- **`P_MONITOR` rows** are assumed to pre-exist (row-not-found is advisory, non-fatal — DT-S).
- **`-913`** is handled defensively though a source comment states it "will never be received
  in our installation".
- Business meaning of context codes / contract numbers is taken from **source comments** and is
  not independently authoritative.

**Repository state:**

- The raw `CASNCTD9` source is **not** committed to this repository — it was removed by merged
  **PR #1** as an "obsolete root-level file" (`CASNCTD9_Version2.txt`). This specification was
  reconstructed from that file in Git history (commit `251e770`). If the source should live
  under `docs/CASNCTD9/`, that is a separate decision. → *Needs clarification.*

---

### Appendix — Change markers referenced

`0005` create-source decode · `0007` `CASGETCC` + AL · `0010` ICD version / diag reformat ·
`0011` RC 0998 empty-input · `0012` claim-status in lookup · `0016` OH CareSource (535) /
`ALT_CLIENT_CD` · `0019` `IS_AUTO_CHECKED` · `0020` ICD9P 10-byte cap · `0021` NY contexts ·
`0023` FL Mass-Tort · `0024` WV · `0026` NY OP1 contexts / 6th–7th context counters ·
`0027` `RX_WRITTEN_DT` · `0028` NY RX-encounter exclusion (`ARTSPRF`).
