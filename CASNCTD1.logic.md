# CASNCTD1 — Logic Documentation

> Strictly source-based analysis of COBOL program **`CASNCTD1`** (source file `CASNCTD1.txt`).
> Every statement below is traceable to the source. Where something cannot be proven from the
> provided artifacts it is explicitly marked **Not proven from source**, **Inferred from
> structure/usage**, **Open question**, or **Referenced but implementation not available**.

---

# 1. Analysis Method

## 1.1 Artifacts inspected

| Artifact | Status | Notes |
|---|---|---|
| `CASNCTD1.txt` | **Inspected (full, 1,455 lines)** | The program under analysis. |
| `NCTCASE` copybook (`NCTCASE.txt`) | **Inspected** | `COPY NCTCASE REPLACING ==(PREFIX)== BY ==NCTC==` at line 129 — defines the 384-byte output record. |
| `SQLCA` | **Referenced but implementation not available** | `EXEC SQL INCLUDE SQLCA` (line 247). Standard DB2 communication area. |
| `PMONITOR` | **Referenced but implementation not available** | `EXEC SQL INCLUDE PMONITOR` (line 251). Supplies `PMONITOR-*` host variables. |
| `ARTCASE` DCLGEN | **Referenced but implementation not available** | `EXEC SQL INCLUDE ARTCASE` (line 287). Supplies `DCLARTCASE` / `CASE-*` host variables. |
| `ARTINDVL` DCLGEN | **Referenced but implementation not available** | `EXEC SQL INCLUDE ARTINDVL` (line 293). Supplies `DCLARTINDV` / `INDV-*` host variables. |
| `ARTCCKP` DCLGEN | **Referenced but implementation not available** | `EXEC SQL INCLUDE ARTCCKP` (line 299). Supplies `DCLARTCCKP` / `CCKP-*` host variables. |
| `CASGETCC` program | **Referenced but implementation not available** | Dynamically called (line 501) to return the contract number. |
| `DSNTIAR` | **Referenced (IBM DB2 utility)** | Called (line 1439) to format SQL error messages. |
| `ILBOABN0` | **Referenced (IBM LE/COBOL abend routine)** | Called (line 1454) to force an abend. |
| JCL / control cards | **Not provided** | DDNAMEs `NCTCASO`, `TCMCASO`, `CLSDO`, `CLSDEXTO`, `NCTCLMI`(n/a) are `ASSIGN` targets resolved by JCL that is not in the repository. |

## 1.2 How logic was traced
- The single `PROCEDURE DIVISION` (starting line 474) was read paragraph by paragraph following
  every `PERFORM ... THRU`, `GO TO`, `EVALUATE`, and `IF`.
- Each embedded `EXEC SQL` block (18 in total) was read in place: 2 `DECLARE CURSOR`, 2 `OPEN`,
  2 `FETCH`, 2 `CLOSE`, 1 `UPDATE`, 1 `INSERT`, 2 `SET`, 2 `COMMIT`, plus 5 `INCLUDE`.
- The output record map was derived directly from the `NCTCASE` copybook and cross-checked: the
  computed field byte positions sum to exactly **384**, matching `FD NCTC-OUT ... PIC X(384)`.

