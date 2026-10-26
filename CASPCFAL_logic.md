# CASPCFAL — Program Logic & Extracted Business Rules

> **Audit-grade · Evidence-based · Zero-hallucination**
>
> Every non-trivial statement below carries an evidence tag:
>
> | Tag | Meaning |
> |-----|---------|
> | ✅ **Proven** | Directly visible in code (paragraph + line / exact snippet) |
> | 🔍 **Inferred** | Reasonable inference from data flow/structure (chain shown) |
> | ❓ **Open** | Cannot be determined from available source (artifact named) |
> | 📎 **Missing artifact** | Referenced but not provided in the analyzed material |
>
> **Golden rule applied:** where the source does not prove something, this document says so rather than guessing. Field names are reproduced exactly as they appear in the source; a name is **not** treated as proof of meaning.

---

## 1. Analysis Method

### 1.1 Artifacts inspected (exhaustive)

All artifacts were read from the `Job-details` branch of `swatisable/Mainframe`, where the program and its copybooks physically reside. Line numbers cited throughout refer to `CASPCFAL.txt`.

| # | Artifact | Path (branch `Job-details`) | Role | Status |
|---|----------|------------------------------|------|--------|
| 1 | `CASPCFAL.txt` | `/CASPCFAL.txt` (1366 lines) | Program under analysis | ✅ Present |
| 2 | `NCTCASE` | `/NCTCASE.txt` | Case-record layout copybook (used twice: prefixes `CASET`, `CASE`) | ✅ Present |
| 3 | `TPLPREFX` | `/TPLPREFX.txt` | Claim "prefix" layout (prefix `PFX`) | ✅ Present |
| 4 | `FDPCF602` | `/FDPCF602.txt` | Input claim HMS-600 body (prefix `CLMI`) | ✅ Present |
| 5 | `FDPCF601` | `/FDPCF601.txt` | Output claim HMS-601 body (prefix `CLM`) | ✅ Present |
| 6 | `CLMPREFX` | `/CLMPREFX.txt` | Output "prefix" layout (prefix `PRO`) | ✅ Present |
| 7 | `FDALINH5/4/3` | `/FDALINH{5,4,3}.txt` | "AL" client-side Institutional headers (prefix `AL5/AL4/AL3`) | ✅ Present |
| 8 | `FDALPHY5/4/3` | `/FDALPHY{5,4,3}.txt` | "AL" client-side Physician headers (prefix `AL5/AL4/AL3`) | ✅ Present |
| 9 | `FDALRXR5/4/3` | `/FDALRXR{5,4,3}.txt` | "AL" client-side Pharmacy headers (prefix `AL5/AL4/AL3`) | ✅ Present |

**Copybooks referenced but intentionally commented out (dead references — not compiled):** `FDALINHD`, `FDALCLMS`, `FDALPHYS`, `FDALRXRX`, `FDPCF600` (lines 122, 124, 133, 135, 144, 146, 163). ✅ Proven dead — each is preceded by the `*` comment indicator in column 7.

### 1.2 Tracing strategy

- **Top-down control flow** from `0000-MAIN` (line 282) through every `PERFORM` target.
- **Data-flow tracing** for each field that changes behavior (compares, switches, accumulators) and for the input→output `MOVE` chain.
- **Copybook resolution**: every `COPY … REPLACING` was expanded mentally by substituting the stated prefix, then the resolved field's `PIC` clause was read from the copybook file.

### 1.3 How "proven" vs. "inferred" is distinguished

- **✅ Proven** = the statement is literally present (a verb, a `PIC`, an `IF`, a `MOVE`). Citation = paragraph + line.
- **🔍 Inferred** = a conclusion assembled from ≥2 proven facts; the chain is shown as `A → B → C`.
- No business meaning is asserted from a name alone.

### 1.4 Known limitations / unavailable dependencies

- 📎 **JCL / execution deck not provided.** The `ASSIGN TO` names `SRCPCFI`, `CASEFLI`, `SRCPCFO`, `MATCHO`, `SYS004` (lines 26–30) are DD/environment names; the datasets they map to, the sort order guaranteed upstream, and the step sequence are **not** in the analyzed material. ❓ Open.
- 📎 **Upstream producer `CASPCFM1`** is named only in a comment ("ORIGINAL CLONED FROM CASPCFM1", line 16). Its code is not present. 🔍 This tells us lineage, not current behavior.
- ❓ **Actual data content** (real recipient IDs, dates, dollar amounts) is unknown; all walkthroughs in `CASPCFAL_illustrations.md` use clearly-labelled **dummy** data.
- ❓ **Guaranteed input sort order.** The merge-match logic (Section 5) only *works correctly* if both inputs are ordered on the recipient/Medicaid number, but no `SORT` verb or JCL proves the ordering inside this program. See Open Questions.

---

## 2. Program Overview

| Attribute | Value | Evidence |
|-----------|-------|----------|
| Program-ID | `CASPCFAL` | ✅ line 2 |
| Author / Installation | `BJW` / `HMS` | ✅ lines 3–4 |
| Date-written | `07/02/2015` | ✅ line 5 |
| Stated purpose | "THIS PROGRAM EXTRACTS PCF CLAIM DATA BASED ON CASE DATA FROM CAS2000 SYSTEM" | ✅ abstract, lines 7–10 |
| Lineage | Cloned from `CASPCFM1` (chg 0000) | ✅ comment line 16 |

**Technical role:** Batch, standalone main program.
🔍 **Inferred (chain):** No `LINKAGE SECTION` anywhere and `PROCEDURE DIVISION.` has no `USING` (line 280) → not called as a subprogram with parameters. Terminates with `STOP RUN` (line 289) → run-unit entry point. Uses only sequential file I/O (`OPEN`/`READ`/`WRITE`/`CLOSE`) with **no** `EXEC CICS` and **no** `EXEC SQL` (verified by exhaustive search) → batch, not online. ✅ Supporting facts: `STOP RUN` line 289; absence of `CALL`, `EXEC SQL`, `EXEC CICS`, `SORT`, `MERGE`, `DECLARATIVES` confirmed by full-file scan.

