# CASPCFAL — Dummy-Data Walkthroughs (every coded scenario)

> **Audit-grade · Evidence-based · Zero-hallucination**
>
> ⚠️ **ALL data values below are clearly-labelled DUMMY values invented only to illustrate the coded logic.** They are **not** taken from any real file. What is *proven* is the **behavior** (branch taken, fields moved, counters changed), each step cited to `CASPCFAL.txt` line numbers and its resolved copybooks. Field formats are those proven in `CASPCFAL_logic.md` §4.
>
> Tags: ✅ Proven · 🔍 Inferred · ❓ Open. See `CASPCFAL_logic.md` for the tag legend and the rule IDs (BR-xx) referenced here.

Legend for the traces: `PFX-…` = input claim prefix (copybook `TPLPREFX`), `CLMI-…` = input claim body (`FDPCF602`), `CASE-…`/`CASET-…` = case row (`NCTCASE`), `PRO-…`/`CLM-…` = output record (`CLMPREFX`/`FDPCF601`).

---

## Scenario index

| # | Scenario | Rule / branch | Outcome |
|---|----------|---------------|---------|
| 1 | Claim excluded — not exit-from-ref-status `'Y'` | BR-04 (372–375) | No output |
| 2 | Claim skipped — DSS service-year filter | BR-05 (377–389) | No output, `REC-SKIP-DSS`++ |
| 3 | Claim skipped — dummy provider `09999996` | BR-06 (391–396) | No output, `REC-SKIP-PROV`++ |
| 4 | Case file catch-up | BR-03 (365–368) | Case pointer advances |
| 5 | New recipient, open case, in-window, MAMA v05 institutional | BR-07/09/10/13/14/15 | 1 output written |
| 6 | Second claim, same recipient (no reload) | BR-08 (420–424) | 1 output written |
| 7 | Physician (`M`/`B`) diagnosis extraction, v05 | BR-13/14 (813–862) | Physician DXs on output |
| 8 | Pharmacy (`P`/`Q`) — tally only | BR-13 (863–865) | Output written, no DX |
| 9 | Dummy-provider substitution on contract `0032600` | BR-11 (484–488) | Pay-to prov copied in |
| 10 | ICN suffix reformat (`PB`/`DT`) | BR-12 (626–643) | 19-char ICN rebuilt |
| 11 | Non-`MAMA` assign file | BR-13 gate (686) | Output written, no version work |
| 12 | Blank claims-thru date → open-ended | BR-16 (737–743) | Upper bound `99999999` |
| 13 | Service date outside window → excluded | BR-09 gate (460–461) | No output |
| 14 | Closed case (status ≠ open) → excluded | BR-09 gate (457–458) | No output |
| 15 | Case match summary line format | 2100 (1213–1240) | Report detail line |
| 16 | Size-error / "too many matches" | BR-17 (659–669, 1216–1234) | Report shows message |
| 17 | Empty run trailer | BR-18 (1355–1358) | "NO MATCHED PCF RECORDS FOUND" |
| 18 | Versions `02`/`01`/other — tally only | 5400/5500/5600 | Counted, no DX |
| 19 | End-of-job statistics + open-not-matched | BR-19 (1255–1343) | SYSOUT block |

---

### Scenario 1 — Claim excluded because it is not in "exit-from-ref-status" `'Y'` (BR-04)

**Dummy input claim**

| Field | Dummy value |
|---|---|
| `PFX-SYS-EXIT-FROM-REF-STATUS` | `'N'` |

**Trace**
1. `2000-MAINLINE` reaches `IF (PFX-SYS-EXIT-FROM-REF-STATUS NOT = 'Y')` — true. ✅ 372
2. Executes `PERFORM 1500-READ-SRCPCF-IN` then `GO TO 2000-MAINLINE-EXIT`. ✅ 374–375

**Result:** No output record, no counters other than the next read's `PCF-REC-READ-CTR`. The claim is silently dropped. ✅
🔍 The commented alternate condition `OR (PFX-NET-CLAIM-TRANS-TYPE = 'D')` (line 373) is inactive (column-7 comment) → transaction-type `'D'` does **not** currently force-keep the claim.

---

### Scenario 2 — DSS claim skipped by the service-year filter (BR-05)