## 1.3 Proven vs inferred handling
- **Proven** = literally present in `CASNCTD1.txt` or the `NCTCASE` copybook.
- **Inferred** = a reasonable reading of structure/usage (e.g., a host variable's business meaning)
  that is *not* fully confirmed because the DCLGEN copybooks are absent. These are labelled inline.
- Field data types for `CASE-*`, `INDV-*`, `CCKP-*`, and `PMONITOR-*` host variables come from
  copybooks that are **not** in the repository; their exact `PIC` clauses are therefore **not proven**.

## 1.4 Limitations
- The five `INCLUDE`/DCLGEN members and the `CASGETCC` subprogram are unavailable, so:
  - exact host-variable pictures and lengths are unknown;
  - the mechanism `CASGETCC` uses to obtain the contract number is unknown;
  - the physical DB2 column definitions are known only by the names used in the SQL.
- No JCL is present, so dataset attributes (DISP, DCB, GDG generation, sort steps) are unknown.
- Business meaning of context codes / client numbers is stated **only where a program comment
  confirms it**; otherwise it is marked inferred.

---

# 2. Program Overview

## 2.1 Identification (proven)
| Attribute | Value | Source |
|---|---|---|
| Program-ID | `CASNCTD1` | line 2 |
| Author | `LLL` | line 3 |
| Installation | `HMS` | line 4 |
| Date-Written | `10/07/2003` | line 5 |
| Latest logged change | `0029 07/16/25 ... CTSCASNJ - MAINFRAME CLAIM PULL` | lines 78–80 |

## 2.2 Purpose (proven — from header comment lines 8–13)
> "THIS PGM WILL SELECT DATA FROM DB2 TABLES AND CREATE NEW GENERATION OF CASUALTY CASE FILE
> (NCTCASE 384 FILE). IT WILL ALSO CREATE 2 FILES OF CLOSED CASES. THIS PROGRAM REPLACES PGM
> CASPCFM0. OLD PROCESS WAS BASED ON CASUALTY FILE FROM THE LAN. NEW PROCESS RETRIEVES DATA FROM
> DB2 TABLES."

So the program is a **DB2‑to‑sequential‑file extract**: it reads casualty **case** data joined to
**individual** data from DB2, reformats each row into a fixed 384‑byte record, and writes it to a
main output file plus (conditionally) a TCM file, a closed‑case file, and a closed‑case key file.

## 2.3 Technical role (proven)
- **Invocation style:** Main batch program. It ends with `MOVE WS-RETURN-CODE TO RETURN-CODE` then
  `GOBACK` (lines 497–498). It also `CALL`s the subprogram `CASGETCC` (line 501). **Inferred:** it is
  the driving program of a batch job step (consistent with `GOBACK`, `RETURN-CODE`, and DDNAME
  `ASSIGN`s), but the JCL step is **not provided**.
- **Processing model:** Sequential, cursor-driven, read-only against DB2 (`FOR READ ONLY` on both
  cursors, lines 355 & 469). The only DB2 writes are to the `MISC.P_MONITOR` monitoring table
  (`UPDATE` line 1276, `INSERT` line 1384).

## 2.4 Business role (proven where commented, otherwise inferred)
- Produces a **"casualty case" extract** keyed by HMS client/case identifiers (header comment).
- Each run targets **one contract** (a 3‑byte contract number returned by `CASGETCC`), which is
  translated into one or more DB2 **context codes** used to filter the case rows.
- **Inferred from structure/usage:** the program is part of a recurring (daily/weekly) "claim pull"
  pipeline — several change entries reference "MAINFRAME DAILY AND WEEKLY CLAIM PULLS" (e.g. lines
  71–77). The scheduling itself is **Not proven from source**.

## 2.5 Upstream / downstream dependencies
| Direction | Dependency | Evidence | Status |
|---|---|---|---|
| Upstream | `CASGETCC` returns the 3‑byte contract number | `CALL WS-CASGETCC` line 501 | **Referenced, implementation not available** |
| Upstream | DB2 tables `DB2AR01.ARTCASE`, `ARTINDV`, `ARTCCKP` | cursor `FROM` clauses (lines 342–343, 399–400, 452–454) | **Proven (names)**; table DDL not available |
| Upstream/Downstream | `MISC.P_MONITOR` monitoring table | `UPDATE`/`INSERT` (lines 1276, 1384) | **Proven** |
| Downstream | 4 output datasets (`NCTCASO`, `TCMCASO`, `CLSDO`, `CLSDEXTO`) | `SELECT ... ASSIGN` (lines 91–94) | **Proven (DDNAMEs)**; consumers not in repo |

---

# 3. Inputs, Outputs, and Dependencies

## 3.1 DB2 inputs (proven from SQL)
| Table (alias) | Purpose per comment | Used by | Access |
|---|---|---|---|
| `ARTCASE` (`A`) | "CASE TABLE" (comment line 15) | both cursors | `SELECT ... FOR READ ONLY` |
| `ARTINDV` (`I`) | "INDIVIDUAL TABLE" (comment line 16) | both cursors | `SELECT ... FOR READ ONLY` |
| `ARTCCKP` (`L`) | "CASE LKUP TABLE (AL ONLY)" (comment line 17) | `NCT_CSR_AL` UNION leg only | `SELECT ... FOR READ ONLY` |
| `MISC.P_MONITOR` | Process monitor | `8000`/`8100` | `UPDATE`, `INSERT` |

> The qualifier `DB2AR01` is named in the comment header (lines 15–17); the SQL itself uses
> unqualified `ARTCASE`/`ARTINDV`/`ARTCCKP`, so the run-time schema is resolved by the DB2 plan/
> package (**not provable from source**).

## 3.2 Sequential output files (proven from `FILE-CONTROL` / `FD`)
| Logical name | DDNAME (`ASSIGN`) | FD record | Length | Written in |
|---|---|---|---|---|
| `NCTC-OUT` | `NCTCASO` | `NCTCASE-RECORD` | `PIC X(384)` | main write, every row (lines 667, 716) |
| `TCM-OUT` | `TCMCASO` | `TCMCASE-RECORD` | `PIC X(384)` | only when `TCM-CONTRACT` true (lines 672, 721) |
| `CLSD-OUT` | `CLSDO` | `CLOSED-RECORD` | `PIC X(384)` | only when status = `'C'` (lines 681, 730) |
| `CLSD-EXTR-OUT` | `CLSDEXTO` | `CLSD-EXTRACT-RECORD` | `PIC X(09)` | only when status = `'C'` (lines 684, 733) |

All four are opened `OUTPUT` together (lines 487–490) and closed together (lines 493–496).

## 3.3 Copybooks / linkage
| Copybook | Role | Status |
|---|---|---|
| `NCTCASE` | 01 `WS-NCTCASE-RECORD` output layout, prefix `NCTC` | **Present & inspected** |
| `SQLCA`, `PMONITOR`, `ARTCASE`, `ARTINDVL`, `ARTCCKP` | DB2 comm area, monitor host vars, DCLGENs | **Referenced, not available** |
| `LINKAGE SECTION` | none | The program has **no** `LINKAGE SECTION`; it is not a called subprogram in this build. `CASGETCC-CALLING-AREA` (WORKING-STORAGE, lines 219–224) is the parameter block **it passes to** `CASGETCC`. |

## 3.4 Called programs
| Called | How | Purpose (proven) |
|---|---|---|
| `CASGETCC` | `CALL WS-CASGETCC USING CASGETCC-CALLING-AREA` (line 501); `WS-CASGETCC PIC X(08) VALUE 'CASGETCC'` (line 218) | Returns `HMS-3BYTE-CONTRACT-NUM` and `CASGETCC-RETURN-CODE`. |
| `DSNTIAR` | `CALL 'DSNTIAR' USING SQLCA, ERROR-MESSAGE, ERROR-LINE-LENGTH` (line 1439) | Formats DB2 error text into `ERROR-MESSAGE-LINE`. |
| `ILBOABN0` | `CALL 'ILBOABN0' USING DUMP-CODE` (line 1454) | Forces an abend with `DUMP-CODE`. |

## 3.5 Control-card / profile dependencies
- The contract that a run processes is **not** a literal in this program; it is provided at run time
  by `CASGETCC` via `HMS-3BYTE-CONTRACT-NUM`. How `CASGETCC` obtains it (PARM, control card, table)
  is **Not proven from source**.

## 3.6 Important status codes / flags (proven)
| Name | Definition | Meaning in code |
|---|---|---|
| `NCT-CSR-FLAG` (88 `START-OF-NCT-CSR`='S', `END-OF-NCT-CSR`='E') | line 135–137 | cursor open/EOF state |
| `SQLCODE` | from `SQLCA` | checked after every OPEN/FETCH/CLOSE/UPDATE/INSERT |
| `TIME-OUT-CTR` `PIC S9(01) COMP-3` | line 232 | counts OPEN retries; loop guard is `>= 5` |
| `WS-RETURN-CODE` `PIC 9(02)` VALUE 0 | line 134 | job return code (0 normal, 04 no data) |
| `DUMP-CODE` `PIC S9(04) COMP` VALUE `+3645` | line 132 | abend code passed to `ILBOABN0` |

**DB2 SQLCODEs explicitly handled:** `+0` (ok), `+100` (row not found / end of cursor), `-904`,
`-911`, `-913` (retryable resource/timeout/deadlock — treated as retry on OPEN), any `OTHER` (fatal).

---

# 4. Data Structures and Important Fields

## 4.1 Output record — `NCTCASE` copybook (proven layout)
`COPY NCTCASE REPLACING ==(PREFIX)== BY ==NCTC==` → all fields below carry the `NCTC-` prefix.
Byte positions are computed from the `PIC` clauses (USAGE DISPLAY assumed, as none is coded); the
total is **384**, equal to the FD length.

| Pos | Len | Field | PIC | Populated from (in `1300-FORMAT-NCTCASE-REC` unless noted) |
|---:|---:|---|---|---|
| 1–6 | 6 | `NCTC-HMS-CLIENT-ID` | X(06) | `WS-MOVE(1:6)` = shortened context code (line 1048) |
| 7–15 | 9 | `NCTC-HMS-CASE-KEY` | 9(09) | `CASE-CASE-ID` (line 1050); also copied to closed-key extract |
| 16–35 | 20 | `NCTC-RECIPIENT-ID-NUM` | X(20) | `INDV-MA-NUM-TEXT(1:len)` (line 1127) |
| 36–44 | 9 | `NCTC-CASE-SOURCE-CODE` | 9(09) | `WS-MOVE(1:9)` from `CASE-CASE-SOURCE-CD` (line 1114) |
| 45–48 | 4 | `NCTC-CASE-TYPE-CODE` | 9(04) | `WS-MOVE(1:4)` from `CASE-CASE-TYPE-CD` (line 1103) |
| 49 | 1 | `NCTC-CASE-STATUS-CODE` | X(01) | `WS-MOVE(1:1)` from `CASE-CASE-STATUS-CD` (line 1106) — **drives O/C/other routing** |
| 50–53 | 4 | `NCTC-CASE-STAGE-CODE` | 9(04) | `WS-MOVE(1:4)` from `CASE-CASE-STAGE-CD` (line 1111) |
| 54–57 | 4 | `NCTC-CASE-PRIORITY-CODE` | 9(04) | `WS-MOVE(1:4)` from `CASE-CASE-PRIORITY-CD` (line 1109) |
| 58–67 | 10 | `NCTC-CASE-OPEN-DATE` | X(10) | `CASE-CASE-OPEN-DT` (line 1100) |
| 68–77 | 10 | `NCTC-CASE-CLOSE-DATE` | X(10) | `CASE-CASE-CLOSE-DT` (line 1101) |
| 78–102 | 25 | `NCTC-LAST-NAME` | X(25) | `INDV-LAST-NM` (line 1134) |
| 103–122 | 20 | `NCTC-FIRST-NAME` | X(20) | `INDV-FIRST-NM` (line 1135) |
| 123 | 1 | `NCTC-MIDDLE-INIT` | X(01) | `INDV-MI-NM` (line 1136) |
| 124 | 1 | `NCTC-SEX` | X(01) | `WS-MOVE(1:1)` from `INDV-GENCD-RF` (line 1139) |
| 125–133 | 9 | `NCTC-SSN` | X(09) | `INDV-SSN-NUM` (line 1133) |
| 134–143 | 10 | `NCTC-DATE-OF-BIRTH` | X(10) | `INDV-DOB-DT` (line 1137) |
| 144 | 1 | `NCTC-MARITAL-STATUS` | X(01) | `WS-MOVE(1:1)` from `INDV-MARST-RF` (line 1141) |
| 145–159 | 15 | `NCTC-SETTLEMENT-AMT` | S9(13)V9(02) | `CASE-SETTLEMENT-AMT` (line 1124) |
| 160–174 | 15 | `NCTC-EXPENSES-AMT` | S9(13)V9(02) | `CASE-EXPENSES-AMT` (line 1116) |
| 175–189 | 15 | `NCTC-COMPROMISE-AMT` | S9(13)V9(02) | `CASE-COMPROMISE-AMT` (line 1115) |
| 190–204 | 15 | `NCTC-LIEN-MEDICAID-AMT` | S9(13)V9(02) | `CASE-LIEN-MEDICAID-AMT` (line 1120) |
| 205–219 | 15 | `NCTC-LIEN-ADJUST-AMT` | S9(13)V9(02) | `CASE-LIEN-ADJUST-AMT` (line 1118) |
| 220–229 | 10 | `NCTC-LIEN-NOTICE-DATE` | X(10) | `CASE-LIEN-NOTICE-DT` (line 1121) |
| 230–239 | 10 | `NCTC-LIEN-RELEASE-DATE` | X(10) | `CASE-LIEN-RELEASE-DT` (line 1122) |
| 240–249 | 10 | `NCTC-INCIDENT-DATE` | X(10) | `WS-NEW-FROM-DATE` (line 1099) — **see §5.6 incident-date rule**; overwritten for TCM write |
| 250–259 | 10 | `NCTC-CLAIMS-THRU-DATE` | X(10) | `CASE-DOS-TO-DT` (line 1062) |
| 260 | 1 | `NCTC-REGISTERED-IND` | X(01) | `SPACES` (line 1142) |
| 261 | 1 | `NCTC-ALL-CLAIMS-IND` | X(01) | `SPACES` (line 1143) |
| 262 | 1 | `NCTC-THERAPY-IND` | X(01) | `SPACES` (line 1144) |
| 263–267 | 5 | `NCTC-ATTOR-FEE-PCT` | 9V9(04) | `CASE-ATTORNEY-FEE-PCT` (line 1125) |
| 268–282 | 15 | `NCTC-FEE-ADJUST-AMT` | S9(13)V9(02) | `CASE-FEE-ADJUST-AMT` (line 1117) |
| 283–288 | 6 | `NCTC-WEL-NUM` | X(06) | `WS-MOVE(1:6)` from `CASE-WEL-NUMBER-CD` (line 1061) |
| 289–298 | 10 | `NCTC-LIKELY-SETTLE-DATE` | X(10) | `CASE-LIKELY-SETTLE-DT` (line 1123) |
| 299–313 | 15 | `NCTC-LIEN-HMO-AMT` | S9(13)V9(02) | `CASE-LIEN-HMO-AMT` (line 1119) |
| 314–319 | 6 | `NCTC-CASE-WORKER-IPKEY` | 9(06) | `WS-MOVE(1:6)` from `CASE-USER-CD` (line 1055) |
| 320–329 | 10 | `NCTC-COUNTY-CODE` | X(10) | `WS-MOVE(1:10)` from `CASE-COUNTY-CD` (line 1059) |
| 330–355 | 26 | `NCTC-LAST-UPDATE-TMS` | X(26) | `CASE-LAST-UPDATE-DTM` (line 1126) |
| 356–384 | 29 | `NCTC-MF-HIT-DATA` group | — | see redefine below |

**Group `NCTC-MF-HIT-DATA` (356–384) and its redefine `NCTC-FILLER-1`:**

| Pos | Len | Primary field | PIC | Redefine field | PIC |
|---:|---:|---|---|---|---|
| 356 | 1 | `NCTC-MF-HIT-IND` | X(01) | `NCTC-INDV-ID` (356–367) | 9(12) ← `CASE-INDV-ID` (line 1052) |
| 357–365 | 9 | `NCTC-MF-HITS-LAST-RUN` | X(09) | (part of `NCTC-INDV-ID`) | |
| 366–374 | 9 | `NCTC-MF-HITS-CUMMULATIVE` | X(09) | `NCTC-CLIENT-CD` (368–372) | X(05) ← Alabama client (line 1132) |
| 375–384 | 10 | `NCTC-MF-HIT-LAST-DTS` | X(10) | `NCTC-FILLER-2` (373–384) | X(12) ← `SPACES` (line 1149) |

> The copybook comments `LLL01`/`LLL02` say this area is "REDEFINE MF-HIT AREA FOR DIFFERENT USE".
> `CASNCTD1` writes the **redefine** view (`NCTC-INDV-ID`, `NCTC-CLIENT-CD`, `NCTC-FILLER-2`); the
> `MF-HIT` sub-fields are only referenced in commented-out lines 1145–1148, so they are **not**
> populated by this program.

## 4.2 Contract → context-code driver fields (proven)
- `HMS-3BYTE-CONTRACT-NUM PIC X(03)` (line 220) — the run's contract, from `CASGETCC`.
- `WS-CONTEXT-CD` … `WS-CONTEXT-CD6`, each `PIC X(16)` (lines 183–189) — up to 7 context codes;
  unused slots hold `'ZZZZZZZZZZZZZZZZ'` (initialised lines 522–527).
- `WS-CURSOR-VALUES` variable-length host structures `CASE-CONTEXT-CD*-T/-L` (lines 254–282) — the
  UNSTRING'd (space-trimmed) context codes bound into the cursor `WHERE` clause.

## 4.3 Scenario-driving 88-levels (proven)
| 88-level | On field | Values | Effect |
|---|---|---|---|
| `VALID-FROM-DATE` | `WS-EDIT-FROM-DATE` | `'1800-01-01' THRU '2199-12-31'` (lines 140–141) | gates the incident-date recalculation (§5.6) |
| `TCM-CONTRACT` | `WS-CASUALTY-CODE` | `CTSCASCT`, `CTSCASNV`, `CTSCASAL` (lines 144–150) | triggers the extra `TCM-OUT` write |
| `CASUALTY-CONTRACT` | `WS-CASUALTY-CODE` | 20 casualty/estate/trust codes (lines 151–182) | triggers the "‑60 days" incident-date adjustment |

## 4.4 Counters (proven — `WS-COUNTERS`, lines 226–235)
| Counter | PIC | Incremented when |
|---|---|---|
| `REC-WRITE-CTR` | S9(07) COMP‑3 | every main `NCTC-OUT` write |
| `TCM-WRITE-CTR` | S9(07) COMP‑3 | every `TCM-OUT` write |
| `OPEN-NCTC-REC-CTR` | S9(07) COMP‑3 | status = `'O'` |
| `CLOSED-NCTC-REC-CTR` | S9(07) COMP‑3 | status = `'C'` |
| `OTHER-NCTC-REC-CTR` | S9(07) COMP‑3 | status not `'O'`/`'C'` |
| `TIME-OUT-CTR` | S9(01) COMP‑3 | each retryable OPEN failure |
| `WS-TOTAL-CONTEXT-CDS` / `WS-START-CONTEXT-CDS` / `WS-WRITTEN-CONTEXT-CNT` | — | P‑Monitor bookkeeping (§5.8) |

`NUM-REC-OUT PIC ZZZ,ZZZ,ZZ9` (line 233) is an edited display field used only in `9000-TERMINATION`.

---

# 5. Processing Logic

## 5.1 Paragraph inventory (proven)
| Paragraph | Lines | Role |
|---|---|---|
| `0000-MAIN` | 475–498 | open files, drive mainline/monitor/termination, close, `GOBACK` |
| `1000-MAINLINE` | 500–752 | get contract, map context codes, choose cursor, fetch/format/write loop |
| `1100-OPEN-NCT-CSR` / `1100-OPEN-EXIT` | 754–806 | build host vars, `OPEN NCT_CSR` with retry |
| `1200-FETCH-NCT-CSR` / `1200-FETCH-EXIT` | 808–865 | `FETCH NCT_CSR`, handle `+100`/errors |
| `1300-FORMAT-NCTCASE-REC` / `1300-FORMAT-EXIT` | 867–1151 | map one DB2 row → `WS-NCTCASE-RECORD` |
| `2100-OPEN-NCT-CSR` / `2100-OPEN-EXIT` | 1153–1212 | build host vars, `OPEN NCT_CSR_AL` with retry |
| `2200-FETCH-NCT-CSR` / `2200-FETCH-EXIT` | 1214–1273 | `FETCH NCT_CSR_AL`, handle `+100`/errors |
| `8000-P-MONITOR` / `8000-P-MONITOR-EXIT` | 1275–1320 | update/insert `MISC.P_MONITOR` |
| `8100-P-MONITOR-INS` / `8100-PM-INS-EXIT` | 1322–1411 | insert one monitor row per context code |
| `9000-TERMINATION` / `9000-TERMINATION-EXIT` | 1413–1435 | print counters |
| `Z9999-ERROR-EXIT` | 1437–1455 | format SQL error, abend via `ILBOABN0` |

## 5.2 Top-level flow (`0000-MAIN`, proven)
1. Display compile date/time derived from `FUNCTION WHEN-COMPILED` (lines 478–486).
2. `OPEN OUTPUT` all four files (487–490).
3. `PERFORM 1000-MAINLINE THRU 1000-MAINLINE-EXIT` (491).
4. `PERFORM 8000-P-MONITOR THRU 8000-P-MONITOR-EXIT` (492).
5. `PERFORM 9000-TERMINATION THRU 9000-TERMINATION-EXIT` (493).
6. `CLOSE` all four files (493–496).
7. `MOVE WS-RETURN-CODE TO RETURN-CODE` then `GOBACK` (497–498).

## 5.3 Startup validation — get contract (`1000-MAINLINE`, proven)
- `CALL WS-CASGETCC USING CASGETCC-CALLING-AREA` (501).
- **If `CASGETCC-RETURN-CODE NOT = '0'`** → display error, `MOVE +0999 TO DUMP-CODE`,
  `GO TO Z9999-ERROR-EXIT` (504–508) → **abend**.

## 5.4 Context-code mapping (`EVALUATE HMS-3BYTE-CONTRACT-NUM`, proven — lines 528–607)
All context slots are first set to `'ZZZZZZZZZZZZZZZZ'` (522–527), then the matched `WHEN` populates
`WS-CONTEXT-CD`…`-CD6`. `WHEN OTHER` (604–606) displays "UNKNOWN HMS-3BYTE-CONTRACT-NUM" and
`GO TO Z9999-ERROR-EXIT` → **abend**.

**Full contract → context-code map (exactly as coded):**

| Contract | Context codes populated | Cursor used (§5.5) |
|---|---|---|
| `300` | CTSCASTST | NCT_CSR |
| `303` | CTSCASNJ | NCT_CSR_AL |
| `309` | CTSESTMI | NCT_CSR |
| `313` | CTSCASFL, CTSESTFL, CTSTRSFL, CTSCASMT-FL | NCT_CSR_AL |
| `316` | CTSCASIA, CTSESTIA | NCT_CSR |
| `317` | CTSWRCCA | NCT_CSR |
| `319` | CTSCASCT | NCT_CSR |
| `320` | CTSCASNY, CTSCASNYC, CTSCASEX-NY, CTSESTNY, CTSESTEX-NY, CTSCASNYOP1, CTSESTNYOP1 | NCT_CSR_AL |
| `326` | CTSCASCO, CTSESTCO, CTSCASCO-HCPF | NCT_CSR |
| `330` | CTSCASAR | NCT_CSR_AL |
| `333` | CTSCASKY, CTSESTKY | NCT_CSR |
| `335` | CTSCASKS, CTSESTKS | NCT_CSR |
| `341` | CTSCASOH | NCT_CSR_AL |
| `358` | CTSCASNV, CTSESTNV, CTSTRSNV, CTSTFRNV | NCT_CSR_AL |
| `359` | CTSCASNM, CTSESTNM, CTSTRSNM | NCT_CSR_AL |
| `395` | CTSCASNC, CTSESTNC | NCT_CSR |
| `396` | CTSCASGA, CTSESTGA | NCT_CSR |
| `444` | CTSCASMS, CTSESTMS | NCT_CSR |
| `534` | CTSCASUH-AZ | NCT_CSR |
| `535` | CTSCASOH (client forced to `341`, §5.5) | NCT_CSR_AL |
| `537` | CTSCASCS-MI | NCT_CSR |
| `547` | CTSDOHFL | NCT_CSR |
| `561` | CTSCASWC-GA | NCT_CSR |
| `564` | CTSCASTN | NCT_CSR_AL |
| `585` | CTSCASAZ, CTSESTAZ | NCT_CSR |
| `590` | CTSCASAL, CTSESTAL, CTSTRSAL | NCT_CSR_AL |
| `593` | CTSESTTX | NCT_CSR |
| `633` | CTSCASHP-NC | NCT_CSR |
| `645` | CTSCASWV, CTSESTWV, CTSCASCH-WV | NCT_CSR_AL |

> **Proven code observation (duplicate `WHEN '564'`):** `'564'` appears twice — first at line 584
> (active line 586 sets `CTSCASTN`), and again at line 602 (`WHEN '564' MOVE 'CTSCASTN'`). A COBOL
> `EVALUATE` executes only the **first** matching `WHEN`, so the second `'564'` is **unreachable dead
> code**. Both set the same value, so behaviour is unaffected.
>
> **State associations** (e.g. "313 = Florida") are taken from the program's own comments (lines
> 639–652 and the modification history). Where only the code name suggests a state it is **inferred**.