**Business role (only what code proves):** For each incoming PCF claim, the program locates matching **open** CAS2000 case rows for the same recipient and, when the claim's date-of-service falls inside the case's incident→claims-thru window, emits a reformatted PCF output record and accumulates a per-case match count and total MA-paid dollars. ✅ Proven by the mainline/matching paragraphs (`2000-MAINLINE` 363, `3010-LOAD-CASE-TABLE` 438, `3020-READ-CASE-TABLE` 452) — detailed in Section 5.

**Upstream / downstream dependencies:**

| Direction | Dependency | Evidence |
|-----------|------------|----------|
| Upstream | PCF claim file on DD `SRCPCFI` | ✅ SELECT line 26 |
| Upstream | CAS2000 case file on DD `CASEFLI` | ✅ SELECT line 27 |
| Upstream | Control cards on DD `SYS004` (chg 0005) | ✅ SELECT line 30 |
| Downstream | Reformatted PCF output on DD `SRCPCFO` | ✅ SELECT line 28 |
| Downstream | Case/PCF match report on DD `MATCHO` (chg 0002) | ✅ SELECT line 29 |
| Downstream | `SYSOUT` run statistics via `DISPLAY` | ✅ `9000-TERMINATION` lines 1259–1344 |

---

## 3. Inputs, Outputs, and Dependencies

### 3.1 Files

| Logical name | DD / ASSIGN | Dir. | `FD` record & mode | Buffer 01-level | Evidence |
|--------------|-------------|------|--------------------|------------------|----------|
| `SRCPCF-IN` | `SRCPCFI` | Input | `RECORD IS VARYING 4 TO 32752 DEPENDING ON PCF-DEP`, `RECORDING MODE S`, labels STANDARD | `CLMI-RECORD PIC X(32752)` | ✅ SELECT 26; FD 41–48 |
| `CASEFL-IN` | `CASEFLI` | Input | `RECORDING MODE F`, labels STANDARD | `CASE-RECORD PIC X(384)` | ✅ SELECT 27; FD 53–57 |
| `CNTL-CARDS` | `SYS004` | Input | `RECORD CONTAINS 80`, `RECORDING MODE F`, labels OMITTED | `CNTL-REC PIC X(80)` | ✅ SELECT 30; FD 35–39 |
| `SRCPCF-OUT` | `SRCPCFO` | Output | `RECORDING MODE F`, labels STANDARD | `CLMO-RECORD PIC X(754)` | ✅ SELECT 28; FD 58–64 |
| `CASE-PCF-MATCH` | `MATCHO` | Output | `RECORDING MODE F`, labels STANDARD | `MATCH-RECORD PIC X(80)` | ✅ SELECT 29; FD 67–72 |

- **No update files.** ✅ No `REWRITE`/`DELETE`/`START` verbs exist (full-file scan). All files are read-only inputs or write-only outputs.
- **No `FILE STATUS` clauses** on any `SELECT`. ✅ Confirmed (0 occurrences). 🔍 Consequence: the program relies solely on `AT END` for EOF and has **no** explicit I/O error-status inspection; an I/O error other than end-of-file would be handled by the runtime default, not by application code. ❓ Open (JCL/abend policy not provided).

### 3.2 Copybooks (with `COPY` location and effective prefix)

| Copybook | `COPY` line(s) | `REPLACING` → prefix | Consumed as |
|----------|----------------|----------------------|-------------|
| `NCTCASE` | 97, 153 | `(PREFIX)`→`CASET` (in 30-row table); `(PREFIX)`→`CASE` (single work record) | Case layout |
| `TPLPREFX` | 106 | `(PFX)`→`PFX` | Input claim prefix (127 bytes) |
| `FDPCF602` | 109 | `(PREFIX)`→`CLMI` | Input claim body |
| `FDALINH5/4/3` | 116/118/120 | `(ALT)`→`AL5/AL4/AL3` | Institutional client data |
| `FDALPHY5/4/3` | 127/129/131 | `(ALT)`→`AL5/AL4/AL3` | Physician client data |
| `FDALRXR5/4/3` | 138/139/142 | `(ALT)`→`AL5/AL4/AL3` | Pharmacy client data |
| `CLMPREFX` | 160 | `(PREFIX)`→`PRO` | Output claim prefix |
| `FDPCF601` | 166 | `(PREFIX)`→`CLM` | Output claim body |

### 3.3 Linkage structures

- **None.** ✅ There is no `LINKAGE SECTION` in the program. 🔍 Reinforces "standalone main" in Section 2.

### 3.4 Called programs (static / dynamic)

- **None.** ✅ No `CALL` (static or dynamic), `CANCEL`, or `GOBACK` verbs exist (full-file scan). The program contains no external subroutine invocations.

### 3.5 Control cards / profile / parm dependencies

| Input | Structure | Behavior | Evidence |
|-------|-----------|----------|----------|
| Control card, tag `'1'` | `CARD-REC`: `CARD-TAG X(01)`, filler, `CARD-COMMENT X(30)`, filler, `CARD-DATA X(02)` | When `CARD-TAG = '1'`, the card is `DISPLAY`-ed and `CARD-DATA(1:2)` is saved into `WS-SAVE-CREATE-SOURCE`; that value later populates `PRO-CREATE-SOURCE` on every output record | ✅ layout 179–184; `1650-READ-CARDS` 342–350; use 472–473 |

- 🔍 **Inferred:** Cards with any tag other than `'1'` are read and discarded (the `IF CARD-TAG = '1'` has no `ELSE`; loop continues). Chain: `1650-READ-CARDS` reads every card until `AT END` (344) → only tag `'1'` triggers a save (348) → other tags fall through with no action.
- ❓ **Open:** The full control-card specification (which columns, allowed values, whether more than one `'1'` card is expected) is not provided; only tag `'1'`/`CARD-DATA(1:2)` is exercised.

### 3.6 Return codes & status flags

- **No `RETURN-CODE` is set** and **no `SET`/`MOVE` to any RC register exists.** ✅ (full-file scan) → the step's completion code is the runtime default for `STOP RUN`. ❓ Open (not provable here).
- Program-internal status flags (`88`-levels) are catalogued in Section 4.3.

---

## 4. Data Structures & Important Fields

### 4.1 Record layouts that materially affect behavior (resolved from copybooks)

**Case record — `NCTCASE`** (fields cited by name use the resolved prefix). Selected behavior-relevant fields (✅ all from `NCTCASE.txt`):

