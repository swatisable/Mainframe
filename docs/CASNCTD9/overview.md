# CASNCTD9 — Overview

> **Scope / source note**
> The task requested analysis of a program named **`CASNCTD1`**. **`CASNCTD1` is not present in the provided repository** (it does not exist in the working tree or in git history) — *Not present in provided source — requires further input.*
> The only mainframe program available in the repository is **`CASNCTD9`** (recovered from the `CASNCTD9_Version2.txt` file that exists in git history). All documentation in this folder describes **`CASNCTD9`**.
>
> **Partial source supplied; analysis limited to visible code.** The program body is complete, but its copybooks, DB2 DCLGENs, called subprograms, and JCL are **not** included and are labeled as *External dependency not analyzed in provided source*.

---

## Program identity

| Attribute | Value (from source) |
|-----------|---------------------|
| Program ID | `CASNCTD9` |
| Type | Batch COBOL program with embedded DB2 SQL (EXEC SQL) |
| Author | `JXZ` |
| Installation | `HMS` |
| Date written | `10/19/2020` |
| Lineage | "THIS PROGRAM CLONED FROM CASNCTD7 FOR NY ONLY" (header comment). Change `0012` also notes a "CLONE OF CASNCTD2". |

## Business purpose (plain language)

CASNCTD9 is a **batch load/update program** that takes a claims extract file and applies it to a set of DB2 "Case Tracking System" tables. Per the header comment:

> "THIS PGM WILL UPDATE DB2 TABLES FROM THE NEW CURRENT GDG OF PCFCASE CLAIMS FILE (NCTCLMS1 300 FILE)."

In plain terms, for each claim record read from the input file the program either **updates an existing claim row** or **inserts a new claim row** (and a related claim-to-case "lookup"/link row) in DB2, deriving a *context code* that identifies the client/state/line-of-business the claim belongs to. It also maintains a per-context primary-key counter table, records progress in a control file for restartability, and reports run statistics to a process-monitor table.

## High-level process overview

1. Display compile date/time banner.
2. Call external routine `CASGETCC` to obtain the 3-byte HMS contract number.
3. Map the contract number to a **context code** and a **last-update user name** (via `EVALUATE`).
4. Load the **NY RX-encounter exclusion list** from the DB2 preferences table `CTSPROD.SEC.ARTSPRF` (change `0028`).
5. Read the DB2 **control file** to determine how many input records were already processed/committed in a prior run, and **skip** that many (restart support).
6. For each remaining input claim record (`1000-MAINLINE`):
   - Refine the context code for multi-context clients using the claim's client id.
   - Transform/normalize input fields into DB2 host variables (dates, amounts, diagnosis codes, VARCHAR lengths).
   - **Look up** the claim (join of `ARTCCLM` + `ARTCLKP`).
   - If found → **UPDATE** `ARTCCLM`; if not found → **INSERT** into `ARTCCLM` (+ `ARTCLKP`), obtaining a new claim id from `ARTCTPK`.
   - Commit every `300` records (checkpoint written to the control file).
7. On end-of-file: final commit, update process monitor with `SUCCESS`, display counters, close files, `GOBACK`.
8. On unrecoverable error: format the SQL error (`DSNTIAR`), `ROLLBACK`, update process monitor with `FAILURE`, and force an abend via `ILBOABN0` with a numeric dump code.

## Key program sections / paragraphs

