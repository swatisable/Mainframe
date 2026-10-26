# CASPCFAL — End-to-End Input/Output Mapping

> **Audit-grade · Evidence-based · Zero-hallucination**
>
> This document maps every data source to every data sink that the program actually reads/writes, with exact field-level moves and transformations. Tags: ✅ Proven · 🔍 Inferred · ❓ Open · 📎 Missing artifact. Line numbers refer to `CASPCFAL.txt`; `PIC`s are read from the resolved copybooks (see `CASPCFAL_logic.md` §3.2). The `MOVE` inventory below was extracted directly from source lines 462–669 (comment lines excluded).

---

## 1. File-level I/O map

```
        CONTROL CARDS (SYS004, 80B) ─┐
                                     │  tag '1' → WS-SAVE-CREATE-SOURCE
   PCF CLAIMS IN (SRCPCFI, VB≤32752)─┤
        │  READ INTO WS-CLMI-RECORD  │
        ▼                            ▼
   ┌─────────────────────  CASPCFAL  ─────────────────────┐
   │  match PCF claim ↔ open CAS2000 case (recipient id)   │
   │  window: incident-month-01 ≤ svc-date ≤ claims-thru   │
   └───────┬───────────────────────────┬──────────────────┘
        ▲  │ WRITE CLMO-RECORD (754B)   │ WRITE MATCH-RECORD (80B)
        │  ▼                            ▼
   CASE IN (CASEFLI, 384B)     PCF OUT (SRCPCFO)     MATCH REPORT (MATCHO)
   READ INTO WS-CASE-RECORD                          + SYSOUT statistics (DISPLAY)
```
✅ Files/verbs: SELECT 26–30; OPEN 297–301; READs 319/330/343; WRITEs 357/655/1235/1357; CLOSE 345/1345–1348.

| Direction | Logical file | DD | Rec len | Buffer | Verb sites |
|---|---|---|---|---|---|
| IN | `SRCPCF-IN` | `SRCPCFI` | VB 4–32752 | `WS-CLMI-RECORD` | READ 319 |
| IN | `CASEFL-IN` | `CASEFLI` | 384 | `WS-CASE-RECORD` | READ 330 |
| IN | `CNTL-CARDS` | `SYS004` | 80 | `CARD-REC` | READ 343 |
| OUT | `SRCPCF-OUT` | `SRCPCFO` | 754 | `WS-SRCPCF-OUT` | WRITE 655 |
| OUT | `CASE-PCF-MATCH` | `MATCHO` | 80 | `WS-MATCH-OUT` | WRITE 357/1235/1357/1360/1362 |
| OUT | `SYSOUT` | (DISPLAY) | — | literals + `NUM-REC-OUT` | 1259–1344 |

📎 The DD-name → physical-dataset binding is in JCL not provided → ❓ Open.

---

## 2. Output record `WS-SRCPCF-OUT` (SRCPCFO, 754 bytes)

The output record = **prefix** (`PRO-…`, copybook `CLMPREFX`, 140B) + **body** (`CLM-…`, copybook `FDPCF601`). It is built in `3020-READ-CASE-TABLE` in this precedence order:

1. `INITIALIZE PRO-CLMPRFX` (462) → prefix numerics=0, alpha=spaces.
2. **Prefix moves** (§2.1).
3. Dummy-provider substitution into the *input* field (§4.2), then
4. **Body copy** `CLMI-… → CLM-…` (§2.2).
5. **ICN-suffix reformat** may overwrite `PRO-ICN`/`CLM-ICN` (§4.3).
6. **Version extraction** (`3030`→`51/52/53/54/55/5600`) may overwrite diagnosis/procedure/ICD-version fields (§3).
7. **ICD-version normalization** sets `CLM-CDE-ICD-VERSION` for the written record (§4.4).
8. `WRITE CLMO-RECORD FROM WS-SRCPCF-OUT` (655).

> 🔍 **Precedence rule:** for the diagnosis/procedure/ICD-version/ICN fields, later steps (5–7) override the body copy (step 4). This is proven by statement order: body copy 492–624 precedes `3030` (645) precedes the normalization `EVALUATE` (646–653) precedes `WRITE` (655).

### 2.1 Prefix build — `PRO-…` (12 moves, lines 462–483 + 639) ✅