| Resolved field (prefix `CASE`/`CASET`) | `PIC` | Used for |
|---|---|---|
| `…-HMS-CLIENT-ID` | `X(06)` | → `PRO-CLIENT-ID` (chg 0012) |
| `…-HMS-CASE-KEY` | `9(09)` | → `PRO-HMS-CASE-KEY` |
| `…-RECIPIENT-ID-NUM` | `X(20)` | Match key vs. `PFX-APP-MEDICAID-NO` |
| `…-CASE-STATUS-CODE` | `X(01)` | Open-case test (`'O'` / `X'96'`) |
| `…-INCIDENT-DATE` | `X(10)` | Lower bound of service-date window |
| `…-CLAIMS-THRU-DATE` | `X(10)` | Upper bound of service-date window |

**Claim prefix — `TPLPREFX`** (prefix `PFX`), behavior-relevant (✅ `TPLPREFX.txt`):

| Field | `PIC` | Used for |
|---|---|---|
| `PFX-SYS-HMS-ASSIGN-FILE` | `X(05)` | `(1:4) = 'MAMA'` gate (line 686) |
| `PFX-SYS-VERSION` | `X(02)` | Version routing `'05'..'01'` (688–718) |
| `PFX-SYS-EXIT-FROM-REF-STATUS` | `X(01)` | Skip test `NOT = 'Y'` (372) |
| `PFX-NET-CLAIM-TRANS-TYPE` | `X(01)` | → `PRO-CLAIM-TRANS-TYPE` (480) |
| `PFX-APP-MEDICAID-NO` | `X(20)` | Primary match key (365,367,398,420) |
| `PFX-APP-DATE-OF-SERVICE` | `9(08) COMP-3` | Service-date window compare (460–461) |

**Output prefix — `CLMPREFX`** (prefix `PRO`), 140 bytes (✅ `CLMPREFX.txt`): `PRO-RECIPIENT-ID-NUM X(20)`, `PRO-HMS-CASE-KEY 9(09)`, `PRO-ICN X(20)`, `PRO-FORMER-ICN X(20)`, `PRO-XACTION-STATUS X(01)`, `PRO-CLM-FROM-DATE 9(08)`, `PRO-RX-WRITTEN-DATE 9(08)`, `PRO-CLAIM-TRANS-TYPE X(01)`, `PRO-INCIDENT-DATE 9(08)`, `PRO-CLM-THRU-DATE 9(08)`, `PRO-LAST-HIT-DATE-TM 9(16)`, `PRO-CREATE-SOURCE X(2)`, `PRO-CLIENT-ID X(06)`, `PRO-FILLER X(13)`.

**Input vs. output claim bodies** — `FDPCF602` (prefix `CLMI`) and `FDPCF601` (prefix `CLM`). The output body is a **field-by-field re-population** of the input body (Section 5.6). Behavior-relevant `PIC` facts (✅):

| Field | Input `CLMI` `PIC` (FDPCF602) | Output `CLM` `PIC` (FDPCF601) |
|---|---|---|
| `…-PCF-CONTRACT-NUM` | `X(07)` (line 263) | — (test only) |
| `…-PM-USER-AREA` | `X(40)` (293) | `X(40)` |
| `…-CLAIM-FROM-DOS` | `9(06) COMP-3` (152) | copied |
| `…-PROV-OF-SVC-NUM` | `X(15)` (45) | copied |
| `…-PAY-TO-PROV-NUM` | `X(15)` (230) | copied |
| `…-PCF-MA-NUM` | `X(20)` (44) | copied |
| `…-ICN` | `X(20)` (144) | copied |
| `…-TOT-MA-PAID-HDR` | `S9(7)V99 COMP-3` (217) | copied; also accumulated |
| `…-PCF-HMS-ICN-SUFFIX` | `X(02)` + redefine `…-N 9(02)` (385–388) | — |
| `…-PRI-DX` / `…-SEC-DX` | `X(05)` (148/149) | `X(07)` (149/150) |
| `…-PROCEDURE-CODE-5` (in) / `…-PROCEDURE-CODE-7` (out) | `X(05)` (48) | `X(07)` (49) |
| `…-DX-3/4/5` | — | `X(07)` (319–321) |
| `…-CDE-ICD-VERSION` | — | `X(02)` (393) |

> 🔍 **Inferred widening:** diagnosis/procedure codes are widened from 5 to 7 characters on output (`CLMI-PRI-DX X(05)` → `CLM-PRI-DX X(07)`; `CLMI-PROCEDURE-CODE-5 X(05)` → `CLM-PROCEDURE-CODE-7 X(07)`). Chain: input `PIC X(05)` (FDPCF602 148/48) + output `PIC X(07)` (FDPCF601 149/49) + the diagnosis values actually written on output come from the 7-char "AL" fields (`WK-DIAG-CODE PIC X(7)`, line 192), not from the 5-char `CLMI` fields → the output layout is ICD-10-capable. ✅ Facts cited; the *reason* (ICD-10) is consistent with comments at 379–383 and 676 but the label "ICD-10" is only asserted where the source says it.

**"AL" client-side headers** — `FDALINH*/FDALPHY*/FDALRXR*`. Behavior-relevant (✅):

| Field (prefix `AL5/AL4/AL3`) | `PIC` / structure | Source |
|---|---|---|
| `…-INST-CLAIM-TYPE-ALPHA` | `X(01)` at record offset 15 | FDALINH5 line 21 (after `INST-ICN X(13)`+`INST-REC-TYPE X(02)`) |
| `…-PHYS-CLAIM-TYPE-ALPHA` | `X(01)` at record offset 15 | FDALPHY5 line 19 (after `PHYS-ICN X(13)`+`PHYS-REC-TYPE X(02)`) |
| `…-RX-CLAIM-TYPE-ALPHA` | `X(01)` at record offset 15 | FDALRXR5 line 9 |
| `…-INST-DIAG` (`OCCURS 14`) | `X(07)` | FDALINH5 165 |
| `…-INST-CDE-ICD-VERSION` | `X(01)` | FDALINH5 166 |
| `…-INST-HDR-SURG-CD` | `X(07)` | FDALINH5 156 |
| `…-PHYS-DIAG` (`OCCURS 14`) | `X(07)` | FDALPHY5 133 |
| `…-PHYS-CDE-ICD-VERSION` | `X(01)` | FDALPHY5 134 |

