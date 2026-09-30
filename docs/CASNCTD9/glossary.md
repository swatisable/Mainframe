# CASNCTD9 — Glossary

> Documents program **`CASNCTD9`** (`CASNCTD1` is *Not present in provided source — requires further input*).
> "Meaning as used in source" reflects only what the code/comments state. Where the source does not define a term it is marked **"Meaning not defined in provided source."** A few widely-standard mainframe/DB2 terms include a general note explicitly labeled as *general industry term*.

## Programs & called modules

| Term | Meaning as used in source |
|------|---------------------------|
| `CASNCTD9` | This program: updates DB2 tables from the PCFCASE claims file; "cloned from CASNCTD7 for NY only". |
| `CASNCTD7`, `CASNCTD2` | Predecessor programs this one was cloned from (per comments). Not otherwise defined. |
| `CASGETCC` | Called program that returns the 3-byte HMS contract number (`CASGETCC-RETURN-CODE = '0'` on success). |
| `DPSGTCON` | Former contract-retrieval routine — **commented out / inactive**. |
| `DSNTIAR` | IBM DB2 routine that formats `SQLCA` into printable error message lines (*general industry term*). |
| `ILBOABN0` | IBM routine that forces a user abend with a numeric dump code (*general industry term*). |

## Files, DDNAMEs & datasets

| Term | Meaning as used in source |
|------|---------------------------|
| `NCTC-IN` | Input claims file (COBOL FD); fixed 316-byte records. |
| `NCTCLMI` | DDNAME assigned to `NCTC-IN`. |
| PCFCASE claims file / "NCTCLMS1 300 FILE" | The source claims extract loaded by this program. Meaning of "PCFCASE"/"300" not further defined in provided source. |
| `NCTCLMS9` | Copybook defining the input record layout (COPY … REPLACING `(PREFIX)` BY `CLM`). Contents not in provided source. |
| `CNTL-IO` | Control/checkpoint file (COBOL FD); 38-byte records; read for restart, written at each commit. |
| `DB2CNTLO` | DDNAME assigned to `CNTL-IO`. |
| GDG ("NEW CURRENT GDG") | The generation of the claims file being processed. *General industry term:* Generation Data Group. Not explicitly defined in source. |

## DB2 tables

| Term | Meaning as used in source |
|------|---------------------------|
| `ARTCCLM` | Claim table (primary target for insert/update). Comment: "CLAIM TABLE". |
| `ARTCLKP` | Claim lookup / claim-to-case link table. Comment: "CLAIM LOOKUP TABLE". |
| `ARTCTPK` / `DB2AR01.ARTCTPK` | Primary-key table: per-context next-number generator. Comment: "PRIMARY KEY TABLE". |
| `CTSPROD.SEC.ARTSPRF` | Preferences table read for the NY RX-encounter exclusion list. Comment: "PREFERENCES TABLE". |
| `MISC.P_MONITOR` | Process-monitor table updated with run status and per-context counts. |
| `SYSIBM.SYSDUMMY1` | DB2 single-row system table used to fetch `CURRENT TIMESTAMP` (*general industry term*). |

## DB2 columns (as used in SQL)

