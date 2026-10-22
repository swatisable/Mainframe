#!/usr/bin/env python3
"""
build_field_mapping_xlsx.py
===========================

Generates ``CASPCFNJ_1x1_Field_Mapping.xlsx`` - a 4-sheet field-to-field
mapping workbook for the COBOL program ``CASPCFNJ`` (PCF claim extract /
reformat / case-match).

Every row in the workbook is derived from a *real* line of the COBOL source
(``CASPCFNJ``).  The line numbers quoted in the ``Comments`` column refer to
that source file.

IMPORTANT - EVIDENCE & "DO NOT GUESS" POLICY
--------------------------------------------
The program COPYs its record layouts from external copybooks that are **not
present in this repository**:

    TPLPREFX  -> PFX-*   (claim input prefix / key area)
    FDPCF602  -> CLMI-*  (claim input body, "HMS-600")
    CLMPREFX  -> PRO-*   (claim output prefix / key area)
    FDPCF601  -> CLM-*   (claim output body, "HMS-601", enlarged diag area)
    NCTCASE   -> CASE-* / CASET-*  (case file + 40-row case table)
    FDNJTPC5 -> CA-*, FDNJTPC4 -> CB-*, FDNJ5INS -> CC-*, FDNJ4INS -> CD-*
                (client-data overlays used for diagnosis / procedure codes)

Because those copybooks are absent, the exact PICTURE clause and byte offset
of each PRO-/CLM-/CLMI- elementary field cannot be read from source.  Where a
PICTURE can be *inferred* from how the field is used in the program (compared
to a literal, moved through a working-storage field of known size, etc.) it is
shown with an ``[inf]`` marker.  Where it cannot, the cell reads
``n/a (FDPCF601 copybook not in repo)`` rather than a guessed value.

The second output file, the CASE-PCF-MATCH report (``WS-MATCH-OUT``), **is**
fully defined inside CASPCFNJ, so its fields carry exact PICTURE clauses and
byte positions.

All sample values are ILLUSTRATIVE and marked as such; they are kept
internally consistent so one sample input record yields the matching output.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_XLSX = "CASPCFNJ_1x1_Field_Mapping.xlsx"

# --------------------------------------------------------------------------- #
# Styling helpers
# --------------------------------------------------------------------------- #
HDR_FILL = PatternFill("solid", fgColor="1F4E78")
HDR_FONT = Font(color="FFFFFF", bold=True, size=10)
SUB_FILL = PatternFill("solid", fgColor="DDEBF7")
PRO_FILL = PatternFill("solid", fgColor="E2EFDA")   # output prefix (PRO)
CLM_FILL = PatternFill("solid", fgColor="FFFFFF")   # output body   (CLM)
OVR_FILL = PatternFill("solid", fgColor="FCE4D6")   # overridden fields
MAT_FILL = PatternFill("solid", fgColor="FFF2CC")   # match report fields
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")
WRAP = Alignment(vertical="top", wrap_text=True)
TOP = Alignment(vertical="top")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# --------------------------------------------------------------------------- #
# Source copybook short names
# --------------------------------------------------------------------------- #
CB_CLMI = "FDPCF602 (CLMI / HMS-600 body)"
CB_PFX = "TPLPREFX (PFX / input prefix)"
CB_CASE = "NCTCASE (CASET / case table)"
CB_CARD = "CNTL-CARDS SYS004 (CARD-DATA)"
CB_WS = "WORKING-STORAGE (derived)"
CB_CONST = "literal (program constant)"

OUT_PRO = "CLMPREFX (PRO / output prefix)"
OUT_CLM = "FDPCF601 (CLM / HMS-601 body)"
OUT_MATCH = "WS-MATCH-OUT (program-defined)"

NA_PIC = "n/a (FDPCF601 copybook not in repo)"
NA_PIC_PRO = "n/a (CLMPREFX copybook not in repo)"
NA_POS = "n/a (copybook not in repo)"

# --------------------------------------------------------------------------- #
# Illustrative sample values by field-name heuristic (all ILLUSTRATIVE).
# For a 1:1 direct move, sample input == sample output.
# --------------------------------------------------------------------------- #
def sample_for(name):
    n = name.upper()
    if "DIAG" in n or n.endswith("-DX") or "-DX-" in n or n in (
            "CLM-PRI-DX", "CLM-SEC-DX"):
        return "4019   "          # 7-char diag (ICD) left-justified
    if "PROCEDURE-CODE-7" in n:
        return "99213  "          # 7-char procedure code
    if "PROCEDURE-CODE-5" in n:
        return "99213"            # 5-char procedure code
    if "PROC-CODE" in n or "PROC-CDE" in n:
        return "99213  "
    if "MOD1" in n or "MOD2" in n:
        return "  "               # 2-char modifier (spaces)
    if "DOB" in n:
        return "19600115"         # yyyymmdd
    if "CLAIM-FROM-DOS" in n or "CLAIM-THRU-DOS" in n or "RECORD-THRU-DOS" in n \
            or "RECORD-FROM-DOS" in n:
        return "0240115"          # 0yymmdd (7-digit, per source comment L459-465)
    if "DATE" in n or "-DOS" in n or n.endswith("-DOR"):
        return "20240115"         # yyyymmdd
    if "ICN" in n:
        return "20240011122233300"      # 17/19-char ICN
    if "MA-NUM" in n or "RECIPIENT-ID" in n or "MC-NUM" in n:
        return "123456789012"
    if "PROV" in n and "NUM" in n:
        return "01234567"
    if "CASE-KEY" in n:
        return "CASEKEY0001         "
    if "CLIENT-ID" in n:
        return "CLIENT0001  "
    if "LAST-NAME" in n:
        return "DOE            "
    if "FIRST-NAME" in n:
        return "JANE           "
    if "MID-INIT" in n:
        return "Q"
    if "SEX" in n:
        return "F"
    if "CLM-TYPE" in n or "CLAIM-TYPE" in n:
        return "01"
    if "CONTRACT-NUM" in n:
        return "0032600"
    if "CREATE-SOURCE" in n:
        return "NJ"
    if "TRANS-TYPE" in n:
        return "A"
    if "CDE-ICD-VERSION" in n or "ICD-VERSION" in n:
        return "09"
    if any(k in n for k in ("BILLED", "PAID", "ALLOWED", "COINS", "DEDUCT",
                            "DOLLARS", "INCOME", "RATE", "AMT")):
        return "000000150.00"     # numeric amount, 2 decimals
    if any(k in n for k in ("DAYS", "CNT", "COUNT", "SEQ-NUM", "NUM-REV",
                            "NUM-OTH", "VISITS", "DRG")):
        return "001"
    if n.endswith("-IND") or "-IND-" in n or n.endswith("-SW") \
            or n.endswith("-FLG") or "STATUS" in n or "SUFFIX" in n:
        return "00"
    return "SAMPLE"               # generic text placeholder


# --------------------------------------------------------------------------- #
# Master field list.
#   Each entry: (target, src_field, mapping_type, src_cb, picture, comment,
#                override_flag)
# --------------------------------------------------------------------------- #
DIRECT = "Direct MOVE (renamed, 1:1)"
DERIVED = "Derived / transformed"
CONST = "Hardcoded constant"
CROSS = "Direct MOVE + per-version crosswalk override"

# ----- PRO (output prefix / key area) -------------------------------------- #
pro_fields = [
    ("PRO-RECIPIENT-ID-NUM", "CLMI-PCF-MA-NUM", DIRECT, CB_CLMI, NA_PIC_PRO,
     "L543  Recipient Medicaid ID = claim PCF MA number.", False),
    ("PRO-HMS-CASE-KEY", "CASET-HMS-CASE-KEY (SUB-I)", "Direct MOVE from case table",
     CB_CASE, NA_PIC_PRO, "L544-545  HMS case key from matched case-table row.", False),
    ("PRO-CLIENT-ID", "CASET-HMS-CLIENT-ID (SUB-I)", "Direct MOVE from case table",
     CB_CASE, NA_PIC_PRO, "L546-547 (CHG0014)  Client id from matched case-table row.", False),
    ("PRO-CREATE-SOURCE", "WS-SAVE-CREATE-SOURCE", "Direct MOVE (from control card)",
     CB_CARD, "X(2) [inf]",
     "L552-553  Value comes from SYS004 card tag '1', CARD-DATA(1:2) at L430.", False),
    ("PRO-ICN", "CLMI-ICN", "Direct MOVE; conditional ICN-suffix reformat override",
     CB_CLMI, "X(19) [inf, WS-ICN-GROUP-19]",
     "L554; override L714-718 rebuilds ICN(17)+suffix(2) when PM-USER-AREA PB/DT, "
     "contract 0032600, non-DSS, numeric non-zero suffix.", True),
    ("PRO-FORMER-ICN", "CLMI-FORMER-ICN", DIRECT, CB_CLMI, NA_PIC_PRO,
     "L555  Former ICN copied straight through.", False),
    ("PRO-XACTION-STATUS", "CLMI-XACTION-STATUS", DIRECT, CB_CLMI, NA_PIC_PRO,
     "L556-557  Transaction status copied straight through.", False),
    ("PRO-CLM-FROM-DATE", "PFX-APP-DATE-OF-SERVICE", "Direct MOVE (prefix -> output)",
     CB_PFX, "9(8) yyyymmdd [inf]",
     "L558-559  Also drives ICD-version decision (L726-730).", False),
    ("PRO-CLAIM-TRANS-TYPE", "PFX-NET-CLAIM-TRANS-TYPE", "Direct MOVE (prefix -> output)",
     CB_PFX, NA_PIC_PRO, "L560-561  Net claim trans type from prefix.", False),
    ("PRO-INCIDENT-DATE", "CASET-INCIDENT-DATE (SUB-I)", DERIVED, CB_CASE,
     "9(8) yyyymmdd [inf]",
     "L562 via WS-INCIDENT-DATE; built L985-991 UNSTRING 'YYYY-MM', day forced to 01.", True),
    ("PRO-CLM-THRU-DATE", "CASET-CLAIMS-THRU-DATE (SUB-I)", DERIVED, CB_CASE,
     "9(8) yyyymmdd [inf]",
     "L563 via WS-CLM-THRU-DATE; built L993-999 UNSTRING 'YYYY-MM-DD', else '99999999'.", True),
]

# ----- CLM (output body, HMS-601) ------------------------------------------ #
# Most are plain CLMI-x -> CLM-x direct 1:1 moves.  Overrides captured per name.
clm_overrides = {
    "CLM-PROV-OF-SVC-NUM": ("X(8) [inf]",
        "L573; pre-step L564-568: if '09999996' and contract '0032600', "
        "source replaced by CLMI-PAY-TO-PROV-NUM first.", True, DIRECT),
    "CLM-PROCEDURE-CODE-7": ("X(7) [inf] (src X(5))",
        "L574-575 base = CLMI-PROCEDURE-CODE-5 (5->7); overlaid per version "
        "(CA/CB/CC/CD *-PROC-CDE) in 3030 - see Sheet 2.", True, CROSS),
    "CLM-PROCEDURE-CODE-MOD1": ("X(2) [inf]",
        "L576-577 base direct; set to SPACES by MAMA/ENCT overlays "
        "(L782,790,810,890,967).", True, CROSS),
    "CLM-PROCEDURE-CODE-MOD2": ("X(2) [inf]",
        "L578-579 base direct; set to SPACES by MAMA/ENCT overlays "
        "(L783,811,891,968).", True, CROSS),
    "CLM-ICN": ("X(19) [inf]",
        "L601 base = CLMI-ICN; override L719-720 rebuilt ICN+suffix "
        "(same condition as PRO-ICN).", True, DIRECT),
    "CLM-PRI-DX": ("X(7) [inf]",
        "L602 base = CLMI-PRI-DX; overlaid per version/claim-type diagnosis "
        "(CA/CB/CC/CD) in 3030 - see Sheet 2.", True, CROSS),
    "CLM-SEC-DX": ("X(7) [inf]",
        "L603 base = CLMI-SEC-DX; overlaid per version/claim-type diagnosis - "
        "see Sheet 2.", True, CROSS),
    "CLM-DX-3": ("X(7) [inf]",
        "L675 base = CLMI-DX-3; overlaid per version/claim-type diagnosis - "
        "see Sheet 2.", True, CROSS),
    "CLM-DX-4": ("X(7) [inf]",
        "L676 base = CLMI-DX-4; overlaid per version/claim-type diagnosis - "
        "see Sheet 2.", True, CROSS),
    "CLM-DX-5": ("X(7) [inf]",
        "L677 base = CLMI-DX-5; overlaid per version/claim-type diagnosis - "
        "see Sheet 2.", True, CROSS),
    "CLM-CLM-TYPE": ("X(2) [inf]",
        "L582  Claim type ('01'..'23'); drives version EVALUATE in 3030.", False, DIRECT),
    "CLM-PCF-CONTRACT-NUM": ("X(7) [inf]",
        "L650  Contract number (e.g. '0032600').", False, DIRECT),
    "CLM-PAY-TO-PROV-NUM": ("X(8) [inf]", "L632  Pay-to provider number.", False, DIRECT),
    "CLM-PCF-HMS-ICN-SUFFIX": ("X(2) [inf]",
        "L699-700  ICN suffix; numeric check feeds ICN reformat (L710-716).", False, DIRECT),
    "CLM-CLAIM-FROM-DOS": ("9(7) 0yymmdd [inf]",
        "L605  From date-of-service; 0yymmdd per source comment L459-465.", False, DIRECT),
}

# ordered base CLM list (target, src) exactly as extracted from source 3020
clm_base = [
    ("CLM-PCF-MA-NUM", "CLMI-PCF-MA-NUM", 572),
    ("CLM-PROV-OF-SVC-NUM", "CLMI-PROV-OF-SVC-NUM", 573),
    ("CLM-PROCEDURE-CODE-7", "CLMI-PROCEDURE-CODE-5", 574),
    ("CLM-PROCEDURE-CODE-MOD1", "CLMI-PROCEDURE-CODE-MOD1", 576),
    ("CLM-PROCEDURE-CODE-MOD2", "CLMI-PROCEDURE-CODE-MOD2", 578),
    ("CLM-SURGERY-DATE", "CLMI-SURGERY-DATE", 580),
    ("CLM-PROC-CODE-DENTAL", "CLMI-PROC-CODE-DENTAL", 581),
    ("CLM-CLM-TYPE", "CLMI-CLM-TYPE", 582),
    ("CLM-ORIG-CLM-TYPE", "CLMI-ORIG-CLM-TYPE", 583),
    ("CLM-CATG-OF-SVC", "CLMI-CATG-OF-SVC", 584),
    ("CLM-TYPE-OF-SVC", "CLMI-TYPE-OF-SVC", 585),
    ("CLM-PLACE-OF-SVC", "CLMI-PLACE-OF-SVC", 586),
    ("CLM-DRG", "CLMI-DRG", 587),
    ("CLM-LEVEL-OF-CARE-IND", "CLMI-LEVEL-OF-CARE-IND", 588),
    ("CLM-CLAIM-FORM-IND", "CLMI-CLAIM-FORM-IND", 589),
    ("CLM-PAT-LAST-NAME", "CLMI-PAT-LAST-NAME", 590),
    ("CLM-PAT-FIRST-NAME", "CLMI-PAT-FIRST-NAME", 591),
    ("CLM-PAT-MID-INIT", "CLMI-PAT-MID-INIT", 592),
    ("CLM-PAT-SEX", "CLMI-PAT-SEX", 593),
    ("CLM-PAT-DOB", "CLMI-PAT-DOB", 594),
    ("CLM-XACTION-TYPE", "CLMI-XACTION-TYPE", 595),
    ("CLM-XACTION-STATUS", "CLMI-XACTION-STATUS", 596),
    ("CLM-DOR", "CLMI-DOR", 597),
    ("CLM-REMIT-ID-NUM", "CLMI-REMIT-ID-NUM", 598),
    ("CLM-ADJ-IND", "CLMI-ADJ-IND", 599),
    ("CLM-ADJ-REASON", "CLMI-ADJ-REASON", 600),
    ("CLM-ICN", "CLMI-ICN", 601),
    ("CLM-PRI-DX", "CLMI-PRI-DX", 602),
    ("CLM-SEC-DX", "CLMI-SEC-DX", 603),
    ("CLM-UNIT-VISITS-DAYS", "CLMI-UNIT-VISITS-DAYS", 604),
    ("CLM-CLAIM-FROM-DOS", "CLMI-CLAIM-FROM-DOS", 605),
    ("CLM-CLAIM-THRU-DOS", "CLMI-CLAIM-THRU-DOS", 606),
    ("CLM-RECORD-THRU-DOS", "CLMI-RECORD-THRU-DOS", 607),
    ("CLM-ADMIT-DATE", "CLMI-ADMIT-DATE", 608),
    ("CLM-DISCH-DATE", "CLMI-DISCH-DATE", 609),
    ("CLM-ELIG-INPAT-DAYS", "CLMI-ELIG-INPAT-DAYS", 610),
    ("CLM-INELIG-INPAT-DAYS", "CLMI-INELIG-INPAT-DAYS", 611),
    ("CLM-NATURE-HSP-ADMISSION", "CLMI-NATURE-HSP-ADMISSION", 612),
    ("CLM-PAT-STATUS-CODE", "CLMI-PAT-STATUS-CODE", 614),
    ("CLM-TRAUMA-IND", "CLMI-TRAUMA-IND", 615),
    ("CLM-TPL-ACCIDENT-IND", "CLMI-TPL-ACCIDENT-IND", 616),
    ("CLM-PROV-CLAIM-NUM", "CLMI-PROV-CLAIM-NUM", 617),
    ("CLM-MA-BILLED-HDR", "CLMI-MA-BILLED-HDR", 618),
    ("CLM-OTHER-INS-PAID-HDR", "CLMI-OTHER-INS-PAID-HDR", 619),
    ("CLM-MC-COINS-DTL", "CLMI-MC-COINS-DTL", 621),
    ("CLM-MC-DEDUCT-DTL", "CLMI-MC-DEDUCT-DTL", 622),
    ("CLM-DRG-ALLOWED", "CLMI-DRG-ALLOWED", 623),
    ("CLM-MA-BILLED-NET-HDR", "CLMI-MA-BILLED-NET-HDR", 624),
    ("CLM-TOT-MA-PAID-HDR", "CLMI-TOT-MA-PAID-HDR", 625),
    ("CLM-MC-ALLOWED-DTL", "CLMI-MC-ALLOWED-DTL", 626),
    ("CLM-OTHER-INS-PAID-DTL", "CLMI-OTHER-INS-PAID-DTL", 627),
    ("CLM-MA-BILLED-NET-DTL", "CLMI-MA-BILLED-NET-DTL", 629),
    ("CLM-MA-PAID-DTL", "CLMI-MA-PAID-DTL", 630),
    ("CLM-PROV-TYPE", "CLMI-PROV-TYPE", 631),
    ("CLM-PAY-TO-PROV-NUM", "CLMI-PAY-TO-PROV-NUM", 632),
    ("CLM-REFER-PROV-NUM", "CLMI-REFER-PROV-NUM", 633),
    ("CLM-PROV-SPECIALTY", "CLMI-PROV-SPECIALTY", 634),
    ("CLM-RX-SUPPLY-DAYS", "CLMI-RX-SUPPLY-DAYS", 635),
    ("CLM-RX-REFILL-IND", "CLMI-RX-REFILL-IND", 636),
    ("CLM-VERSION-NUMBER", "CLMI-VERSION-NUMBER", 637),
    ("CLM-PCF-MC-NUM", "CLMI-PCF-MC-NUM", 638),
    ("CLM-MC-ATTACHMENT-IND", "CLMI-MC-ATTACHMENT-IND", 639),
    ("CLM-MC-FORCE-IND", "CLMI-MC-FORCE-IND", 640),
    ("CLM-MC-BENEFITS-EXHAUSTED", "CLMI-MC-BENEFITS-EXHAUSTED", 641),
    ("CLM-FAMILY-PLANNING-IND", "CLMI-FAMILY-PLANNING-IND", 643),
    ("CLM-MULTI-MATCH-IND", "CLMI-MULTI-MATCH-IND", 645),
    ("CLM-RUNTIME-SEQ-NUM", "CLMI-RUNTIME-SEQ-NUM", 646),
    ("CLM-NUM-REV-CHARGES", "CLMI-NUM-REV-CHARGES", 647),
    ("CLM-NUM-OTH-SEGS", "CLMI-NUM-OTH-SEGS", 648),
    ("CLM-FILE-DATA-SOURCE", "CLMI-FILE-DATA-SOURCE", 649),
    ("CLM-PCF-CONTRACT-NUM", "CLMI-PCF-CONTRACT-NUM", 650),
    ("CLM-CLAIM-EMERGENCY-IND", "CLMI-CLAIM-EMERGENCY-IND", 651),
    ("CLM-STAT-DOLLARS-HDR-OR-DTL", "CLMI-STAT-DOLLARS-HDR-OR-DTL", 653),
    ("CLM-SUMMED-BILL-ANC-DOLLARS", "CLMI-SUMMED-BILL-ANC-DOLLARS", 655),
    ("CLM-BILL-TYPE", "CLMI-BILL-TYPE", 657),
    ("CLM-RECORD-FROM-DOS-DTL", "CLMI-RECORD-FROM-DOS-DTL", 658),
    ("CLM-FORMER-ICN", "CLMI-FORMER-ICN", 660),
    ("CLM-SRC-LINE-ITEM-DTL-CNT", "CLMI-SRC-LINE-ITEM-DTL-CNT", 661),
    ("CLM-NET-DUPE-DATE", "CLMI-NET-DUPE-DATE", 663),
    ("CLM-OTP-COB-IND", "CLMI-OTP-COB-IND", 665),
    ("CLM-PM-USER-AREA", "CLMI-PM-USER-AREA", 667),
    ("CLM-PM-USER-AREA-2", "CLMI-PM-USER-AREA-2", 668),
    ("CLM-XWALKED-PROC-CODE1", "CLMI-XWALKED-PROC-CODE1", 669),
    ("CLM-APPLIED-INCOME", "CLMI-APPLIED-INCOME", 671),
    ("CLM-NUM-LEAVE-DAYS", "CLMI-NUM-LEAVE-DAYS", 672),
    ("CLM-RATE-PAID", "CLMI-RATE-PAID", 673),
    ("CLM-FACILITY-PROV-NUM", "CLMI-FACILITY-PROV-NUM", 674),
    ("CLM-DX-3", "CLMI-DX-3", 675),
    ("CLM-DX-4", "CLMI-DX-4", 676),
    ("CLM-DX-5", "CLMI-DX-5", 677),
    ("CLM-INST-ADDITIONAL-FIELDS", "CLMI-INST-ADDITIONAL-FIELDS", 678),
    ("CLM-NEW-DRG", "CLMI-NEW-DRG", 680),
    ("CLM-PROV-NUM-FROM-PREFIX", "CLMI-PROV-NUM-FROM-PREFIX", 681),
    ("CLM-DATE-REFORMATTED", "CLMI-DATE-REFORMATTED", 683),
    ("CLM-SYS-DELETE-STATUS", "CLMI-SYS-DELETE-STATUS", 684),
    ("CLM-STAMP-DATE-TIME", "CLMI-STAMP-DATE-TIME", 685),
    ("CLM-STAMP-SEQ-NUM", "CLMI-STAMP-SEQ-NUM", 686),
    ("CLM-ORIG-TOT-MA-PAID-HDR", "CLMI-ORIG-TOT-MA-PAID-HDR", 687),
    ("CLM-ORIG-MA-PAID-DTL", "CLMI-ORIG-MA-PAID-DTL", 689),
    ("CLM-PCF-CLASSIFICATION-STAT", "CLMI-PCF-CLASSIFICATION-STAT", 691),
    ("CLM-PCF-CLASSIFICATION-DATE", "CLMI-PCF-CLASSIFICATION-DATE", 693),
    ("CLM-PCF-IN-PROGRESS-IND", "CLMI-PCF-IN-PROGRESS-IND", 695),
    ("CLM-PCF-LOGICAL-DELETE-IND", "CLMI-PCF-LOGICAL-DELETE-IND", 697),
    ("CLM-PCF-HMS-ICN-SUFFIX", "CLMI-PCF-HMS-ICN-SUFFIX", 699),
    ("CLM-PCF-FILE-NAME", "CLMI-PCF-FILE-NAME", 701),
    ("CLM-PCF-VERSION-NUMBER", "CLMI-PCF-VERSION-NUMBER", 703),
]


def build_master_rows():
    """Return list of dict rows for Sheet 1 (one per output field)."""
    rows = []

    # --- PRO prefix fields ---
    for tgt, src, mtype, cb, pic, comment, ovr in pro_fields:
        si = sample_for(tgt)
        if mtype == DERIVED and "INCIDENT" in tgt:
            si_in, si_out = "2024-01 (CASE)", "20240101"
        elif mtype == DERIVED and "THRU" in tgt:
            si_in, si_out = "2024-12-31 (CASE)", "20241231"
        elif tgt == "PRO-CREATE-SOURCE":
            si_in, si_out = "card '1..NJ'", "NJ"
        else:
            si_in = si_out = si
        rows.append(dict(copybook=OUT_PRO, target=tgt, pic=pic, pos=NA_POS,
                         mtype=mtype, src_cb=cb, src=src,
                         s_in=si_in, s_out=si_out, path="SRCPCF-OUT",
                         comment=comment, fill=OVR_FILL if ovr else PRO_FILL))

    # --- CLM body fields ---
    for tgt, src, ln in clm_base:
        pic, comment, ovr, mtype = (NA_PIC, f"L{ln}  CLMI body field copied to "
                                    "matching CLM output field.", False, DIRECT)
        if tgt in clm_overrides:
            pic, comment, ovr, mtype = clm_overrides[tgt]
        if tgt == "CLM-PROCEDURE-CODE-7":
            si_in, si_out = "99213", "99213  "         # 5 -> 7
        else:
            si = sample_for(tgt)
            si_in = si_out = si
        rows.append(dict(copybook=OUT_CLM, target=tgt, pic=pic, pos=NA_POS,
                         mtype=mtype, src_cb=CB_CLMI, src=src,
                         s_in=si_in, s_out=si_out, path="SRCPCF-OUT",
                         comment=comment, fill=OVR_FILL if ovr else CLM_FILL))

    # --- CLM-CDE-ICD-VERSION (constant, date-derived; set at L726-730) ---
    rows.append(dict(copybook=OUT_CLM, target="CLM-CDE-ICD-VERSION",
                     pic="X(2) [inf]", pos=NA_POS, mtype=CONST,
                     src_cb=CB_CONST, src="'09' or '10' (literal)",
                     s_in="FROM-DATE 20240115", s_out="09",
                     path="SRCPCF-OUT",
                     comment="L726-730  '09' when PRO-CLM-FROM-DATE < 20151001, "
                             "else '10'. Runs after 3030 overlay, so always "
                             "date-based.", fill=OVR_FILL))
    return rows


# --- CASE-PCF-MATCH report fields (fully defined in program) --------------- #
# (target, pic, byte_start, byte_end, mtype, src, s_in, s_out, comment)
match_rows = [
    ("F (FILLER)", "X(3)", 1, 3, CONST, "literal ' * '", "-", " * ",
     "L227  Field separator literal."),
    ("MATCH-CASE-ID-OUT", "X(20)", 4, 23, "Direct MOVE (derived key)",
     "WS-CASE-ID = CASET-RECIPIENT-ID-NUM(1)", "123456789012",
     "123456789012        ",
     "Header literal 'CASE ID' at init (L228); per case value set L1527 "
     "(from L735)."),
    ("F (FILLER)", "X(3)", 24, 26, CONST, "literal ' * '", "-", " * ",
     "L229  Field separator literal."),
    ("MATCH-TOT-PCF-REC-OUT", "X(19)", 27, 45, DERIVED,
     "WS-TOT-PCF-REC-MATCH (PIC ZZZZ9, left-trimmed)", "5 (count)", "5",
     "Header 'PCF RECORDS MATCHED' (L230-231); value formatted L1529-1534."),
    ("F (FILLER)", "X(3)", 46, 48, CONST, "literal ' * '", "-", " * ",
     "L232  Field separator literal."),
    ("MATCH-TOT-PCF-MA-PAID-OUT", "X(18)", 49, 66, DERIVED,
     "WS-TOT-PCF-MA-PAID (PIC $$$,$$$,$$$,$$9.99, left-trimmed)",
     "750.00 (sum)", "$750.00",
     "Header 'PCF TOT $$ MA PAID' (L233-234); value formatted L1536-1541."),
    ("F (FILLER)", "X(2)", 67, 68, CONST, "literal ' *'", "-", " *",
     "L235  Trailing literal; bytes 69-80 space-filled by 80-byte WRITE."),
]


# --------------------------------------------------------------------------- #
# SHEET 1 - Field Mapping
# --------------------------------------------------------------------------- #
def sheet_field_mapping(wb):
    ws = wb.active
    ws.title = "Field Mapping"
    ws.cell(row=1, column=1,
            value="CASPCFNJ - Field-to-Field Mapping (one row per output field)")
    ws.cell(row=1, column=1).font = TITLE_FONT
    note = ("Evidence-based: 'Comments' cite CASPCFNJ source line numbers. "
            "PRO-/CLM-/CLMI- PICTUREs and byte positions live in external "
            "copybooks NOT in this repo (CLMPREFX, FDPCF601, FDPCF602); shown "
            "as 'n/a (...)' unless inferable from usage ([inf]). "
            "CASE-PCF-MATCH fields are fully defined in-program (exact PIC/pos). "
            "All sample values are ILLUSTRATIVE.")
    ws.cell(row=2, column=1, value=note)
    ws.cell(row=2, column=1).alignment = WRAP
    ws.merge_cells("A2:M2")
    ws.row_dimensions[2].height = 58

    headers = ["Field No", "Output Copybook", "Target Field", "Picture",
               "Byte Location", "Mapping Type", "Source Copybook",
               "Source Field", "Sample Input", "Sample Output",
               "SRCPCF-OUT (claim, 754B)", "CASE-PCF-MATCH (report, 80B)",
               "Comments"]
    hr = 4
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    style_header(ws, hr, len(headers))

    r = hr + 1
    n = 0
    for row in build_master_rows():
        n += 1
        vals = [n, row["copybook"], row["target"], row["pic"], row["pos"],
                row["mtype"], row["src_cb"], row["src"], row["s_in"],
                row["s_out"], "Yes", "", row["comment"]]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.alignment = WRAP
            cell.border = BORDER
            cell.fill = row["fill"]
        r += 1

    # match report rows
    for (tgt, pic, b0, b1, mtype, src, s_in, s_out, comment) in match_rows:
        n += 1
        vals = [n, OUT_MATCH, tgt, pic, f"{b0}-{b1}", mtype,
                "program-defined" if "literal" not in src else CB_CONST,
                src, s_in, s_out, "", "Yes", comment]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.alignment = WRAP
            cell.border = BORDER
            cell.fill = MAT_FILL
        r += 1

    set_widths(ws, [8, 26, 30, 22, 14, 34, 28, 34, 20, 22, 14, 16, 60])
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A{hr}:M{r-1}"
    return n


# --------------------------------------------------------------------------- #
# SHEET 2 - Overrides & Crosswalks
# --------------------------------------------------------------------------- #
def sheet_overrides(wb):
    ws = wb.create_sheet("Overrides & Crosswalks")
    ws.cell(row=1, column=1, value="Overrides & Crosswalks (per input format / version)")
    ws.cell(row=1, column=1).font = TITLE_FONT

    headers = ["Path/Format", "Source Field", "Target Field",
               "Assigned/Translated Value", "Condition", "Sample In -> Out",
               "Description"]
    hr = 3
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    style_header(ws, hr, len(headers))

    rows = [
        # ICN reformat
        ("SRCPCF-OUT (all)", "CLMI-ICN + CLMI-PCF-HMS-ICN-SUFFIX",
         "PRO-ICN / CLM-ICN", "ICN(17) || suffix(2) = 19-byte ICN",
         "PM-USER-AREA(1:2) in {'PB','DT'} AND contract='0032600' AND "
         "PM-USER-AREA(27:3) not 'DSS' AND suffix numeric & <> 0",
         "ICN=20240011122233300, suffix='05' -> 2024001112223330005",
         "L706-723  Rebuilds ICN with 2-char suffix via WS-ICN-GROUP-19."),
        # ICD version
        ("SRCPCF-OUT (all)", "PRO-CLM-FROM-DATE", "CLM-CDE-ICD-VERSION",
         "'09' or '10'", "FROM-DATE < 20151001 -> '09'; else '10'",
         "20140115 -> 09 ; 20160115 -> 10",
         "L726-730  ICD-9 vs ICD-10 indicator by date of service."),
        # provider replace
        ("SRCPCF-OUT (all)", "CLMI-PAY-TO-PROV-NUM", "CLM-PROV-OF-SVC-NUM",
         "pay-to prov number", "CLMI-PROV-OF-SVC-NUM='09999996' AND "
         "contract='0032600'", "09999996 -> 01234567",
         "L564-568  Dummy prov-of-svc replaced by pay-to prov before move."),
        # Version MAMA v06 -> CA
        ("MAMA v06 (FDNJTPC5 -> CA)", "CA-A-PROC-CDE", "CLM-PROCEDURE-CODE-7",
         "client-data proc code", "PFX-SYS-HMS-ASSIGN-FILE='MAMA' AND "
         "PFX-SYS-VERSION='06' AND CLM-TYPE in listed set",
         "CA-A-PROC-CDE='99213' -> '99213  '",
         "L764-789  Overlays procedure code; MOD1/MOD2 set to SPACES."),
        ("MAMA v06 (FDNJTPC5 -> CA)", "CA-A-DIAG-CDE(1..5)",
         "CLM-PRI-DX / SEC-DX / DX-3 / DX-4 / DX-5", "client-data diag codes",
         "same as above", "CA-A-DIAG-CDE(1)='4019' -> CLM-PRI-DX='4019   '",
         "L784-788  Overlays 5 diagnosis codes from CA activity record."),
        # Version MAMA/CCAR v05 -> CB
        ("MAMA/CCAR v05 (FDNJTPC4 -> CB)", "CB-A-PROC-CDE",
         "CLM-PROCEDURE-CODE-7", "client-data proc code",
         "PFX-SYS-HMS-ASSIGN-FILE in {'MAMA','CCAR'} AND PFX-SYS-VERSION='05' "
         "AND CLM-TYPE in listed set", "CB-A-PROC-CDE='99213' -> '99213  '",
         "L791-811  Overlays procedure code; MOD1/MOD2 set to SPACES."),
        ("MAMA/CCAR v05 (FDNJTPC4 -> CB)", "CB-A-DIAG-CDE(1..5)",
         "CLM-PRI-DX / SEC-DX / DX-3 / DX-4 / DX-5", "client-data diag codes",
         "same as above", "CB-A-DIAG-CDE(1)='4019' -> CLM-PRI-DX='4019   '",
         "L812-816  Overlays 5 diagnosis codes from CB activity record."),
        # Version ENCT v05 -> CC
        ("ENCT v05 (FDNJ5INS -> CC)", "CC-HNI/OP/PR/HH/TR/VI-DIAG(n)",
         "CLM-PRI-DX / SEC-DX / DX-3 / DX-4 / DX-5",
         "claim-type-specific diag source",
         "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='05'; "
         "EVALUATE CLMI-CLM-TYPE (01,02,03,04,06,07,18)",
         "type 02: CC-HNI-DIAG(1) if not spaces else CC-OP-DIAG(1)",
         "L819-886  Diagnosis source chosen by claim type; HNI preferred, "
         "OP fallback for type 02."),
        ("ENCT v05 (FDNJ5INS -> CC)", "CC-E-PROC-CDE", "CLM-PROCEDURE-CODE-7",
         "encounter proc code", "ENCT v05 AND CLMI-CLM-TYPE <> '12'",
         "CC-E-PROC-CDE='99213' -> '99213  '",
         "L888-892  Overlays procedure code; MOD1/MOD2 set to SPACES."),
        # Version ENCT v04 -> CD
        ("ENCT v04 (FDNJ4INS -> CD)", "CD-HNI/OP/PR/HH/TR/VI-DIAG(n)",
         "CLM-PRI-DX / SEC-DX / DX-3 / DX-4 / DX-5",
         "claim-type-specific diag source",
         "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='04'; "
         "EVALUATE CLMI-CLM-TYPE (01,02,03,04,06,07,18)",
         "type 03: CD-OP-DIAG(1..5) -> CLM-PRI..DX-5",
         "L895-964  Diagnosis source chosen by claim type (note: type 04 "
         "skips SEC-DX in source)."),
        ("ENCT v04 (FDNJ4INS -> CD)", "CD-E-PROC-CDE", "CLM-PROCEDURE-CODE-7",
         "encounter proc code", "ENCT v04 AND CLMI-CLM-TYPE <> '12'",
         "CD-E-PROC-CDE='99213' -> '99213  '",
         "L965-969  Overlays procedure code; MOD1/MOD2 set to SPACES."),
        # Other versions
        ("Other versions", "(none)", "(no overlay)", "-",
         "Any file/version not MAMA06, MAMA/CCAR05, ENCT05, ENCT04",
         "base CLMI diag/proc flow unchanged",
         "L970-972 / 5500-PROCESS-RECS: only ADD 1 TO OTHER-VERS; record is "
         "still written with the base CLMI->CLM moves."),
        # Match report crosswalk-style
        ("CASE-PCF-MATCH", "WS-TOT-PCF-REC-MATCH", "MATCH-TOT-PCF-REC-OUT",
         "count edited to ZZZZ9", "per matched CASE-ID",
         "5 -> '5'", "L1529-1534  Numeric match count, space-trimmed."),
        ("CASE-PCF-MATCH", "WS-TOT-PCF-MA-PAID", "MATCH-TOT-PCF-MA-PAID-OUT",
         "amount edited to $-float", "per matched CASE-ID; SIZE-OK",
         "750.00 -> '$750.00'",
         "L1536-1541  Sum of CLMI-TOT-MA-PAID-HDR; 'TOO MANY MATCHES...' on "
         "SIZE ERROR (L1542-1545)."),
    ]
    r = hr + 1
    for row in rows:
        for c, v in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.alignment = WRAP
            cell.border = BORDER
        r += 1
    set_widths(ws, [28, 34, 34, 26, 44, 40, 60])
    ws.freeze_panes = "A4"
    return len(rows)


# --------------------------------------------------------------------------- #
# SHEET 3 - Routing / Format Logic
# --------------------------------------------------------------------------- #
def sheet_routing(wb):
    ws = wb.create_sheet("Routing & Format Logic")
    ws.cell(row=1, column=1, value="Routing / Format Logic")
    ws.cell(row=1, column=1).font = TITLE_FONT

    blocks = [
        ("Program role",
         "Reformat + Filter + Multi-output. Reads one PCF claim file and a "
         "Case file, matches claims to OPEN cases by Medicaid number, "
         "reformats the claim (HMS-600 -> HMS-601, enlarged diagnosis area), "
         "and writes two outputs."),
        ("Inputs",
         "SRCPCF-IN (SRCPCFI, VB 4..32752, read INTO WS-CLMI-RECORD); "
         "CASEFL-IN (CASEFLI, FB 384, read INTO WS-CASE-RECORD); "
         "CNTL-CARDS (SYS004, FB 80) - card tag '1' supplies CREATE-SOURCE."),
        ("Outputs",
         "SRCPCF-OUT (SRCPCFO, FB 754, CLMO-RECORD) = reformatted claim; "
         "CASE-PCF-MATCH (MATCHO, FB 80, MATCH-RECORD) = match report "
         "(header + one line per matched CASE-ID + trailer)."),
        ("Outputs per input record",
         "0 or 1 SRCPCF-OUT record per PCF input record (written only when a "
         "claim matches an OPEN case and passes the date window). The "
         "CASE-PCF-MATCH file gets 1 summary line per matched CASE-ID (not per "
         "claim), plus header/trailer."),
        ("Driver",
         "0000-MAIN: 1000-INITIALIZE, then 2000-MAINLINE UNTIL PCF-EOF, then "
         "9000-TERMINATION. Records are matched by comparing "
         "CASE-RECIPIENT-ID-NUM with PFX-APP-MEDICAID-NO (ordered merge)."),
        ("SKIP #1 - ref status",
         "L452-455  IF PFX-SYS-EXIT-FROM-REF-STATUS NOT = 'Y' -> read next "
         "PCF and skip (claim never written)."),
        ("SKIP #2 - DSS window",
         "L457-469  contract='0032600' AND PM-USER-AREA(27:3)='DSS' AND "
         "CLAIM-FROM-DOS > 0040000 AND < 0900000 -> ADD 1 REC-SKIP-DSS, skip."),
        ("SKIP #3 - dummy provider",
         "L471-476  PROV-OF-SVC-NUM='09999996' AND PAY-TO-PROV-NUM='09999996' "
         "-> ADD 1 REC-SKIP-PROV, skip."),
        ("WRITE gate - date window",
         "L537-541  Case status 'O' or X'96' AND "
         "PFX-APP-DATE-OF-SERVICE >= WS-INCIDENT-DATE-NEW-RE AND "
         "<= WS-CLM-THRU-DATE-N. Only then are PRO/CLM built and written."),
        ("Case table",
         "Up to 40 recipients loaded into WS-CASE-TABLE (CASET) per MA number "
         "(3010-LOAD-CASE-TABLE); each claim is tested against every loaded "
         "case row (3020 VARYING SUB-I)."),
        ("Version routing (diag/proc overlay)",
         "3030-REVIEW-CLMS-VERS keys on PFX-SYS-HMS-ASSIGN-FILE + "
         "PFX-SYS-VERSION: MAMA/06->CA, MAMA|CCAR/05->CB, ENCT/05->CC, "
         "ENCT/04->CD, else 5500 (count only). See Sheet 2."),
        ("STOP / ABEND",
         "No ABEND/STOP RUN on error paths. STOP RUN only at normal end "
         "(L365). ON SIZE ERROR sets SIZE-ERROR, which makes the match line "
         "read 'TOO MANY MATCHES, $$ PAID NOT AVAILABLE !' (L1542-1545)."),
        ("Bulk move?",
         "No whole-record move. The group move MOVE CLMI-HMS-600 TO CLM-HMS-601 "
         "is commented out (L570) because HMS-601 enlarges the diagnosis area; "
         "fields are moved individually (L572-704)."),
    ]
    hr = 3
    ws.cell(row=hr, column=1, value="Topic")
    ws.cell(row=hr, column=2, value="Explanation")
    style_header(ws, hr, 2)
    r = hr + 1
    for topic, text in blocks:
        a = ws.cell(row=r, column=1, value=topic)
        b = ws.cell(row=r, column=2, value=text)
        a.font = Font(bold=True)
        a.alignment = WRAP
        b.alignment = WRAP
        a.border = BORDER
        b.border = BORDER
        r += 1
    set_widths(ws, [30, 110])
    ws.freeze_panes = "A4"
    return len(blocks)


# --------------------------------------------------------------------------- #
# SHEET 4 - Sample Records
# --------------------------------------------------------------------------- #
def sheet_samples(wb):
    ws = wb.create_sheet("Sample Records")
    ws.cell(row=1, column=1, value="Sample Records (ILLUSTRATIVE, internally consistent)")
    ws.cell(row=1, column=1).font = TITLE_FONT
    ws.cell(row=2, column=1, value=(
        "One full worked example: a MAMA version-06 claim that matches an OPEN "
        "case. Field positions inside CLMI/PRO/CLM are governed by copybooks "
        "not in the repo, so the claim records are shown field-by-field, not as "
        "fixed-column byte strings. Values marked ILLUSTRATIVE."))
    ws.cell(row=2, column=1).alignment = WRAP
    ws.merge_cells("A2:D2")
    ws.row_dimensions[2].height = 46

    def section(ws, r, title):
        c = ws.cell(row=r, column=1, value=title)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        return r + 1

    def kv_header(ws, r, cols):
        for i, h in enumerate(cols, start=1):
            cell = ws.cell(row=r, column=i, value=h)
            cell.fill = SUB_FILL
            cell.font = Font(bold=True)
            cell.border = BORDER
        return r + 1

    r = 4
    # INPUT 1: control card
    r = section(ws, r, "INPUT A - CNTL-CARDS (SYS004, 80B) - control card")
    r = kv_header(ws, r, ["Field", "Value", "PIC", "Note"])
    for f, v, p, nt in [
        ("CARD-TAG", "1", "X(1)", "tag '1' row"),
        ("FILLER", "  ", "X(2)", ""),
        ("CARD-COMMENT", "CREATE SOURCE".ljust(30), "X(30)", ""),
        ("FILLER", " ", "X(1)", ""),
        ("CARD-DATA", "NJ", "X(2)", "-> WS-SAVE-CREATE-SOURCE (L430)")]:
        for i, val in enumerate([f, v, p, nt], start=1):
            ws.cell(row=r, column=i, value=val).border = BORDER
        r += 1
    r += 1

    # INPUT 2: Case record
    r = section(ws, r, "INPUT B - CASEFL-IN (CASEFLI, 384B, NCTCASE) - matched case row")
    r = kv_header(ws, r, ["Field (CASET-*)", "Value", "PIC", "Note"])
    for f, v, p, nt in [
        ("CASE-RECIPIENT-ID-NUM", "123456789012", "see NCTCASE",
         "matches PFX-APP-MEDICAID-NO"),
        ("CASET-CASE-STATUS-CODE", "O", "X(1)", "Open case (also X'96')"),
        ("CASET-HMS-CASE-KEY", "CASEKEY0001", "see NCTCASE", "-> PRO-HMS-CASE-KEY"),
        ("CASET-HMS-CLIENT-ID", "CLIENT0001", "see NCTCASE", "-> PRO-CLIENT-ID"),
        ("CASET-INCIDENT-DATE", "2024-01", "text", "-> PRO-INCIDENT-DATE 20240101"),
        ("CASET-CLAIMS-THRU-DATE", "2024-12-31", "text",
         "-> PRO-CLM-THRU-DATE 20241231")]:
        for i, val in enumerate([f, v, p, nt], start=1):
            ws.cell(row=r, column=i, value=val).border = BORDER
        r += 1
    r += 1

    # INPUT 3: PCF claim
    r = section(ws, r, "INPUT C - SRCPCF-IN (SRCPCFI, VB) - PCF claim (PFX + CLMI + client data)")
    r = kv_header(ws, r, ["Field", "Value", "Area", "Note"])
    for f, v, area, nt in [
        ("PFX-APP-MEDICAID-NO", "123456789012", "TPLPREFX/PFX", "match key"),
        ("PFX-SYS-EXIT-FROM-REF-STATUS", "Y", "TPLPREFX/PFX", "must be 'Y' (L452)"),
        ("PFX-APP-DATE-OF-SERVICE", "20240115", "TPLPREFX/PFX",
         "in [20240101 .. 20241231] window"),
        ("PFX-NET-CLAIM-TRANS-TYPE", "A", "TPLPREFX/PFX", "-> PRO-CLAIM-TRANS-TYPE"),
        ("PFX-SYS-HMS-ASSIGN-FILE", "MAMA", "TPLPREFX/PFX", "version routing"),
        ("PFX-SYS-VERSION", "06", "TPLPREFX/PFX", "-> CA overlay path"),
        ("CLMI-PCF-MA-NUM", "123456789012", "FDPCF602/CLMI",
         "-> PRO/CLM-RECIPIENT/MA"),
        ("CLMI-ICN", "20240011122233300", "FDPCF602/CLMI", "-> PRO-ICN / CLM-ICN"),
        ("CLMI-CLM-TYPE", "01", "FDPCF602/CLMI", "in MAMA06 WHEN set"),
        ("CLMI-PCF-CONTRACT-NUM", "0032600", "FDPCF602/CLMI", ""),
        ("CLMI-PROV-OF-SVC-NUM", "01234567", "FDPCF602/CLMI", "not dummy"),
        ("CLMI-TOT-MA-PAID-HDR", "000000150.00", "FDPCF602/CLMI",
         "summed into match $$"),
        ("CLMI-PRI-DX", "2500", "FDPCF602/CLMI",
         "base value (overlaid by CA-A-DIAG-CDE(1))"),
        ("CLMI-CLIENT-DATA(CA-A-PROC-CDE)", "99213", "FDNJTPC5/CA",
         "-> CLM-PROCEDURE-CODE-7"),
        ("CLMI-CLIENT-DATA(CA-A-DIAG-CDE 1..5)", "4019 / 2724 / E785 / Z00 / I10",
         "FDNJTPC5/CA", "-> CLM-PRI-DX..DX-5")]:
        for i, val in enumerate([f, v, area, nt], start=1):
            ws.cell(row=r, column=i, value=val).border = BORDER
        r += 1
    r += 1

    # OUTPUT 1: claim
    r = section(ws, r, "OUTPUT 1 - SRCPCF-OUT (CLMO-RECORD, 754B) - key fields of reformatted claim")
    r = kv_header(ws, r, ["Target field", "Value", "Source", "Rule"])
    for f, v, s, rule in [
        ("PRO-RECIPIENT-ID-NUM", "123456789012", "CLMI-PCF-MA-NUM", "direct L543"),
        ("PRO-CREATE-SOURCE", "NJ", "card CARD-DATA", "direct L552"),
        ("PRO-HMS-CASE-KEY", "CASEKEY0001", "CASET-HMS-CASE-KEY", "direct L544"),
        ("PRO-CLIENT-ID", "CLIENT0001", "CASET-HMS-CLIENT-ID", "direct L546"),
        ("PRO-ICN", "20240011122233300", "CLMI-ICN", "direct L554 (no suffix reformat)"),
        ("PRO-CLM-FROM-DATE", "20240115", "PFX-APP-DATE-OF-SERVICE", "direct L558"),
        ("PRO-INCIDENT-DATE", "20240101", "CASET-INCIDENT-DATE", "reformat L562/985"),
        ("PRO-CLM-THRU-DATE", "20241231", "CASET-CLAIMS-THRU-DATE", "reformat L563/993"),
        ("CLM-CLM-TYPE", "01", "CLMI-CLM-TYPE", "direct L582"),
        ("CLM-PROV-OF-SVC-NUM", "01234567", "CLMI-PROV-OF-SVC-NUM", "direct L573"),
        ("CLM-PROCEDURE-CODE-7", "99213", "CA-A-PROC-CDE", "MAMA06 overlay L781"),
        ("CLM-PROCEDURE-CODE-MOD1", "(spaces)", "SPACES", "overlay L782"),
        ("CLM-PRI-DX", "4019", "CA-A-DIAG-CDE(1)", "MAMA06 overlay L784"),
        ("CLM-SEC-DX", "2724", "CA-A-DIAG-CDE(2)", "MAMA06 overlay L785"),
        ("CLM-DX-3", "E785", "CA-A-DIAG-CDE(3)", "MAMA06 overlay L786"),
        ("CLM-DX-4", "Z00", "CA-A-DIAG-CDE(4)", "MAMA06 overlay L787"),
        ("CLM-DX-5", "I10", "CA-A-DIAG-CDE(5)", "MAMA06 overlay L788"),
        ("CLM-CDE-ICD-VERSION", "10", "literal", "FROM-DATE>=20151001 -> '10' (L729)"),
        ("CLM-TOT-MA-PAID-HDR", "000000150.00", "CLMI-TOT-MA-PAID-HDR", "direct L625"),
    ]:
        for i, val in enumerate([f, v, s, rule], start=1):
            ws.cell(row=r, column=i, value=val).border = BORDER
        r += 1
    r += 1

    # OUTPUT 2: match
    r = section(ws, r, "OUTPUT 2 - CASE-PCF-MATCH (MATCH-RECORD, 80B) - report line for this CASE-ID")
    r = kv_header(ws, r, ["Target field", "Bytes", "Value", "Source / rule"])
    for f, b, v, s in [
        ("F (FILLER)", "1-3", " * ", "literal"),
        ("MATCH-CASE-ID-OUT", "4-23", "123456789012", "WS-CASE-ID (CASET-RECIPIENT-ID-NUM(1))"),
        ("F (FILLER)", "24-26", " * ", "literal"),
        ("MATCH-TOT-PCF-REC-OUT", "27-45", "1", "WS-TOT-PCF-REC-MATCH (ZZZZ9, trimmed)"),
        ("F (FILLER)", "46-48", " * ", "literal"),
        ("MATCH-TOT-PCF-MA-PAID-OUT", "49-66", "$150.00",
         "WS-TOT-PCF-MA-PAID ($$$,...,$$9.99, trimmed)"),
        ("F (FILLER)", "67-68", " *", "literal; 69-80 spaces"),
    ]:
        for i, val in enumerate([f, b, v, s], start=1):
            ws.cell(row=r, column=i, value=val).border = BORDER
        r += 1

    set_widths(ws, [40, 22, 40, 48])
    ws.freeze_panes = "A4"
    return r


# --------------------------------------------------------------------------- #
def main():
    wb = Workbook()
    n_fields = sheet_field_mapping(wb)
    n_ovr = sheet_overrides(wb)
    n_route = sheet_routing(wb)
    sheet_samples(wb)
    wb.save(OUT_XLSX)
    print(f"Wrote {OUT_XLSX}")
    print(f"  Sheet 1 Field Mapping   : {n_fields} output-field rows")
    print(f"  Sheet 2 Overrides       : {n_ovr} rows")
    print(f"  Sheet 3 Routing         : {n_route} topics")
    print(f"  Sheet 4 Sample Records  : 1 full worked example")


if __name__ == "__main__":
    main()