> ⚠️ **Behavioral note (see Rule BR-13):** the program keys *all three* branches of `5100/5200/5300-PROCESS-RECS` off the **institutional** field `AL{v}-INST-CLAIM-TYPE-ALPHA` (lines 751, 813, 863). 🔍 Inferred equivalence chain: `INST-REC{v}`, `PROF-REC{v}` and `RX-REC{v}` each receive the **same** `CLMI-CLIENT-DATA` (lines 689–691) → in all three copybooks `CLAIM-TYPE-ALPHA` sits at the identical offset 15 (proven above) → `AL{v}-INST-CLAIM-TYPE-ALPHA` therefore reads the same byte the physician/RX field would. So reusing the INST name is functionally consistent, **not** a defect. ✅ offsets proven; equivalence inferred.

### 4.2 Sort / match / window keys

| Purpose | Key(s) | Evidence |
|---|---|---|
| Primary match | `CASE-RECIPIENT-ID-NUM` / `CASET-RECIPIENT-ID-NUM` **vs.** `PFX-APP-MEDICAID-NO` | ✅ 365,367,398–399,420–421,443 |
| Open-case filter | `CASE-CASE-STATUS-CODE`/`CASET-CASE-STATUS-CODE = 'O' OR X'96'` | ✅ 335,457–458 |
| Service-date window | `WS-INCIDENT-DATE-NEW-RE ≤ PFX-APP-DATE-OF-SERVICE ≤ WS-CLM-THRU-DATE-N` | ✅ 460–461 |

> ✅ `X'96'` is the hexadecimal literal used as the second accepted open-status value alongside `'O'` (335, 458). Its business meaning beyond "treated as open" is **not** stated in source → ❓ Open.

### 4.3 Status & flag fields (`88`-levels)

| Field | `PIC`/value | `88` condition(s) | Set where | Read where | Evidence |
|---|---|---|---|---|---|
| `EOC-SWITCH` | `X(01)`='N' | `END-OF-CARDS`='Y' | 344 | 308 | ✅ 198–199 |
| `WS-PCF-EOF-SW` | `X(01)`='N' | `PCF-EOF`='Y' | 320 | 286 | ✅ 200–201 |
| `WS-CASE-EOF-SW` | `X(01)`='N' | `CASE-EOF`='Y' | 331 | 287,368,444 | ✅ 202–203 |
| `WS-RECIPIENT-SW` | `X(01)`='N' | `RECIPIENT-END`='Y' | 409,447 | 412 | ✅ 204–205 |
| `WS-SIZE-ERROR-FLAG` | `X(01)`='N' | `SIZE-OK`='N', `SIZE-ERROR`='Y' | 662,665,1233 | 400,659,1216,1245 | ✅ 274–276 |
| `PCF-DEP` | `9(05)`=32752 | — | (static) | FD `DEPENDING ON` (47) | ✅ 207 |
| `WS-PROCESSED-SW` | `X(01)`='N' | — | **never** | **never** | ✅ 206 — **dead** (1 reference: its own definition) |

### 4.4 Counters / accumulators

All initialized by `INITIALIZE WS-COUNTERS` (line 303) unless noted. ✅ Definitions lines 210–233; `COMP-3` accumulators 256–265.

| Counter | `PIC` | Meaning (from `DISPLAY` label / usage) | Evidence |
|---|---|---|---|
| `PCF-REC-READ-CTR` | `9(09)` | PCF records read | ✅ +1 at 323; label 1268 |
| `CASE-REC-READ-CTR` | `9(09)` | Case records read | ✅ +1 at 334; label 1277 |
| `REC-WRITE-CTR` | `9(09)` | PCF records written to output | ✅ +1 at 644; label 1290 |
| `REC-SKIP-PROV` (0007) | `9(09)` | Claims skipped for dummy provider `09999996` | ✅ +1 at 393; label 1271 |
| `REC-SKIP-DSS` (0010) | `9(09)` | DSS claims skipped for service year filter | ✅ +1 at 386; label 1274 |
| `TABLE-ENTRIES` | `9(09)` | Case rows loaded for current recipient | ✅ set 445 |
| `VER-5/4/3-INST-ILOAC` | `9(09)` | Institutional diag updates by version | ✅ +1 at 797/922/1047; labels 1293/1305/1317 |
| `VER-5/4/3-PROC-CD` | `9(09)` | Surgical/procedure-code updates by version | ✅ +1 at 809/934/1059 |
| `VER-5/4/3-PROF-MB` | `9(09)` | Physician diag updates by version | ✅ +1 at 859/984/1109 |
| `VER-5/4/3-RX-PQ` | `9(09)` | Pharmacy (P/Q) claims counted by version | ✅ +1 at 865/990/1115 |
| `VER-2` / `VER-1` | `9(09)` | Version-02 / version-01 claims counted | ✅ +1 at 1126/1200 |
| `OTHER-VERS` | `9(09)` | Claims with any other/unhandled version | ✅ +1 at 1208 |
| `OPEN-CASES-READ-CTR` (0004) | `S9(9) COMP-3` | Open case rows read | ✅ +1 at 336 |
| `OPEN-CASES-MATCH-OK-CTR` (0004) | `S9(9) COMP-3` | Open case rows matched to ≥1 PCF | ✅ +1 at 469 |
| `OPEN-CASES-NO-MATCH-CTR` (0004) | `S9(9) COMP-3` | `READ − MATCH-OK` | ✅ COMPUTE 1255–1256 |
| `WS-TOT-PCF-REC-MATCH` | `S9(5) COMP-3` | PCF matches for current case-id | ✅ +1 at 661 |
| `WS-TOT-PCF-MA-PAID` | `S9(11)V99 COMP-3` | Σ MA-paid for current case-id | ✅ +… at 664 |
| `NUM-REC-OUT` | `ZZZ,ZZZ,ZZ9` | Edited display field for all counters | ✅ 233 |

> ✅ **Dead / vestigial counters:** `VER-4-INST-ILOAC`…`VER-4-RX-PQ` and `VER-3-…` are defined and *do* increment (versions 04/03 are live). The version-02 institutional/physician detail counters (`VER-2-INST-ILOAC`, etc.) named inside `5400-PROCESS-RECS` exist **only in commented-out code** (lines 1149, 1161, 1183, 1189) and are **not** defined in `WORKING-STORAGE`; only the scalar `VER-2` (line 230) is live. 🔍 The version-02 and version-01 paths therefore *count* the claim but perform **no** diagnosis extraction (`5400`/`5500` bodies are `ADD +1` only; the extraction code is commented, lines 1128–1192). ✅ Proven.