After mapping, `WS-TOTAL-CONTEXT-CDS` is set to the count of populated slots (1–7) by testing which
slot first equals `'ZZ…Z'` (`EVALUATE TRUE`, lines 618–633). This count is used by P‑Monitor (§5.8).

## 5.5 Cursor selection (proven — lines 635–750)
```
INITIALIZE DCLARTCASE DCLARTINDV DCLARTCCKP
IF HMS-3BYTE-CONTRACT-NUM = '590' OR '320' OR '341' OR '313' OR '330'
                         OR '358' OR '359' OR '645' OR '535' OR '564' OR '303'
    → AL path : 2100-OPEN-NCT-CSR / 2200-FETCH-NCT-CSR  (cursor NCT_CSR_AL)
ELSE
    → standard path : 1100-OPEN-NCT-CSR / 1200-FETCH-NCT-CSR (cursor NCT_CSR)
END-IF
```
- **`NCT_CSR`** (lines 304–356): join `ARTCASE A` × `ARTINDV I` on `INDV_ID` + `CLIENT_CD`, filtered
  by up to 7 context codes `OR`-ed together **and** `A.CLIENT_CD = :CASE-CLIENT-CD`,
  `I.CLIENT_CD = :INDV-CLIENT-CD`.
- **`NCT_CSR_AL`** (lines 360–470): a `UNION` of
  1. the same `A × I` join (with `I.CLIENT_CD` selected), and
  2. `A × I × ARTCCKP L` where `L.CONTEXT_CD = A.CONTEXT_CD AND L.CASE_ID = A.CASE_ID AND
     L.CASLK_RF = 'MA_NUM'`, selecting `L.DATA_TXT` in the MA-number position.
  The comment (lines 37–39 of the header, change 0007) explains this leg "EXTRACT[s] ALL MA NBRS
  FROM ARTCCKP FOR THE MA RECIPIENT IN EACH CASE".