| Column | Table | Meaning as used in source |
|--------|-------|---------------------------|
| `CONTEXT_CD` | ARTCCLM/ARTCLKP/ARTCTPK/P_MONITOR/ARTSPRF | Client/state/line-of-business routing key derived by the program. |
| `CLAIM_ID` | ARTCCLM/ARTCLKP | Claim surrogate key generated from `ARTCTPK`. |
| `ICN_NUM` | ARTCCLM | Claim ICN number (from `CLM-ICN`). "ICN" not expanded in source. |
| `PREV_ICN_NUM` | ARTCCLM | Prior/former ICN (from `CLM-FORMER-ICN`). |
| `RECIP_MA_NUM` | ARTCCLM | Recipient Medicaid number (from `CLM-RECIPIENT-ID-NUM`). |
| `PROVIDER_ID` | ARTCCLM | Provider id (from `CLM-PROVIDER-NUM`). |
| `CLMST_RF` | ARTCCLM | Claim-status reference (from `CLM-CLAIM-STATUS`); also a lookup key. |
| `TRNTP_RF` | ARTCCLM | Transaction-type reference (from `CLM-TRANSACTION-TYPE`). |
| `CLMTP_RF` | ARTCCLM | Claim-type reference (from `CLM-CLAIM-TYPE`). |
| `UNITS_NUM` | ARTCCLM | Units of service. |
| `CHARGE_AMT` / `PAID_AMT` | ARTCCLM | Charge / paid amounts (de-edited numeric). |
| `REMIT_DT` | ARTCCLM | Remittance date (`YYYY-MM-DD`) from `CLM-DOR-A`. |
| `SERVICE_FROM_DT` / `SERVICE_TO_DT` | ARTCCLM | Service date range (`YYYY-MM-DD`). |
| `ICD9P_RF` | ARTCCLM | Procedure code (non-RX claims); capped at 10 chars. |
| `ICD9D_RF` / `ICD9D_2ND_RF` | ARTCCLM | Primary / secondary diagnosis code references. |
| `NDCCD_RF` | ARTCCLM | NDC drug code (RX claims, `CLM-CLAIM-TYPE='12'`). |
| `CREATE_SOURCE_NM` | ARTCCLM | Decoded source name (`STANDARD MEDICAID` / `DSS`). |
| `ICD_VERSION` | ARTCCLM | ICD code version (from `CLM-CDE-ICD-VERSION`). |
| `ALT_CLIENT_CD` | ARTCCLM | Alternate client code (`'535'` for contract 535). |
| `AGENCY_CD` | ARTCCLM | Agency code. |
| `COUNTY_CD` | ARTCCLM | County code. |
| `RX_WRITTEN_DT` | ARTCCLM | Prescription written date (nullable). |
| `LAST_UPDATE_NM` / `LAST_UPDATE_DTM` | ARTCCLM/ARTCLKP/ARTCTPK | Audit user id / timestamp. |
| `CASE_ID` | ARTCLKP | Case key (from `CLM-HMS-CASE-KEY`). |
| `RELATE_IND` | ARTCLKP | Relate indicator; constant `'0'` on insert. Meaning not defined in provided source. |
| `IS_AUTO_CHECKED` | ARTCLKP | Auto-checked flag; constant `'N'` on insert. Meaning not defined in provided source. |
| `PK_TYPE_CD` | ARTCTPK | Primary-key type; this program uses `'CLM'`. |
| `PK_NEXT_NUM` | ARTCTPK | Next primary-key number (incremented; value-1 used as new id). |
| `PK_DSC` / `PK_MASK_TXT` | ARTCTPK | PK description (`'CASE TRACKING SYSTEM CLAIM'`) / mask text. |
| `NAME_CD` / `VALUE_TXT` | ARTSPRF | Preference key / value; queried for `NY_RX_ENCOUNTER_EXCLUSION` = `'TRUE'`. |
| `CLIENT_CD` / `PROCESS_NM` / `TASK_STEP_TXT` / `STATUS_TXT` / `DATA_CNT` / `END_DTM` | P_MONITOR | Monitor keys/values updated at end of run. |

## Context codes (values assigned in code)