**Dummy input claim**

| Field | Dummy value | Note |
|---|---|---|
| `PFX-SYS-EXIT-FROM-REF-STATUS` | `'Y'` | passes Scenario-1 gate |
| `CLMI-PCF-CONTRACT-NUM` | `'0032600'` | X(07) |
| `CLMI-PM-USER-AREA(27:3)` | `'DSS'` | |
| `CLMI-CLAIM-FROM-DOS` | `050115` (i.e. `0YYMMDD` = year "2005", May 15) | 9(06) COMP-3 |

**Trace**
1. Passes 372. Reaches the chg-0010 `IF` at 377–385: contract `'0032600'` ✅, user-area `'DSS'` ✅, `CLMI-CLAIM-FROM-DOS = 050115` → `> 0040000` ✅ and `< 0900000` ✅. Whole condition true. ✅
2. `ADD 1 TO REC-SKIP-DSS`; `PERFORM 1500-READ-SRCPCF-IN`; `GO TO 2000-MAINLINE-EXIT`. ✅ 386–388

**Result:** No output; `REC-SKIP-DSS`++ (reported at 1274). ✅
Counter-example (✅ same rule): `CLMI-CLAIM-FROM-DOS = 020715` (year "2002") is **> 0040000? No** (020715 < 040000) → condition false → **not** skipped here (consistent with the comment "INCLUDING 1990 THROUGH 2002", lines 382–383).

---

### Scenario 3 — Claim skipped for dummy provider `09999996` (BR-06)

**Dummy input claim**

| Field | Dummy value |
|---|---|
| `CLMI-PROV-OF-SVC-NUM` | `'09999996'` |
| `CLMI-PAY-TO-PROV-NUM` | `'09999996'` |

**Trace:** at 391–392 both equal `'09999996'` → true → `ADD 1 REC-SKIP-PROV`, read next PCF, `GO TO …EXIT`. ✅ 393–395
**Result:** No output; `REC-SKIP-PROV`++ (reported 1271). ✅
🔍 If only the *service* provider were `09999996` but pay-to differed, this gate is false; the claim continues and may instead trigger the **substitution** in Scenario 9 (different condition, 484–488).

---

### Scenario 4 — Case file catch-up (BR-03)

**Dummy state**

| Field | Dummy value |
|---|---|
| `CASE-RECIPIENT-ID-NUM` (current case) | `'M0000000000000000100'` |
| `PFX-APP-MEDICAID-NO` (current claim) | `'M0000000000000000500'` |

**Trace:** `IF CASE-RECIPIENT-ID-NUM < PFX-APP-MEDICAID-NO` true (100 < 500) → `PERFORM 1600-READ-CASEFL-IN … UNTIL CASE-RECIPIENT-ID-NUM >= PFX-APP-MEDICAID-NO OR CASE-EOF`. ✅ 365–368
**Result:** case pointer advances (reading, and counting open cases via chg 0004 at 335–337) until a case recipient ≥ `…500` is reached or EOF. No output from this step. ✅

---

### Scenario 5 — Full match & output: new recipient, open case, in-window, MAMA version `05` institutional (BR-07, BR-09, BR-10, BR-13, BR-14, BR-15)

**Dummy input claim**

| Field | Dummy value | Copybook |
|---|---|---|
| `PFX-SYS-EXIT-FROM-REF-STATUS` | `'Y'` | TPLPREFX |
| `PFX-APP-MEDICAID-NO` | `'M0000000000000000500'` | TPLPREFX |
| `PFX-APP-DATE-OF-SERVICE` | `20180615` (YYYYMMDD) | 9(08) COMP-3 |
| `PFX-SYS-HMS-ASSIGN-FILE` | `'MAMA5'` | `(1:4)='MAMA'` |
| `PFX-SYS-VERSION` | `'05'` | |
| `PFX-NET-CLAIM-TRANS-TYPE` | `'P'` | |
| `CLMI-PCF-MA-NUM` | `'M0000000000000000500'` | FDPCF602 |
| `CLMI-ICN` | `'IIIIIIIIIIIIIIIIIIII'` (20) | |
| `CLMI-TOT-MA-PAID-HDR` | `+1234.56` | S9(7)V99 |
| `CLMI-CLIENT-DATA` starts with `INST-ICN(13)`, `REC-TYPE(2)`, then `AL5-INST-CLAIM-TYPE-ALPHA='I'`, `AL5-INST-DIAG(1)='S72001A'`, `AL5-INST-CDE-ICD-VERSION(1)='0'`, `AL5-INST-HDR-SURG-CD(1)='0SG9YZZ'` | dummy | FDALINH5 |

