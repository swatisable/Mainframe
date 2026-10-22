#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_caspcfnj_mapping.py
============================================================================
Builds the CASPCFNJ 1x1 field-mapping workbook:

    CASPCFNJ_1x1_Field_Mapping.xlsx   (exactly 4 sheets)

The script reads the real COBOL source file ``CASPCFNJ`` in the repository
root, parses every *active* (non-comment) MOVE statement in the PROCEDURE
DIVISION and uses those statements as the authoritative source for the
output-field mapping.  Each mapping row therefore points at a real line of
code (the ``Code Line`` column).

"Do not guess" notes
--------------------
The COBOL program COPYs several external copybooks that are **not present**
in this repository:

    TPLPREFX  (prefix PFX )  - input  claim prefix  (~127 bytes)
    FDPCF602  (prefix CLMI)  - input  claim HMS-600 body (600 bytes)
    NCTCASE   (prefix CASET/CASE) - case record (384 bytes)
    FDNJTPC5 / FDNJTPC4 / FDNJ5INS / FDNJ4INS - client-side claim detail
    CLMPREFX  (prefix PRO )  - output claim prefix
    FDPCF601  (prefix CLM )  - output claim HMS-601 body (enlarged diag area)

Because those copybooks are absent, the exact PICTURE clauses and absolute
byte positions of the PRO-/CLM-/CLMI-/PFX-/CASET- fields are unknown.  Where
a value cannot be proven from the code it is marked ``[UNCERTAIN ...]`` and
every fabricated sample value is suffixed ``(illus.)`` for *illustrative*.

Only the match-report record (WS-MATCH-OUT, file CASE-PCF-MATCH) is fully
defined inside the program, so that record's PICTURE clauses and byte
positions are exact.

Requirements
------------
    pip install openpyxl        (openpyxl is not in the Python stdlib)

Usage
-----
    python3 generate_caspcfnj_mapping.py