- **Special case `535` (OH CareSource):** in `2100`, `IF HMS-3BYTE-CONTRACT-NUM = '535'` the DB2
  filter client is forced to `'341'` (`MOVE '341' TO CASE-CLIENT-CD INDV-CLIENT-CD`, lines 1185–1191);
  otherwise the 3‑byte contract itself is used.

Both OPEN paragraphs first `UNSTRING` each `WS-CONTEXT-CD*` (delimited by all spaces) into the
variable-length host `CASE-CONTEXT-CD*-T/-L` (lines 755–782 / 1154–1183), then set the client host
variables and `OPEN` the cursor.

## 5.6 Row processing loop (proven — identical body in both paths)
For each successful `FETCH` (`SQLCODE +0`):
1. `PERFORM 1300-FORMAT-NCTCASE-REC` — build `WS-NCTCASE-RECORD`.
2. `WRITE NCTCASE-RECORD FROM WS-NCTCASE-RECORD`; `ADD 1 TO REC-WRITE-CTR`.
3. **TCM branch:** `IF TCM-CONTRACT` → `MOVE CASE-INCIDENT-DT TO NCTC-INCIDENT-DATE`,
   `WRITE TCMCASE-RECORD FROM WS-NCTCASE-RECORD`, `ADD +1 TO TCM-WRITE-CTR` (lines 670–674 / 719–723).