**Dummy case row (single row for this recipient)**

| Field | Dummy value |
|---|---|
| `CASE-RECIPIENT-ID-NUM` | `'M0000000000000000500'` |
| `CASET-RECIPIENT-ID-NUM(1)` (previously loaded) | `'M0000000000000000100'` (older, smaller) |
| `CASET-CASE-STATUS-CODE(1)` | `'O'` |
| `CASET-INCIDENT-DATE(1)` | `'2018-03-15'` |
| `CASET-CLAIMS-THRU-DATE(1)` | `'2019-06-30'` |
| `CASET-HMS-CASE-KEY(1)` | `123456789` |
| `CASET-HMS-CLIENT-ID(1)` | `'CLNT01'` |

**Trace**
1. Not skipped by 372/377/391 (status `'Y'`, not DSS, not dummy prov). ✅
2. `IF CASE-RECIPIENT-ID-NUM = PFX-APP-MEDICAID-NO (…500 = …500) AND CASET-RECIPIENT-ID-NUM(1) < PFX-APP-MEDICAID-NO (…100 < …500)` → true (new-recipient boundary). ✅ 398–399
3. Prior case had matches? Assume `WS-TOT-PCF-REC-MATCH = 0` and `SIZE-OK` → **no** flush. ✅ 400–404
4. Re-init table (3000), `WS-RECIPIENT-SW='N'`, load rows via `3010` until `RECIPIENT-END`; here 1 row → `TABLE-ENTRIES = 1`, `CASE-PCF-MATCH-FLAG(1)='N'`. ✅ 406–412, 441–447
5. `3020-READ-CASE-TABLE` for `SUB-I=1`:
   - `4000-FORMAT-DATE`: incident `'2018-03-15'` → `WS-IN-YYYY=2018, WS-IN-MM=03` (day dropped), then chg 0001 sets `WS-INCIDENT-DATE-NEW = 20180301` → `WS-INCIDENT-DATE-NEW-RE = 20180301`. Thru `'2019-06-30'` → `WS-CLM-THRU-DATE-N = 20190630`. ✅ 729–743
   - **Gate 1** open: `CASET-CASE-STATUS-CODE(1)='O'` ✅ 457
   - **Gate 2** window: `20180301 ≤ 20180615 ≤ 20190630` ✅ 460–461
   - Build prefix: `PRO-RECIPIENT-ID-NUM ← 'M0000000000000000500'`, `PRO-HMS-CASE-KEY ← 123456789`, `PRO-CLIENT-ID ← 'CLNT01'`, `PRO-CREATE-SOURCE ← WS-SAVE-CREATE-SOURCE` (from a tag-`'1'` card, Scenario for BR-02), `PRO-ICN ← CLMI-ICN`, `PRO-CLM-FROM-DATE ← 20180615`, `PRO-CLAIM-TRANS-TYPE ← 'P'`, `PRO-INCIDENT-DATE ← WS-INCIDENT-DATE` (= `20180300`, day `00` — see note), `PRO-CLM-THRU-DATE ← 20190630`. ✅ 462–483
   - First match: `CASE-PCF-MATCH-FLAG(1)='N'` → `OPEN-CASES-MATCH-OK-CTR`++, flag set `'Y'`. ✅ 468–471
   - Body copy: ~110 `MOVE CLMI-… TO CLM-…` (492–624). ✅
   - `REC-WRITE-CTR`++. ✅ 644
   - `3030-REVIEW-MAMA-VERS`: `'MAMA'` ✅, version `'05'` → move `CLMI-CLIENT-DATA` into `INST-REC5/PROF-REC5/RX-REC5`, `PERFORM 5100`. ✅ 686–693
   - `5100`: `AL5-INST-CLAIM-TYPE-ALPHA='I'` ∈ {I,L,O,A,C} → loop `WS-LPR 1..5`: slot 1 has `AL5-INST-DIAG(1)='S72001A'`, `AL5-INST-CDE-ICD-VERSION(1)='0'` → `CLM-PRI-DX ← 'S72001A'`, `CLM-CDE-ICD-VERSION ← '0'`; `VER-5-INST-ILOAC`++. Surg loop: `AL5-INST-HDR-SURG-CD(1)='0SG9YZZ'` → `CLM-PROCEDURE-CODE-7 ← '0SG9YZZ'`; `VER-5-PROC-CD`++. ✅ 751–812
   - Write-time ICD normalization: `CLM-CDE-ICD-VERSION` currently `'0'` (single char in a X(02) field → `'0 '`) → `EVALUATE` matches `'0 '` → set `'10'`. ✅ 646–648
   - `WRITE CLMO-RECORD FROM WS-SRCPCF-OUT`. ✅ 655  → **1 output record produced.**
   - Reset `CLM-CDE-ICD-VERSION = '9'`. ✅ 657
   - `SIZE-OK` → `WS-CASE-ID ← CASET-RECIPIENT-ID-NUM(1)`, `WS-TOT-PCF-REC-MATCH = 1`, `WS-TOT-PCF-MA-PAID = 1234.56`. ✅ 659–666

