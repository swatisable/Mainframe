#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASPCFNJ_build_mapping.py
=========================
Builds the field-to-field mapping workbook ``CASPCFNJ_1x1_Field_Mapping.xlsx``
for the COBOL program ``CASPCFNJ`` (PCF claim extract based on CAS2000 case data).

Design notes / honesty rules
----------------------------
* Every output field row below is anchored to a REAL line of code in ``CASPCFNJ``
  (the line number is shown in the Comments column / Source Field column).
* The identity MOVE block (CLMI-* -> CLM-*) is parsed directly out of the
  program source so the list cannot drift from the code.
* The input/output copybooks (CLMPREFX, FDPCF601, FDPCF602, TPLPREFX, NCTCASE,
  FDNJTPC5/4, FDNJ5INS, FDNJ4INS ...) are NOT present in this repository.
  Therefore exact PICTURE clauses and byte offsets for the PRO-* (CLMPREFX) and
  CLM-* (FDPCF601) fields cannot be read and are marked ``[UNCERTAIN - copybook
  not in repo]``.  Where a size/type can be *derived from the program itself*
  (e.g. an inline redefinition, a literal, or a numeric comparison) it is shown
  and tagged ``(derived)``.
* The CASE-PCF-MATCH report record (WS-MATCH-OUT) IS defined inline in the
  program, so its fields carry exact PIC clauses and exact byte positions.
* All claim sample values are consistent across input/output and are tagged
  ``(illustrative)`` because the real PICs live in the absent copybooks.