4. **Status branch** (`EVALUATE TRUE`, lines 676–687 / 725–736):
   - `NCTC-CASE-STATUS-CODE = 'O'` → `ADD 1 TO OPEN-NCTC-REC-CTR`.
   - `NCTC-CASE-STATUS-CODE = 'C'` → `ADD 1 TO CLOSED-NCTC-REC-CTR`;
     `WRITE CLOSED-RECORD FROM WS-NCTCASE-RECORD`; `MOVE NCTC-HMS-CASE-KEY TO CLSD-EXTRACT-RECORD`;
     `WRITE CLSD-EXTRACT-RECORD`.
   - `WHEN OTHER` → `ADD 1 TO OTHER-NCTC-REC-CTR`.
5. `INITIALIZE DCLARTCASE DCLARTINDV DCLARTCCKP`.

> **Proven ordering side-effect:** the TCM branch (step 3) overwrites `NCTC-INCIDENT-DATE` **before**
> the status branch (step 4). Therefore, for a row that is **both** `TCM-CONTRACT` and status `'C'`,
> the `CLSD-OUT` record carries the **original** `CASE-INCIDENT-DT`, not the ±60‑day value written to
> `NCTC-OUT`. (See §7 edge cases.)

### 5.6.1 Incident-date rule inside `1300-FORMAT` (proven — lines 1064–1099)
`WS-CASUALTY-CODE` is loaded with the row's context code (line 1064). Then:

| `DOS-FROM` valid? | `INCIDENT` valid? | `CASUALTY-CONTRACT`? | `NCTC-INCIDENT-DATE` result |
|---|---|---|---|
| Yes | — | Yes | `DATE(DOS-FROM) - 60 DAYS` (DB2 `SET`, line 1074) |
| Yes | — | No | `DOS-FROM` unchanged |
| No | Yes | Yes | `DATE(INCIDENT) - 60 DAYS` (DB2 `SET`, line 1088) |
| No | Yes | No | `INCIDENT` unchanged |
| No | No | — | `INCIDENT` unchanged (raw value) |

"Valid" = the 88 `VALID-FROM-DATE` range `1800-01-01`…`2199-12-31`. The comment for change 0015
(lines 47–63 of header) matches this behaviour.

## 5.7 Context-code shortening in `1300-FORMAT` (proven — lines 868–1048)
For contracts `320`, `313`, `326`, `358`, `645`, `564`, the long context code in `WS-MOVE` is mapped
to a fixed 6‑character output code, e.g. (contract 320/NY): `CTSCASEX-NY→CTSCEN`, `CTSCASNYC→CTSCCN`,
`CTSESTNY→CTSECN`, `CTSESTEX-NY→CTSEEN`, `CTSCASNYOP1→CTSCON`, `CTSESTNYOP1→CTSEON`, `OTHER→CTSCAS`.
Similar `EVALUATE`s exist for 313 (FL), 326 (CO), 358 (NV), 645 (WV), 564 (TN). The first 6 bytes of
the resulting `WS-MOVE` become `NCTC-HMS-CLIENT-ID` (line 1048). Contracts not in this list keep the
first 6 characters of their (single) context code.