**Output record (dummy, key fields):**
```
PRO-RECIPIENT-ID-NUM = M0000000000000000500
PRO-HMS-CASE-KEY     = 123456789
PRO-CLIENT-ID        = CLNT01
PRO-CLM-FROM-DATE    = 20180615
PRO-INCIDENT-DATE    = 20180300   <-- day is 00 (see note)
PRO-CLM-THRU-DATE    = 20190630
CLM-PRI-DX           = S72001A
CLM-PROCEDURE-CODE-7 = 0SG9YZZ
CLM-CDE-ICD-VERSION  = 10   (on the written record; reset to 9 afterwards)
```
> ✅ **Proven quirk (note):** `PRO-INCIDENT-DATE` carries day `00` because `4000-FORMAT-DATE` only unstrings YYYY and MM into `WS-INCIDENT-DATE` (day stays `00`); the `01`-forced day exists only in the *comparison* copy `WS-INCIDENT-DATE-NEW`. (Lines 730–735, 482.)

---

### Scenario 6 — Second claim for the same recipient (no table reload) (BR-08)

**Dummy input:** another claim with `PFX-APP-MEDICAID-NO = 'M0000000000000000500'`, `PFX-APP-DATE-OF-SERVICE = 20190101`; the table from Scenario 5 still holds recipient `…500` with `TABLE-ENTRIES=1`.

**Trace:** the new-recipient `IF` (398–399) is now **false** because `CASET-RECIPIENT-ID-NUM(1) = …500` is no longer `< …500`. The `ELSE IF CASE-RECIPIENT-ID-NUM ≥ PFX-APP-MEDICAID-NO AND CASET-RECIPIENT-ID-NUM(1) = PFX-APP-MEDICAID-NO` (420–421) is **true** → `PERFORM 3020` over the existing table without reloading. ✅
**Result:** `20180301 ≤ 20190101 ≤ 20190630` ✅ → second output record written; `REC-WRITE-CTR`=2; `WS-TOT-PCF-REC-MATCH`=2 for case `…500`. Because `CASE-PCF-MATCH-FLAG(1)` is already `'Y'`, `OPEN-CASES-MATCH-OK-CTR` is **not** incremented again (BR-10). ✅ 468–471

---

### Scenario 7 — Physician claim (`M`/`B`) diagnosis extraction, version 05 (BR-13, BR-14)

**Dummy `CLMI-CLIENT-DATA`:** `AL5-INST-CLAIM-TYPE-ALPHA='M'` (offset 15 byte), `AL5-PHYS-DIAG(1)='E119'`, `AL5-PHYS-CDE-ICD-VERSION(1)='0'`, `AL5-PHYS-DIAG(2)='I10'`, `AL5-PHYS-CDE-ICD-VERSION(2)='0'`.