| Output `PRO-` field | `PIC` | ← Source | Transformation | Line |
|---|---|---|---|---|
| `PRO-RECIPIENT-ID-NUM` | `X(20)` | `CLMI-PCF-MA-NUM` | direct | 463 |
| `PRO-HMS-CASE-KEY` | `9(09)` | `CASET-HMS-CASE-KEY(SUB-I)` | from matched **case** row | 464 |
| `PRO-CLIENT-ID` | `X(06)` | `CASET-HMS-CLIENT-ID(SUB-I)` | from case row (chg 0012) | 466 |
| `PRO-CREATE-SOURCE` | `X(02)` | `WS-SAVE-CREATE-SOURCE` | from control card tag `'1'` (chg 0005) | 472 |
| `PRO-ICN` | `X(20)` | `CLMI-ICN` | direct (may be overwritten §4.3) | 474 |
| `PRO-FORMER-ICN` | `X(20)` | `CLMI-FORMER-ICN` | direct | 475 |
| `PRO-XACTION-STATUS` | `X(01)` | `CLMI-XACTION-STATUS` | direct | 476 |
| `PRO-CLM-FROM-DATE` | `9(08)` | `PFX-APP-DATE-OF-SERVICE` | from claim prefix | 478 |
| `PRO-CLAIM-TRANS-TYPE` | `X(01)` | `PFX-NET-CLAIM-TRANS-TYPE` | from claim prefix | 480 |
| `PRO-INCIDENT-DATE` | `9(08)` | `WS-INCIDENT-DATE` | derived (§4.1); **day = 00** | 482 |
| `PRO-CLM-THRU-DATE` | `9(08)` | `WS-CLM-THRU-DATE` | derived (§4.1) | 483 |
| `PRO-ICN` (conditional) | `X(20)` | `WS-ICN-GROUP-19` | reformatted 17+2 (§4.3, chg 0008) | 637 |

> ✅ **Prefix fields NOT populated** (remain at `INITIALIZE` defaults): `PRO-RX-WRITTEN-DATE` (=0), `PRO-LAST-HIT-DATE-TM` (=0), `PRO-FILLER` (=spaces). No `MOVE` targets them (verified in the extracted inventory). 🔍 They are emitted as zero/space.

### 2.2 Body copy — `CLMI-… → CLM-…` (106 moves, lines 492–624) ✅

**105 fields are copied name-for-name** (`CLMI-<x>` → `CLM-<x>`) and **1 is renamed**:

| Renamed body move | Input `PIC` | Output `PIC` | Line |
|---|---|---|---|
| `CLMI-PROCEDURE-CODE-5` → `CLM-PROCEDURE-CODE-7` | `X(05)` | `X(07)` | 494–495 |

The 105 name-for-name `CLMI-<x> → CLM-<x>` copies (`<x>` shown once):

```
PCF-MA-NUM              PROV-OF-SVC-NUM         PROCEDURE-CODE-MOD1     PROCEDURE-CODE-MOD2
SURGERY-DATE            PROC-CODE-DENTAL        CLM-TYPE                ORIG-CLM-TYPE
CATG-OF-SVC             TYPE-OF-SVC             PLACE-OF-SVC            DRG
LEVEL-OF-CARE-IND       CLAIM-FORM-IND          PAT-LAST-NAME          PAT-FIRST-NAME
PAT-MID-INIT            PAT-SEX                 PAT-DOB                 XACTION-TYPE
XACTION-STATUS          DOR                     REMIT-ID-NUM           ADJ-IND
ADJ-REASON              ICN                     PRI-DX*                 SEC-DX*
UNIT-VISITS-DAYS        CLAIM-FROM-DOS          CLAIM-THRU-DOS         RECORD-THRU-DOS
ADMIT-DATE              DISCH-DATE              ELIG-INPAT-DAYS        INELIG-INPAT-DAYS
NATURE-HSP-ADMISSION    PAT-STATUS-CODE         TRAUMA-IND             TPL-ACCIDENT-IND
PROV-CLAIM-NUM          MA-BILLED-HDR           OTHER-INS-PAID-HDR     MC-COINS-DTL
MC-DEDUCT-DTL           DRG-ALLOWED             MA-BILLED-NET-HDR      TOT-MA-PAID-HDR
MC-ALLOWED-DTL          OTHER-INS-PAID-DTL      MA-BILLED-NET-DTL      MA-PAID-DTL
PROV-TYPE               PAY-TO-PROV-NUM         REFER-PROV-NUM         PROV-SPECIALTY
RX-SUPPLY-DAYS          RX-REFILL-IND           VERSION-NUMBER         PCF-MC-NUM
MC-ATTACHMENT-IND       MC-FORCE-IND            MC-BENEFITS-EXHAUSTED  FAMILY-PLANNING-IND
MULTI-MATCH-IND         RUNTIME-SEQ-NUM         NUM-REV-CHARGES        NUM-OTH-SEGS
FILE-DATA-SOURCE        PCF-CONTRACT-NUM        CLAIM-EMERGENCY-IND    STAT-DOLLARS-HDR-OR-DTL
SUMMED-BILL-ANC-DOLLARS BILL-TYPE               RECORD-FROM-DOS-DTL    FORMER-ICN
SRC-LINE-ITEM-DTL-CNT   NET-DUPE-DATE           OTP-COB-IND            PM-USER-AREA
PM-USER-AREA-2          XWALKED-PROC-CODE1      APPLIED-INCOME         NUM-LEAVE-DAYS
RATE-PAID               FACILITY-PROV-NUM       DX-3*                  DX-4*
DX-5*                   INST-ADDITIONAL-FIELDS  NEW-DRG                PROV-NUM-FROM-PREFIX
DATE-REFORMATTED        SYS-DELETE-STATUS       STAMP-DATE-TIME        STAMP-SEQ-NUM
ORIG-TOT-MA-PAID-HDR    ORIG-MA-PAID-DTL        PCF-CLASSIFICATION-STAT PCF-CLASSIFICATION-DATE
PCF-IN-PROGRESS-IND     PCF-LOGICAL-DELETE-IND  PCF-HMS-ICN-SUFFIX     PCF-FILE-NAME
PCF-VERSION-NUMBER
```
`*` = also a candidate for **override** by version extraction (§3): `PRI-DX`, `SEC-DX`, `DX-3`, `DX-4`, `DX-5`. Additionally `CLM-PROCEDURE-CODE-7` (the renamed copy) and `CLM-ICN` may be overridden (§3, §4.3). ✅