Run:  python3 CASPCFNJ_build_mapping.py
Out:  CASPCFNJ_1x1_Field_Mapping.xlsx  (4 sheets)
"""

import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SRC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CASPCFNJ")
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "CASPCFNJ_1x1_Field_Mapping.xlsx")

UNCERTAIN_CLM = "[UNCERTAIN - FDPCF601 copybook not in repo]"
UNCERTAIN_PRO = "[UNCERTAIN - CLMPREFX copybook not in repo]"
ILLUS = "(illustrative)"

# --------------------------------------------------------------------------- #
#  1.  Parse the identity MOVE block (CLMI-* -> CLM-*) straight from the source #
# --------------------------------------------------------------------------- #
def parse_identity_block(path):
    """Return ordered list of (lineno, source, target) for every active
    ``MOVE CLMI-xxx TO CLM-xxx`` in paragraph 3020 (lines ~572-704)."""
    rows = []
    with open(path, encoding="latin-1") as fh:
        lines = [ln.rstrip("\r\n") for ln in fh]

    # Tokenise active (non-comment) code with line numbers.
    tokens = []
    for i, raw in enumerate(lines, 1):
        indicator = raw[6] if len(raw) > 6 else " "
        if indicator == "*":                       # full-line comment
            continue
        code = raw[7:] if len(raw) > 7 else ""
        for word in code.split():
            tokens.append((word, i))

    verbs = {"MOVE", "IF", "ADD", "PERFORM", "WRITE", "READ", "INITIALIZE",
             "SET", "GO", "END-IF", "ELSE", "COMPUTE", "EVALUATE", "WHEN",
             "END-EVALUATE", "DISPLAY", "INSPECT", "UNSTRING", "CONTINUE",
             "CLOSE", "OPEN", "END-READ", "END-ADD", "STOP"}

    i = 0
    while i < len(tokens):
        word, lineno = tokens[i]
        if word == "MOVE":
            j = i + 1
            src = []
            while j < len(tokens) and tokens[j][0] != "TO":
                src.append(tokens[j][0])
                j += 1
            tgt = []
            k = j + 1
            while k < len(tokens) and tokens[k][0] not in verbs:
                t = tokens[k][0]
                tgt.append(t)
                k += 1
                if t.endswith(".") and not re.search(r"\d\.$", t):
                    break
            source = " ".join(src)
            target = " ".join(tgt).rstrip(".")
            # Keep only the straight field-by-field claim copy block.
            if (572 <= lineno <= 704 and target.startswith("CLM-")
                    and source.startswith("CLMI-")):
                rows.append((lineno, source, target))
            i = j
        else:
            i += 1
    return rows


IDENTITY = parse_identity_block(SRC_FILE)

# --------------------------------------------------------------------------- #
#  2.  Per-field annotations (PIC hint, mapping type, samples, comments)       #
#      Only fields that need something beyond "1x1 identity" are listed here.  #
# --------------------------------------------------------------------------- #
# Illustrative sample values keyed by the CLMI-* source field name.
SAMPLE = {
    "CLMI-PCF-MA-NUM": "100000000001",
    "CLMI-PROV-OF-SVC-NUM": "09888801",
    "CLMI-PROCEDURE-CODE-5": "99213",
    "CLMI-PROCEDURE-CODE-MOD1": "25",
    "CLMI-PROCEDURE-CODE-MOD2": "  ",
    "CLMI-SURGERY-DATE": "20230115",
    "CLMI-PROC-CODE-DENTAL": "       ",
    "CLMI-CLM-TYPE": "01",
    "CLMI-ORIG-CLM-TYPE": "01",
    "CLMI-CATG-OF-SVC": "01",
    "CLMI-TYPE-OF-SVC": "1",
    "CLMI-PLACE-OF-SVC": "21",
    "CLMI-DRG": "470",
    "CLMI-LEVEL-OF-CARE-IND": "1",
    "CLMI-CLAIM-FORM-IND": "A",
    "CLMI-PAT-LAST-NAME": "DOE",
    "CLMI-PAT-FIRST-NAME": "JOHN",
    "CLMI-PAT-MID-INIT": "Q",
    "CLMI-PAT-SEX": "M",
    "CLMI-PAT-DOB": "19550310",
    "CLMI-XACTION-TYPE": "01",
    "CLMI-XACTION-STATUS": "P",
    "CLMI-DOR": "20230220",
    "CLMI-REMIT-ID-NUM": "RA2023020012345",
    "CLMI-ADJ-IND": "N",
    "CLMI-ADJ-REASON": "   ",
    "CLMI-ICN": "2023051000001234567",
    "CLMI-PRI-DX": "E1165  ",
    "CLMI-SEC-DX": "I10    ",
    "CLMI-UNIT-VISITS-DAYS": "003",
    "CLMI-CLAIM-FROM-DOS": "0230115",
    "CLMI-CLAIM-THRU-DOS": "0230115",
    "CLMI-RECORD-THRU-DOS": "0230115",
    "CLMI-ADMIT-DATE": "20230114",
    "CLMI-DISCH-DATE": "20230116",
    "CLMI-ELIG-INPAT-DAYS": "002",
    "CLMI-INELIG-INPAT-DAYS": "000",
    "CLMI-NATURE-HSP-ADMISSION": "3",
    "CLMI-PAT-STATUS-CODE": "01",
    "CLMI-TRAUMA-IND": "N",
    "CLMI-TPL-ACCIDENT-IND": "N",
    "CLMI-PROV-CLAIM-NUM": "PC2023000123456",
    "CLMI-MA-BILLED-HDR": "00000150000",
    "CLMI-OTHER-INS-PAID-HDR": "00000000000",
    "CLMI-MC-COINS-DTL": "00000000000",
    "CLMI-MC-DEDUCT-DTL": "00000000000",
    "CLMI-DRG-ALLOWED": "00000120000",
    "CLMI-MA-BILLED-NET-HDR": "00000150000",
    "CLMI-TOT-MA-PAID-HDR": "00000120000",
    "CLMI-MC-ALLOWED-DTL": "00000000000",
    "CLMI-OTHER-INS-PAID-DTL": "00000000000",
    "CLMI-MA-BILLED-NET-DTL": "00000150000",
    "CLMI-MA-PAID-DTL": "00000120000",
    "CLMI-PROV-TYPE": "08",
    "CLMI-PAY-TO-PROV-NUM": "09888801",
    "CLMI-REFER-PROV-NUM": "09777701",
    "CLMI-PROV-SPECIALTY": "011",
    "CLMI-RX-SUPPLY-DAYS": "000",
    "CLMI-RX-REFILL-IND": "0",
    "CLMI-VERSION-NUMBER": "06",
    "CLMI-PCF-MC-NUM": "               ",
    "CLMI-MC-ATTACHMENT-IND": "N",
    "CLMI-MC-FORCE-IND": "N",
    "CLMI-MC-BENEFITS-EXHAUSTED": "N",
    "CLMI-FAMILY-PLANNING-IND": "N",
    "CLMI-MULTI-MATCH-IND": "N",
    "CLMI-RUNTIME-SEQ-NUM": "000001",
    "CLMI-NUM-REV-CHARGES": "001",
    "CLMI-NUM-OTH-SEGS": "000",
    "CLMI-FILE-DATA-SOURCE": "MA",
    "CLMI-PCF-CONTRACT-NUM": "0032600",
    "CLMI-CLAIM-EMERGENCY-IND": "N",
    "CLMI-STAT-DOLLARS-HDR-OR-DTL": "00000000000",
    "CLMI-SUMMED-BILL-ANC-DOLLARS": "00000000000",
    "CLMI-BILL-TYPE": "111",
    "CLMI-RECORD-FROM-DOS-DTL": "0230115",
    "CLMI-FORMER-ICN": "                   ",
    "CLMI-SRC-LINE-ITEM-DTL-CNT": "001",
    "CLMI-NET-DUPE-DATE": "20230220",
    "CLMI-OTP-COB-IND": "N",
    "CLMI-PM-USER-AREA": "PB                        ",
    "CLMI-PM-USER-AREA-2": "                    ",
    "CLMI-XWALKED-PROC-CODE1": "0000000",
    "CLMI-APPLIED-INCOME": "00000000000",
    "CLMI-NUM-LEAVE-DAYS": "000",
    "CLMI-RATE-PAID": "00000060000",
    "CLMI-FACILITY-PROV-NUM": "09888801",
    "CLMI-DX-3": "       ",
    "CLMI-DX-4": "       ",
    "CLMI-DX-5": "       ",
    "CLMI-INST-ADDITIONAL-FIELDS": "   ",
    "CLMI-NEW-DRG": "470",
    "CLMI-PROV-NUM-FROM-PREFIX": "09888801",
    "CLMI-DATE-REFORMATTED": "20230115",
    "CLMI-SYS-DELETE-STATUS": " ",
    "CLMI-STAMP-DATE-TIME": "2023022014300100",
    "CLMI-STAMP-SEQ-NUM": "0001",
    "CLMI-ORIG-TOT-MA-PAID-HDR": "00000120000",
    "CLMI-ORIG-MA-PAID-DTL": "00000120000",
    "CLMI-PCF-CLASSIFICATION-STAT": " ",
    "CLMI-PCF-CLASSIFICATION-DATE": "20230220",
    "CLMI-PCF-IN-PROGRESS-IND": "N",
    "CLMI-PCF-LOGICAL-DELETE-IND": "N",
    "CLMI-PCF-HMS-ICN-SUFFIX": "00",
    "CLMI-PCF-FILE-NAME": "PCF       ",
    "CLMI-PCF-VERSION-NUMBER": "06",
}

# Fields whose behaviour is NOT a plain 1x1 identity copy.  Keyed by target.
SPECIAL = {
    "CLM-PROCEDURE-CODE-7": dict(
        pic="X(7) (derived from name; src is X(5))",
        mtype="derived/transformed (widen 5->7) + crosswalk override",
        comment=("L574 base MOVE CLMI-PROCEDURE-CODE-5 (5 bytes) into 7-byte "
                 "target. For client file versions it is OVERRIDDEN in 3030 by "
                 "CA/CB/CC/CD-?-PROC-CDE (L781/809/889/966). See Sheet 2."),
        samp_in="99213", samp_out="99213  "),
    "CLM-PROV-OF-SVC-NUM": dict(
        mtype="direct MOVE + conditional source swap",
        comment=("L573. BEFORE the move, L564-568 swaps CLMI-PROV-OF-SVC-NUM := "
                 "CLMI-PAY-TO-PROV-NUM when CLMI-PROV-OF-SVC-NUM='09999996' AND "
                 "contract='0032600'. See Sheet 2.")),
    "CLM-ICN": dict(
        pic="X(19) (derived: WS-ICN-17 + WS-ICN-02)",
        mtype="1x1 identity + conditional ICN reformat",
        comment=("L601 base = CLMI-ICN. OVERRIDDEN at L719 with WS-ICN-GROUP-19 "
                 "(17-char ICN + 2-char HMS suffix) when PM-USER-AREA(1:2) in "
                 "{PB,DT}, contract='0032600', not DSS, suffix numeric & <>0. "
                 "See Sheet 2."),
        samp_in="2023051000001234567", samp_out="2023051000001234500"),
    "CLM-PRI-DX": dict(
        mtype="1x1 identity + diagnosis crosswalk override",
        comment=("L602 base = CLMI-PRI-DX. OVERRIDDEN in 3030 by client-side "
                 "DIAG code (CA/CB/CC/CD) per file version + CLM-TYPE. Sheet 2."),
        samp_in="E1165  ", samp_out="E1165  "),
    "CLM-SEC-DX": dict(
        mtype="1x1 identity + diagnosis crosswalk override",
        comment="L603 base = CLMI-SEC-DX; crosswalk override in 3030. Sheet 2.",
        samp_in="I10    ", samp_out="I10    "),
    "CLM-DX-3": dict(
        mtype="1x1 identity + diagnosis crosswalk override",
        comment="L675 base = CLMI-DX-3; crosswalk override in 3030. Sheet 2."),
    "CLM-DX-4": dict(
        mtype="1x1 identity + diagnosis crosswalk override",
        comment="L676 base = CLMI-DX-4; crosswalk override in 3030. Sheet 2."),
    "CLM-DX-5": dict(
        mtype="1x1 identity + diagnosis crosswalk override",
        comment="L677 base = CLMI-DX-5; crosswalk override in 3030. Sheet 2."),
    "CLM-PROCEDURE-CODE-MOD1": dict(
        mtype="1x1 identity + SPACES override (crosswalk paths)",
        comment=("L576 base = CLMI-PROCEDURE-CODE-MOD1. Set to SPACES at "
                 "L782/810/890/967 on the client-crosswalk paths. Sheet 2.")),
    "CLM-PROCEDURE-CODE-MOD2": dict(
        mtype="1x1 identity + SPACES override (crosswalk paths)",
        comment=("L578 base = CLMI-PROCEDURE-CODE-MOD2. Set to SPACES at "
                 "L783/811/891/968 on the client-crosswalk paths. Sheet 2.")),
    "CLM-PCF-HMS-ICN-SUFFIX": dict(
        pic="X(2) (derived: moved to WS-ICN-02 X(02))",
        mtype="1x1 identity",
        comment="L699 = CLMI-PCF-HMS-ICN-SUFFIX; 2-byte HMS ICN suffix."),
    "CLM-TOT-MA-PAID-HDR": dict(
        mtype="1x1 identity (also accumulated for match report)",
        comment=("L625 = CLMI-TOT-MA-PAID-HDR. Also ADDED to WS-TOT-PCF-MA-PAID "
                 "(L739) which feeds CASE-PCF-MATCH report.")),
}

# PIC hints that can be DERIVED from the program for identity fields.
DERIVED_PIC = {
    "CLM-PCF-HMS-ICN-SUFFIX": "X(2) (derived)",
    "CLM-ICN": "X(19) (derived)",
}


def sample_for(src):
    """Illustrative sample for an identity field, from table or heuristics."""
    if src in SAMPLE:
        return SAMPLE[src]
    s = src[5:] if src.startswith("CLMI-") else src
    if any(k in s for k in ("DATE", "DOB", "-DOS", "DOR")):
        return "20230115"
    if s.endswith(("-IND", "-SW", "-FLAG")) or s.endswith("SEX"):
        return "N"
    if any(k in s for k in ("PAID", "BILLED", "ALLOWED", "DOLLAR", "INCOME",
                            "COINS", "DEDUCT", "RATE")):
        return "00000000000"
    if "NAME" in s:
        return "SMITH"
    if "DX" in s or "DIAG" in s:
        return "E119   "
    if "PROC" in s:
        return "99213"
    if "DRG" in s:
        return "470"
    if any(k in s for k in ("NUM", "ID", "KEY")):
        return "000000000001"
    return "ABCDE"


# --------------------------------------------------------------------------- #
#  3.  Assemble the master Sheet-1 row list                                    #
# --------------------------------------------------------------------------- #
# Columns:
# No | OutCopybook | Target | PIC | Byte | MapType | SrcCopybook | SrcField |
# SampleIn | SampleOut | Path:SRCPCF-OUT | Path:CASE-PCF-MATCH | Comments
rows = []
n = 0

# --- 3a. CLMPREFX (PRO-*) prefix fields of SRCPCF-OUT, code order ----------- #
pro_fields = [
    ("PRO-RECIPIENT-ID-NUM", "direct MOVE (renamed source)", "FDPCF602 (PFX/HMS)",
     "CLMI-PCF-MA-NUM", "100000000001", "100000000001",
     "L543 recipient/MA number copied into output prefix."),
    ("PRO-HMS-CASE-KEY", "direct MOVE (renamed source)", "NCTCASE (CASET table)",
     "CASET-HMS-CASE-KEY (SUB-I)", "CASEKEY0000001234", "CASEKEY0000001234",
     "L544 from matched case-table occurrence (subscript SUB-I)."),
    ("PRO-CLIENT-ID", "direct MOVE (renamed source)", "NCTCASE (CASET table)",
     "CASET-HMS-CLIENT-ID (SUB-I)", "CLIENT0001234", "CLIENT0001234",
     "L546 (chg 0014) from matched case-table occurrence."),
    ("PRO-CREATE-SOURCE", "hardcoded constant (run control card)",
     "CNTL-CARDS/CARD-REC", "WS-SAVE-CREATE-SOURCE", "NJ", "NJ",
     "L552. Value comes from SYS004 control card tag '1', CARD-DATA(1:2) "
     "(L428-430). Constant for the whole run."),
    ("PRO-ICN", "1x1 identity + conditional ICN reformat", "FDPCF602 (CLMI)",
     "CLMI-ICN", "2023051000001234567", "2023051000001234500",
     "L554 base = CLMI-ICN. OVERRIDDEN L717 by WS-ICN-GROUP-19 (ICN 17 + HMS "
     "suffix 2) on the PB/DT 0032600 non-DSS numeric-suffix path. Sheet 2."),
    ("PRO-FORMER-ICN", "1x1 identity", "FDPCF602 (CLMI)",
     "CLMI-FORMER-ICN", "                   ", "                   ",
     "L555 former ICN carried through."),
    ("PRO-XACTION-STATUS", "1x1 identity", "FDPCF602 (CLMI)",
     "CLMI-XACTION-STATUS", "P", "P", "L556 transaction status."),
    ("PRO-CLM-FROM-DATE", "direct MOVE (renamed source)", "FDPCF602 (PFX)",
     "PFX-APP-DATE-OF-SERVICE", "20230115", "20230115",
     "L558. 8-digit YYYYMMDD (derived: compared to 20151001 at L726 to pick "
     "ICD version)."),
    ("PRO-CLAIM-TRANS-TYPE", "direct MOVE (renamed source)", "FDPCF602 (PFX)",
     "PFX-NET-CLAIM-TRANS-TYPE", "A", "A", "L560 net claim transaction type."),
    ("PRO-INCIDENT-DATE", "derived/transformed (date reformat)",
     "NCTCASE (CASET table)", "WS-INCIDENT-DATE <- CASET-INCIDENT-DATE (SUB-I)",
     "2023-01 (case text)", "20230100",
     "L562. 4000-FORMAT-DATE UNSTRINGs CASET-INCIDENT-DATE on '-'/'  ' into "
     "YYYY+MM (DD stays 00 in this field). 8-digit YYYYMMDD."),
    ("PRO-CLM-THRU-DATE", "derived/transformed (date reformat / default)",
     "NCTCASE (CASET table)", "WS-CLM-THRU-DATE <- CASET-CLAIMS-THRU-DATE (SUB-I)",
     "2023-12-31 (case text)", "20231231",
     "L563. 4000-FORMAT-DATE UNSTRINGs CASET-CLAIMS-THRU-DATE; if SPACES -> "
     "'99999999' (L999). 8-digit YYYYMMDD."),
]
for tgt, mtype, scpy, sfld, sin, sout, cmt in pro_fields:
    n += 1
    rows.append([n, "CLMPREFX (PRO-)", tgt, UNCERTAIN_PRO, UNCERTAIN_PRO,
                 mtype, scpy, sfld, f"{sin} {ILLUS}", f"{sout} {ILLUS}",
                 "populated", "-", cmt])

# --- 3b. FDPCF601 (CLM-*) claim body, parsed identity block in code order --- #
for lineno, source, target in IDENTITY:
    n += 1
    spec = SPECIAL.get(target, {})
    pic = spec.get("pic", DERIVED_PIC.get(target, UNCERTAIN_CLM))
    mtype = spec.get("mtype", "1x1 identity")
    sin = spec.get("samp_in", sample_for(source))
    sout = spec.get("samp_out", sin)
    cmt = spec.get("comment", f"L{lineno} straight field-by-field copy "
                              f"(no bulk move; see L569-570).")
    rows.append([n, "FDPCF601 (CLM-)", target, pic, UNCERTAIN_CLM, mtype,
                 "FDPCF602 (CLMI-)", f"{source}  [L{lineno}]",
                 f"{sin} {ILLUS}", f"{sout} {ILLUS}", "populated", "-", cmt])

# --- 3c. CLM-CDE-ICD-VERSION (set after the identity block) ----------------- #
n += 1
rows.append([n, "FDPCF601 (CLM-)", "CLM-CDE-ICD-VERSION",
             "X(2) (derived; literals '09'/'10')", UNCERTAIN_CLM,
             "hardcoded constant (date-driven)", "(literal)",
             "'09' or '10'  [L726-730]", "from-date 20230115 " + ILLUS,
             "10 " + ILLUS, "populated", "-",
             "L726-730: MOVE '09' if PRO-CLM-FROM-DATE < 20151001 else '10'. "
             "ICD-9 vs ICD-10 flag."])

# --- 3d. CASE-PCF-MATCH report record (WS-MATCH-OUT) - exact inline layout --- #
# pos(1-based), length, target, source/header, mapType, sampleIn, sampleOut, cmt
match_fields = [
    (1, 3, "FILLER (F)", "hardcoded constant", "(literal)",
     "n/a", "' * '", "L227 literal separator ' * '."),
    (4, 20, "MATCH-CASE-ID-OUT", "direct MOVE (renamed) / header",
     "WS-CASE-ID <- CASET-RECIPIENT-ID-NUM(1)", "100000000001",
     "100000000001        ",
     "Header row value 'CASE ID' (L228); detail value = WS-CASE-ID set L735 "
     "from CASET-RECIPIENT-ID-NUM(1); moved to field L1527."),
    (24, 3, "FILLER (F)", "hardcoded constant", "(literal)",
     "n/a", "' * '", "L229 literal separator ' * '."),
    (27, 19, "MATCH-TOT-PCF-REC-OUT", "derived/transformed (count, de-edited)",
     "WS-CONVERT-MATCH <- WS-TOT-PCF-REC-MATCH", "(3 matched)",
     "3                  ",
     "Header value 'PCF RECORDS MATCHED' (L230). Detail: WS-TOT-PCF-REC-MATCH "
     "(count of written claims, L736) edited via ZZZZ9 then left-trimmed "
     "(L1529-1534)."),
    (46, 3, "FILLER (F)", "hardcoded constant", "(literal)",
     "n/a", "' * '", "L232 literal separator ' * '."),
    (49, 18, "MATCH-TOT-PCF-MA-PAID-OUT",
     "derived/transformed (sum, currency-edited)",
     "WS-CONVERT-PCF-PAID <- WS-TOT-PCF-MA-PAID", "(sum 1,200.00)",
     "$1,200.00         ",
     "Header value 'PCF TOT $$ MA PAID' (L233). Detail: WS-TOT-PCF-MA-PAID "
     "(sum of CLMI-TOT-MA-PAID-HDR, L739) edited via $$$,$$$,$$$,$$9.99 then "
     "left-trimmed (L1536-1541)."),
    (67, 2, "FILLER (F)", "hardcoded constant", "(literal)",
     "n/a", "' *'", "L235 literal trailing ' *'."),
]
for pos, length, tgt, mtype, sfld, sin, sout, cmt in match_fields:
    n += 1
    byte = f"{pos}-{pos + length - 1} (len {length})"
    rows.append([n, "WS-MATCH-OUT (inline)", tgt, f"X({length:02d})", byte,
                 mtype, "WORKING-STORAGE / NCTCASE", sfld,
                 f"{sin}", f"{sout}", "-", "populated", cmt])

# Record-level note rows for the two output records.
n += 1
rows.append([n, "SRCPCF-OUT (FD)", "CLMO-RECORD", "X(754)", "1-754",
             "record (reformat target)", "-", "WS-SRCPCF-OUT written L732",
             "-", "-", "whole record", "-",
             "Output claim record = CLMPREFX(PRO) + CLM-HMS-601(FDPCF601). "
             "Total 754 bytes. PRO/CLM split needs the copybooks (absent)."])
n += 1
rows.append([n, "CASE-PCF-MATCH (FD)", "MATCH-RECORD", "X(80)", "1-80",
             "record (report line)", "-",
             "WS-MATCH-OUT / WS-CASE-PCF-MATCH written L437/439/547/1547/1711+",
             "-", "-", "-", "whole record",
             "Fixed 80-byte report line (header/detail/trailer). Bytes 69-80 "
             "space padding."])

TOTAL_OUT_FIELDS = n

# Completeness caveat row (make the copybook-absence limitation explicit).
rows.append(["NOTE", "(completeness)", "FDPCF601 / CLMPREFX unreferenced fields",
             "n/a", "n/a", "not populated (cannot enumerate)", "-", "-",
             "-", "-", "see note", "see note",
             "Every output field REFERENCED in CASPCFNJ is listed above "
             "(106 CLMI->CLM copies + 11 PRO- + CLM-CDE-ICD-VERSION + the "
             "inline 80-byte report). Any FDPCF601/CLMPREFX field that the "
             "program never names cannot be listed because those copybooks "
             "are not in the repository; such fields would carry their "
             "INITIALIZE/record default. The CLM-HMS-601 area is NOT "
             "re-initialised per record, so an unreferenced CLM field retains "
             "the prior record's value (see Gaps in the markdown report)."])

# --------------------------------------------------------------------------- #
#  4.  Styling helpers                                                         #
# --------------------------------------------------------------------------- #
HDR_FILL = PatternFill("solid", fgColor="1F4E78")
HDR_FONT = Font(bold=True, color="FFFFFF", size=10)
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
BORDER = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
TOP = Alignment(vertical="top", wrap_text=True)
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")
NOTE_FONT = Font(italic=True, size=9, color="555555")


def style_header(ws, row_idx, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row_idx, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(vertical="top", wrap_text=True,
                                   horizontal="center")
        cell.border = BORDER


def finalize(ws, ncols, widths, header_row=1, freeze=None):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=header_row + 1):
        for cell in row:
            cell.alignment = TOP
            cell.border = BORDER
    ws.freeze_panes = freeze or f"A{header_row + 1}"


# --------------------------------------------------------------------------- #
#  5.  Build the workbook                                                      #
# --------------------------------------------------------------------------- #
wb = Workbook()

# ---------- Sheet 1 : Field Mapping ---------------------------------------- #
ws1 = wb.active
ws1.title = "Field Mapping"
headers1 = ["Field No", "Output Copybook", "Target Field", "Picture",
            "Byte Location", "Mapping Type", "Source Copybook", "Source Field",
            "Sample Input", "Sample Output", "Path: SRCPCF-OUT (claim X754)",
            "Path: CASE-PCF-MATCH (report X80)", "Comments"]
ws1.append(["CASPCFNJ - Field Mapping (one row per output field). "
            "PIC/byte for PRO-/CLM- are UNCERTAIN: copybooks CLMPREFX/FDPCF601 "
            "are not in the repository. Match-report fields are exact (inline)."]
           )
ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers1))
ws1.cell(row=1, column=1).font = NOTE_FONT
ws1.cell(row=1, column=1).alignment = Alignment(wrap_text=True, vertical="top")
ws1.append(headers1)
style_header(ws1, 2, len(headers1))
for r in rows:
    ws1.append(r)
    # tint the per-record note rows and match rows lightly
finalize(ws1, len(headers1),
         [8, 20, 30, 30, 16, 34, 20, 34, 24, 24, 16, 16, 56],
         header_row=2, freeze="C3")

# ---------- Sheet 2 : Overrides & Crosswalks ------------------------------- #
ws2 = wb.create_sheet("Overrides & Crosswalks")
headers2 = ["Path/Format", "Source Field", "Target Field",
            "Assigned/Translated Value", "Condition", "Sample In -> Out",
            "Description"]
ws2.append(["CASPCFNJ - Overrides, crosswalks, conditional assignments and "
            "value translations (all anchored to code lines)."])
ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers2))
ws2.cell(row=1, column=1).font = NOTE_FONT
ws2.append(headers2)
style_header(ws2, 2, len(headers2))

overrides = [
    ("SRCPCF-OUT / all", "CLMI-PAY-TO-PROV-NUM", "CLMI-PROV-OF-SVC-NUM "
     "(then -> CLM-PROV-OF-SVC-NUM)", "PAY-TO value",
     "CLMI-PROV-OF-SVC-NUM='09999996' AND CLMI-PCF-CONTRACT-NUM='0032600' "
     "(L564-568)", "09999996 -> 09888801",
     "Dummy provider 09999996 is replaced by the pay-to provider before the "
     "field-by-field copy."),
    ("SRCPCF-OUT / all", "CLMI-ICN + CLMI-PCF-HMS-ICN-SUFFIX",
     "PRO-ICN and CLM-ICN", "ICN(17) || suffix(2) -> 19-char ICN",
     "PM-USER-AREA(1:2) in {PB,DT} AND contract='0032600' AND "
     "PM-USER-AREA(27:3)<>'DSS' AND suffix NUMERIC AND suffix<>0 (L706-723)",
     "ICN ...4567 + 05 -> ...4505 (19)",
     "ICN reformat for HMS suffix: WS-ICN-17=CLMI-ICN, WS-ICN-02=suffix, "
     "WS-ICN-GROUP-19 moved to PRO-ICN (L717) and CLM-ICN (L719)."),
    ("SRCPCF-OUT / all", "PRO-CLM-FROM-DATE", "CLM-CDE-ICD-VERSION",
     "'09' or '10'", "PRO-CLM-FROM-DATE < 20151001 -> '09' else '10' "
     "(L726-730)", "20230115 -> 10",
     "ICD version flag: dates before 2015-10-01 are ICD-9 ('09'), on/after "
     "are ICD-10 ('10')."),
    ("Input fmt MAMA v06", "CA-A-DIAG-CDE(1..5) / CA-A-PROC-CDE "
     "(FDNJTPC5)", "CLM-PRI-DX,SEC-DX,DX-3..5 / CLM-PROCEDURE-CODE-7",
     "client diag/proc codes", "PFX-SYS-HMS-ASSIGN-FILE='MAMA' AND "
     "PFX-SYS-VERSION='06' AND CLMI-CLM-TYPE in {01,02,03,04,06,07,09,13,14,"
     "15,18,20,21,23} (L764-789)", "CA-A-DIAG-CDE(1)=E1165 -> CLM-PRI-DX",
     "MOVE CLMI-CLIENT-DATA to INST-RECA(FDNJTPC5); DX1-5 from CA-A-DIAG-CDE, "
     "proc from CA-A-PROC-CDE, MOD1/MOD2 set SPACES (L781-788)."),
    ("Input fmt MAMA/CCAR v05", "CB-A-DIAG-CDE(1..5) / CB-A-PROC-CDE "
     "(FDNJTPC4)", "CLM-PRI-DX,SEC-DX,DX-3..5 / CLM-PROCEDURE-CODE-7",
     "client diag/proc codes", "PFX-SYS-HMS-ASSIGN-FILE in {MAMA,CCAR} AND "
     "PFX-SYS-VERSION='05' AND CLMI-CLM-TYPE in {01..23 subset} (L791-817)",
     "CB-A-DIAG-CDE(1) -> CLM-PRI-DX",
     "MOVE CLMI-CLIENT-DATA to CB-CLMS-ACTIVITY-RECORD(FDNJTPC4); DX1-5 from "
     "CB-A-DIAG-CDE, proc from CB-A-PROC-CDE, MOD1/2 SPACES (L808-816)."),
    ("Input fmt ENCT v05", "CC-??-DIAG(n) / CC-E-PROC-CDE (FDNJ5INS)",
     "CLM-PRI-DX,SEC-DX,DX-3..5 / CLM-PROCEDURE-CODE-7",
     "client diag/proc codes by CLM-TYPE",
     "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='05'; "
     "EVALUATE CLMI-CLM-TYPE WHEN 01/02/03/04/06/07/18 (L819-892)",
     "type 01: CC-HNI-DIAG(1) -> CLM-PRI-DX",
     "MOVE CLMI-CLIENT-DATA to INST-RECC(FDNJ5INS). DX source set varies by "
     "claim type (HNI/OP/PR/HH/TR/VI). Proc=CC-E-PROC-CDE when CLM-TYPE<>'12' "
     "(L888-892)."),
    ("Input fmt ENCT v04", "CD-??-DIAG(n) / CD-E-PROC-CDE (FDNJ4INS)",
     "CLM-PRI-DX,SEC-DX,DX-3..5 / CLM-PROCEDURE-CODE-7",
     "client diag/proc codes by CLM-TYPE",
     "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='04'; "
     "EVALUATE CLMI-CLM-TYPE WHEN 01/02/03/04/06/07/18 (L895-969)",
     "type 03: CD-OP-DIAG(1) -> CLM-PRI-DX",
     "MOVE CLMI-CLIENT-DATA to CD-ENC-ACTIVITY-RECORD(FDNJ4INS). Proc="
     "CD-E-PROC-CDE when CLM-TYPE<>'12' (L965-969)."),
    ("Input fmt (other)", "n/a", "n/a (counter only)", "n/a",
     "Any file/version not matched above (L970-972)", "n/a -> OTHER-VERS+1",
     "5500-PROCESS-RECS just increments OTHER-VERS (L1518-1520); CLM DX/proc "
     "keep the base CLMI-* identity values."),
    ("Case table", "(literal)", "CASE-PCF-MATCH-FLAG (SUB-I)", "'N' then 'Y'",
     "Init 'N' on load (L521); set 'Y' on first PCF match (L548-551)",
     "N -> Y", "Per-case match flag; drives OPEN-CASES-MATCH-OK-CTR. Work "
     "field inside the case table, not an output-record field."),
    ("CASE-PCF-MATCH / detail", "WS-TOT-PCF-MA-PAID",
     "WS-MATCH-OUT(27:) message", "'TOO MANY MATCHES, $$ PAID NOT AVAILABLE !'",
     "SIZE ERROR adding to WS-TOT-PCF-REC-MATCH/MA-PAID (SIZE-ERROR 88, "
     "L734-744, L1542-1545)", "overflow -> message text",
     "On arithmetic overflow the paid total is suppressed and a literal "
     "warning is written instead of the numbers."),
]
for r in overrides:
    ws2.append(list(r))
finalize(ws2, len(headers2), [22, 30, 34, 26, 44, 30, 60], header_row=2)

# ---------- Sheet 3 : Routing / Format Logic ------------------------------- #
ws3 = wb.create_sheet("Routing & Format Logic")
ws3.append(["CASPCFNJ - Routing / format / skip-reject logic"])
ws3.cell(row=1, column=1).font = TITLE_FONT
ws3.append([])
routing = [
    ("Program role",
     "Reformat + Filter/Matcher + MULTI-OUTPUT. Different input vs output "
     "claim layouts (FDPCF602 600-byte HMS area -> FDPCF601 larger diag area) "
     "copied field-by-field 'by column' (the bulk MOVE at L569-570 is "
     "deliberately commented out). Records are selected by matching PCF claims "
     "to OPEN case-table rows, and two files are written."),
    ("Inputs",
     "SRCPCF-IN (ddname SRCPCFI, VB 4-32752, read INTO WS-CLMI-RECORD) = PCF "
     "claim file. CASEFL-IN (CASEFLI, FB 384, INTO WS-CASE-RECORD) = CAS2000 "
     "case file (must be in recipient-id order). CNTL-CARDS (SYS004, FB 80) = "
     "run control cards (card tag '1' supplies CREATE-SOURCE)."),
    ("Outputs",
     "SRCPCF-OUT (SRCPCFO, FB 754) = matched/reformatted PCF claim extract. "
     "CASE-PCF-MATCH (MATCHO, FB 80) = per-case match summary report "
     "(header + one detail line per matched case + trailer)."),
    ("Matching / join",
     "Driver loop 2000-MAINLINE is PCF-claim driven (UNTIL PCF-EOF). The case "
     "file is advanced so CASE-RECIPIENT-ID-NUM >= PFX-APP-MEDICAID-NO "
     "(L445-448). When the PCF recipient equals the case recipient, the case "
     "rows for that recipient are loaded into WS-CASE-TABLE (OCCURS 40) by "
     "3010-LOAD-CASE-TABLE and scanned by 3020-READ-CASE-TABLE."),
    ("Outputs per input claim",
     "0 or 1 SRCPCF-OUT record per PCF claim. A claim is written only if a "
     "matching case row is OPEN and the service date falls inside the case "
     "window (see write gate). The claim is compared against up to "
     "TABLE-ENTRIES case rows but the write happens per matched open case."),
    ("WRITE gate (3020)",
     "Write occurs only when: CASET-CASE-STATUS-CODE(SUB-I) = 'O' OR X'96' "
     "(open) AND PFX-APP-DATE-OF-SERVICE >= WS-INCIDENT-DATE-NEW-RE (incident, "
     "day forced to 01) AND PFX-APP-DATE-OF-SERVICE <= WS-CLM-THRU-DATE-N "
     "(L537-541). Then WRITE CLMO-RECORD FROM WS-SRCPCF-OUT (L732)."),
    ("SKIP: eligibility",
     "If PFX-SYS-EXIT-FROM-REF-STATUS NOT = 'Y' the claim is skipped: read "
     "next PCF and GO TO mainline exit (L452-455). Only EXIT-FROM-REF-STATUS "
     "= 'Y' claims proceed."),
    ("SKIP: DSS historical",
     "If CLMI-PCF-CONTRACT-NUM='0032600' AND CLMI-PM-USER-AREA(27:3)='DSS' AND "
     "CLMI-CLAIM-FROM-DOS > 0040000 AND < 0900000 -> ADD 1 REC-SKIP-DSS, read "
     "next, skip (L457-469). Excludes DSS service years ~2004+."),
    ("SKIP: dummy provider",
     "If CLMI-PROV-OF-SVC-NUM='09999996' AND CLMI-PAY-TO-PROV-NUM='09999996' "
     "-> ADD 1 REC-SKIP-PROV, read next, skip (L471-476)."),
    ("No-match handling",
     "Non-open cases or claims outside the case date window are simply not "
     "written (no reject file). OPEN-CASES-NO-MATCH-CTR = OPEN-CASES-READ-CTR "
     "- OPEN-CASES-MATCH-OK-CTR (L1567-1569)."),
    ("CASE-PCF-MATCH cadence",
     "Header written once at init (L391/437-439). A detail line is written "
     "when the recipient changes and WS-TOT-PCF-REC-MATCH>0 (L480-484) and at "
     "end of job (L1557-1559). Trailer (counts / 'NO MATCHED...' / '***') at "
     "termination (L1565, 9100)."),
    ("STOP / end",
     "Normal: 2000-MAINLINE repeats UNTIL PCF-EOF, then 9000-TERMINATION, STOP "
     "RUN (L361-366). No ABEND / STOP literals in the active code; size-error "
     "on match totals is trapped, not fatal (SIZE-ERROR 88)."),
]
ws3.append(["Topic", "Explanation"])
style_header(ws3, 3, 2)
for t, e in routing:
    ws3.append([t, e])
finalize(ws3, 2, [26, 118], header_row=3)

# ---------- Sheet 4 : Sample Records --------------------------------------- #
ws4 = wb.create_sheet("Sample Records")
ws4.append(["CASPCFNJ - Worked sample (ILLUSTRATIVE: exact PICs live in the "
            "absent copybooks). One PCF input claim -> one SRCPCF-OUT claim "
            "and the matching CASE-PCF-MATCH lines."])
ws4.cell(row=1, column=1).font = NOTE_FONT
ws4.append([])
samples = [
    ("INPUT  PCF claim (SRCPCF-IN / WS-CLMI-RECORD)", ""),
    ("  TPLPREFX  PFX-APP-MEDICAID-NO", "100000000001"),
    ("  TPLPREFX  PFX-APP-DATE-OF-SERVICE", "20230115 (YYYYMMDD)"),
    ("  TPLPREFX  PFX-SYS-EXIT-FROM-REF-STATUS", "Y  (required to process)"),
    ("  TPLPREFX  PFX-SYS-HMS-ASSIGN-FILE / VERSION", "MAMA / 06"),
    ("  TPLPREFX  PFX-NET-CLAIM-TRANS-TYPE", "A"),
    ("  FDPCF602  CLMI-PCF-MA-NUM", "100000000001"),
    ("  FDPCF602  CLMI-ICN", "2023051000001234567"),
    ("  FDPCF602  CLMI-CLM-TYPE", "01 (institutional)"),
    ("  FDPCF602  CLMI-PROCEDURE-CODE-5", "99213"),
    ("  FDPCF602  CLMI-PRI-DX / SEC-DX", "E1165 / I10"),
    ("  FDPCF602  CLMI-PROV-OF-SVC-NUM / PAY-TO", "09888801 / 09888801"),
    ("  FDPCF602  CLMI-TOT-MA-PAID-HDR", "00000120000  (= 1,200.00)"),
    ("  FDPCF602  CLMI-PCF-CONTRACT-NUM", "0032600"),
    ("  FDPCF602  CLMI-PM-USER-AREA(1:2) / (27:3)", "PB / (not DSS)"),
    ("  FDPCF602  CLMI-PCF-HMS-ICN-SUFFIX", "00 (numeric, zero -> no reformat)"),
    ("  client   CLIENT-DATA -> FDNJTPC5 CA-A-DIAG-CDE(1)", "E1165"),
    ("", ""),
    ("CASE row (CASEFL-IN / WS-CASE-RECORD -> CASET table)", ""),
    ("  CASET-RECIPIENT-ID-NUM(1)", "100000000001 (matches PFX-APP-MEDICAID-NO)"),
    ("  CASET-CASE-STATUS-CODE(1)", "O  (open -> eligible to write)"),
    ("  CASET-INCIDENT-DATE(1)", "2023-01  -> WS-INCIDENT-DATE-NEW 20230101"),
    ("  CASET-CLAIMS-THRU-DATE(1)", "2023-12-31 -> WS-CLM-THRU-DATE 20231231"),
    ("  CASET-HMS-CASE-KEY(1)", "CASEKEY0000001234"),
    ("  CASET-HMS-CLIENT-ID(1)", "CLIENT0001234"),
    ("", ""),
    ("Eligibility: DOS 20230115 >= incident 20230101 AND <= thru 20231231",
     "PASS -> claim is written"),
    ("", ""),
    ("OUTPUT  SRCPCF-OUT claim (CLMO-RECORD, 754 bytes = PRO + CLM)", ""),
    ("  PRO-RECIPIENT-ID-NUM", "100000000001"),
    ("  PRO-HMS-CASE-KEY", "CASEKEY0000001234"),
    ("  PRO-CLIENT-ID", "CLIENT0001234"),
    ("  PRO-CREATE-SOURCE", "NJ (from control card)"),
    ("  PRO-ICN", "2023051000001234567 (no reformat; suffix=00)"),
    ("  PRO-CLM-FROM-DATE", "20230115"),
    ("  PRO-INCIDENT-DATE / PRO-CLM-THRU-DATE", "20230100 / 20231231"),
    ("  CLM-PCF-MA-NUM", "100000000001"),
    ("  CLM-PROCEDURE-CODE-7", "99213   (MAMA v06 -> CA-A-PROC-CDE, MODs space)"),
    ("  CLM-PRI-DX / CLM-SEC-DX", "E1165 / I10 (MAMA v06 -> CA-A-DIAG-CDE)"),
    ("  CLM-TOT-MA-PAID-HDR", "00000120000"),
    ("  CLM-CDE-ICD-VERSION", "10 (DOS 20230115 >= 20151001)"),
    ("", ""),
    ("OUTPUT  CASE-PCF-MATCH report (MATCH-RECORD, 80 bytes)", ""),
    ("  Header line", "' * CASE ID            * PCF RECORDS MATCHED * "
                      "PCF TOT $$ MA PAID *'"),
    ("  Detail line (this case)", "' * 100000000001        * 1  "
                                  "               * $1,200.00         *'"),
    ("  Trailer", "spaces line, then 80x '*' (L1713-1716)"),
]
ws4.append(["Field / step", "Value (illustrative)"])
style_header(ws4, 3, 2)
for a, b in samples:
    ws4.append([a, b])
finalize(ws4, 2, [52, 70], header_row=3)

# --------------------------------------------------------------------------- #
#  6.  Save                                                                    #
# --------------------------------------------------------------------------- #
wb.save(OUT_FILE)
print(f"Wrote {OUT_FILE}")
print(f"Sheets: {wb.sheetnames}")
print(f"Output field rows on Sheet 1 (incl. 2 record rows): {TOTAL_OUT_FIELDS}")
print(f"Identity CLMI->CLM moves parsed from source: {len(IDENTITY)}")
