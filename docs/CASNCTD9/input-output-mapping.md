# CASNCTD9 — Input / Output Mapping

> Documents program **`CASNCTD9`** (the requested `CASNCTD1` is *Not present in provided source — requires further input*).
> Input-record and DB2 column data types/lengths live in copybooks/DCLGENs that are *External dependency not analyzed in provided source*; where a type or length is not visible it is marked accordingly and **not** assumed.

## Input sources

| Source Name | Type | Description | Key fields | Notes |
|-------------|------|-------------|-----------|-------|
| `NCTC-IN` (DDNAME `NCTCLMI`) | Sequential file, fixed `316`-byte records | PCFCASE claims extract ("NCTCLMS1 300 FILE"); one record per claim | `CLM-HMS-CLIENT-ID`, `CLM-ICN`, `CLM-HMS-CASE-KEY` | Layout from copybook `NCTCLMS9` (prefix `CLM`). Field types *not present in provided source*. |
| `CNTL-IO` (DDNAME `DB2CNTLO`) | Sequential file, `38`-byte records | Restart/checkpoint control file | `CNTL-PROC-FLAG`, `NUM-REC-OUT` | Opened INPUT first (restart count), then OUTPUT (checkpoint writes). |
| `CTSPROD.SEC.ARTSPRF` | DB2 table (SELECT via cursor `ARTSPRF-CSR`) | Preferences table | `NAME_CD`, `VALUE_TXT`, `CONTEXT_CD` | Read where `NAME_CD='NY_RX_ENCOUNTER_EXCLUSION'` AND `UPPER(VALUE_TXT)='TRUE'`. |
| `ARTCCLM` + `ARTCLKP` | DB2 tables (singleton SELECT / join) | Existing-claim lookup | `CONTEXT_CD`, `ICN_NUM`, `CLMST_RF`, `CASE_ID`, `CLAIM_ID` | Determines UPDATE vs INSERT. |
| `ARTCTPK` | DB2 table (SELECT) | Per-context primary-key counter | `CONTEXT_CD`, `PK_TYPE_CD` (`'CLM'`) | Supplies next `CLAIM_ID`. |
| `CASGETCC` (linkage) | Called program | Returns 3-byte HMS contract number | `HMS-3BYTE-CONTRACT-NUM` | Return code `'0'` = success. |

## Output targets

| Target Name | Type | Description | Key fields | Notes |
|-------------|------|-------------|-----------|-------|
| `ARTCCLM` | DB2 table (INSERT / UPDATE) | Claim table (primary target) | `CONTEXT_CD`, `CLAIM_ID`, `ICN_NUM` | UPDATE when claim exists, INSERT when new. |
| `ARTCLKP` | DB2 table (INSERT) | Claim lookup / claim-to-case link | `CONTEXT_CD`, `CASE_ID`, `CLAIM_ID` | Inserted only on new-claim path; `RELATE_IND='0'`, `IS_AUTO_CHECKED='N'`. |
| `ARTCTPK` | DB2 table (UPDATE / INSERT) | Primary-key generator per context | `CONTEXT_CD`, `PK_TYPE_CD='CLM'` | `PK_NEXT_NUM` incremented; row inserted with `PK_NEXT_NUM=+2` if missing. |
| `MISC.P_MONITOR` | DB2 table (UPDATE) | Process monitor | `CLIENT_CD`, `CONTEXT_CD`, `PROCESS_NM LIKE 'CLKP_LOAD_DURATION_%'` | Sets `END_DTM`, `TASK_STEP_TXT='LOAD'`, `STATUS_TXT`, `DATA_CNT`. |
| `CNTL-IO` (DDNAME `DB2CNTLO`) | Sequential file (WRITE) | Checkpoint record at each commit | `CNTL-PROC-FLAG='-'`, `NUM-REC-OUT` | Enables restart-skip on rerun. |
| Job log (`DISPLAY`) | SYSOUT | Banners, info/warn/err, counters | — | See `9100-DISPLAY-COUNTERS`. |

## Parameters / control values (from source)

| Value | Meaning in code |
|-------|-----------------|
| `SQL-COMMIT-FREQ = +300` | Commit frequency (records per unit of work). |
| `DUMP-CODE` default `+3645` | Abend code passed to `ILBOABN0` for generic failures. |
| `DUMP-CODE +0999` | Unknown/failed contract number → abend. |
| `DUMP-CODE +0998` | Input empty / all records already processed (per comment `0011`, treated as "good completion"). |
| `TIME-OUT-CTR >= 5` | Max DB2 lock/timeout retries before terminating. |
| `WS-RX-EXCL-MAX = +50` | Max exclusion context codes held in memory. |
| `PK_TYPE_CD = 'CLM'` | Primary-key type filter for `ARTCTPK`. |
| `NAME_CD = 'NY_RX_ENCOUNTER_EXCLUSION'` | Preference key read from `ARTSPRF`. |