| Value | Meaning as used in source |
|-------|---------------------------|
| `CTSCASNY` | Casualty New York (contract 320 default). |
| `CTSCASEX-NY`, `CTSCASNYC`, `CTSESTNY`, `CTSESTEX-NY`, `CTSCASNYOP1`, `CTSESTNYOP1` | NY sub-contexts selected by `CLM-HMS-CLIENT-ID` (see data-mapping.md; comments explain the CEN/CCN/ECN/EEN/CON/EON letter codes). |
| `CTSCASTST` | Test context (contract 300). |
| `CTSCASCO`, `CTSCASOH`, `CTSCASFL`, `CTSCASCT`, `CTSWRCCA`, `CTSCASAL`, `CTSCASAR`, `CTSCASNV`, `CTSCASNM`, `CTSCASWV` | State/client base contexts (CO, OH, FL, CT, CA, AL, AR, NV, NM, WV). |
| `CTSESTFL`, `CTSTRSFL`, `CTSCASMT-FL` | FL sub-contexts (Estate, Trust, Mass Tort) selected by client id (contract 313). |

## Working-storage flags, codes & values

| Term | Meaning as used in source |
|------|---------------------------|
| `HMS-3BYTE-CONTRACT-NUM` | 3-byte contract number from `CASGETCC`; drives all routing. |
| `WS-CONTEXT-CD` | Current derived context code. |
| `WS-LAST-UPDATE-NM` | Audit user id chosen per contract (e.g., `WNYCDF40`). |
| `CNTL-PROC-FLAG` | `'-'` = valid checkpoint record; `'N'` = bypass control-file processing. |
| `CLM-CLAIM-TYPE = '12'` | RX / pharmacy claim (routes service code to NDC; subject to NY RX exclusion). |
| `CLM-CREATE-SOURCE '00' / '01'` | `STANDARD MEDICAID` / `DSS`. |
| `SQL-COMMIT-FREQ (+300)` | Commit frequency. |
| `TIME-OUT-CTR` | DB2 lock/timeout retry counter; loop aborts at `>= 5`. |
| `WS-RX-EXCL-*` | In-memory NY RX-exclusion context table and counters (max 50). |
| `RX-WRITTEN-DT-INDICATOR` | DB2 null indicator (`-1` NULL, `+1` value) for `RX_WRITTEN_DT`. |

## Status / return codes

| Code | Meaning as used in source |
|------|---------------------------|
| `SQLCODE +0` | Success. |
| `SQLCODE +100` | No row found. |
| `SQLCODE -811` | Singleton SELECT returned multiple rows (fatal). |
| `SQLCODE -904` | Resource unavailable (retry). |
| `SQLCODE -911` | Deadlock/timeout, rollback performed (retry). |
| `SQLCODE -913` | Deadlock/timeout, no rollback (retry). |
| Dump `0999` | Contract retrieval failure / unknown contract → abend. |
| Dump `0998` | Input empty or all records already processed; documented as "good completion" for no data. |
| Dump `3645` | Default abend code for generic fatal errors. |
| `STATUS_TXT 'SUCCESS' / 'FAILURE'` | Run outcome written to `P_MONITOR`. |

## Abbreviations

| Abbrev. | Meaning as used in source |
|---------|---------------------------|
| HMS | Installation name (program header `INSTALLATION. HMS`); also prefix in `HMS-3BYTE-CONTRACT-NUM`, `HMS-CASE-KEY`, `HMS-CLIENT-ID`. Not expanded in source. |
| CTS | Prefix of all context codes ("Case Tracking System" per `PK_DSC = 'CASE TRACKING SYSTEM CLAIM'`). |
| ICN | Claim number stored in `ICN_NUM`. Full expansion not defined in provided source. |
| RF (in `*_RF` columns) | Reference/code suffix. Meaning not defined in provided source. |
| NDC | Drug code stored in `NDCCD_RF` (RX claims). *General industry term:* National Drug Code. |
| ICD / ICD9P / ICD9D | Diagnosis/procedure code fields. *General industry term:* International Classification of Diseases. |
| DSS | Create-source decode for `CLM-CREATE-SOURCE = '01'`. Full expansion not defined in provided source. |
| LUW | "Unit of work" referenced in comments (DB2 commit scope). *General industry term:* Logical Unit of Work. |
| RC | Return code (used in comments, e.g., "RC 0998"). |