## 5.8 Cursor close & mainline exit (proven)
After the loop, the active cursor is closed (`CLOSE NCT_CSR_AL` line 692 / `CLOSE NCT_CSR` line 741).
A non-zero `SQLCODE` on close → `Z9999-ERROR-EXIT`.

## 5.9 P‑Monitor update (`8000`/`8100`, proven — lines 1275–1411)
- `UPDATE MISC.P_MONITOR SET START_DTM=CURRENT TIMESTAMP, END_DTM=NULL, TASK_STEP_TXT='LOAD',
  STATUS_TXT='RUNNING', DATA_CNT=0 WHERE CLIENT_CD=:HMS-3BYTE-CONTRACT-NUM AND PROCESS_NM LIKE
  'CLKP_LOAD_DURATION_%'` (1276–1284).
- `SQLCODE +0`: compare `SQLERRD(3)` (rows updated) with `WS-TOTAL-CONTEXT-CDS`. If **not equal**,
  some context codes are new → `PERFORM 8100-P-MONITOR-INS ... UNTIL WS-WRITTEN-CONTEXT-CNT = +7`,
  then `COMMIT` (1294–1309).
- `SQLCODE +100` (no monitor row exists): `PERFORM 8100-P-MONITOR-INS ... 7 TIMES` (1310–1313).
- `OTHER`: error → `Z9999-ERROR-EXIT`.
- `8100-P-MONITOR-INS` walks context slots 0–6, building `PROCESS_NM = 'CLKP_LOAD_DURATION_'` +
  context code, and `INSERT`s one `MISC.P_MONITOR` row per real context code (skipping `'ZZ…Z'`
  slots via `GO TO 8100-PM-INS-EXIT`), `COMMIT`ting after each insert.

## 5.10 Termination (`9000`, proven — lines 1413–1435)
Displays a banner and five counters: records written, TCM records written, open, closed, and other.
No file or DB2 action here. Return code was already set (0 or 04).

---

# 6. Extracted Business Logic

> Expressed as source-backed rules. "Contract" = `HMS-3BYTE-CONTRACT-NUM`; "context code" = the DB2
> `CONTEXT_CD` filter values.

1. **Contract resolution** — *When the program starts, it shall obtain the 3‑byte contract number
   from `CASGETCC`. If `CASGETCC` returns a code other than `'0'`, the program shall abend with dump
   code `0999`.* (lines 501–508)
2. **Contract validation** — *If the contract number does not match any coded `WHEN`, the program
   shall abend* ("UNKNOWN HMS-3BYTE-CONTRACT-NUM"). (lines 604–606)
3. **Context selection** — *Each contract maps to a fixed set of 1–7 context codes* used to select
   the case rows. (EVALUATE §5.4)
4. **Cursor routing** — *Contracts 590, 320, 341, 313, 330, 358, 359, 645, 535, 564, 303 shall use
   the Alabama-style cursor (`NCT_CSR_AL`, which UNIONs in `ARTCCKP` MA-number lookup rows); all
   other contracts shall use the standard cursor (`NCT_CSR`).* (lines 639–642)
5. **OH CareSource remap** — *When the contract is 535, the DB2 selection client shall be 341* (while
   the output client id still derives from the context code). (lines 1185–1191)
6. **Row inclusion** — *A case row is included only if it joins to an individual on
   `INDV_ID`+`CLIENT_CD` and its `CONTEXT_CD` matches one of the run's context codes and its
   `CLIENT_CD` matches the run client.* (cursor `WHERE`)
7. **Incident-date lookback** — *For casualty contracts, the output incident date shall be the valid
   `DOS_FROM_DT` (or, if that is invalid, the valid `INCIDENT_DT`) minus 60 days; for non‑casualty
   contracts the date is used unchanged; if neither date is valid, the raw `INCIDENT_DT` is used.*
   (§5.6.1)
8. **TCM duplicate output** — *For contracts whose context code is `CTSCASCT`, `CTSCASNV`, or
   `CTSCASAL`, the program shall also write the row to the TCM file using the original (un‑adjusted)
   incident date.* (lines 670–674 / 719–723)
9. **Status routing / closed-case extraction** — *When a case status is `'O'` it is counted as open;
   when `'C'` it is counted as closed and additionally written to the closed-case file and its
   9‑digit case key is written to the closed-key extract; any other status is counted as "other".*
   (lines 676–687 / 725–736)
10. **Output client id** — *For multi-context contracts (320, 313, 326, 358, 645, 564) the long
    context code shall be translated to a fixed 6‑character output client id; otherwise the first 6
    characters of the context code are used.* (§5.7)
11. **Alabama recipient/client handling** — *For the AL cursor, the MA-number position may be sourced
    from `ARTCCKP.DATA_TXT`, and `I.CLIENT_CD` (received into `CCKP-DATA-AMT`) is reformatted into the
    output `NCTC-CLIENT-CD`.* (lines 1127–1132, cursor UNION)