---

## 5. Processing Logic (section-by-section)

### 5.0 Top-level driver — `0000-MAIN` (282–290)
```
PERFORM 1000-INITIALIZE
PERFORM 2000-MAINLINE UNTIL PCF-EOF OR CASE-EOF     (chg 0013 added "OR CASE-EOF")
PERFORM 9000-TERMINATION
STOP RUN
```
✅ Proven. 🔍 The loop is **PCF-driven** but also stops the instant the case file hits EOF (chg 0013, line 287). Consequence documented as Rule BR-01.

### 5.1 Initialization — `1000-INITIALIZE` (294–313)
1. `OPEN INPUT SRCPCF-IN CASEFL-IN CNTL-CARDS  OUTPUT SRCPCF-OUT CASE-PCF-MATCH` (297–301). ✅
2. `INITIALIZE WS-COUNTERS` (303). ✅
3. Prime first PCF (`1500`) and first case (`1600`). ✅ 305–306
4. Read **all** control cards until `END-OF-CARDS` (`1650`). ✅ 307–308
5. `INITIALIZE` all 30 case-table rows (`3000`, `VARYING SUB-I 1..30`). ✅ 309–310
6. Write the two-line match report header (`1700`). ✅ 311–312

### 5.2 Startup validation
- 🔍 **Inferred: none beyond EOF/size handling.** There is no explicit validation of card content, file emptiness, or record structure at startup (no such `IF`/abend exists between OPEN and the first mainline iteration). Chain: `1000-INITIALIZE` (294–313) contains only OPEN + primes + table init + header — no validating `IF`. ✅ by absence.

### 5.3 Read routines
- `1500-READ-SRCPCF-IN` (317–324): `READ … INTO WS-CLMI-RECORD; AT END SET PCF-EOF; ELSE ADD 1 PCF-REC-READ-CTR`. ✅
- `1600-READ-CASEFL-IN` (328–338): `READ … INTO WS-CASE-RECORD; AT END SET CASE-EOF; ELSE ADD 1 CASE-REC-READ-CTR`; and (chg 0004) if the just-read case is open (`= 'O' OR X'96'`) `ADD 1 OPEN-CASES-READ-CTR`. ✅
- `1650-READ-CARDS` (342–353): `READ CNTL-CARDS INTO CARD-REC; AT END MOVE 'Y' EOC-SWITCH, CLOSE CNTL-CARDS`; if `CARD-TAG='1'` DISPLAY + save `CARD-DATA(1:2)`. ✅

### 5.4 Main read/process/write loop — `2000-MAINLINE` (363–427)

Executed once per PCF claim. Decision order (✅ exactly as coded):

| Step | Condition | Action | Lines |
|---|---|---|---|
| A | `CASE-RECIPIENT-ID-NUM < PFX-APP-MEDICAID-NO` | Advance case file (`1600`) until `≥` claim's Medicaid no **or** `CASE-EOF` (chg 003) | 365–368 |
| B | `PFX-SYS-EXIT-FROM-REF-STATUS NOT = 'Y'` | Read next PCF; **skip** this claim (`GO TO … EXIT`) | 372–375 |
| C | `CLMI-PCF-CONTRACT-NUM='0032600'` **and** `CLMI-PM-USER-AREA(27:3)='DSS'` **and** `0040000 < CLMI-CLAIM-FROM-DOS < 0900000` (chg 0010) | `ADD 1 REC-SKIP-DSS`; read next PCF; skip | 377–389 |
| D | `CLMI-PROV-OF-SVC-NUM='09999996'` **and** `CLMI-PAY-TO-PROV-NUM='09999996'` (chg 0007/0009) | `ADD 1 REC-SKIP-PROV`; read next PCF; skip | 391–396 |
| E | `CASE-RECIPIENT-ID-NUM = PFX-APP-MEDICAID-NO` **and** `CASET-RECIPIENT-ID-NUM(1) < PFX-APP-MEDICAID-NO` | New recipient boundary: flush prior case summary if pending (chg 0002); re-init table; load this recipient's case rows (`3010`); process claim vs. every loaded row (`3020`) | 398–417 |
| F | `else if CASE-RECIPIENT-ID-NUM ≥ PFX-APP-MEDICAID-NO` **and** `CASET-RECIPIENT-ID-NUM(1) = PFX-APP-MEDICAID-NO` | Same recipient already in table → process claim vs. table (`3020`) | 420–424 |
| G | (always, at end) | Read next PCF (`1500`) | 426 |

> 🔍 **Inferred merge model:** the interplay of Step A (advance cases while behind), Step E (load table at a new matching recipient), and Step F (reprocess for subsequent claims of the same recipient) is a classic **sequential match-merge** of two files ordered on recipient id. Chain: A moves the case pointer forward monotonically; E fires only when `CASET(1)` (the loaded key) is *behind* the claim; F fires while they are *equal*. This only yields correct matches if **both inputs are ascending on recipient id** — an ordering the program itself does not enforce (no `SORT`). ✅ control facts proven; ordering requirement is the key ❓ Open dependency.

### 5.5 Case-table build — `3000/3010` (431–450)
- `3000-INITIALIZE-TABLE` (431–434): `INITIALIZE WS-CASE-TABLE(SUB-I)`. ✅
- `3010-LOAD-CASE-TABLE` (438–447): store `WS-CASE-RECORD` into row `SUB-I`; set that row's `CASE-PCF-MATCH-FLAG='N'` (chg 0004); read the next case; when `CASE-RECIPIENT-ID-NUM > CASET-RECIPIENT-ID-NUM(SUB-I)` **or** `CASE-EOF`, set `TABLE-ENTRIES=SUB-I` and `WS-RECIPIENT-SW='Y'` (ends the load). ✅
- 🔍 **Capacity caveat:** the load `PERFORM … VARYING SUB-I FROM 1 UNTIL RECIPIENT-END` (410–412) has **no** guard for `SUB-I > 30`, yet the table is `OCCURS 30` (line 96). If a single recipient has >30 consecutive case rows, `WS-CASE-TABLE(SUB-I)` indexes past the table. Chain: table bound 30 (96) + loop bounded only by `RECIPIENT-END` (412) + `3010` writes `WS-CASE-TABLE(SUB-I)` unconditionally (440). ✅ facts proven; whether it occurs depends on data → ❓ Open / risk noted as Rule BR-14.