## Field mapping — input record → DB2 `ARTCCLM`

> Source = input copybook `NCTCLMS9` field (prefix `CLM`); Target = `ARTCCLM` column. Types/Lengths are *not present in provided source* unless the code reveals them; those cells say "Not in source".

| Field Name | Source | Target | Type | Length | Description | Notes |
|------------|--------|--------|------|--------|-------------|-------|
| Context code | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | VARCHAR (DCLGEN) | Not in source | Client/state/LOB identifier | Derived from contract number + client id; length set via UNSTRING. |
| Claim id | `ARTCTPK.PK_NEXT_NUM - 1` | `CLAIM_ID` | Not in source | Not in source | Generated surrogate key | Insert path only; from `ARTCTPK`. |
| ICN | `CLM-ICN` | `ICN_NUM` | Not in source | Not in source | Claim ICN | UNSTRING to strip trailing spaces. |
| Former ICN | `CLM-FORMER-ICN` | `PREV_ICN_NUM` | Not in source | Not in source | Prior/void ICN | UNSTRING. |
| Recipient id | `CLM-RECIPIENT-ID-NUM` | `RECIP_MA_NUM` | Not in source | Not in source | Recipient Medicaid number | UNSTRING. |
| Provider number | `CLM-PROVIDER-NUM` | `PROVIDER_ID` | Not in source | Not in source | Provider id | UNSTRING. |
| Claim status | `CLM-CLAIM-STATUS` | `CLMST_RF` | Not in source | length 1 | Claim status reference | Length hard-set to 1. Also a join key on lookup. |
| Transaction type | `CLM-TRANSACTION-TYPE` | `TRNTP_RF` | Not in source | length 1 | Transaction type reference | Length hard-set to 1. |
| Claim type | `CLM-CLAIM-TYPE` | `CLMTP_RF` | Not in source | 2-char value (`'12'` tested) | Claim type reference | UNSTRING; also routes SVC code (see below). |
| Units of service | `CLM-UNITS-OF-SERVICE` | `UNITS_NUM` | Not in source | Not in source | Units | UNSTRING. |
| Charge amount | `CLM-CHARGE-AMT` | `CHARGE_AMT` | numeric `S9(7)V99` (via `WS-DE-EDIT`) | 9 digits + 2 dec | Billed amount | De-edited through `WS-DE-EDIT`. |
| Paid amount | `CLM-PAID-AMT` | `PAID_AMT` | numeric `S9(7)V99` (via `WS-DE-EDIT`) | 9 digits + 2 dec | Paid amount | De-edited through `WS-DE-EDIT`. |
| Date of remittance | `CLM-DOR-A` | `REMIT_DT` | date text | 8→10 | Remit date | `YYYYMMDD` → `YYYY-MM-DD`. |
| Service from date | `CLM-SERVICE-DATE-FROM-A` | `SERVICE_FROM_DT` | date text | 8→10 | Service start | `YYYYMMDD` → `YYYY-MM-DD`. |
| Service to date | `CLM-SERVICE-DATE-TO-A` | `SERVICE_TO_DT` | date text | 8→10 | Service end | `YYYYMMDD` → `YYYY-MM-DD`. |
| Service/procedure code | `CLM-SVC-CODE` | `ICD9P_RF` **or** `NDCCD_RF` | Not in source | ICD9P truncated to 10 | Procedure or NDC drug code | If `CLM-CLAIM-TYPE='12'` → `NDCCD_RF`; else → `ICD9P_RF` (len capped at 10). |
| Primary diagnosis | `CLM-PRIMARY-DIAG-CODE` | `ICD9D_RF` | Not in source | Not in source | Primary diagnosis code | Decimal-point normalization (see data-mapping.md). |
| Secondary diagnosis | `CLM-SECOND-DIAG-CODE` | `ICD9D_2ND_RF` | Not in source | Not in source | Secondary diagnosis code | Same normalization as primary. |
| Create source | `CLM-CREATE-SOURCE` | `CREATE_SOURCE_NM` | code `'00'`/`'01'` | Not in source | Source system name | `'00'`→`STANDARD MEDICAID`, `'01'`→`DSS`. |
| ICD version | `CLM-CDE-ICD-VERSION` | `ICD_VERSION` | Not in source | Not in source | ICD code version | UNSTRING. |
| Agency code | `CLM-AGENCY-CODE` | `AGENCY_CD` | Not in source | Not in source | Agency code | UNSTRING. |
| County code | `CLM-COUNTY-CD` | `COUNTY_CD` | Not in source | Not in source | County code | Moved directly. |
| Alt client code | literal `'535'` or spaces | `ALT_CLIENT_CD` | literal | 3 | Alternate client code | `'535'` when contract `535`, else spaces. |
| RX written date | `CLM-RX-WRITTEN-DATE` | `RX_WRITTEN_DT` | date text | 10 | Prescription written date | Null indicator set when spaces/zeros/low-values (change `0027`). |
| Last update name | `WS-LAST-UPDATE-NM` (derived) | `LAST_UPDATE_NM` | text | length 8 | Audit user id | From contract mapping; length hard-set to 8. |
| Last update timestamp | `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | timestamp | — | Audit timestamp | DB2 `CURRENT TIMESTAMP`. |

## Field mapping — input/derived → DB2 `ARTCLKP` (insert path)

| Field Name | Source | Target | Notes |
|------------|--------|--------|-------|
| Context code | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | Same context as claim. |
| Case id | `CLM-HMS-CASE-KEY` | `CASE_ID` | Moved to `CLKP-CASE-ID`. |
| Claim id | `ARTCTPK.PK_NEXT_NUM - 1` | `CLAIM_ID` | Same id as inserted claim. |
| Relate indicator | literal `'0'` | `RELATE_IND` | Constant. |
| Auto-checked flag | literal `'N'` | `IS_AUTO_CHECKED` | Constant (change `0019`). |
| Last update name | `WS-LAST-UPDATE-NM` | `LAST_UPDATE_NM` | Length 8. |
| Last update timestamp | `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | DB2 timestamp. |