| Paragraph | Responsibility (from code) |
|-----------|----------------------------|
| `0000-MAIN` | Entry point: banner, get contract number, map context, load exclusions, restart-skip logic, drive mainline loop, final commit/termination. |
| `0500-CREATE-INFILE-CRP` | Read the control file and compute the count of previously committed records to skip. |
| `0600-LOAD-RX-EXCLUSIONS` | Open cursor `ARTSPRF-CSR` and load NY RX-encounter exclusion context codes into a working-storage table. |
| `1000-MAINLINE` | Per-record: derive context, transform fields, look up claim, branch to update or insert, commit at frequency, read next record. |
| `1100-UPDATE-ARTCCLM` | Update an existing `ARTCCLM` claim row. |
| `1200-INSERT-ARTCCLM` | RX-exclusion check; bump `ARTCTPK` primary key; insert `ARTCCLM` and `ARTCLKP`; tally per-context counts. |
| `1210-INSERT-ARTCTPK` | Insert a new `ARTCTPK` primary-key row when none exists for the context. |
| `1900-IMPLICIT-COMMIT` | `COMMIT`, capture timestamp, write checkpoint control record, roll counters. |
| `8000-P-MONITOR` | Update `MISC.P_MONITOR` rows with end time, status, and per-context counts. |
| `9000-TERMINATION` / `9100-DISPLAY-COUNTERS` | Normal-end banner and counter report. |
| `Z9999-ERROR-EXIT` | Error handler: `DSNTIAR`, `ROLLBACK`, counters, `FAILURE` monitor update, abend via `ILBOABN0`. |

## Inputs consumed

| Name | Kind | Notes |
|------|------|-------|
| `NCTC-IN` (DDNAME `NCTCLMI`) | Sequential input file, fixed `316`-char records | The "PCFCASE CLAIMS FILE (NCTCLMS1 300 FILE)"; record layout from copybook `NCTCLMS9` (prefix `CLM`). |
| `CNTL-IO` (DDNAME `DB2CNTLO`) | Sequential control file, `38`-char records | Read at start for restart/checkpoint counts; written at each commit. |
| `CTSPROD.SEC.ARTSPRF` | DB2 table (read) | Preferences; supplies the NY RX-encounter exclusion context list. |
| `ARTCCLM`, `ARTCLKP`, `ARTCTPK` | DB2 tables (read) | Read via singleton SELECTs to look up claims and next primary key. |
| `HMS-3BYTE-CONTRACT-NUM` | Value returned by `CASGETCC` | Drives all context/state routing. |

## Outputs produced

| Name | Kind | Notes |
|------|------|-------|
| `ARTCCLM` | DB2 table (insert/update) | Claim table — primary target. |
| `ARTCLKP` | DB2 table (insert) | Claim lookup / claim-to-case link table. |
| `ARTCTPK` | DB2 table (update/insert) | Per-context primary-key counter table. |
| `MISC.P_MONITOR` | DB2 table (update) | Process-monitor run status and per-context data counts. |
| `CNTL-IO` (DDNAME `DB2CNTLO`) | Control file (write) | Checkpoint records written at each commit. |
| `SYSOUT` (`DISPLAY`) | Job log | Banners, informational/warning/error messages, and end-of-run counters. |
| Abend dump code | Return signal | `ILBOABN0` invoked with a numeric code (e.g., `0998`, `0999`, default `3645`). |

## External dependencies

*All of the following are External dependency not analyzed in provided source:*

- **Copybook** `NCTCLMS9` — input claim record layout (COPY … REPLACING `(PREFIX)` BY `CLM`).
- **DB2 DCLGEN includes**: `CARTCTPK` (for `ARTCTPK`), `ARTCCLM`, `ARTCLKP`, `ARTSPRF`, `PMONITOR`, plus `SQLCA`.
- **Called subprograms**: `CASGETCC` (retrieve contract number), `DSNTIAR` (IBM DB2 message formatter), `ILBOABN0` (IBM abend routine).
- **JCL / GDG definitions**: the "NEW CURRENT GDG" of the PCFCASE claims file and all DD statements (`NCTCLMI`, `DB2CNTLO`) — not provided.

## Notes on assumptions / missing information

- **Data types and lengths of input fields** (copybook `NCTCLMS9`) are *not present in provided source*; only behavior visible in code (e.g., `CLM-CLAIM-TYPE = '12'`, 8-digit date substrings) is documented. Types are not assumed.
- The exact **column definitions** of the DB2 tables are in the DCLGEN copybooks, which are *not present in provided source*; column names and usage are taken from the embedded SQL.
- Several code paths are commented out in the source (e.g., `DPSGTCON` call, `8100-P-MONITOR-INS`); these are noted where relevant but are **not** active logic.
- The record-length arithmetic of the 38-byte control record vs. the `WS-CONTROL-RECORD` layout is *Transformation not fully visible in provided source*; only the documented field roles are asserted.