> ✅ **Widening note:** input `CLMI-PRI-DX`/`CLMI-SEC-DX` are `X(05)` but output `CLM-PRI-DX`/`CLM-SEC-DX` are `X(07)`; the 5-char values are copied here, then (for MAMA v3–v5 claims) replaced by 7-char `AL` diagnosis codes (§3). ✅ (FDPCF602 148–149; FDPCF601 149–150.)
> ✅ **`CLM-CDE-ICD-VERSION` is NOT body-copied** (no such field on `CLMI`); it is set only by extraction and the write-time normalization (§4.4). ✅

---

## 3. Diagnosis / procedure extraction overrides (client "AL" data → `CLM-…`)

Runs only when `PFX-SYS-HMS-ASSIGN-FILE(1:4)='MAMA'` (686) and version ∈ {05,04,03} (694–705). Source is `CLMI-CLIENT-DATA` reinterpreted through `FDALINH{v}` / `FDALPHY{v}`. All values pass through intermediates `WK-DIAG-CODE X(7)` / `WK-ICD-VERSION X(2)` (192–194). ✅

| Claim-type (`AL{v}-INST-CLAIM-TYPE-ALPHA`) | Source (occurs 5 unless noted) | → Output field | Line (v05) |
|---|---|---|---|
| `I`/`L`/`O`/`A`/`C` (institutional) | `AL{v}-INST-DIAG(1)` | `CLM-PRI-DX` | 763 |
| | `AL{v}-INST-DIAG(2)` | `CLM-SEC-DX` | 770 |
| | `AL{v}-INST-DIAG(3/4/5)` | `CLM-DX-3/4/5` | 777/784/791 |
| | `AL{v}-INST-CDE-ICD-VERSION(n)` | `CLM-CDE-ICD-VERSION` (last non-blank wins) | 766/773/780/787/794 |
| | `AL{v}-INST-HDR-SURG-CD(1)` | `CLM-PROCEDURE-CODE-7` | 807 |
| `M`/`B` (physician) | `AL{v}-PHYS-DIAG(1..5)` | `CLM-PRI-DX`/`SEC-DX`/`DX-3/4/5` | 825/832/839/846/853 |
| | `AL{v}-PHYS-CDE-ICD-VERSION(n)` | `CLM-CDE-ICD-VERSION` | 828/835/842/849/856 |
| `P`/`Q` (pharmacy) | — (no diagnosis) | — (counter only `VER-{v}-RX-PQ`) | 865 |
| other | — | — (`CONTINUE`) | 867 |