### 5.6 Per-case processing & output build — `3020-READ-CASE-TABLE` (452–671)
For each loaded row `SUB-I` (`1..TABLE-ENTRIES`):
1. `PERFORM 4000-FORMAT-DATE` to derive the comparison window (see 5.7). ✅ 454
2. **Gate 1 – open case:** `CASET-CASE-STATUS-CODE(SUB-I) = 'O' OR X'96'` (457–458). ✅
3. **Gate 2 – service-date window:** `PFX-APP-DATE-OF-SERVICE ≥ WS-INCIDENT-DATE-NEW-RE` (chg 0001, 460) **and** `≤ WS-CLM-THRU-DATE-N` (461). ✅
4. When both gates pass, build the output record `WS-SRCPCF-OUT`:
   - `INITIALIZE PRO-CLMPRFX`; set prefix fields: `PRO-RECIPIENT-ID-NUM ← CLMI-PCF-MA-NUM` (463), `PRO-HMS-CASE-KEY ← CASET-HMS-CASE-KEY(SUB-I)` (464), `PRO-CLIENT-ID ← CASET-HMS-CLIENT-ID(SUB-I)` (chg 0012, 466), `PRO-CREATE-SOURCE ← WS-SAVE-CREATE-SOURCE` (chg 0005, 472), `PRO-ICN ← CLMI-ICN`, `PRO-FORMER-ICN ← CLMI-FORMER-ICN`, `PRO-XACTION-STATUS ← CLMI-XACTION-STATUS`, `PRO-CLM-FROM-DATE ← PFX-APP-DATE-OF-SERVICE`, `PRO-CLAIM-TRANS-TYPE ← PFX-NET-CLAIM-TRANS-TYPE`, `PRO-INCIDENT-DATE ← WS-INCIDENT-DATE`, `PRO-CLM-THRU-DATE ← WS-CLM-THRU-DATE`. ✅ 462–483
   - **First-match accounting (chg 0004):** if `CASE-PCF-MATCH-FLAG(SUB-I)='N'` then `ADD 1 OPEN-CASES-MATCH-OK-CTR` and set the flag to `'Y'` (so each open case counts once regardless of how many PCF rows match it). ✅ 468–471
   - **Dummy-provider substitution (chg 0009):** if `CLMI-PROV-OF-SVC-NUM='09999996'` and `CLMI-PCF-CONTRACT-NUM='0032600'`, move `CLMI-PAY-TO-PROV-NUM` into `CLMI-PROV-OF-SVC-NUM` **before** copying to output. ✅ 484–488
   - **Body copy:** ~110 explicit `MOVE CLMI-… TO CLM-…` statements re-populate the HMS-601 output body "by column" (comment 489). ✅ 492–624. (Full list in `CASPCFAL_io_mapping.md`.)
   - **ICN-suffix reformat (chg 0008):** if `(CLMI-PM-USER-AREA(1:2)='PB' OR 'DT')` and `CLMI-PCF-CONTRACT-NUM='0032600'` and `CLMI-PM-USER-AREA(27:3) NOT='DSS'`, and `CLMI-PCF-HMS-ICN-SUFFIX IS NUMERIC` and non-zero, build a 19-char ICN = `CLMI-ICN(17)` ∥ `suffix(2)` (via `WS-ICN-GROUP-19`) into both `PRO-ICN` and `CLM-ICN`. ✅ 626–643
   - `ADD 1 REC-WRITE-CTR` (644). ✅
   - `PERFORM 3030-REVIEW-MAMA-VERS` (diagnosis extraction, 5.8). ✅ 645
   - **ICD-version normalization (write-time):** `EVALUATE TRUE … WHEN CLM-CDE-ICD-VERSION = '0 ' → '10'; WHEN ' 0' → '10'; WHEN OTHER → '9'` (646–653). ✅
   - `WRITE CLMO-RECORD FROM WS-SRCPCF-OUT` (655). ✅
   - `MOVE '9' TO CLM-CDE-ICD-VERSION` — reset **after** write (657). ✅ 🔍 So the normalization at 646–653 affects only the record just written.
   - **Match accumulation (chg 0002), only if `SIZE-OK`:** `MOVE CASET-RECIPIENT-ID-NUM(1) TO WS-CASE-ID`; `ADD 1 TO WS-TOT-PCF-REC-MATCH ON SIZE ERROR SET SIZE-ERROR`; `ADD CLMI-TOT-MA-PAID-HDR TO WS-TOT-PCF-MA-PAID ON SIZE ERROR SET SIZE-ERROR`. ✅ 659–669

### 5.7 Date-window derivation — `4000-FORMAT-DATE` (725–746)
- `INITIALIZE WS-COMPARE-DATES` (727). ✅
- If `CASET-INCIDENT-DATE(SUB-I) NOT = SPACES`: `UNSTRING … DELIMITED BY '-' OR '  ' INTO WS-IN-YYYY WS-IN-MM` — **only two** receiving fields, so the day component is not captured (730–733). Then (chg 0001) copy to `WS-INCIDENT-DATE-NEW` and force `WS-IN-NEW-DD = 01` (734–735). ✅ 🔍 The lower bound therefore becomes **YYYY-MM-01** of the incident month (used at 460), while the value stored on output (`PRO-INCIDENT-DATE`, 482) is `WS-INCIDENT-DATE` whose day is `00`. ✅ facts proven.
- If `CASET-CLAIMS-THRU-DATE(SUB-I) NOT = SPACES`: `UNSTRING … INTO WS-THRU-YYYY WS-THRU-MM WS-THRU-DD`; **else** `MOVE '99999999' TO WS-CLM-THRU-DATE` (open-ended upper bound). ✅ 737–743