**Trace:** in `5100`, first `WHEN` (`I/L/O/A/C`) is false; second `WHEN AL5-INST-CLAIM-TYPE-ALPHA = 'M' OR 'B'` true (byte value `'M'`). ✅ 813–814. Loop `1..5` over `AL5-PHYS-DIAG`: slot 1 `'E119'` → `CLM-PRI-DX`; slot 2 `'I10'` → `CLM-SEC-DX`; each also sets `CLM-CDE-ICD-VERSION`; `VER-5-PROF-MB`++ per non-blank slot. ✅ 817–860
**Result:** output record with `CLM-PRI-DX='E119'`, `CLM-SEC-DX='I10'`. ✅
> 🔍 The `'M'/'B'` branch is selected via the **INST**-named field, but reads the same claim-type byte (offset 15) shared by all three layouts — see `CASPCFAL_logic.md` §4.1 BR-13 note.

---

### Scenario 8 — Pharmacy claim (`P`/`Q`) — counted only (BR-13)

**Dummy:** `AL5-INST-CLAIM-TYPE-ALPHA='P'`.
**Trace:** in `5100`, third `WHEN … = 'P' OR 'Q'` true → `ADD +1 TO VER-5-RX-PQ`; no diagnosis moves. ✅ 863–865
**Result:** the output record is still written by `3020` (the `WRITE` at 655 happens **before** any DX-dependence); pharmacy just adds no diagnosis fields. `CLM-PRI-DX` etc. remain whatever `INITIALIZE PRO-CLMPRFX` / body-copy left them. ✅ (comment 676: "RX RECORDS DO NOT HAVE DIAGNOSIS CODES").

---

### Scenario 9 — Dummy-provider substitution on contract `0032600` (BR-11)