- Each move is guarded by `IF … NOT EQUAL SPACES` (762–795), so blank slots do not overwrite. ✅
- Versions **02/01/other** perform **no** field overrides (counters only, §5). ✅ 1123–1211
- 🔍 The `CLM-CDE-ICD-VERSION` ends up holding the **last non-blank** slot's ICD version because every slot moves into the same field (no positional target). ✅ by repeated target.

---

## 4. Specific transformations (with exact rules)

### 4.1 Date-window derivation — `4000-FORMAT-DATE` (725–743) ✅
| Output | Rule | Line |
|---|---|---|
| `WS-INCIDENT-DATE` (`9(08)` group YYYY MM DD) | `UNSTRING CASET-INCIDENT-DATE DELIMITED BY '-' OR '  ' INTO WS-IN-YYYY WS-IN-MM` (day untouched ⇒ `00`) | 730–733 |
| `WS-INCIDENT-DATE-NEW-RE` (compare lower bound) | copy of above **with day forced to `01`** (chg 0001) | 734–735 |
| `WS-CLM-THRU-DATE` / `-N` (upper bound) | `UNSTRING CASET-CLAIMS-THRU-DATE … INTO YYYY MM DD`; **blank ⇒ `'99999999'`** | 737–743 |

### 4.2 Dummy-provider substitution (chg 0009, 484–488) ✅
`IF CLMI-PROV-OF-SVC-NUM='09999996' AND CLMI-PCF-CONTRACT-NUM='0032600' → MOVE CLMI-PAY-TO-PROV-NUM TO CLMI-PROV-OF-SVC-NUM` **before** the body copy — so `CLM-PROV-OF-SVC-NUM` receives the pay-to number.

### 4.3 ICN-suffix reformat (chg 0008, 626–643) ✅
Condition: `(CLMI-PM-USER-AREA(1:2)='PB' OR 'DT') AND CLMI-PCF-CONTRACT-NUM='0032600' AND CLMI-PM-USER-AREA(27:3) NOT='DSS' AND CLMI-PCF-HMS-ICN-SUFFIX IS NUMERIC AND …-SUFFIX-N ≠ 0`.
Action: `WS-ICN-17 ← CLMI-ICN(1:17)`, `WS-ICN-02 ← CLMI-PCF-HMS-ICN-SUFFIX`, then `WS-ICN-GROUP-19 → PRO-ICN` **and** `→ CLM-ICN`. (`WS-ICN-GROUP-19` = 17+2, def 87–89.) When suffix `= 0`, `CONTINUE` (no change).

### 4.4 ICD-version normalization at write (646–657) ✅
`EVALUATE TRUE: WHEN CLM-CDE-ICD-VERSION='0 ' → '10'; WHEN ' 0' → '10'; WHEN OTHER → '9'`, then `WRITE`, then `MOVE '9' TO CLM-CDE-ICD-VERSION` (reset). So the **written** record's ICD version is `'10'` only when the extracted value was `'0'`-ish, otherwise `'9'`.

---

## 5. Match report output `WS-MATCH-OUT` (MATCHO, 80 bytes)

Layout (168–177): `' * '` `MATCH-CASE-ID-OUT X(20)` `' * '` `MATCH-TOT-PCF-REC-OUT X(19)` `' * '` `MATCH-TOT-PCF-MA-PAID-OUT X(18)` `' *'`.

| Line type | Content | Source → transform | Site |
|---|---|---|---|
| Header (×1 + blank) | `CASE ID` / `PCF RECORDS MATCHED` / `PCF TOT $$ MA PAID` | literals (init values 170–176) | 357–359 |
| Detail (per matched case) | case id, match count, $ paid | `WS-CASE-ID`; `WS-TOT-PCF-REC-MATCH`→`WS-CONVERT-MATCH (ZZZZ9)`; `WS-TOT-PCF-MA-PAID`→`WS-CONVERT-PCF-PAID ($$$,$$$,$$$,$$9.99)`; both left-justified via `INSPECT…TALLYING`+refmod | 1215–1235 |
| Detail (size error) | `TOO MANY MATCHES, $$ PAID NOT AVAILABLE !` | literal overlay at `WS-MATCH-OUT(27:)` | 1231–1232 |
| Trailer | `NO MATCHED PCF RECORDS FOUND` (only if `REC-WRITE-CTR=0`), blank, all-`'*'` | literals | 1355–1362 |

Accumulator sources (per case, chg 0002/0004): `WS-TOT-PCF-REC-MATCH += 1` (661), `WS-TOT-PCF-MA-PAID += CLMI-TOT-MA-PAID-HDR` (664), `WS-CASE-ID ← CASET-RECIPIENT-ID-NUM(1)` (660); reset via `INITIALIZE WS-CASE-PCF-MATCH` (1236). ✅