## Field mapping — DB2 `ARTCTPK` (key generation)

| Field Name | Source | Target | Notes |
|------------|--------|--------|-------|
| Context code | `WS-CONTEXT-CD` (derived) | `CONTEXT_CD` | Filter/key. |
| PK type | literal `'CLM'` | `PK_TYPE_CD` | Filter/key. |
| Next number | `PK_NEXT_NUM + 1` | `PK_NEXT_NUM` | Incremented on update; `+2` on insert of a new row. |
| PK description | literal `'CASE TRACKING SYSTEM CLAIM'` | `PK_DSC` | Insert path only. |
| PK mask | `CTPK-PK-MASK-TXT` | `PK_MASK_TXT` | Insert path only; source *not fully visible in provided source*. |
| Last update name | `WS-LAST-UPDATE-NM` | `LAST_UPDATE_NM` | Audit. |
| Last update timestamp | `CURRENT TIMESTAMP` | `LAST_UPDATE_DTM` | Audit. |

## Field mapping — DB2 `MISC.P_MONITOR` (run monitor)

| Field Name | Source | Target | Notes |
|------------|--------|--------|-------|
| Client code | `HMS-3BYTE-CONTRACT-NUM` | `CLIENT_CD` | WHERE filter. |
| Context code | `WS-CONTEXT-CD-1..7` | `CONTEXT_CD` | WHERE filter, per distinct context. |
| Process name | literal `LIKE 'CLKP_LOAD_DURATION_%'` | `PROCESS_NM` | WHERE filter. |
| End timestamp | `CURRENT TIMESTAMP` | `END_DTM` | Set. |
| Task step | literal `'LOAD'` | `TASK_STEP_TXT` | Set. |
| Status | `'SUCCESS'` / `'FAILURE'` | `STATUS_TXT` | Set from `WS-STATUS-TXT`. |
| Data count | `WS-CONTEXT-CD-n-CNT` (or `0`) | `DATA_CNT` | Per-context committed insert count. |

## Linkage-section / calling areas (from source)

| Structure | Fields | Purpose |
|-----------|--------|---------|
| `CASGETCC-CALLING-AREA` | `HMS-3BYTE-CONTRACT-NUM` X(3), FILLERs, `CASGETCC-RETURN-CODE` X(1) | Passed to `CASGETCC` to retrieve the contract number. |
| `ERROR-MESSAGE` | `ERROR-MESSAGE-LENGTH` S9(4) COMP +560, `ERROR-MESSAGE-LINE` X(80) OCCURS 7 | Passed to `DSNTIAR` for SQL error text. |
| `DUMP-CODE` | S9(4) COMP | Passed to `ILBOABN0` as the user abend code. |
| `DPSGTCON-CALLING-AREA` | (commented out) | Former contract-retrieval routine, **inactive**. |