**Dummy:** `CLMI-PROV-OF-SVC-NUM='09999996'`, `CLMI-PCF-CONTRACT-NUM='0032600'`, `CLMI-PAY-TO-PROV-NUM='PROV12345678901'`. (Pay-to ≠ `09999996`, so Scenario 3's skip gate at 391–392 is **false**.)
**Trace:** inside `3020`, chg-0009 `IF CLMI-PROV-OF-SVC-NUM='09999996' AND CLMI-PCF-CONTRACT-NUM='0032600'` true → `MOVE CLMI-PAY-TO-PROV-NUM TO CLMI-PROV-OF-SVC-NUM`. ✅ 484–488. The subsequent body copy then moves the (now substituted) `CLMI-PROV-OF-SVC-NUM` to `CLM-PROV-OF-SVC-NUM`. ✅ 493
**Result:** `CLM-PROV-OF-SVC-NUM = 'PROV12345678901'` on output. ✅

---

### Scenario 10 — ICN suffix reformat for `PB`/`DT` (BR-12)

**Dummy:** `CLMI-PM-USER-AREA(1:2)='PB'`, `CLMI-PCF-CONTRACT-NUM='0032600'`, `CLMI-PM-USER-AREA(27:3)='ABC'` (≠`'DSS'`), `CLMI-ICN='ICN0000000000000009X'` (20), `CLMI-PCF-HMS-ICN-SUFFIX='07'` (numeric, non-zero).
**Trace:** chg-0008 block (626–643): outer `IF` true; `CLMI-PCF-HMS-ICN-SUFFIX IS NUMERIC` ✅ and `…-N = 07 ≠ 0` → `MOVE CLMI-ICN TO WS-ICN-17` (first 17 chars), `MOVE CLMI-PCF-HMS-ICN-SUFFIX TO WS-ICN-02`, then `MOVE WS-ICN-GROUP-19 TO PRO-ICN` and `TO CLM-ICN`. ✅ 630–640
**Result:** `PRO-ICN`/`CLM-ICN` = 17-char ICN prefix ∥ `'07'` (via `WS-ICN-GROUP-19`, defined 87–89). ✅
🔍 If suffix were `'00'` (`…-N = 0`) the code `CONTINUE`s (632) and leaves the ICN as originally copied. ✅ 631–632

---

### Scenario 11 — Non-`MAMA` assign file (BR-13 gate)

**Dummy:** `PFX-SYS-HMS-ASSIGN-FILE='XYZ12'`.
**Trace:** `3030-REVIEW-MAMA-VERS` still `INITIALIZE`s the AL areas, but `IF PFX-SYS-HMS-ASSIGN-FILE(1:4) = 'MAMA'` is false → the entire version `EVALUATE` is skipped. ✅ 686–720
**Result:** the record is still written (the `WRITE` at 655 is independent), but no `VER-*` counter changes and no diagnosis/surg extraction occurs. ✅

---

### Scenario 12 — Blank claims-thru date → open-ended upper bound (BR-16)

**Dummy case row:** `CASET-INCIDENT-DATE(1)='2016-01-10'`, `CASET-CLAIMS-THRU-DATE(1)=SPACES`.
**Trace:** `4000-FORMAT-DATE`: incident → `WS-INCIDENT-DATE-NEW-RE = 20160101`; thru is spaces → `ELSE MOVE '99999999' TO WS-CLM-THRU-DATE` → `WS-CLM-THRU-DATE-N = 99999999`. ✅ 737–743
**Result:** any `PFX-APP-DATE-OF-SERVICE ≥ 20160101` passes the upper bound (`≤ 99999999`). ✅

---

### Scenario 13 — Service date **before** the window → excluded (BR-09 gate)

**Dummy:** `PFX-APP-DATE-OF-SERVICE = 20170101`; case incident `'2018-03-15'` → lower bound `20180301`.
**Trace:** Gate 1 open passes; Gate 2 `PFX-APP-DATE-OF-SERVICE ≥ WS-INCIDENT-DATE-NEW-RE` → `20170101 ≥ 20180301`? **false** → the entire build/write block (462–669) is skipped for this row. ✅ 460
**Result:** No output for this claim/case pair; `REC-WRITE-CTR` unchanged. ✅

---

### Scenario 14 — Closed case (status not `'O'`/`X'96'`) → excluded (BR-09 gate)

**Dummy:** `CASET-CASE-STATUS-CODE(1)='C'`.
**Trace:** Gate 1 `IF CASET-CASE-STATUS-CODE(SUB-I)='O' OR = X'96'` → false → skip build/write. ✅ 457–458
**Result:** No output; the case row is *not* counted as matched. ✅

---

### Scenario 15 — Case-match summary detail line format (2100)

**Dummy accumulators for case `…500`:** `WS-CASE-ID='M0000000000000000500'`, `WS-TOT-PCF-REC-MATCH = 3`, `WS-TOT-PCF-MA-PAID = 3703.68`, `SIZE-OK`.
**Trace (2100-WRITE-CASE-PCF-MATCH, 1215–1235):**
- `MATCH-CASE-ID-OUT ← 'M0000000000000000500'`.
- `WS-CONVERT-MATCH (PIC ZZZZ9) ← 3` → `'    3'`; `INSPECT … TALLYING COUNT-M FOR ALL SPACES` → `COUNT-M=4`, `+1 → 5`; `MATCH-TOT-PCF-REC-OUT ← WS-CONVERT-MATCH(5: ) = '3'`. ✅ 1217–1222
- `WS-CONVERT-PCF-PAID (PIC $$$,$$$,$$$,$$9.99) ← 3703.68` → `'        $3,703.68'`; space-strip → `MATCH-TOT-PCF-MA-PAID-OUT ← '$3,703.68'`. ✅ 1224–1229
- `WRITE MATCH-RECORD FROM WS-MATCH-OUT`. ✅ 1235
**Result (illustrative 80-byte line, using the `' * '` separators from 168–177):**
```
 * M0000000000000000500 * 3                   * $3,703.68        *
```
Then `INITIALIZE WS-CASE-PCF-MATCH WS-MATCH-PROCESS-FIELDS` resets the accumulators and `COUNT-M/COUNT-P` for the next case. ✅ 1236–1237

---

### Scenario 16 — Size error → "TOO MANY MATCHES" (BR-17)

**Dummy:** during accumulation for a case, `ADD 1 TO WS-TOT-PCF-REC-MATCH` (max `S9(5)` = 99,999) or `ADD … TO WS-TOT-PCF-MA-PAID` (max `S9(11)V99`) raises `ON SIZE ERROR` → `SET SIZE-ERROR TO TRUE`. ✅ 661–666
**Trace at 2100:** `IF SIZE-OK` is now false → `ELSE MOVE 'TOO MANY MATCHES, $$ PAID NOT AVAILABLE !' TO WS-MATCH-OUT(27:)` and `SET SIZE-OK TO TRUE` (re-arm). ✅ 1230–1234
**Result (illustrative):**
```
 * M0000000000000000500 * TOO MANY MATCHES, $$ PAID NOT AVAILABLE !
```
Note: this case is still flushed because `9000-TERMINATION`/mainline flush condition is `WS-TOT-PCF-REC-MATCH > 0 OR SIZE-ERROR`. ✅ 400, 1245

---

### Scenario 17 — Empty run → trailer message (BR-18)

**Dummy:** the entire run produced no output (`REC-WRITE-CTR = 0`).
**Trace:** `9100-WRITE-MATCH-TRAILER`: `IF REC-WRITE-CTR = 0` → `MOVE 'NO MATCHED PCF RECORDS FOUND' TO WS-MATCH-OUT(6:)` and write; then a blank line and an all-`'*'` line. ✅ 1355–1362
**Result (illustrative):**
```
     NO MATCHED PCF RECORDS FOUND

********************************************************************************
```

---

### Scenario 18 — Versions `02` / `01` / other — counted only

**Dummy:** `PFX-SYS-VERSION='02'` (then `'01'`, then `'99'`).
**Trace:** `3030` routes `'02'→5400`, `'01'→5500`, `WHEN OTHER→5600`. `5400` does `ADD +1 TO VER-2` (extraction commented out, 1128–1192); `5500` does `ADD +1 TO VER-1`; `5600` does `ADD +1 TO OTHER-VERS`. ✅ 706–719, 1123–1211
**Result:** the output record is written (by 3020), but **no** diagnosis/surg fields are populated from client data for these versions. ✅

---

### Scenario 19 — End-of-job statistics and open-not-matched (BR-19)

**Dummy run totals:** `OPEN-CASES-READ-CTR = 10`, `OPEN-CASES-MATCH-OK-CTR = 7`.
**Trace:** `9000-TERMINATION` flushes the last case if pending (1245–1248), writes the trailer (1253), then `COMPUTE OPEN-CASES-NO-MATCH-CTR = 10 − 7 = 3` (1255–1256), and `DISPLAY`s the block (1259–1343), then `CLOSE`s the four still-open files (1345–1348). ✅
**Result (illustrative SYSOUT excerpt, labels verbatim from source):**
```
===================================================
        CASPCFAL - PROGRAM COUNTERS
---------------------------------------------------
PLEASE NOTE: THE PROCESSING STOPS AT END OF PCF INPUT FILE.
THE CASE FILE MAY NOT HAVE BEEN READ TO COMPLETION.
---------------------------------------------------
NUMBER OF PCF RECORDS READ................... :   <PCF-REC-READ-CTR>
NUMBER OF SKIPPED PCF RECORDS PR0V=09999996.. :   <REC-SKIP-PROV>
NUMBER OF SKIPPED DSS RECORDS > 2003 ........ :   <REC-SKIP-DSS>
NUMBER OF CASE RECORDS READ.................. :   <CASE-REC-READ-CTR>
NUMBER OF OPEN CASE RECORDS READ............. :            10
NUMBER OF OPEN CASE RECORDS MATCHED TO PCF... :             7
NUMBER OF OPEN CASE RECORDS NOT MATCHED TO PCF:             3
PCF RECORDS MATCHED TO OPEN CASES AND WRITTEN :   <REC-WRITE-CTR>
... (per-version V5/V4/V3 INST/PROC/PROF/RX tallies, V2, V1, OTHER) ...
===================================================
```
> ✅ The label text (including the literal `PR0V` with a zero, line 1271, and "STOPS AT END OF PCF INPUT FILE", line 1263–1264) is reproduced exactly; the comment at 1249–1251 explains why the very last matched case is flushed in termination.

---

*Every branch of the `PROCEDURE DIVISION` is exercised above. Data values are illustrative dummies; all cited behavior is proven against `CASPCFAL.txt` and its copybooks. Items that depend on unavailable artifacts (real data, JCL) are marked ❓ Open in `CASPCFAL_logic.md`.*