---

## 6. SYSOUT statistics (`DISPLAY`, 1259–1344) ✅

Each counter is edited through `NUM-REC-OUT (PIC ZZZ,ZZZ,ZZ9)` then displayed with a fixed label. Mapping (counter → label):

| Counter | Label (verbatim) | Line |
|---|---|---|
| `PCF-REC-READ-CTR` | `NUMBER OF PCF RECORDS READ...` | 1267–1269 |
| `REC-SKIP-PROV` | `NUMBER OF SKIPPED PCF RECORDS PR0V=09999996..` | 1270–1272 |
| `REC-SKIP-DSS` | `NUMBER OF SKIPPED DSS RECORDS > 2003 ...` | 1273–1275 |
| `CASE-REC-READ-CTR` | `NUMBER OF CASE RECORDS READ...` | 1276–1278 |
| `OPEN-CASES-READ-CTR` | `NUMBER OF OPEN CASE RECORDS READ...` | 1279–1281 |
| `OPEN-CASES-MATCH-OK-CTR` | `...OPEN CASE RECORDS MATCHED TO PCF...` | 1282–1284 |
| `OPEN-CASES-NO-MATCH-CTR` | `...OPEN CASE RECORDS NOT MATCHED TO PCF` | 1285–1287 |
| `REC-WRITE-CTR` | `PCF RECORDS MATCHED TO OPEN CASES AND WRITTEN` | 1288–1291 |
| `VER-5/4/3-INST-ILOAC` | `PCF RECORDS INST ILOA OR C UPDATED V5/V4/V3` | 1292–1318 |
| `VER-5/4/3-PROC-CD` | `PCF RECORDS PROC CD UPDATED V5/V4/V3` | 1295–1321 |
| `VER-5/4/3-PROF-MB` | `PCF RECORDS PROF M OR B UPDATED V5/V4/V3` | 1298–1323 |
| `VER-5/4/3-RX-PQ` | `PCF RECORDS RX P OR Q UPDATED V5/V4/V3` | 1301–1326 |
| `VER-2` / `VER-1` | `PCF RECORDS V2 / V1` | 1328–1333 |
| `OTHER-VERS` | `PCF RECORDS OTHER` | 1340–1342 |

> ✅ `OPEN-CASES-NO-MATCH-CTR` and `REC-WRITE-CTR` are displayed **twice** (also at 1334–1339) — proven duplicate labels, not a transcription error.

---

## 7. Control-card input mapping (`SYS004` → program state) ✅

| Input columns (`CARD-REC`, 179–184) | Field | Rule | → Effect |
|---|---|---|---|
| col 1 | `CARD-TAG X(01)` | `IF = '1'` | gate (348) |
| cols 4–33 | `CARD-COMMENT X(30)` | (read but never referenced individually) | informational only |
| cols 35–36 | `CARD-DATA X(02)` | `MOVE CARD-DATA(1:2) TO WS-SAVE-CREATE-SOURCE` | later → every `PRO-CREATE-SOURCE` (472) |

🔍 Only tag `'1'` cards influence output; all other cards are consumed and discarded (no `ELSE`). ✅ 342–350

---

## 8. End-to-end business examples

### Example A — an institutional MAMA-v05 claim that matches an open case
*Inputs (dummy):* claim `PFX-APP-MEDICAID-NO='M…500'`, `PFX-APP-DATE-OF-SERVICE=20180615`, `PFX-SYS-EXIT-FROM-REF-STATUS='Y'`, `PFX-SYS-HMS-ASSIGN-FILE='MAMA5'`, `PFX-SYS-VERSION='05'`, `CLMI-PCF-MA-NUM='M…500'`, `CLMI-TOT-MA-PAID-HDR=1234.56`, client data claim-type `'I'`, `INST-DIAG(1)='S72001A'` (ICD ver `'0'`), `INST-HDR-SURG-CD(1)='0SG9YZZ'`; case row open, incident `2018-03-15`, thru `2019-06-30`, case-key `123456789`, client `CLNT01`; control card tag `'1'` data `'HM'`.