12. **No-data outcome** — *If no rows are returned, the program shall warn and set return code 04.*
    (lines 854–859 / 1262–1267)
13. **Process monitoring** — *The program shall mark the `MISC.P_MONITOR` "CLKP_LOAD_DURATION_*"
    rows for the client as RUNNING, and insert monitor rows for any context codes not already
    present.* (§5.9)

---

# 7. Error Handling and Edge Cases

## 7.1 DB2 status handling (proven)
| Operation | `+0` | `+100` | `-904/-911/-913` | `OTHER` |
|---|---|---|---|---|
| OPEN (1100/2100) | set `START-OF-NCT-CSR` | n/a | display, `ADD 1 TO TIME-OUT-CTR`, exit para (retry) | `Z9999-ERROR-EXIT` |
| FETCH (1200/2200) | continue | set `END-OF-NCT-CSR`; if `REC-WRITE-CTR = 0` warn + RC=04 | n/a | `Z9999-ERROR-EXIT` |
| CLOSE (692/741) | continue | n/a | n/a | `Z9999-ERROR-EXIT` |
| UPDATE P_MONITOR (1276) | update path | insert-7 path | n/a | `Z9999-ERROR-EXIT` |
| INSERT P_MONITOR (1384) | `COMMIT` | n/a | n/a | `Z9999-ERROR-EXIT` |

## 7.2 OPEN retry / timeout protection (proven)
`PERFORM 2100/1100 ... UNTIL START-OF-NCT-CSR OR TIME-OUT-CTR >= 5` (lines 654–658 / 703–707). On a
retryable SQLCODE the OPEN paragraph increments `TIME-OUT-CTR` and returns; after **5** failures the
mainline does `GO TO Z9999-ERROR-EXIT` (abend). **Inferred:** `-904/-911/-913` are DB2
resource-unavailable / timeout / deadlock; the comment at line 794/1200 notes `-913` "will never be
received in our installation".

## 7.3 Abend path (`Z9999-ERROR-EXIT`, proven — lines 1437–1455)
- If `SQLCODE NOT = +0`, call `DSNTIAR` and display the 7 formatted `ERROR-MESSAGE-LINE`s.
- Display "PGM CASNCTD1 ABENDED", `CALL 'ILBOABN0' USING DUMP-CODE`, `GOBACK`.
- `DUMP-CODE` = `+3645` by default, or `+0999` if reached from the `CASGETCC` failure.

## 7.4 Return codes (proven)
| RC | Cause |
|---|---|
| `00` | normal (default `WS-RETURN-CODE`) |
| `04` | cursor returned `+100` with **zero** rows written (no matching data) |
| abend (`ILBOABN0`) | contract error, unknown contract, OPEN timeout (5x), or any fatal SQLCODE |

## 7.5 Edge cases & observations (proven from code)
- **Closed TCM row incident date:** overwrite ordering (§5.6) means a `TCM-CONTRACT` + `'C'` row has
  the *original* incident date in `CLSD-OUT`. Whether intended is an **open question**.
- **Duplicate `WHEN '564'`** — dead but harmless (§5.4).
- **`INITIALIZE` before FETCH** — `1200`/`2200` initialise `DCLARTCASE`/`DCLARTINDV`(`/DCLARTCCKP`)
  before every fetch, so `VALUE(...,' ')`/`VALUE(...,0)` in the cursor guarantee non-null host values.
- **`NCTC-INCIDENT-DATE` "invalid" pass-through:** if both dates fail the `VALID-FROM-DATE` test, the
  raw `INCIDENT_DT` (possibly spaces from the `VALUE(...,' ')` default) is written unchanged.

## 7.6 Restart / recovery (proven scope)
- No checkpoint/restart logic is present. The only `COMMIT`s are around `MISC.P_MONITOR`
  writes (lines 1308, 1403). The four output files are sequential `OUTPUT` (re-created each run).
  **Inferred:** re-run safety depends on JCL (GDG/DISP), which is **not provided**.

---

# 8. Proven vs Inferred vs Unknown

## 8.1 Proven from source
- Program id, author, install, date; purpose (header comments).
- Four output files, their DDNAMEs, record layouts, and exact write conditions.
- Both cursor definitions, their tables/joins/filters, and which contracts use which cursor.
- The full contract → context-code map, incl. the duplicate `WHEN '564'`.
- The incident-date "‑60 days" decision logic and the `VALID-FROM-DATE` range.
- Status routing (`O`/`C`/other), TCM write condition, closed-key extract.
- Counters, return codes (00/04), abend path and dump codes.
- `MISC.P_MONITOR` update/insert behaviour and the `CLKP_LOAD_DURATION_*` naming.
- The `NCTCASE` 384-byte record map (positions sum to 384).

## 8.2 Inferred from structure/usage
- Business meaning of each context code / state (comments confirm many, not all).
- `-904/-911/-913` semantics (DB2 resource/timeout/deadlock).
- The program is a scheduled batch step in a claim-pull pipeline.
- Host-variable business meaning where only the name is available.

## 8.3 Open questions / not proven
- Exact `PIC`/lengths of all `CASE-*`, `INDV-*`, `CCKP-*`, `PMONITOR-*` host variables (DCLGENs
  `ARTCASE`, `ARTINDVL`, `ARTCCKP`, `PMONITOR` not in repo).
- How `CASGETCC` determines the contract number (subprogram not in repo).
- Physical DB2 schema (`DB2AR01` qualifier is a comment only), plan/package, and table DDL.
- JCL: dataset attributes, GDG handling, sort steps, downstream consumers.
- Whether the closed-TCM incident-date overwrite is intentional.
- The `MISC.P_MONITOR` column order in the positional `INSERT` (line 1384) — the `VALUES` list is
  positional and the copybook defining the columns is unavailable.