"""

import os
import re
import sys

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "ERROR: openpyxl is required.  Install it with:  pip install openpyxl\n"
    )
    raise

HERE = os.path.dirname(os.path.abspath(__file__))
COBOL = os.path.join(HERE, "CASPCFNJ")
OUT_XLSX = os.path.join(HERE, "CASPCFNJ_1x1_Field_Mapping.xlsx")

# Copybook not in repo marker (kept short so columns stay readable).
NA_PIC = "[UNCERTAIN: FDPCF601 not in repo]"
NA_PIC_PRO = "[UNCERTAIN: CLMPREFX not in repo]"
NA_POS = "[UNCERTAIN: copybook not in repo]"

# ---------------------------------------------------------------------------
# 1.  COBOL parsing helpers
# ---------------------------------------------------------------------------
VERBS = {
    "MOVE", "IF", "PERFORM", "ADD", "WRITE", "READ", "INITIALIZE", "COMPUTE",
    "DISPLAY", "SET", "INSPECT", "UNSTRING", "EVALUATE", "WHEN", "ELSE",
    "END-IF", "GO", "CONTINUE", "ON", "END-ADD", "END-EVALUATE",
    "END-PERFORM", "END-READ", "CLOSE", "OPEN", "STOP",
}


def read_active_tokens(path):
    """Return a list of (token, line_number) for every active code token.

    Mainframe fixed-format rules used by this source file:
      * columns 1-6  -> change-flag / sequence area (ignored)
      * column  7    -> indicator ('*' or '/' = comment line)
      * columns 8+   -> COBOL Area A / Area B code
    """
    with open(path, "r", newline="") as fh:
        raw = fh.read().split("\n")

    tokens = []
    for lineno, line in enumerate(raw, start=1):
        line = line.rstrip("\r")
        if len(line) < 8:
            continue
        indicator = line[6]
        if indicator in ("*", "/"):
            continue
        code = line[7:]
        if not code.strip():
            continue
        for tok in code.split():
            tokens.append((tok, lineno))
    return tokens


def parse_moves(tokens):
    """Yield (lineno, source, target) for every active ``MOVE a TO b`` pair."""
    moves = []
    i, n = 0, len(tokens)
    while i < n:
        tok, ln = tokens[i]
        if tok == "MOVE" and i + 1 < n:
            source = tokens[i + 1][0]
            j = i + 2
            while j < n and tokens[j][0] not in ("TO", "MOVE"):
                source += " " + tokens[j][0]
                j += 1
            if j < n and tokens[j][0] == "TO":
                targets, k = [], j + 1
                while k < n and tokens[k][0] not in VERBS:
                    t = tokens[k][0]
                    targets.append(t)
                    if t.endswith("."):
                        break
                    k += 1
                tgt = " ".join(targets).rstrip(".")
                moves.append((ln, source.strip(), tgt.strip()))
                i = k
                continue
        i += 1
    return moves


# ---------------------------------------------------------------------------
# 2.  Source-area / input-format classification
# ---------------------------------------------------------------------------
def source_area(src):
    """Map a source field name to its input copybook / area."""
    s = src.upper()
    if s.startswith("PFX-"):
        return "TPLPREFX (PFX) - input prefix"
    if s.startswith("CLMI-"):
        if "CLIENT-DATA" in s:
            return "FDPCF602 client remainder"
        return "FDPCF602 (CLMI) - HMS-600 body"
    if s.startswith("CASET-") or s.startswith("CASE-"):
        return "NCTCASE (CASET) - case table"
    if s.startswith(("CA-", "CB-", "CC-", "CD-")):
        return "Client-data (FDNJTPC5/4, FDNJ5/4INS)"
    if s.startswith("WS-SAVE-CREATE"):
        return "CNTL-CARDS control card"
    if s.startswith("WS-"):
        return "WORKING-STORAGE (derived)"
    if s.startswith("'") or s[:1].isdigit() or s in ("SPACES", "ZEROS", "ZERO"):
        return "Literal / constant"
    return "WORKING-STORAGE (derived)"


def fmt_flag(area, kind):
    """Return the source field token for a given input-format column, else ''."""
    return area if kind in area else ""


# ---------------------------------------------------------------------------
# 3.  Curated per-target annotations (classification / samples / comments)
#     Keyed by output target field.  Everything here is tied to a real line.
# ---------------------------------------------------------------------------
# Worked-example scenario (single consistent input -> output record):
#   Recipient MA#      : 100200300
#   ICN                : 20152740001          Former ICN : 20150010002
#   HMS case key       : NJ0001234567         Client id  : CLT000765432
#   Control-card source: NJ
#   CASET incident date: 2015-03   -> WS-INCIDENT-DATE 20150300 (DD not parsed)
#   CASET thru date    : 2016-12-31-> WS-CLM-THRU-DATE 20161231
#   PFX date-of-service: 20150615  (>= 20150301 and <= 20161231  -> matches)
#   PFX trans type     : A         PFX exit-from-ref-status : Y
#   File/version       : MAMA / 06  claim type 01 -> client data = CA (FDNJTPC5)
#   Tot MA paid        : 00000001234.56
#   from-date 20150615 < 20151001  -> CLM-CDE-ICD-VERSION '09'
#
# Each entry: target -> (mapping_type, sample_in, sample_out, comment)
ANNOT = {
    # ---- PRO- prefix (CLMPREFX, output claim prefix) --------------------
    "PRO-RECIPIENT-ID-NUM": ("direct MOVE (renamed)", "100200300 (illus.)",
        "100200300 (illus.)", "Recipient Medicaid # from matched PCF claim."),
    "PRO-HMS-CASE-KEY": ("direct MOVE (renamed, from case table)",
        "NJ0001234567 (illus.)", "NJ0001234567 (illus.)",
        "From matched NCTCASE table entry CASET-HMS-CASE-KEY(SUB-I)."),
    "PRO-CLIENT-ID": ("direct MOVE (renamed, from case table)",
        "CLT000765432 (illus.)", "CLT000765432 (illus.)",
        "From NCTCASE CASET-HMS-CLIENT-ID(SUB-I).  Added chg 0014."),
    "PRO-CREATE-SOURCE": ("direct MOVE (control-card value)", "NJ (illus.)",
        "NJ (illus.)",
        "WS-SAVE-CREATE-SOURCE loaded from CNTL-CARDS card tag '1' (L428-430)."),
    "PRO-ICN": ("1x1 identity + conditional derived (ICN+suffix)",
        "20152740001 (illus.)", "20152740001 (illus.)",
        "Base CLMI-ICN; may be rebuilt as ICN(17)+HMS-ICN-SUFFIX(02) at L706-718."),
    "PRO-FORMER-ICN": ("1x1 identity", "20150010002 (illus.)",
        "20150010002 (illus.)", "CLMI-FORMER-ICN."),
    "PRO-XACTION-STATUS": ("1x1 identity", "P (illus.)", "P (illus.)",
        "CLMI-XACTION-STATUS."),
    "PRO-CLM-FROM-DATE": ("direct MOVE (renamed)", "20150615 (illus.)",
        "20150615 (illus.)",
        "PFX-APP-DATE-OF-SERVICE (YYYYMMDD).  Drives ICD version at L726."),
    "PRO-CLAIM-TRANS-TYPE": ("direct MOVE (renamed)", "A (illus.)",
        "A (illus.)", "PFX-NET-CLAIM-TRANS-TYPE."),
    "PRO-INCIDENT-DATE": ("derived/transformed (date reformat)",
        "2015-03 (illus.)", "20150300 (illus.)",
        "WS-INCIDENT-DATE built by UNSTRING of CASET-INCIDENT-DATE 'YYYY-MM' "
        "(L986); DD not parsed so =00 here (compare path forces DD=01)."),
    "PRO-CLM-THRU-DATE": ("derived/transformed (date reformat)",
        "2016-12-31 (illus.)", "20161231 (illus.)",
        "WS-CLM-THRU-DATE from UNSTRING of CASET-CLAIMS-THRU-DATE; "
        "SPACES -> '99999999' (L993-999)."),

    # ---- CLM- body overrides / derived ---------------------------------
    "CLM-PROCEDURE-CODE-7": ("derived/transformed (resize 5->7; crosswalk)",
        "99213 (illus.)", "99213   (illus.)",
        "Base CLMI-PROCEDURE-CODE-5 (L574); OVERRIDDEN from client-data "
        "proc code by file/version & claim type in 3030 (see Sheet 2)."),
    "CLM-PROCEDURE-CODE-MOD1": ("1x1 identity; override SPACES",
        "25 (illus.)", "  (SPACES)",
        "CLMI base (L576); set to SPACES in client-data paths (L782/810/890/967)."),
    "CLM-PROCEDURE-CODE-MOD2": ("1x1 identity; override SPACES",
        "59 (illus.)", "  (SPACES)",
        "CLMI base (L578); set to SPACES in client-data paths."),
    "CLM-PRI-DX": ("derived/transformed (crosswalk by version/claim type)",
        "25000 (illus.)", "25000  (illus.)",
        "Base CLMI-PRI-DX (L602); OVERRIDDEN from client-data diag(1) (see Sheet 2)."),
    "CLM-SEC-DX": ("derived/transformed (crosswalk by version/claim type)",
        "4019 (illus.)", "4019   (illus.)",
        "Base CLMI-SEC-DX (L603); OVERRIDDEN from client-data diag(2)."),
    "CLM-DX-3": ("derived/transformed (crosswalk by version/claim type)",
        "2720 (illus.)", "2720   (illus.)",
        "Base CLMI-DX-3 (L675); OVERRIDDEN from client-data diag(3)."),
    "CLM-DX-4": ("derived/transformed (crosswalk by version/claim type)",
        "V5867 (illus.)", "V5867  (illus.)",
        "Base CLMI-DX-4 (L676); OVERRIDDEN from client-data diag(4)."),
    "CLM-DX-5": ("derived/transformed (crosswalk by version/claim type)",
        "41400 (illus.)", "41400  (illus.)",
        "Base CLMI-DX-5 (L677); OVERRIDDEN from client-data diag(5)."),
    "CLM-ICN": ("1x1 identity + conditional derived (ICN+suffix)",
        "20152740001 (illus.)", "20152740001 (illus.)",
        "Base CLMI-ICN (L601); rebuilt as ICN(17)+suffix(02) at L719 under same "
        "condition as PRO-ICN."),
    "CLM-CDE-ICD-VERSION": ("derived (date-based constant)", "n/a",
        "09 (illus.)",
        "'09' when PRO-CLM-FROM-DATE < 20151001 else '10' (L726-730).  "
        "No CLMI source field."),
    "CLM-PROV-OF-SVC-NUM": ("1x1 identity (conditionally substituted source)",
        "09999996 (illus.)", "00123456 (illus.)",
        "CLMI-PROV-OF-SVC-NUM; if '09999996' & contract '0032600' the source is "
        "first replaced by CLMI-PAY-TO-PROV-NUM (L564-568)."),
    "CLM-TOT-MA-PAID-HDR": ("1x1 identity", "00000001234.56 (illus.)",
        "00000001234.56 (illus.)",
        "CLMI-TOT-MA-PAID-HDR; also accumulated into WS-TOT-PCF-MA-PAID (L739)."),
    # ---- CLM- body plain copies pinned to the worked example scenario ----
    "CLM-PCF-MA-NUM": ("1x1 identity", "100200300 (illus.)",
        "100200300 (illus.)", "CLMI-PCF-MA-NUM (recipient Medicaid #)."),
    "CLM-CLM-TYPE": ("1x1 identity", "01 (illus.)", "01 (illus.)",
        "CLMI-CLM-TYPE; 01 = institutional (drives the diag/proc crosswalk)."),
    "CLM-FORMER-ICN": ("1x1 identity", "20150010002 (illus.)",
        "20150010002 (illus.)", "CLMI-FORMER-ICN (matches PRO-FORMER-ICN)."),
    "CLM-XACTION-STATUS": ("1x1 identity", "P (illus.)", "P (illus.)",
        "CLMI-XACTION-STATUS (matches PRO-XACTION-STATUS)."),
    "CLM-PCF-CONTRACT-NUM": ("1x1 identity", "0032600 (illus.)",
        "0032600 (illus.)",
        "CLMI-PCF-CONTRACT-NUM; '0032600' triggers DSS/ICN/prov special logic."),
    "CLM-PAY-TO-PROV-NUM": ("1x1 identity", "00123456 (illus.)",
        "00123456 (illus.)", "CLMI-PAY-TO-PROV-NUM."),
    "CLM-CLAIM-FROM-DOS": ("1x1 identity", "0150615 (illus.)",
        "0150615 (illus.)",
        "CLMI-CLAIM-FROM-DOS; numeric 0YYMMDD per L459-465 (e.g. 0150615=2015)."),
    # ---- Match-report detail fields (WS-MATCH-OUT) ----------------------
    "MATCH-CASE-ID-OUT": ("direct MOVE (detail) / constant (header)",
        "100200300 (illus.)", "100200300 (illus.)",
        "Header row value 'CASE ID'; detail row = WS-CASE-ID (L1527)."),
    "MATCH-TOT-PCF-REC-OUT": ("derived (edited count) / constant (header)",
        "1 (illus.)", "1 (illus.)",
        "Header 'PCF RECORDS MATCHED'; detail = edited WS-TOT-PCF-REC-MATCH "
        "(ZZZZ9, leading spaces stripped, L1529-1534)."),
    "MATCH-TOT-PCF-MA-PAID-OUT": ("derived (edited $$) / constant (header)",
        "1234.56 (illus.)", "$1,234.56 (illus.)",
        "Header 'PCF TOT $$ MA PAID'; detail = edited WS-TOT-PCF-MA-PAID "
        "($$$,$$$,$$$,$$9.99, L1536-1541)."),
}

# Exact layout of the match-report record WS-MATCH-OUT (fully defined in-program,
# L226-235).  (target, picture, byte_start, byte_end, value_or_source)
MATCH_FIELDS = [
    ("FILLER-1",                 "X(03)",  1,  3,  "VALUE ' * '"),
    ("MATCH-CASE-ID-OUT",        "X(20)",  4, 23,  "VALUE 'CASE ID' / WS-CASE-ID"),
    ("FILLER-2",                 "X(03)", 24, 26,  "VALUE ' * '"),
    ("MATCH-TOT-PCF-REC-OUT",    "X(19)", 27, 45,  "VALUE 'PCF RECORDS MATCHED'"),
    ("FILLER-3",                 "X(03)", 46, 48,  "VALUE ' * '"),
    ("MATCH-TOT-PCF-MA-PAID-OUT","X(18)", 49, 66,  "VALUE 'PCF TOT $$ MA PAID'"),
    ("FILLER-4",                 "X(02)", 67, 68,  "VALUE ' *'"),
    ("(unused tail)",            "X(12)", 69, 80,  "record is X(80); 69-80 spaces"),
]


def default_annot(target, source):
    """Classification + illustrative samples for plain 1x1 identity copies."""
    base = target[4:] if target.startswith("CLM-") else target
    # type hint from the field name for a type-consistent illustrative sample.
    u = base.upper()
    if any(k in u for k in ("DATE", "-DOS", "-DOB", "DATE-TIME")):
        s = "20150615 (illus.)"
    elif any(k in u for k in ("PAID", "BILLED", "ALLOWED", "DOLLARS",
                              "INCOME", "COINS", "DEDUCT", "RATE")):
        s = "00000001234.56 (illus.)"
    elif any(k in u for k in ("DAYS", "CNT", "-CTR", "SEQ", "CHARGES",
                              "SEGS", "VISITS", "NUM")):
        s = "00005 (illus.)"
    elif "LAST-NAME" in u:
        s = "DOE (illus.)"
    elif "FIRST-NAME" in u:
        s = "JANE (illus.)"
    elif "MID-INIT" in u:
        s = "Q (illus.)"
    elif u.endswith("-SEX"):
        s = "F (illus.)"
    elif any(k in u for k in ("-IND", "-SW", "-FLAG", "-STATUS", "-TYPE",
                              "-CODE", "-CD", "OF-CARE")):
        s = "1 (illus.)"
    else:
        s = "ABC123 (illus.)"
    return ("1x1 identity", s, s,
            "Field-for-field copy (same base name) from input HMS-600 to output "
            "HMS-601; done per-field because the diag area grew 600->601 bytes.")


# ---------------------------------------------------------------------------
# 4.  Build the ordered output-field mapping
# ---------------------------------------------------------------------------
def build_rows():
    tokens = read_active_tokens(COBOL)
    moves = parse_moves(tokens)

    # Primary assignments inside 3020 (the record build, L540-L704) plus the
    # ICD-version set at L726-730.  We take the FIRST active assignment for each
    # PRO-/CLM- target so the field appears in copybook (code) order.
    pro_order, clm_order = [], []
    primary = {}        # target -> (source, line)
    for ln, src, tgt in moves:
        t = tgt.split("(")[0].strip()      # drop any subscript/ref-mod
        if not (t.startswith("PRO-") or t.startswith("CLM-")):
            continue
        if t not in primary:
            primary[t] = (src, ln)
            (pro_order if t.startswith("PRO-") else clm_order).append(t)

    rows = []
    fieldno = 0

    def emit(target, out_copybook, picture, byte_loc, out_path, src, src_cpy,
             line, annot):
        nonlocal fieldno
        fieldno += 1
        mtype, s_in, s_out, comment = annot
        area = source_area(src) if src else ""
        rows.append({
            "no": fieldno,
            "out_cpy": out_copybook,
            "target": target,
            "pic": picture,
            "byte": byte_loc,
            "mtype": mtype,
            "src_cpy": src_cpy,
            "src": src,
            "s_in": s_in,
            "s_out": s_out,
            "out_claim": "X" if out_path == "claim" else "",
            "out_match": "X" if out_path == "match" else "",
            "in_pfx":  src if area.startswith("TPLPREFX") else "",
            "in_clmi": src if area.startswith("FDPCF602") else "",
            "in_cli":  src if area.startswith("Client-data") else "",
            "in_case": src if area.startswith("NCTCASE") else "",
            "in_card": src if "CNTL-CARDS" in area else "",
            "in_wsc":  src if (area.startswith("WORKING-STORAGE")
                               or area.startswith("Literal")) else "",
            "line": "L%s" % line if line else "",
            "comment": comment,
        })

    # --- PRO- prefix fields (output copybook CLMPREFX) -------------------
    for t in pro_order:
        src, ln = primary[t]
        src_cpy = {
            "CLMI": "FDPCF602 (CLMI)",
            "CASE": "NCTCASE (CASET)",
            "PFX-": "TPLPREFX (PFX)",
            "WS-S": "CNTL card",
            "WS-I": "WORKING-STORAGE",
            "WS-C": "WORKING-STORAGE",
        }.get(src[:4], "WORKING-STORAGE")
        annot = ANNOT.get(t, default_annot(t, src))
        emit(t, "CLMPREFX (PRO)", NA_PIC_PRO, NA_POS, "claim", src, src_cpy,
             ln, annot)

    # Note row: remaining PRO fields initialised to spaces/zeros.
    fieldno += 1
    rows.append({
        "no": fieldno, "out_cpy": "CLMPREFX (PRO)",
        "target": "(other PRO-CLMPRFX fields)", "pic": NA_PIC_PRO,
        "byte": NA_POS, "mtype": "default SPACES/ZEROS",
        "src_cpy": "-", "src": "INITIALIZE PRO-CLMPRFX",
        "s_in": "n/a", "s_out": "SPACES / ZEROS",
        "out_claim": "X", "out_match": "", "in_pfx": "", "in_clmi": "",
        "in_cli": "", "in_case": "", "in_card": "", "in_wsc": "INITIALIZE",
        "line": "L542",
        "comment": "PRO-CLMPRFX is INITIALIZE'd each matched record (L542); any "
                   "prefix field not explicitly moved is left SPACES/ZEROS.  "
                   "Full field list unavailable - CLMPREFX not in repo.",
    })

    # --- CLM- body fields (output copybook FDPCF601) ---------------------
    for t in clm_order:
        src, ln = primary[t]
        annot = ANNOT.get(t, default_annot(t, src))
        emit(t, "FDPCF601 (CLM)", NA_PIC, NA_POS, "claim", src,
             "FDPCF602 (CLMI)" if src.startswith("CLMI") else
             ("Client-data" if src.startswith(("CA-", "CB-", "CC-", "CD-"))
              else "literal/WS"),
             ln, annot)

    # CLM-CDE-ICD-VERSION is set from a literal, not via a PRO-/CLM- primary
    # MOVE captured above only if present; ensure it is included exactly once.
    if "CLM-CDE-ICD-VERSION" not in primary:
        emit("CLM-CDE-ICD-VERSION", "FDPCF601 (CLM)", NA_PIC, NA_POS, "claim",
             "'09' / '10'", "literal", 727, ANNOT["CLM-CDE-ICD-VERSION"])

    # Note row: remaining FDPCF601 body fields that the program never populates.
    fieldno += 1
    rows.append({
        "no": fieldno, "out_cpy": "FDPCF601 (CLM)",
        "target": "(other FDPCF601 fields not referenced in code)",
        "pic": NA_PIC, "byte": NA_POS, "mtype": "not populated",
        "src_cpy": "-", "src": "",
        "s_in": "n/a", "s_out": "carry-over / undefined",
        "out_claim": "X", "out_match": "", "in_pfx": "", "in_clmi": "",
        "in_cli": "", "in_case": "", "in_card": "", "in_wsc": "",
        "line": "",
        "comment": "CLM-HMS-601 is NOT re-initialised per record (only PRO prefix "
                   "is).  Any FDPCF601 field not in the MOVE list keeps the prior "
                   "record's value.  Complete field list unavailable - FDPCF601 "
                   "not in repo.  [UNCERTAIN]",
    })

    # --- Match-report record fields (output copybook WS-MATCH-OUT) -------
    for (tgt, pic, b0, b1, val) in MATCH_FIELDS:
        annot = ANNOT.get(tgt, (
            "hardcoded constant", "n/a", val.replace("VALUE ", "").strip("'"),
            "Literal header/separator defined in WS-MATCH-OUT."))
        fieldno += 1
        rows.append({
            "no": fieldno, "out_cpy": "WS-MATCH-OUT (MATCH-RECORD X(80))",
            "target": tgt, "pic": pic, "byte": "%d-%d" % (b0, b1),
            "mtype": annot[0], "src_cpy": "in-program WS", "src": val,
            "s_in": annot[1], "s_out": annot[2],
            "out_claim": "", "out_match": "X",
            "in_pfx": "", "in_clmi": "", "in_cli": "", "in_case": "",
            "in_card": "", "in_wsc": val,
            "line": "L226-235",
            "comment": annot[3],
        })

    return rows


# ---------------------------------------------------------------------------
# 5.  Workbook styling helpers
# ---------------------------------------------------------------------------
HDR_FILL = PatternFill("solid", fgColor="1F4E78")
HDR_FONT = Font(bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")
WRAP = Alignment(vertical="top", wrap_text=True)
TOP = Alignment(vertical="top")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
ALT_FILL = PatternFill("solid", fgColor="F2F6FC")


def style_header(ws, row_idx, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row_idx, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER


def finalize(ws, header_row, ncols, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    # borders + wrap + zebra for data rows
    for r in range(header_row + 1, ws.max_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.alignment = WRAP
            cell.border = BORDER
        if (r - header_row) % 2 == 0:
            for c in range(1, ncols + 1):
                ws.cell(row=r, column=c).fill = ALT_FILL


# ---------------------------------------------------------------------------
# 6.  Sheet builders
# ---------------------------------------------------------------------------
def sheet_field_mapping(wb, rows):
    ws = wb.active
    ws.title = "Field Mapping"
    ws["A1"] = ("CASPCFNJ - 1x1 Field Mapping  (one row per output field).  "
                "Mappings trace to real PROCEDURE DIVISION lines in CASPCFNJ.  "
                "PIC/byte for PRO-/CLM-/CLMI- fields are [UNCERTAIN] because the "
                "copybooks (CLMPREFX/FDPCF601/FDPCF602) are not in the repo; "
                "match-report PICs are exact.  All fabricated samples = (illus.).")
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = WRAP
    ws.merge_cells("A1:S1")
    ws.row_dimensions[1].height = 54

    headers = [
        "Field No", "Output Copybook", "Target Field", "Picture",
        "Byte Location", "Mapping Type", "Source Copybook", "Source Field",
        "Sample Input", "Sample Output",
        "Out: SRCPCF-OUT", "Out: CASE-PCF-MATCH",
        "In: PFX/TPLPREFX", "In: CLMI/FDPCF602", "In: CLIENT-DATA/FDNJ*",
        "In: CASE/NCTCASE", "In: CNTL/WS/Const",
        "Code Line", "Comments",
    ]
    hr = 2
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    style_header(ws, hr, len(headers))

    for row in rows:
        ws.append([
            row["no"], row["out_cpy"], row["target"], row["pic"], row["byte"],
            row["mtype"], row["src_cpy"], row["src"], row["s_in"], row["s_out"],
            row["out_claim"], row["out_match"],
            row["in_pfx"], row["in_clmi"], row["in_cli"], row["in_case"],
            row["in_card"] or row["in_wsc"],
            row["line"], row["comment"],
        ])

    widths = [8, 20, 30, 24, 22, 32, 20, 28, 20, 20, 13, 15, 18, 20, 20, 18,
              18, 10, 54]
    finalize(ws, hr, len(headers), widths)
    return ws


def sheet_overrides(wb):
    ws = wb.create_sheet("Overrides & Crosswalks")
    ws["A1"] = ("Sheet 2 - Overrides & Crosswalks.  Conditional re-assignments "
                "applied AFTER the base record build (paragraph 3030 and the ICN "
                "reformat / PROV substitution logic).")
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = WRAP
    ws.merge_cells("A1:G1")
    ws.row_dimensions[1].height = 36

    headers = ["Path/Format", "Source Field", "Target Field",
               "Assigned/Translated Value", "Condition", "Sample In -> Out",
               "Description"]
    hr = 2
    for c, h in enumerate(headers, start=1):
        ws.cell(row=hr, column=c, value=h)
    style_header(ws, hr, len(headers))

    data = [
        # Diagnosis / proc crosswalk by file + version + claim type
        ("MAMA v06 (client data CA / FDNJTPC5)",
         "CA-A-DIAG-CDE(1..5), CA-A-PROC-CDE",
         "CLM-PRI-DX, CLM-SEC-DX, CLM-DX-3/4/5, CLM-PROCEDURE-CODE-7",
         "diag(1..5) -> 5 DX fields; proc -> PROC-CODE-7; MOD1/MOD2 -> SPACES",
         "PFX-SYS-HMS-ASSIGN-FILE='MAMA' AND PFX-SYS-VERSION='06' AND "
         "CLMI-CLM-TYPE in (01,02,03,04,06,07,09,13,14,15,18,20,21,23)",
         "CA-A-DIAG-CDE(1)=25000 -> CLM-PRI-DX 25000 (illus.)",
         "L764-789.  Institutional TPC v5 client layout."),
        ("MAMA/CCAR v05 (client data CB / FDNJTPC4)",
         "CB-A-DIAG-CDE(1..5), CB-A-PROC-CDE",
         "CLM-PRI-DX, CLM-SEC-DX, CLM-DX-3/4/5, CLM-PROCEDURE-CODE-7",
         "diag(1..5) -> 5 DX fields; proc -> PROC-CODE-7; MOD1/MOD2 -> SPACES",
         "PFX-SYS-HMS-ASSIGN-FILE in ('MAMA','CCAR') AND PFX-SYS-VERSION='05' "
         "AND CLMI-CLM-TYPE in (01..23 list)",
         "CB-A-DIAG-CDE(1)=25000 -> CLM-PRI-DX 25000 (illus.)",
         "L791-816.  TPC v4 client layout."),
        ("ENCT v05 (client data CC / FDNJ5INS)",
         "CC-HNI-DIAG / CC-OP-DIAG / CC-PR-DIAG / CC-HH-DIAG / CC-TR-DIAG / "
         "CC-VI-DIAG, CC-E-PROC-CDE",
         "CLM-PRI-DX, CLM-SEC-DX, CLM-DX-3/4/5, CLM-PROCEDURE-CODE-7",
         "DX source chosen by claim type via EVALUATE; proc -> PROC-CODE-7",
         "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='05'; EVALUATE "
         "CLMI-CLM-TYPE WHEN 01/02/03/04/06/07/18",
         "CC-HNI-DIAG(1)=25000 -> CLM-PRI-DX 25000 (illus.)",
         "L819-892.  Encounter v5.  Proc set only if CLMI-CLM-TYPE not = '12'."),
        ("ENCT v04 (client data CD / FDNJ4INS)",
         "CD-HNI-DIAG / CD-OP-DIAG / CD-PR-DIAG / CD-HH-DIAG / CD-TR-DIAG / "
         "CD-VI-DIAG, CD-E-PROC-CDE",
         "CLM-PRI-DX, CLM-SEC-DX, CLM-DX-3/4/5, CLM-PROCEDURE-CODE-7",
         "DX source chosen by claim type via EVALUATE; proc -> PROC-CODE-7",
         "PFX-SYS-HMS-ASSIGN-FILE='ENCT' AND PFX-SYS-VERSION='04'; EVALUATE "
         "CLMI-CLM-TYPE WHEN 01/02/03/04/06/07/18",
         "CD-HNI-DIAG(1)=25000 -> CLM-PRI-DX 25000 (illus.)",
         "L895-969.  Encounter v4.  Proc set only if CLMI-CLM-TYPE not = '12'."),
        ("Any other file/version",
         "-", "CLM-PRI-DX..DX-5, CLM-PROCEDURE-CODE-7",
         "unchanged (keep CLMI base values)",
         "No file/version branch matched",
         "base CLMI values retained (illus.)",
         "L970-972 PERFORM 5500 only increments OTHER-VERS counter."),
        ("ICD version (all paths)",
         "PRO-CLM-FROM-DATE", "CLM-CDE-ICD-VERSION",
         "'09' (ICD-9) or '10' (ICD-10)",
         "PRO-CLM-FROM-DATE < 20151001 -> '09' else '10'",
         "20150615 -> 09 ; 20151105 -> 10 (illus.)",
         "L726-730."),
        ("ICN suffix reformat",
         "CLMI-ICN (17) + CLMI-PCF-HMS-ICN-SUFFIX (02)",
         "PRO-ICN, CLM-ICN",
         "WS-ICN-GROUP-19 = ICN(1:17) || suffix(2)",
         "CLMI-PM-USER-AREA(1:2) in ('PB','DT') AND contract='0032600' AND "
         "PM-USER-AREA(27:3) not='DSS' AND suffix numeric and <> 0",
         "ICN 20152740001 + suffix 07 -> 2015274000100007 (illus.)",
         "L706-723."),
        ("Provider-of-service substitution",
         "CLMI-PAY-TO-PROV-NUM", "CLM-PROV-OF-SVC-NUM",
         "PAY-TO-PROV-NUM copied into PROV-OF-SVC-NUM",
         "CLMI-PROV-OF-SVC-NUM='09999996' AND contract='0032600'",
         "09999996 -> 00123456 (illus.)",
         "L564-568.  (Both = 09999996 instead causes a skip, L471-476.)"),
        ("Create source (control card)",
         "CARD-DATA(1:2)", "PRO-CREATE-SOURCE",
         "2-char source from JCL control card tag '1'",
         "CNTL-CARDS record with CARD-TAG='1'",
         "card '1..NJ' -> PRO-CREATE-SOURCE 'NJ' (illus.)",
         "L428-430, L552-553."),
        ("Match-report edited values",
         "WS-TOT-PCF-REC-MATCH / WS-TOT-PCF-MA-PAID",
         "MATCH-TOT-PCF-REC-OUT / MATCH-TOT-PCF-MA-PAID-OUT",
         "numeric-edited then left-justified (leading spaces stripped)",
         "On each 2100-WRITE-CASE-PCF-MATCH",
         "1 -> '1' ; 1234.56 -> '$1,234.56' (illus.)",
         "L1529-1541."),
    ]
    for d in data:
        ws.append(list(d))
    widths = [34, 34, 34, 36, 46, 34, 48]
    finalize(ws, hr, len(headers), widths)
    return ws


def sheet_routing(wb):
    ws = wb.create_sheet("Routing and Format Logic")
    ws["A1"] = "Sheet 3 - Routing / Format Logic"
    ws["A1"].font = TITLE_FONT
    ws.row_dimensions[1].height = 22

    bullets = [
        ("Program role",
         "Reformat + Filter/Match + Multi-output.  Reads PCF claims (SRCPCF-IN) "
         "and an open-case extract (CASEFL-IN), matches claims to OPEN cases by "
         "recipient Medicaid # and service-date window, reformats the matched "
         "claim from HMS-600 (FDPCF602) to HMS-601 (FDPCF601, enlarged diag), "
         "and writes two outputs."),
        ("Inputs",
         "SRCPCF-IN  (CLMI-RECORD, VB up to X(32752); prefix PFX 127 + HMS-600 "
         "600 + client-data 32025).  CASEFL-IN (CASE-RECORD X(384), NCTCASE).  "
         "CNTL-CARDS (SYS004, X(80)) supplies the 2-char create-source."),
        ("Outputs",
         "(1) SRCPCF-OUT (CLMO-RECORD X(754)) = CLMPREFX(PRO) + HMS-601(CLM) - "
         "one reformatted claim per matching open case.  (2) CASE-PCF-MATCH "
         "(MATCH-RECORD X(80)) - a human-readable match summary: header lines, "
         "one detail line per matched case-id, and a trailer."),
        ("How many outputs per input",
         "A single PCF claim can write ZERO, ONE or MANY SRCPCF-OUT records: "
         "3020-READ-CASE-TABLE loops the loaded case table (PERFORM VARYING "
         "SUB-I 1..TABLE-ENTRIES) and writes once for every table entry that is "
         "OPEN and whose date window contains the claim DOS."),
        ("Match / write condition (per case-table entry, L537-741)",
         "WRITE occurs only when: CASET-CASE-STATUS-CODE(SUB-I) = 'O' or X'96' "
         "AND PFX-APP-DATE-OF-SERVICE >= WS-INCIDENT-DATE-NEW-RE AND "
         "PFX-APP-DATE-OF-SERVICE <= WS-CLM-THRU-DATE-N."),
        ("Recipient synchronisation (L445-504)",
         "Case file and claim file are read in recipient order.  When "
         "CASE-RECIPIENT-ID-NUM < PFX-APP-MEDICAID-NO the case file is advanced; "
         "when equal a new case table is loaded; a matched case-id's summary is "
         "written when the recipient changes."),
        ("Skip / reject conditions",
         "1) PFX-SYS-EXIT-FROM-REF-STATUS not = 'Y'  -> skip claim (L452-455).  "
         "2) contract '0032600' + PM-USER-AREA(27:3)='DSS' + from-DOS in "
         "(0040001..0899999) -> skip, count REC-SKIP-DSS (L457-469).  "
         "3) PROV-OF-SVC-NUM = PAY-TO-PROV-NUM = '09999996' -> skip, count "
         "REC-SKIP-PROV (L471-476).  4) Claim whose recipient matches no open "
         "case simply writes nothing."),
        ("Stop condition",
         "Main loop runs 2000-MAINLINE UNTIL PCF-EOF.  Processing stops at end "
         "of the PCF (claim) file; the case file may not be read to completion "
         "(noted in 9000-TERMINATION display)."),
        ("No bulk move",
         "The whole-record copy (MOVE CLMI-HMS-600 TO CLM-HMS-601) is commented "
         "out at L569-570; the record is rebuilt field-by-field because the "
         "output diag area is one byte larger (600 -> 601)."),
    ]
    hr = 2
    ws.cell(row=hr, column=1, value="Topic")
    ws.cell(row=hr, column=2, value="Explanation")
    style_header(ws, hr, 2)
    for topic, text in bullets:
        ws.append([topic, text])
    finalize(ws, hr, 2, [34, 118])
    return ws


def sheet_samples(wb):
    ws = wb.create_sheet("Sample Records")
    ws["A1"] = ("Sheet 4 - Sample Records (one worked end-to-end example).  All "
                "values are illustrative because field PICs live in copybooks "
                "not present in the repo.")
    ws["A1"].font = TITLE_FONT
    ws["A1"].alignment = WRAP
    ws.merge_cells("A1:C1")
    ws.row_dimensions[1].height = 34

    hr = 2
    for c, h in enumerate(["Record / Field", "Illustrative Value", "Notes"], 1):
        ws.cell(row=hr, column=c, value=h)
    style_header(ws, hr, 3)

    def section(title):
        ws.append([title, "", ""])
        r = ws.max_row
        for c in range(1, 4):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor="D9E1F2")
            ws.cell(row=r, column=c).font = Font(bold=True)

    section("INPUT 1 - PCF claim (SRCPCF-IN, format PFX + HMS-600 + client-data)")
    for k, v, n in [
        ("PFX-APP-MEDICAID-NO", "100200300 (illus.)", "recipient key"),
        ("PFX-APP-DATE-OF-SERVICE", "20150615", "YYYYMMDD; inside case window"),
        ("PFX-NET-CLAIM-TRANS-TYPE", "A", "add"),
        ("PFX-SYS-EXIT-FROM-REF-STATUS", "Y", "must be 'Y' to process"),
        ("PFX-SYS-HMS-ASSIGN-FILE / -VERSION", "MAMA / 06", "selects CA client data"),
        ("CLMI-PCF-MA-NUM", "100200300", "-> PRO-RECIPIENT-ID-NUM / CLM-PCF-MA-NUM"),
        ("CLMI-ICN", "20152740001", "-> PRO-ICN / CLM-ICN"),
        ("CLMI-FORMER-ICN", "20150010002", "-> PRO-FORMER-ICN / CLM-FORMER-ICN"),
        ("CLMI-CLM-TYPE", "01", "institutional -> CA diag/proc crosswalk"),
        ("CLMI-PROCEDURE-CODE-5", "99213", "base proc (overridden by CA-A-PROC-CDE)"),
        ("CLMI-PRI-DX / SEC-DX / DX-3/4/5", "25000 / 4019 / 2720 / V5867 / 41400",
         "base DX (overridden by CA-A-DIAG-CDE)"),
        ("CLMI-TOT-MA-PAID-HDR", "00000001234.56", "-> CLM-TOT-MA-PAID-HDR + summary"),
        ("CLMI-PCF-CONTRACT-NUM", "0032600", "used by DSS/ICN/prov logic"),
        ("CA-A-PROC-CDE", "99213", "client proc -> CLM-PROCEDURE-CODE-7"),
        ("CA-A-DIAG-CDE(1..5)", "25000 / 4019 / 2720 / V5867 / 41400",
         "client diags -> CLM-PRI-DX..CLM-DX-5"),
    ]:
        ws.append([k, v, n])

    section("INPUT 2 - open-case record (CASEFL-IN, NCTCASE)")
    for k, v, n in [
        ("CASE-RECIPIENT-ID-NUM", "100200300", "matches PFX-APP-MEDICAID-NO"),
        ("CASET-CASE-STATUS-CODE", "O", "open case -> eligible"),
        ("CASET-HMS-CASE-KEY", "NJ0001234567", "-> PRO-HMS-CASE-KEY"),
        ("CASET-HMS-CLIENT-ID", "CLT000765432", "-> PRO-CLIENT-ID"),
        ("CASET-INCIDENT-DATE", "2015-03", "-> WS-INCIDENT-DATE 20150300 / cmp 20150301"),
        ("CASET-CLAIMS-THRU-DATE", "2016-12-31", "-> WS-CLM-THRU-DATE 20161231"),
    ]:
        ws.append([k, v, n])

    section("INPUT 3 - control card (CNTL-CARDS / SYS004)")
    ws.append(["CARD-TAG / CARD-DATA", "1 / NJ", "CARD-TAG '1' -> create-source 'NJ'"])

    section("OUTPUT 1 - reformatted claim (SRCPCF-OUT, X(754))")
    for k, v, n in [
        ("PRO-RECIPIENT-ID-NUM", "100200300", "from CLMI-PCF-MA-NUM"),
        ("PRO-HMS-CASE-KEY", "NJ0001234567", "from matched case entry"),
        ("PRO-CLIENT-ID", "CLT000765432", "from matched case entry"),
        ("PRO-CREATE-SOURCE", "NJ", "from control card"),
        ("PRO-ICN", "20152740001", "from CLMI-ICN (no suffix rebuild here)"),
        ("PRO-CLM-FROM-DATE", "20150615", "from PFX-APP-DATE-OF-SERVICE"),
        ("PRO-INCIDENT-DATE", "20150300", "reformatted; DD=00"),
        ("PRO-CLM-THRU-DATE", "20161231", "reformatted"),
        ("CLM-PCF-MA-NUM", "100200300", "1x1"),
        ("CLM-CLM-TYPE", "01", "1x1"),
        ("CLM-PROCEDURE-CODE-7", "99213  ", "from CA-A-PROC-CDE (7 wide)"),
        ("CLM-PROCEDURE-CODE-MOD1/MOD2", "SPACES", "cleared in client-data path"),
        ("CLM-PRI-DX..CLM-DX-5", "25000 / 4019 / 2720 / V5867 / 41400",
         "from CA-A-DIAG-CDE(1..5)"),
        ("CLM-TOT-MA-PAID-HDR", "00000001234.56", "1x1"),
        ("CLM-CDE-ICD-VERSION", "09", "20150615 < 20151001"),
    ]:
        ws.append([k, v, n])

    section("OUTPUT 2 - match summary (CASE-PCF-MATCH, X(80))")
    for k, v, n in [
        ("Header line", " * CASE ID            * PCF RECORDS MATCHED * "
         "PCF TOT $$ MA PAID *", "written once at start (L437-439)"),
        ("Detail line", " * 100200300           * 1                  * "
         "$1,234.56         *", "one per matched case-id (illus. spacing)"),
        ("Trailer", "all '*' line + blank", "L1707-1716"),
    ]:
        ws.append([k, v, n])

    finalize(ws, hr, 3, [34, 44, 60])
    # darken the section rows' zebra back out (optional) - leave as is.
    return ws


# ---------------------------------------------------------------------------
# 7.  main
# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(COBOL):
        sys.stderr.write("ERROR: CASPCFNJ source not found next to this script.\n")
        sys.exit(1)

    rows = build_rows()
    wb = Workbook()
    sheet_field_mapping(wb, rows)
    sheet_overrides(wb)
    sheet_routing(wb)
    sheet_samples(wb)
    wb.save(OUT_XLSX)

    n_claim = sum(1 for r in rows if r["out_claim"] == "X")
    n_match = sum(1 for r in rows if r["out_match"] == "X")
    print("Wrote %s" % OUT_XLSX)
    print("  Sheets: %s" % ", ".join(wb.sheetnames))
    print("  Output-field rows: %d  (claim=%d, match=%d)"
          % (len(rows), n_claim, n_match))


if __name__ == "__main__":
    main()