*End-to-end result (proven path — see `CASPCFAL_illustrations.md` Scenario 5):*
| Output field | Value | Origin |
|---|---|---|
| `PRO-RECIPIENT-ID-NUM` | `M…500` | `CLMI-PCF-MA-NUM` (463) |
| `PRO-HMS-CASE-KEY` | `123456789` | case row (464) |
| `PRO-CLIENT-ID` | `CLNT01` | case row (466) |
| `PRO-CREATE-SOURCE` | `HM` | control card (472) |
| `PRO-CLM-FROM-DATE` | `20180615` | `PFX-APP-DATE-OF-SERVICE` (478) |
| `PRO-INCIDENT-DATE` | `20180300` | derived, day 00 (482) |
| `PRO-CLM-THRU-DATE` | `20190630` | derived (483) |
| `CLM-PRI-DX` | `S72001A` | AL5 extraction override (763) |
| `CLM-PROCEDURE-CODE-7` | `0SG9YZZ` | AL5 surg override (807) |
| `CLM-CDE-ICD-VERSION` | `10` | normalized from `'0'` (648) |
| *+ 100+ body fields* | copied `CLMI→CLM` | body copy (492–624) |
*Side effects:* `REC-WRITE-CTR`+1, `OPEN-CASES-MATCH-OK-CTR`+1 (first match), `WS-TOT-PCF-REC-MATCH`=1, `WS-TOT-PCF-MA-PAID`=1234.56 → later a MATCHO detail line for case `M…500`.

### Example B — a claim that is excluded (never reaches output)
*Input (dummy):* `PFX-SYS-EXIT-FROM-REF-STATUS='N'`. → `2000-MAINLINE` line 372 true → read next PCF, `GO TO …EXIT` (374–375). **No SRCPCFO record, no MATCHO effect.** ✅ (see Scenario 1).

### Example C — a DSS claim in the excluded service-year range
*Input (dummy):* contract `0032600`, `PM-USER-AREA(27:3)='DSS'`, `CLMI-CLAIM-FROM-DOS=050115`. → line 377–385 true → `REC-SKIP-DSS`+1, skip (386–388). Reported at 1273–1275. ✅ (see Scenario 2).

---

## 9. Input-field → decision/where-used quick index (behavior-driving)

| Input field | Source | Used for | Line(s) |
|---|---|---|---|
| `PFX-APP-MEDICAID-NO` | claim prefix | primary match key | 365,367,398,420 |
| `PFX-APP-DATE-OF-SERVICE` | claim prefix | service-date window + `PRO-CLM-FROM-DATE` | 460–461,478 |
| `PFX-SYS-EXIT-FROM-REF-STATUS` | claim prefix | exclude non-`'Y'` | 372 |
| `PFX-SYS-HMS-ASSIGN-FILE` | claim prefix | `'MAMA'` gate | 686 |
| `PFX-SYS-VERSION` | claim prefix | version route | 688–718 |
| `PFX-NET-CLAIM-TRANS-TYPE` | claim prefix | `PRO-CLAIM-TRANS-TYPE` | 480 |
| `CLMI-PCF-CONTRACT-NUM` | claim body | DSS/prov/ICN rules | 377,485,628 |
| `CLMI-PM-USER-AREA` | claim body | DSS/`PB`/`DT` rules | 378,626–629 |
| `CLMI-CLAIM-FROM-DOS` | claim body | DSS year filter | 384–385 |
| `CLMI-PROV-OF-SVC-NUM` / `CLMI-PAY-TO-PROV-NUM` | claim body | dummy-prov skip/substitute | 391–392,484–487 |
| `CLMI-PCF-HMS-ICN-SUFFIX` | claim body | ICN reformat | 630–635 |
| `CLMI-TOT-MA-PAID-HDR` | claim body | $ accumulation | 664 |
| `CASE/CASET-RECIPIENT-ID-NUM` | case | match key | 365,399,421,443 |
| `CASET-CASE-STATUS-CODE` | case | open-case gate | 335,457–458 |
| `CASET-INCIDENT-DATE` / `CASET-CLAIMS-THRU-DATE` | case | window bounds | 729–743 |
| `CASET-HMS-CASE-KEY` / `CASET-HMS-CLIENT-ID` | case | `PRO-HMS-CASE-KEY`/`PRO-CLIENT-ID` | 464,466 |
| `CARD-TAG` / `CARD-DATA` | control card | create-source | 348–350 |

---

*All field mappings above were extracted directly from `CASPCFAL.txt` (lines 462–669 for the output build) and cross-checked against the resolved copybooks. Unavailable bindings (JCL/dataset) are marked ❓ Open. No field name was invented; the single renamed move (`PROCEDURE-CODE-5`→`-7`) is called out explicitly.*
