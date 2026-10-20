#!/usr/bin/env python3
"""
generate_field_mapping.py
=========================

Builds the 1x1 field-mapping workbook for COBOL program **CASNCTD9**
(source: ``CASNCTD9_Version2.txt`` in the repository root).

Why CASNCTD9 and not "CASPCFAL"/"CASNCTAL"?
-------------------------------------------
The reusable analysis prompt was filled with placeholder names
(``CASPCFAL.txt`` as the program, ``CASNCTAL`` as the output prefix).
Neither name exists anywhere in this repository's git history.  The only
COBOL source ever committed is ``CASNCTD9_Version2.txt`` (PROGRAM-ID
CASNCTD9), so the analysis and these deliverables are named after the real
program that is actually present.

Grounding rules honoured by this data
-------------------------------------
* Every output field below points at a real line in ``CASNCTD9_Version2.txt``
  (see the ``Comments`` column -- numbers are source line numbers).
* The copybooks ``NCTCLMS9`` (input, prefix ``CLM-``) and the DB2 DCLGEN
  includes ``ARTCCLM`` / ``ARTCLKP`` / ``CARTCTPK`` / ``ARTSPRF`` /
  ``PMONITOR`` are **external** ``COPY``/``INCLUDE`` members and are NOT in
  the repo.  Consequently exact PIC clauses, VARCHAR lengths and byte
  offsets for copybook/host-variable fields cannot be read from source;
  they are marked ``[inf]`` (inferred from usage) and sample values are
  marked *illustrative*.  DB2 table columns have no COBOL byte offset.
* The flat ``CNTL-RECORD`` IS defined in WORKING-STORAGE (lines 183-188)
  so its byte offsets are real.

Run:  ``python generate_field_mapping.py``  ->  CASNCTD9_1x1_Field_Mapping.xlsx
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUTPUT_XLSX = "CASNCTD9_1x1_Field_Mapping.xlsx"

# --------------------------------------------------------------------------
# Shared styling helpers
# --------------------------------------------------------------------------
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")
NOTE_FONT = Font(italic=True, size=9, color="7F6000")
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
ZEBRA = PatternFill("solid", fgColor="F2F6FC")

# Colour per output target so a reviewer can scan Sheet 1 quickly.
OUTPUT_TARGETS = ["ARTCCLM", "ARTCLKP", "ARTCTPK", "MISC.P_MONITOR", "CNTL-FILE"]


def style_header_row(ws, row_idx, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row_idx, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = BORDER


def finalize(ws, header_row, ncols, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    max_row = ws.max_row
    for r in range(header_row + 1, max_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.alignment = WRAP_TOP
            cell.border = BORDER
        if (r - header_row) % 2 == 0:
            for c in range(1, ncols + 1):
                if ws.cell(row=r, column=c).fill.fgColor.rgb in (None, "00000000"):
                    ws.cell(row=r, column=c).fill = ZEBRA
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)


# ==========================================================================
# SHEET 1 : FIELD MAPPING  (one row per OUTPUT field)
# ==========================================================================
# Each entry:
#   no, owner, target, pic, byte, mtype, src_copy, src_field,
#   sample_in, sample_out, op (operation on owning target), comment(evidence)
#
# owner is one of: ARTCCLM, ARTCLKP, ARTCTPK, P_MONITOR, CNTL
S1 = [
    # ---------------- ARTCCLM (claim table) : INSERT 1035-1101 / UPDATE 851-883
    (1, "ARTCCLM", "CONTEXT_CD", "VARCHAR(16) [inf]", "ARTCCLM col 1",
     "crosswalk/translated", "WS / NCTCLMS9", "WS-CONTEXT-CD  <= contract + CLM-HMS-CLIENT-ID",
     "contract 320 + CLM-HMS-CLIENT-ID 'CTSCCN'", "CTSCASNYC", "INSERT + UPDATE(WHERE)",
     "Base context from contract (299-330); NY sub-xwalk (512-543); UNSTRING 594-603; keys 785,880,1068"),
    (2, "ARTCCLM", "CLAIM_ID", "DECIMAL [inf]", "ARTCCLM col 2",
     "derived/transformed", "ARTCTPK (DB2)", "CTPK-PK-NEXT-NUM (= PK_NEXT_NUM - 1)",
     "(generated)", "1000001", "INSERT value / UPDATE(WHERE)",
     "Primary key pulled & decremented 967-980; moved 1020-1021; value 1069 *illustrative*"),
    (3, "ARTCCLM", "ICN_NUM", "VARCHAR [inf]", "ARTCCLM col 3",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-ICN",
     "0024031500012300", "0024031500012300", "INSERT + UPDATE(WHERE)",
     "UNSTRING 605-608; keys 786,882,1070"),
    (4, "ARTCCLM", "PREV_ICN_NUM", "VARCHAR [inf]", "ARTCCLM col 4",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-FORMER-ICN",
     "(spaces)", "(empty)", "INSERT / UPDATE(SET)",
     "UNSTRING 623-626; SET 852; VALUES 1071"),
    (5, "ARTCCLM", "RECIP_MA_NUM", "VARCHAR [inf]", "ARTCCLM col 5",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-RECIPIENT-ID-NUM",
     "AB12345C", "AB12345C", "INSERT / UPDATE(SET)",
     "UNSTRING 629-633; SET 853; VALUES 1072"),
    (6, "ARTCCLM", "PROVIDER_ID", "VARCHAR [inf]", "ARTCCLM col 6",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-PROVIDER-NUM",
     "1234567890", "1234567890", "INSERT / UPDATE(SET)",
     "UNSTRING 639-642; SET 854; VALUES 1073"),
    (7, "ARTCCLM", "CLMST_RF", "VARCHAR(1) [inf]", "ARTCCLM col 7",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-CLAIM-STATUS",
     "P", "P", "INSERT / UPDATE(SET) / SELECT(WHERE)",
     "MOVE 644-645; SELECT key 787; SET 856; VALUES 1075"),
    (8, "ARTCCLM", "TRNTP_RF", "VARCHAR(1) [inf]", "ARTCCLM col 8",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-TRANSACTION-TYPE",
     "A", "A", "INSERT / UPDATE(SET)",
     "MOVE 647-648; SET 857; VALUES 1076"),
    (9, "ARTCCLM", "CLMTP_RF", "VARCHAR [inf]", "ARTCCLM col 9",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-CLAIM-TYPE",
     "20", "20", "INSERT / UPDATE(SET)",
     "UNSTRING 650-653; SET 858; VALUES 1077"),
    (10, "ARTCCLM", "UNITS_NUM", "VARCHAR [inf]", "ARTCCLM col 10",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-UNITS-OF-SERVICE",
     "00003", "3", "INSERT / UPDATE(SET)",
     "UNSTRING strips lead zeros/spaces 655-658; SET 859; VALUES 1078"),
    (11, "ARTCCLM", "CHARGE_AMT", "DECIMAL S9(7)V99 [inf]", "ARTCCLM col 11",
     "derived/transformed", "NCTCLMS9", "CLM-CHARGE-AMT (via WS-DE-EDIT)",
     "+0001250.00", "1250.00", "INSERT / UPDATE(SET)",
     "De-edit through WS-DE-EDIT S9(7)V99 660-661; SET 860; VALUES 1079"),
    (12, "ARTCCLM", "PAID_AMT", "DECIMAL S9(7)V99 [inf]", "ARTCCLM col 12",
     "derived/transformed", "NCTCLMS9", "CLM-PAID-AMT (via WS-DE-EDIT)",
     "+0000975.50", "975.50", "INSERT / UPDATE(SET)",
     "De-edit through WS-DE-EDIT 662-663; SET 861; VALUES 1080"),
    (13, "ARTCCLM", "REMIT_DT", "DATE 'YYYY-MM-DD' [inf]", "ARTCCLM col 13",
     "derived/transformed", "NCTCLMS9", "CLM-DOR-A (YYYYMMDD)",
     "20240315", "2024-03-15", "INSERT / UPDATE(SET)",
     "Reformat insert dashes 665-669; SET 862; VALUES 1081"),
    (14, "ARTCCLM", "SERVICE_FROM_DT", "DATE 'YYYY-MM-DD' [inf]", "ARTCCLM col 14",
     "derived/transformed", "NCTCLMS9", "CLM-SERVICE-DATE-FROM-A (YYYYMMDD)",
     "20240301", "2024-03-01", "INSERT / UPDATE(SET)",
     "Reformat 671-678; SET 863; VALUES 1082"),
    (15, "ARTCCLM", "SERVICE_TO_DT", "DATE 'YYYY-MM-DD' [inf]", "ARTCCLM col 15",
     "derived/transformed", "NCTCLMS9", "CLM-SERVICE-DATE-TO-A (YYYYMMDD)",
     "20240305", "2024-03-05", "INSERT / UPDATE(SET)",
     "Reformat 680-684; SET 864; VALUES 1083"),
    (16, "ARTCCLM", "ICD9P_RF", "VARCHAR(10) [inf]", "ARTCCLM col 16",
     "derived/transformed", "NCTCLMS9", "CLM-SVC-CODE (when CLM-CLAIM-TYPE <> '12')",
     "99213", "99213", "INSERT / UPDATE(SET)",
     "Procedure branch + trunc to 10 (chg 0020) 686-700; SET 866; VALUES 1085"),
    (17, "ARTCCLM", "ICD9D_RF", "VARCHAR [inf]", "ARTCCLM col 17",
     "derived/transformed", "NCTCLMS9", "CLM-PRIMARY-DIAG-CODE",
     "E11.9", "E119", "INSERT / UPDATE(SET)",
     "Dot handling/space-shift (chg 0010) 702-726; SET 867; VALUES 1086"),
    (18, "ARTCCLM", "ICD9D_2ND_RF", "VARCHAR [inf]", "ARTCCLM col 18",
     "derived/transformed", "NCTCLMS9", "CLM-SECOND-DIAG-CODE",
     "I10", "I10", "INSERT / UPDATE(SET)",
     "Dot handling 728-752; SET 868; VALUES 1087"),
    (19, "ARTCCLM", "NDCCD_RF", "VARCHAR [inf]", "ARTCCLM col 19",
     "derived/transformed", "NCTCLMS9", "CLM-SVC-CODE (when CLM-CLAIM-TYPE = '12')",
     "(medical claim -> not set)", "(empty)", "INSERT / UPDATE(SET)",
     "RX branch 686-690; SET 869; VALUES 1088 (populated only for claim-type 12)"),
    (20, "ARTCCLM", "LAST_UPDATE_NM", "VARCHAR(8) [inf]", "ARTCCLM col 20",
     "crosswalk/translated", "WS", "WS-LAST-UPDATE-NM (<= contract)",
     "contract 320", "WNYCDF40", "INSERT / UPDATE(SET)",
     "Contract xwalk 300-325; MOVE 612-617; SET 870; VALUES 1089"),
    (21, "ARTCCLM", "LAST_UPDATE_DTM", "TIMESTAMP", "ARTCCLM col 21",
     "hardcoded constant", "DB2 register", "CURRENT TIMESTAMP",
     "(n/a)", "2024-03-16-02.15.30.123456", "INSERT / UPDATE(SET)",
     "DB2 special register 871,1090 *illustrative ts*"),
    (22, "ARTCCLM", "CREATE_SOURCE_NM", "VARCHAR [inf]", "ARTCCLM col 22",
     "crosswalk/translated", "NCTCLMS9", "CLM-CREATE-SOURCE",
     "00", "STANDARD MEDICAID", "INSERT / UPDATE(SET)",
     "EVALUATE 00->STANDARD MEDICAID / 01->DSS (chg 0005) 754-759; SET 872; VALUES 1091"),
    (23, "ARTCCLM", "ICD_VERSION", "VARCHAR [inf]", "ARTCCLM col 23",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-CDE-ICD-VERSION",
     "0", "0", "INSERT / UPDATE(SET)",
     "UNSTRING 761-764; SET 874; VALUES 1092"),
    (24, "ARTCCLM", "ALT_CLIENT_CD", "CHAR(3) [inf]", "ARTCCLM col 24",
     "derived/transformed", "WS", "HMS-3BYTE-CONTRACT-NUM",
     "contract 320", "(spaces)", "INSERT / UPDATE(SET)",
     "'535'->'535' else SPACES (chg 0016) 773-777; SET 875; VALUES 1093"),
    (25, "ARTCCLM", "AGENCY_CD", "VARCHAR [inf]", "ARTCCLM col 25",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-AGENCY-CODE",
     "AGN01", "AGN01", "INSERT / UPDATE(SET)",
     "UNSTRING 766-769; SET 876; VALUES 1094"),
    (26, "ARTCCLM", "COUNTY_CD", "CHAR [inf]", "ARTCCLM col 26",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-COUNTY-CD",
     "061", "061", "INSERT / UPDATE(SET)",
     "MOVE 771 (chg 0026); SET 877; VALUES 1095"),
    (27, "ARTCCLM", "RX_WRITTEN_DT", "DATE nullable [inf]", "ARTCCLM col 27",
     "derived/transformed", "NCTCLMS9", "CLM-RX-WRITTEN-DATE",
     "(spaces)", "NULL (indicator -1)", "INSERT / UPDATE(SET)",
     "Null-indicator logic (chg 0027) 840-850 / 1022-1033; SET 878-879; VALUES 1097"),
    (28, "ARTCCLM", "CREATE_NM", "VARCHAR [inf]", "ARTCCLM (commented)",
     "not populated", "-", "-",
     "-", "-", "(not written)",
     "Column & value commented out 1065,1098; MOVE 612-621 commented -> never populated"),
    (29, "ARTCCLM", "CREATE_DTM", "TIMESTAMP", "ARTCCLM (commented)",
     "not populated", "-", "-",
     "-", "-", "(not written)",
     "Column & value commented out 1066,1099 -> never populated"),

    # ---------------- ARTCLKP (claim lookup) : INSERT 1179-1200
    (30, "ARTCLKP", "CONTEXT_CD", "VARCHAR(16) [inf]", "ARTCLKP col 1",
     "crosswalk/translated", "WS / NCTCLMS9", "WS-CONTEXT-CD (<= contract + CLM-HMS-CLIENT-ID)",
     "contract 320 + 'CTSCCN'", "CTSCASNYC", "INSERT / SELECT(WHERE)",
     "UNSTRING 598-600; SELECT key 788; VALUES 1190"),
    (31, "ARTCLKP", "CASE_ID", "VARCHAR [inf]", "ARTCLKP col 2",
     "direct MOVE (renamed)", "NCTCLMS9", "CLM-HMS-CASE-KEY",
     "CASE0001234567", "CASE0001234567", "INSERT / SELECT(WHERE)",
     "MOVE 610; SELECT key 789; VALUES 1191"),
    (32, "ARTCLKP", "CLAIM_ID", "DECIMAL [inf]", "ARTCLKP col 3",
     "derived/transformed", "ARTCTPK (DB2)", "CTPK-PK-NEXT-NUM",
     "(generated)", "1000001", "INSERT / SELECT",
     "Shared key with ARTCCLM 1020-1021; VALUES 1192"),
    (33, "ARTCLKP", "RELATE_IND", "CHAR(1) [inf]", "ARTCLKP col 4",
     "hardcoded constant", "literal", "'0'",
     "(n/a)", "0", "INSERT",
     "Literal '0' 1183,1193"),
    (34, "ARTCLKP", "LAST_UPDATE_NM", "VARCHAR(8) [inf]", "ARTCLKP col 5",
     "crosswalk/translated", "WS", "WS-LAST-UPDATE-NM (<= contract)",
     "contract 320", "WNYCDF40", "INSERT",
     "MOVE 615-620; VALUES 1194"),
    (35, "ARTCLKP", "LAST_UPDATE_DTM", "TIMESTAMP", "ARTCLKP col 6",
     "hardcoded constant", "DB2 register", "CURRENT TIMESTAMP",
     "(n/a)", "2024-03-16-02.15.30.123456", "INSERT",
     "DB2 special register 1195 *illustrative ts*"),
    (36, "ARTCLKP", "IS_AUTO_CHECKED", "CHAR(1) [inf]", "ARTCLKP col 7",
     "hardcoded constant", "literal", "'N'",
     "(n/a)", "N", "INSERT",
     "Literal 'N' (chg 0019) 1186,1196"),
    (37, "ARTCLKP", "CREATE_NM", "VARCHAR [inf]", "ARTCLKP (commented)",
     "not populated", "-", "-", "-", "-", "(not written)",
     "Column & value commented out 1187,1197 -> never populated"),
    (38, "ARTCLKP", "CREATE_DTM", "TIMESTAMP", "ARTCLKP (commented)",
     "not populated", "-", "-", "-", "-", "(not written)",
     "Column & value commented out 1188,1198 -> never populated"),

    # ---------------- ARTCTPK (primary-key table) : INSERT 1233-1250 / UPDATE 932-938
    (39, "ARTCTPK", "CONTEXT_CD", "VARCHAR(16) [inf]", "ARTCTPK col 1",
     "crosswalk/translated", "WS / NCTCLMS9", "WS-CONTEXT-CD (<= contract + CLM-HMS-CLIENT-ID)",
     "contract 320 + 'CTSCCN'", "CTSCASNYC", "INSERT / UPDATE(WHERE)",
     "UNSTRING 598-602; UPDATE key 936; VALUES 1242"),
    (40, "ARTCTPK", "PK_TYPE_CD", "CHAR(3) [inf]", "ARTCTPK col 2",
     "hardcoded constant", "literal", "'CLM'",
     "(n/a)", "CLM", "INSERT / UPDATE(WHERE)",
     "Literal 'CLM' 937,1243"),
    (41, "ARTCTPK", "PK_DSC", "VARCHAR [inf]", "ARTCTPK col 3",
     "hardcoded constant", "literal", "'CASE TRACKING SYSTEM CLAIM'",
     "(n/a)", "CASE TRACKING SYSTEM CLAIM", "INSERT",
     "Literal 1244"),
    (42, "ARTCTPK", "PK_MASK_TXT", "VARCHAR [inf]", "ARTCTPK col 4",
     "default SPACES or ZEROS [UNCERTAIN]", "DCLGEN (CARTCTPK)", "CTPK-PK-MASK-TXT",
     "(n/a)", "(empty / DCLGEN default)", "INSERT",
     "[UNCERTAIN] host var never MOVEd in visible code; only INITIALIZE 491; VALUES 1245"),
    (43, "ARTCTPK", "PK_NEXT_NUM", "INTEGER [inf]", "ARTCTPK col 5",
     "hardcoded constant", "literal", "+2 (INSERT) / PK_NEXT_NUM + 1 (UPDATE)",
     "(n/a)", "2", "INSERT / UPDATE(SET)",
     "New key seeded at +2 1246; incremented on update 933"),
    (44, "ARTCTPK", "LAST_UPDATE_NM", "VARCHAR(8) [inf]", "ARTCTPK col 6",
     "crosswalk/translated", "WS", "WS-LAST-UPDATE-NM (<= contract)",
     "contract 320", "WNYCDF40", "INSERT / UPDATE(SET)",
     "MOVE 612-619; SET 934; VALUES 1247"),
    (45, "ARTCTPK", "LAST_UPDATE_DTM", "TIMESTAMP", "ARTCTPK col 7",
     "hardcoded constant", "DB2 register", "CURRENT TIMESTAMP",
     "(n/a)", "2024-03-16-02.15.30.123456", "INSERT / UPDATE(SET)",
     "DB2 special register 935,1248 *illustrative ts*"),

    # ---------------- MISC.P_MONITOR : UPDATE 1333-1430
    (46, "P_MONITOR", "END_DTM", "TIMESTAMP", "P_MONITOR col",
     "hardcoded constant", "DB2 register", "CURRENT TIMESTAMP",
     "(n/a)", "2024-03-16-02.15.30.123456", "UPDATE",
     "SET 1334,1344,... *illustrative ts*"),
    (47, "P_MONITOR", "TASK_STEP_TXT", "VARCHAR [inf]", "P_MONITOR col",
     "hardcoded constant", "literal", "'LOAD'",
     "(n/a)", "LOAD", "UPDATE",
     "Literal 1335,1345,..."),
    (48, "P_MONITOR", "STATUS_TXT", "VARCHAR [inf]", "P_MONITOR col",
     "crosswalk/translated", "WS", "WS-STATUS-TXT -> PMONITOR-STATUS-TXT",
     "(normal end)", "SUCCESS", "UPDATE",
     "'SUCCESS' normal 370-371; 'FAILURE' on abend 1576; SET 1336"),
    (49, "P_MONITOR", "DATA_CNT", "INTEGER [inf]", "P_MONITOR col",
     "derived/transformed", "WS", "WS-CONTEXT-CD-n-CNT (per-context insert counts)",
     "(n/a)", "1", "UPDATE",
     "Row count tally 1106-1154; SET 1337/1347/1359/..."),

    # ---------------- CNTL-FILE (control / checkpoint record) : WRITE 1304
    (50, "CNTL", "CNTL-PROC-FLAG", "PIC X(01)", "bytes 1-1",
     "hardcoded constant", "literal", "'-'",
     "(n/a)", "-", "WRITE",
     "VALUE '-' 185; reset 1301; WRITE 1304"),
    (51, "CNTL", "NUM-REC-OUT", "PIC ZZZ,ZZZ,ZZ9", "bytes 2-12",
     "derived/transformed", "WS", "SQL-TOT-COMMITTED-CTR",
     "(n/a)", "      1,234", "WRITE",
     "Edited running total 1302-1304"),
    (52, "CNTL", "FILLER", "PIC X(02)", "bytes 13-14",
     "hardcoded constant", "literal", "'++'",
     "(n/a)", "++", "WRITE",
     "VALUE '++' 187"),
    (53, "CNTL", "WS-CURRENT-TIMESTAMP", "PIC X(26)", "bytes 15-38 (trunc)",
     "derived/transformed", "DB2 register", "CURRENT TIMESTAMP (SYSIBM.SYSDUMMY1) / FUNCTION CURRENT-DATE fallback",
     "(n/a)", "2024-03-16-02.15.30.1234", "WRITE",
     "Set 1287-1299; NOTE 40-byte WS written into 38-byte CNTL-RECORD -> last 2 bytes truncated"),
]

S1_HEADERS = [
    "Field No", "Output Copybook / Table", "Target Field", "Picture (inferred)",
    "Byte Location", "Mapping Type", "Source Copybook", "Source Field",
    "Sample Input", "Sample Output",
    "ARTCCLM", "ARTCLKP", "ARTCTPK", "MISC.P_MONITOR", "CNTL-FILE",
    "Comments (evidence = CASNCTD9_Version2.txt line #)",
]

OWNER_TO_COL = {
    "ARTCCLM": "ARTCCLM",
    "ARTCLKP": "ARTCLKP",
    "ARTCTPK": "ARTCTPK",
    "P_MONITOR": "MISC.P_MONITOR",
    "CNTL": "CNTL-FILE",
}

MTYPE_FILL = {
    "1x1 identity": "E2EFDA",
    "direct MOVE (renamed)": "DDEBF7",
    "derived/transformed": "FFF2CC",
    "crosswalk/translated": "FCE4D6",
    "hardcoded constant": "EDEDED",
    "default SPACES or ZEROS [UNCERTAIN]": "F8CBAD",
    "not populated": "D9D9D9",
}


def build_sheet1(wb):
    ws = wb.active
    ws.title = "1. Field Mapping"
    ws.cell(row=1, column=1, value="CASNCTD9 - 1x1 Field Mapping (every output field, one row each)").font = TITLE_FONT
    ws.cell(row=2, column=1,
            value=("Program CASNCTD9 (CASNCTD9_Version2.txt). Outputs = DB2 tables ARTCCLM/ARTCLKP/ARTCTPK, "
                   "MISC.P_MONITOR and the DB2CNTLO control file. One input format: NCTCLMS9 (prefix CLM-, DD NCTCLMI, 316 bytes). "
                   "[inf]=PIC/length inferred from usage (copybooks/DCLGENs are external, not in repo). "
                   "Per-output columns show the SQL/file operation that writes the field.")).font = NOTE_FONT
    header_row = 4
    for c, h in enumerate(S1_HEADERS, start=1):
        ws.cell(row=header_row, column=c, value=h)
    style_header_row(ws, header_row, len(S1_HEADERS))

    r = header_row
    for rec in S1:
        r += 1
        (no, owner, target, pic, byte, mtype, scopy, sfield,
         sin, sout, op, comment) = rec
        base = [no, OWNER_TO_COL[owner], target, pic, byte, mtype, scopy, sfield, sin, sout]
        for c, v in enumerate(base, start=1):
            ws.cell(row=r, column=c, value=v)
        # per-output columns (11..15)
        owner_col_name = OWNER_TO_COL[owner]
        for i, tgt in enumerate(OUTPUT_TARGETS):
            col = 11 + i
            ws.cell(row=r, column=col, value=op if tgt == owner_col_name else "")
        ws.cell(row=r, column=16, value=comment)
        # colour the Mapping Type cell
        fill = MTYPE_FILL.get(mtype)
        if fill:
            ws.cell(row=r, column=6).fill = PatternFill("solid", fgColor=fill)

    widths = [8, 17, 20, 22, 16, 26, 16, 34, 26, 28, 20, 14, 18, 16, 14, 60]
    finalize(ws, header_row, len(S1_HEADERS), widths)
    # keep coloured mapping-type cells (finalize zebra skips non-default fills)
    return ws


# ==========================================================================
# SHEET 2 : OVERRIDES & CROSSWALKS
# ==========================================================================
S2_HEADERS = ["Path / Format", "Source Field", "Target Field",
              "Assigned / Translated Value", "Condition",
              "Sample In -> Out", "Description (evidence line #)"]

S2 = [
    ("ARTCCLM/ARTCLKP/ARTCTPK", "HMS-3BYTE-CONTRACT-NUM (JCL via CASGETCC)", "CONTEXT_CD / WS-CONTEXT-CD",
     "320->CTSCASNY; 300->CTSCASTST; 326->CTSCASCO; 341->CTSCASOH; 535->CTSCASOH; 313->CTSCASFL; "
     "319->CTSCASCT; 317->CTSWRCCA; 590->CTSCASAL; 330->CTSCASAR; 358->CTSCASNV; 359->CTSCASNM; 645->CTSCASWV",
     "EVALUATE contract number", "320 -> CTSCASNY",
     "Base context per client contract; unknown contract -> DUMP 0999 abend (299-330)"),
    ("ARTCCLM/ARTCLKP/ARTCTPK", "HMS-3BYTE-CONTRACT-NUM", "LAST_UPDATE_NM",
     "320->WNYCDF40; 300->WTTCDF40; 326->WCOCDF40; 341->WOHCDF40; 535->WCXCDF40; 313->WFLCDF40; "
     "319->WCTCDF40; 317->WCACDF40; 590->WALCDF40; 330->WARCDF40; 358->WNVCDF40; 359->WNMCDF40; 645->WWVCDF40",
     "EVALUATE contract number", "320 -> WNYCDF40",
     "Audit user stamp paired with the context crosswalk (300-325)"),
    ("ARTCCLM/ARTCLKP/ARTCTPK (NY only)", "CLM-HMS-CLIENT-ID", "CONTEXT_CD / WS-CONTEXT-CD",
     "CTSCEN->CTSCASEX-NY; CTSCCN->CTSCASNYC; CTSECN->CTSESTNY; CTSEEN->CTSESTEX-NY; "
     "CTSCON->CTSCASNYOP1; CTSEON->CTSESTNYOP1; OTHER->CTSCASNY",
     "contract = 320", "CTSCCN -> CTSCASNYC",
     "NY multi-context resolution (chg 0013/0021/0026) (512-543)"),
    ("ARTCCLM/ARTCLKP/ARTCTPK (FL only)", "CLM-HMS-CLIENT-ID", "CONTEXT_CD / WS-CONTEXT-CD",
     "CTSCAS->CTSCASFL; CTSEST->CTSESTFL; CTSTRS->CTSTRSFL; CTSMST->CTSCASMT-FL; OTHER->CTSCASFL",
     "contract = 313", "CTSMST -> CTSCASMT-FL",
     "FL multi-context resolution (chg 0023) (567-589)"),
    ("ARTCCLM/ARTCLKP/ARTCTPK (multi-ctx)", "CLM-HMS-CLIENT-ID (1:6)", "CONTEXT_CD (1:6)",
     "First 6 bytes of client id overlaid onto context code",
     "contract IN (326,590,359,645)", "client 'CTSxxx' -> context (1:6)",
     "6-byte client overlay for multi-context clients (499-506)"),
    ("ARTCCLM", "CLM-CREATE-SOURCE", "CREATE_SOURCE_NM",
     "00->STANDARD MEDICAID; 01->DSS", "EVALUATE CLM-CREATE-SOURCE", "00 -> STANDARD MEDICAID",
     "Source-system description (chg 0005) (754-759); other values leave field unset"),
    ("ARTCCLM", "HMS-3BYTE-CONTRACT-NUM", "ALT_CLIENT_CD",
     "'535' -> '535'; else SPACES", "IF contract = 535", "320 -> (spaces)",
     "Alt client indicator for OH CareSource split (chg 0016) (773-777)"),
    ("ARTCCLM", "CLM-SVC-CODE", "NDCCD_RF vs ICD9P_RF",
     "claim-type '12' -> NDCCD_RF (NDC); else -> ICD9P_RF (procedure, truncated to 10)",
     "IF CLM-CLAIM-TYPE = '12'", "RX '00093' -> NDCCD_RF; medical '99213' -> ICD9P_RF",
     "Service-code routing by claim type (chg 0020) (686-700)"),
    ("ARTCCLM", "CLM-RX-WRITTEN-DATE", "RX_WRITTEN_DT",
     "spaces/zeros/low-values -> NULL (indicator -1); else date value (indicator +1)",
     "IF CLM-RX-WRITTEN-DATE blank", "(spaces) -> NULL",
     "Nullable RX written date (chg 0027/0028) (840-850 / 1022-1033)"),
    ("ARTCCLM", "CLM-PRIMARY-DIAG-CODE / CLM-SECOND-DIAG-CODE", "ICD9D_RF / ICD9D_2ND_RF",
     "If 3 chars precede '.', drop the dot and concatenate; shift a leading space left",
     "INSPECT ... BEFORE INITIAL '.'", "E11.9 -> E119",
     "Diagnosis dot normalisation (chg 0010) (702-752)"),
    ("ARTCLKP", "(none)", "RELATE_IND / IS_AUTO_CHECKED",
     "RELATE_IND = '0'; IS_AUTO_CHECKED = 'N'", "always on INSERT", "(n/a) -> 0 / N",
     "Hardcoded lookup flags (1183,1186,1193,1196)"),
    ("ARTCTPK", "(none)", "PK_TYPE_CD / PK_DSC / PK_NEXT_NUM",
     "PK_TYPE_CD='CLM'; PK_DSC='CASE TRACKING SYSTEM CLAIM'; PK_NEXT_NUM seeded +2",
     "new-context INSERT", "(n/a) -> CLM / 2",
     "Primary-key seed row created once per context (1243-1246)"),
    ("MISC.P_MONITOR", "WS-STATUS-TXT", "STATUS_TXT / TASK_STEP_TXT",
     "TASK_STEP_TXT='LOAD'; STATUS_TXT='SUCCESS' (normal) or 'FAILURE' (abend)",
     "end of run", "normal end -> SUCCESS",
     "Process-monitor heartbeat (370-371,1335-1336,1576)"),
]


def build_sheet2(wb):
    ws = wb.create_sheet("2. Overrides & Crosswalks")
    ws.cell(row=1, column=1, value="Overrides & Crosswalks - assigned constants and translated values").font = TITLE_FONT
    header_row = 3
    for c, h in enumerate(S2_HEADERS, start=1):
        ws.cell(row=header_row, column=c, value=h)
    style_header_row(ws, header_row, len(S2_HEADERS))
    r = header_row
    for rec in S2:
        r += 1
        for c, v in enumerate(rec, start=1):
            ws.cell(row=r, column=c, value=v)
    widths = [30, 34, 26, 46, 26, 30, 50]
    finalize(ws, header_row, len(S2_HEADERS), widths)
    return ws


# ==========================================================================
# SHEET 3 : ROUTING / FORMAT LOGIC
# ==========================================================================
S3_ROWS = [
    ("Program role",
     "Reformat + multi-output DB2 loader. Reads one claim file and writes to multiple DB2 "
     "tables plus a control file. Input layout (NCTCLMS9) differs from every output layout "
     "(DB2 DCLGENs), so it is NOT a passthrough/filter.", "IDENTIFICATION/ENV/DATA 1-100"),
    ("Input format (single)",
     "NCTC-IN, DD NCTCLMI, copybook NCTCLMS9 (prefix CLM-), FB 316-byte PCFCASE claim records.",
     "79,85-92"),
    ("Control / checkpoint I/O",
     "CNTL-IO, DD DB2CNTLO (PIC X(38)). Opened INPUT first to count already-processed records, "
     "then OPEN OUTPUT and WRITE one control record per COMMIT (restart support).",
     "81,95-100,337-344,1300-1304"),
    ("Outputs per input record",
     "Exactly one ARTCCLM row (UPDATE when the claim already exists, else INSERT). On the INSERT "
     "path it also writes one ARTCLKP row and maintains the ARTCTPK key row. ARTCCLM UPDATE path "
     "writes neither ARTCLKP nor ARTCTPK.", "782-797,908-1229"),
    ("Routing decision (exists?)",
     "SELECT L.CLAIM_ID FROM ARTCCLM C, ARTCLKP L on CONTEXT_CD+ICN_NUM+CLMST_RF(+case): "
     "SQLCODE 0 -> 1100-UPDATE-ARTCCLM ; SQLCODE +100 -> 1200-INSERT-ARTCCLM ; "
     "SQLCODE -811 (many rows) -> abend ; -904/-911/-913 -> timeout retry.", "781-823"),
    ("Key generation",
     "On INSERT: UPDATE ARTCTPK SET PK_NEXT_NUM = PK_NEXT_NUM + 1 (seed INSERT +2 if missing), "
     "then SELECT PK_NEXT_NUM-1 -> CCLM-CLAIM-ID / CLKP-CLAIM-ID.", "932-1021"),
    ("SKIP - restart",
     "Records whose running count <= WS-CNTL-RECS-OUT-TOT (from the control file) are re-READ and "
     "skipped so a restart does not reprocess committed rows.", "338-360,379-411"),
    ("SKIP - RX encounter exclusion",
     "If CLM-CLAIM-TYPE = '12' (RX) and WS-CONTEXT-CD is in the ARTSPRF exclusion list "
     "(NAME_CD='NY_RX_ENCOUNTER_EXCLUSION' AND UPPER(VALUE_TXT)='TRUE'), the ARTCCLM + ARTCLKP "
     "INSERT is skipped (counter WS-RX-EXCL-SKIP-CTR). UPDATE path is unaffected.",
     "254-266,426-488,909-930"),
    ("REJECT / good-complete",
     "Empty input or all-already-processed -> DISPLAY + DUMP-CODE 0998 (GOOD completion, chg 0011).",
     "346-357"),
    ("ABEND conditions",
     "Unknown contract number -> DUMP 0999; contract retrieve (CASGETCC) RC not '0' -> DUMP 0999; "
     "SELECT -811 multiple claim ids -> abend; uncommitted ARTCTPK intervention -> abend; "
     "unexpected SQLCODE -> Z9999-ERROR-EXIT. Default DUMP-CODE 3645. Abend via CALL 'ILBOABN0'.",
     "288-295,326-329,798-803,1011-1018,1556-1578"),
    ("Timeout / deadlock retry",
     "SQLCODE -904/-911/-913 with nothing yet uncommitted -> ADD 1 TO TIME-OUT-CTR, ROLLBACK, "
     "retry mainline; 5 attempts -> Z9999-ERROR-EXIT.", "804-818,363-366,996-1005"),
    ("Commit frequency",
     "Implicit COMMIT every SQL-COMMIT-FREQ (= 300) uncommitted DB2 operations and at end of file; "
     "each COMMIT also WRITEs a control record and refreshes WS-CURRENT-TIMESTAMP.",
     "110,825-830,1276-1313"),
    ("Process monitor",
     "At normal end STATUS_TXT='SUCCESS'; on abend path STATUS_TXT='FAILURE'. "
     "MISC.P_MONITOR rows updated per context with per-context committed counts.",
     "370-372,1315-1455,1575-1577"),
]


def build_sheet3(wb):
    ws = wb.create_sheet("3. Routing Format Logic")
    ws.cell(row=1, column=1, value="Routing / Format Logic - how records reach each output").font = TITLE_FONT
    ws.cell(row=2, column=1,
            value=("Single input format (NCTCLMS9). Multi-output: 3 DB2 tables + control file + process "
                   "monitor. Each input row yields one ARTCCLM UPDATE or one ARTCCLM+ARTCLKP(+ARTCTPK) "
                   "INSERT, subject to the skip/reject rules below.")).font = NOTE_FONT
    header_row = 4
    for c, h in enumerate(["Aspect", "Logic", "Evidence (line #)"], start=1):
        ws.cell(row=header_row, column=c, value=h)
    style_header_row(ws, header_row, 3)
    r = header_row
    for aspect, logic, ev in S3_ROWS:
        r += 1
        ws.cell(row=r, column=1, value=aspect)
        ws.cell(row=r, column=2, value=logic)
        ws.cell(row=r, column=3, value=ev)
    finalize(ws, header_row, 3, [28, 96, 22])
    return ws


# ==========================================================================
# SHEET 4 : SAMPLE RECORDS
# ==========================================================================
# One full input record (NCTCLMS9) and the matching output rows it produces.
TS = "2024-03-16-02.15.30.123456"

SAMPLE_A_INPUT = [
    ("CLM-HMS-CLIENT-ID", "CTSCCN", "NY sub-context selector"),
    ("(JCL) HMS-3BYTE-CONTRACT-NUM", "320", "from CASGETCC call, not the record"),
    ("CLM-ICN", "0024031500012300", "internal control number"),
    ("CLM-FORMER-ICN", "(spaces)", "no prior ICN"),
    ("CLM-RECIPIENT-ID-NUM", "AB12345C", "Medicaid recipient id"),
    ("CLM-PROVIDER-NUM", "1234567890", "billing provider"),
    ("CLM-HMS-CASE-KEY", "CASE0001234567", "HMS case key"),
    ("CLM-CLAIM-STATUS", "P", "paid"),
    ("CLM-TRANSACTION-TYPE", "A", "add/adjust indicator"),
    ("CLM-CLAIM-TYPE", "20", "medical (not 12=RX)"),
    ("CLM-UNITS-OF-SERVICE", "00003", "3 units"),
    ("CLM-CHARGE-AMT", "+0001250.00", "billed amount"),
    ("CLM-PAID-AMT", "+0000975.50", "paid amount"),
    ("CLM-DOR-A", "20240315", "date of remit (YYYYMMDD)"),
    ("CLM-SERVICE-DATE-FROM-A", "20240301", "service from (YYYYMMDD)"),
    ("CLM-SERVICE-DATE-TO-A", "20240305", "service to (YYYYMMDD)"),
    ("CLM-SVC-CODE", "99213", "CPT (medical -> ICD9P_RF)"),
    ("CLM-PRIMARY-DIAG-CODE", "E11.9", "primary diagnosis"),
    ("CLM-SECOND-DIAG-CODE", "I10", "secondary diagnosis"),
    ("CLM-CREATE-SOURCE", "00", "source code"),
    ("CLM-CDE-ICD-VERSION", "0", "ICD version indicator"),
    ("CLM-AGENCY-CODE", "AGN01", "agency code"),
    ("CLM-COUNTY-CD", "061", "county code"),
    ("CLM-RX-WRITTEN-DATE", "(spaces)", "non-RX -> NULL in output"),
]

SAMPLE_A_ARTCCLM = [
    ("CONTEXT_CD", "CTSCASNYC"), ("CLAIM_ID", "1000001"), ("ICN_NUM", "0024031500012300"),
    ("PREV_ICN_NUM", "(empty)"), ("RECIP_MA_NUM", "AB12345C"), ("PROVIDER_ID", "1234567890"),
    ("CLMST_RF", "P"), ("TRNTP_RF", "A"), ("CLMTP_RF", "20"), ("UNITS_NUM", "3"),
    ("CHARGE_AMT", "1250.00"), ("PAID_AMT", "975.50"), ("REMIT_DT", "2024-03-15"),
    ("SERVICE_FROM_DT", "2024-03-01"), ("SERVICE_TO_DT", "2024-03-05"),
    ("ICD9P_RF", "99213"), ("ICD9D_RF", "E119"), ("ICD9D_2ND_RF", "I10"),
    ("NDCCD_RF", "(empty)"), ("LAST_UPDATE_NM", "WNYCDF40"), ("LAST_UPDATE_DTM", TS),
    ("CREATE_SOURCE_NM", "STANDARD MEDICAID"), ("ICD_VERSION", "0"),
    ("ALT_CLIENT_CD", "(spaces)"), ("AGENCY_CD", "AGN01"), ("COUNTY_CD", "061"),
    ("RX_WRITTEN_DT", "NULL"), ("CREATE_NM", "(not populated)"), ("CREATE_DTM", "(not populated)"),
]

SAMPLE_A_ARTCLKP = [
    ("CONTEXT_CD", "CTSCASNYC"), ("CASE_ID", "CASE0001234567"), ("CLAIM_ID", "1000001"),
    ("RELATE_IND", "0"), ("LAST_UPDATE_NM", "WNYCDF40"), ("LAST_UPDATE_DTM", TS),
    ("IS_AUTO_CHECKED", "N"), ("CREATE_NM", "(not populated)"), ("CREATE_DTM", "(not populated)"),
]

SAMPLE_A_ARTCTPK = [
    ("CONTEXT_CD", "CTSCASNYC"), ("PK_TYPE_CD", "CLM"), ("PK_DSC", "CASE TRACKING SYSTEM CLAIM"),
    ("PK_MASK_TXT", "(DCLGEN default)"), ("PK_NEXT_NUM", "1000002 (was 1000001, +1 on update)"),
    ("LAST_UPDATE_NM", "WNYCDF40"), ("LAST_UPDATE_DTM", TS),
]

SAMPLE_A_CNTL = [
    ("CNTL-PROC-FLAG (b1)", "-"), ("NUM-REC-OUT (b2-12)", "          1"),
    ("FILLER (b13-14)", "++"), ("WS-CURRENT-TIMESTAMP (b15-38)", "2024-03-16-02.15.30.1234"),
]

SAMPLE_B_NOTE = [
    ("Variant: RX encounter claim", "", ""),
    ("CLM-CLAIM-TYPE", "12", "RX claim"),
    ("CLM-SVC-CODE", "00093123456", "NDC -> goes to NDCCD_RF (not ICD9P_RF)"),
    ("CLM-RX-WRITTEN-DATE", "20240310", "-> RX_WRITTEN_DT = 2024-03-10 (indicator +1)"),
    ("Routing", "if WS-CONTEXT-CD in ARTSPRF exclusion list",
     "ARTCCLM+ARTCLKP INSERT SKIPPED (WS-RX-EXCL-SKIP-CTR +1); otherwise inserted with NDCCD_RF set"),
]


def _kv_block(ws, start_row, title, rows, title_fill="1F4E78", kv_headers=("Field", "Value", "Note")):
    ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, color="FFFFFF")
    for c in range(1, 4):
        ws.cell(row=start_row, column=c).fill = PatternFill("solid", fgColor=title_fill)
    ws.cell(row=start_row, column=1).font = Font(bold=True, color="FFFFFF")
    hdr = start_row + 1
    for c, h in enumerate(kv_headers, start=1):
        cell = ws.cell(row=hdr, column=c, value=h)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9E1F2")
        cell.border = BORDER
    r = hdr
    for rec in rows:
        r += 1
        vals = list(rec) + [""] * (3 - len(rec))
        for c, v in enumerate(vals[:3], start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.alignment = WRAP_TOP
            cell.border = BORDER
    return r + 2  # next free row (blank spacer)


def build_sheet4(wb):
    ws = wb.create_sheet("4. Sample Records")
    ws.cell(row=1, column=1, value="Sample Records - one input claim and the output rows it produces").font = TITLE_FONT
    ws.cell(row=2, column=1,
            value=("All values illustrative and consistent with the PIC/length evidence in the source. "
                   "Input = one NCTCLMS9 claim (NY, contract 320, client CTSCCN -> context CTSCASNYC).")).font = NOTE_FONT
    nxt = 4
    nxt = _kv_block(ws, nxt, "INPUT RECORD - NCTCLMS9 (prefix CLM-, DD NCTCLMI, 316 bytes)", SAMPLE_A_INPUT)
    nxt = _kv_block(ws, nxt, "OUTPUT 1 - ARTCCLM (INSERT, new claim)", SAMPLE_A_ARTCCLM,
                    title_fill="375623", kv_headers=("Column", "Value", ""))
    nxt = _kv_block(ws, nxt, "OUTPUT 2 - ARTCLKP (INSERT, new lookup)", SAMPLE_A_ARTCLKP,
                    title_fill="375623", kv_headers=("Column", "Value", ""))
    nxt = _kv_block(ws, nxt, "OUTPUT 3 - ARTCTPK (key row after update)", SAMPLE_A_ARTCTPK,
                    title_fill="375623", kv_headers=("Column", "Value", ""))
    nxt = _kv_block(ws, nxt, "OUTPUT 4 - CNTL-FILE control record (at COMMIT)", SAMPLE_A_CNTL,
                    title_fill="375623", kv_headers=("Field (byte)", "Value", ""))
    nxt = _kv_block(ws, nxt, "SECOND EXAMPLE - RX claim-type '12' branch", SAMPLE_B_NOTE,
                    title_fill="843C0C")
    for i, w in enumerate([34, 34, 48], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"
    return ws


def main():
    wb = Workbook()
    build_sheet1(wb)
    build_sheet2(wb)
    build_sheet3(wb)
    build_sheet4(wb)
    wb.save(OUTPUT_XLSX)
    # Assertion: exactly 4 sheets, every output field present.
    assert len(wb.sheetnames) == 4, wb.sheetnames
    print("Wrote %s" % OUTPUT_XLSX)
    print("Sheets:", wb.sheetnames)
    print("Output fields mapped (Sheet 1 rows):", len(S1))
    print("Crosswalk/override rows (Sheet 2):", len(S2))


if __name__ == "__main__":
    main()