### 5.8 Version routing & diagnosis extraction — `3030` + `5100/5200/5300/5400/5500/5600`
- `3030-REVIEW-MAMA-VERS` (675–723): `INITIALIZE` the v5/v4/v3 INST/PROF/RX areas; **only if** `PFX-SYS-HMS-ASSIGN-FILE(1:4) = 'MAMA'`, `EVALUATE PFX-SYS-VERSION`: `'05'→5100`, `'04'→5200`, `'03'→5300`, `'02'→5400`, `'01'→5500`, `WHEN OTHER→5600`; the matching version first `MOVE CLMI-CLIENT-DATA` into that version's INST/PROF/RX areas. ✅ 686–720
  - 🔍 If `PFX-SYS-HMS-ASSIGN-FILE(1:4) ≠ 'MAMA'`, **none** of 5100–5600 runs and no per-version counter increments (the whole `EVALUATE` is inside the `IF`, 686–720). ✅
- `5100/5200/5300-PROCESS-RECS` (748/873/998): identical structure per version (v5/v4/v3). `EVALUATE TRUE` on `AL{v}-INST-CLAIM-TYPE-ALPHA`:
  - `'I'/'L'/'O'/'A'/'C'` (institutional): loop `WS-LPR 1..5` — when `AL{v}-INST-DIAG(WS-LPR)` **or** `…-INST-CDE-ICD-VERSION(WS-LPR)` non-space, move the diag to `CLM-PRI-DX`/`CLM-SEC-DX`/`CLM-DX-3/4/5` by position and the ICD version to `CLM-CDE-ICD-VERSION`; `ADD 1 VER-{v}-INST-ILOAC`. Then loop `1..1` moving `AL{v}-INST-HDR-SURG-CD(1)` to `CLM-PROCEDURE-CODE-7`; `ADD 1 VER-{v}-PROC-CD`. ✅ 751–812
  - `'M'/'B'` (physician): loop `1..5` over `AL{v}-PHYS-DIAG`/`…-PHYS-CDE-ICD-VERSION` into the same `CLM` diagnosis slots; `ADD 1 VER-{v}-PROF-MB`. ✅ 813–862
  - `'P'/'Q'` (pharmacy): `ADD 1 VER-{v}-RX-PQ` only (no diagnosis; comment 676 "RX RECORDS DO NOT HAVE DIAGNOSIS CODES"). ✅ 863–865
  - `WHEN OTHER`: `CONTINUE`. ✅ 866–867
- `5400-PROCESS-RECS` (v2, 1123–1195): `ADD +1 TO VER-2` only; extraction code commented ("ICD-10 SEGMENTS ARE NOT BEING CREATED", 1124). ✅
- `5500-PROCESS-RECS` (v1, 1197–1203): `ADD +1 TO VER-1` only. ✅
- `5600-PROCESS-RECS` (other, 1205–1211): `ADD +1 TO OTHER-VERS` only. ✅

### 5.9 Match-report writes — `1700` / `2100` / `9100`
- `1700-WRITE-MATCH-HEADER` (355–361): write the labelled header line, then a blank line, to `MATCHO`. ✅
- `2100-WRITE-CASE-PCF-MATCH` (1213–1240): `MOVE WS-CASE-ID TO MATCH-CASE-ID-OUT`; if `SIZE-OK`, edit `WS-TOT-PCF-REC-MATCH` (via `WS-CONVERT-MATCH`, leading spaces stripped with `INSPECT … TALLYING`) and `WS-TOT-PCF-MA-PAID` (via `WS-CONVERT-PCF-PAID`, `$$$,$$$,$$$,$$9.99`) into the output line; **else** overlay `'TOO MANY MATCHES, $$ PAID NOT AVAILABLE !'` and reset `SIZE-OK`. Write the line; `INITIALIZE WS-CASE-PCF-MATCH WS-MATCH-PROCESS-FIELDS`; blank `WS-MATCH-OUT`. ✅
- `9100-WRITE-MATCH-TRAILER` (1353–1364): if `REC-WRITE-CTR = 0` write `'NO MATCHED PCF RECORDS FOUND'`; then write a blank line and an all-`'*'` line. ✅

### 5.10 End-of-job — `9000-TERMINATION` (1242–1351)
1. Flush the **last** case's summary if pending: `IF WS-TOT-PCF-REC-MATCH > 0 OR SIZE-ERROR → 2100` (1245–1248). ✅ (The comment at 1249–1251 documents the last-matched-case edge case.)
2. `9100-WRITE-MATCH-TRAILER` (1253). ✅
3. `COMPUTE OPEN-CASES-NO-MATCH-CTR = OPEN-CASES-READ-CTR − OPEN-CASES-MATCH-OK-CTR` (chg 0004, 1255–1256). ✅
4. `DISPLAY` the full statistics block (counts of PCF read, skipped-prov, skipped-DSS, case read, open read/matched/not-matched, written, and per-version tallies). ✅ 1259–1343
5. `CLOSE SRCPCF-IN CASEFL-IN SRCPCF-OUT CASE-PCF-MATCH` (1345–1348). ✅ (`CNTL-CARDS` was already closed at `AT END`, 345.)

### 5.11 Restart / recovery / checkpoint
- **None present.** ✅ No checkpoint/restart verbs, no commit points, no `RERUN`. 🔍 The job is restart-from-start only. ❓ Any external restart strategy would live in JCL (not provided).

---

## 6. Extracted Business Logic

Format: **When** *&lt;condition proven in code&gt;*, **the program** *&lt;action proven in code&gt;*. Each rule cites its source and tag.

| ID | Business rule | Evidence |
|----|---------------|----------|
| **BR-01** | **When** the PCF input reaches end-of-file **or** the case input reaches end-of-file, the program stops the main loop and proceeds to end-of-job. | ✅ `0000-MAIN` 286–288 (chg 0013) |
| **BR-02** | **When** a control card has tag `'1'`, the program records its 2-character `CARD-DATA` as the *create source* stamped onto every output PCF record (`PRO-CREATE-SOURCE`). | ✅ 348–350, 472–473 |
| **BR-03** | **When** the current case's recipient id is less than the claim's Medicaid number, the program reads forward through the case file until the case recipient id catches up (or the case file ends). | ✅ 365–368 |
| **BR-04** | **When** a claim's `PFX-SYS-EXIT-FROM-REF-STATUS` is not `'Y'`, the program excludes that claim (no output) and moves to the next claim. | ✅ 372–375 |
| **BR-05** | **When** a claim is on contract `'0032600'`, is tagged `'DSS'` in `PM-USER-AREA(27:3)`, and its from-date-of-service is in the numeric range `0040001‥0899999` (`0YYMMDD` form), the program skips it and increments the DSS-skip counter. The in-code comment states this **includes** service years 1990–2002 and **excludes** 2004+. | ✅ 377–389; comment 379–383 |
| **BR-06** | **When** both the service provider and pay-to provider equal `'09999996'`, the program skips the claim and increments the provider-skip counter. | ✅ 391–396 |
| **BR-07** | **When** a claim's Medicaid number matches a recipient not yet loaded, the program (a) writes out the previous case's match summary if it had any matches or a size error, (b) loads all consecutive case rows for that recipient into a 30-row table, and (c) evaluates the claim against each loaded row. | ✅ 398–417 |
| **BR-08** | **When** a subsequent claim belongs to the recipient already loaded in the table, the program evaluates it against the existing table without reloading. | ✅ 420–424 |
| **BR-09** | **When** a loaded case row is open (`'O'` or `X'96'`) **and** the claim's date-of-service falls between the case incident month-start and the claims-thru date, the program produces one reformatted PCF output record for that claim/case pair. | ✅ 457–461, 655 |
| **BR-10** | **When** an open case row is matched to a PCF claim for the first time, the program counts it once as an "open case matched" (subsequent PCF matches to the same case row do not re-count). | ✅ 468–471 (chg 0004) |
| **BR-11** | **When** a claim's service provider is the dummy `'09999996'` on contract `'0032600'`, the program substitutes the pay-to provider number into the service-provider field before writing output. | ✅ 484–488 (chg 0009) |
| **BR-12** | **When** a claim is on contract `'0032600'`, tagged `'PB'`/`'DT'` (and not `'DSS'`) in `PM-USER-AREA`, with a numeric non-zero ICN suffix, the program rebuilds the ICN as the first 17 characters of the original ICN concatenated with the 2-character suffix (into both output ICN fields). | ✅ 626–643 (chg 0008) |
| **BR-13** | **When** the claim's HMS assign-file begins `'MAMA'`, the program selects diagnosis/procedure extraction by client-file version (`05/04/03` extract; `02/01/other` only tally). Extraction routes by claim-type letter: `I/L/O/A/C`→institutional diagnoses + surgical code; `M/B`→physician diagnoses; `P/Q`→pharmacy (counted only). | ✅ 686–720, 748–1211 |
| **BR-14** | **When** diagnoses are extracted, up to five are mapped positionally to `CLM-PRI-DX`, `CLM-SEC-DX`, `CLM-DX-3`, `CLM-DX-4`, `CLM-DX-5`, each with the ICD code version; and the first header surgical code maps to `CLM-PROCEDURE-CODE-7`. | ✅ 760–808 (v5), mirror in v4/v3 |
| **BR-15** | **When** writing each output record, the program normalizes the ICD version indicator: `'0 '`/`' 0'` → `'10'`, anything else → `'9'`; it then resets the field to `'9'` after the write. | ✅ 646–657 |
| **BR-16** | **When** the claims-thru date on a case is blank, the program treats the upper date bound as open-ended (`'99999999'`). | ✅ 737–743 |
| **BR-17** | **When** accumulating a case's match totals overflows the counter or dollar accumulator (`ON SIZE ERROR`), the program sets a size-error state; the match report then prints `'TOO MANY MATCHES, $$ PAID NOT AVAILABLE !'` instead of numeric totals for that case. | ✅ 659–669, 1216–1234 |
| **BR-18** | **When** no PCF records were written for the whole run (`REC-WRITE-CTR = 0`), the match report emits `'NO MATCHED PCF RECORDS FOUND'`. | ✅ 1355–1358 |
| **BR-19** | **At end of job**, the program computes open cases *not* matched as open-read minus open-matched, prints the full statistics block, and closes the files. | ✅ 1255–1348 |

> ⚠️ **Risk observations (proven facts; impact depends on data / ❓ Open):**
> - **R-1 (table overflow):** the case-table load loop is bounded only by `RECIPIENT-END`, not by `SUB-I ≤ 30`, while `WS-CASE-TABLE OCCURS 30` (5.5). More than 30 consecutive case rows for one recipient would index past the table.
> - **R-2 (no file-status handling):** no `FILE STATUS` and no non-EOF I/O checks (3.1) → non-EOF I/O errors are left to the runtime.
> - **R-3 (ordering assumption):** correct matching depends on both inputs being ascending on recipient id, which this program does not enforce (5.4).

---

## 7. Open Questions (surfaced by analysis)

1. ❓ **Input ordering** — What guarantees `SRCPCF-IN` and `CASEFL-IN` are both ascending on recipient/Medicaid number? *Needed:* the JCL / upstream `SORT` step. (Impacts BR-03/07/08.)
2. ❓ **DD-to-dataset mapping** — What datasets back `SRCPCFI`, `CASEFLI`, `SRCPCFO`, `MATCHO`, `SYS004`? *Needed:* execution JCL.
3. ❓ **`X'96'` semantics** — Beyond "treated as open", what case status does `X'96'` represent? *Needed:* CAS2000 status code table / data dictionary.
4. ❓ **Control-card spec** — Are non-`'1'` tags valid? Can multiple `'1'` cards appear (last wins)? *Needed:* the card layout / operations doc.
5. ❓ **Version-02/01 intent** — Is the tally-only behavior (no diagnosis extraction) for versions `02`/`01` intended, or pending future work (code is commented, not deleted)? *Needed:* change-control record for chg 0008/0010 era.
6. ❓ **Max case rows per recipient** — Can a recipient legitimately have >30 case rows (R-1)? *Needed:* CAS2000 data profile.
7. ❓ **Prompt naming** — The prompt names `TPLPBUS3.txt` / branch `docs/tplpbus3-analysis`, but no `TPLPBUS3` artifact exists; every concrete deliverable and the analysis target are `CASPCFAL`. Confirm `TPLPBUS3` is a template placeholder. (`TPLPREFX` is a *copybook* used by `CASPCFAL`, not a program named `TPLPBUS3`.)

---

*Prepared strictly from the cited source lines of `CASPCFAL.txt` and its resolved copybooks. Where the source does not prove a claim, it is marked ❓ Open or 📎 Missing artifact rather than guessed.*
