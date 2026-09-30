# CASNCTD9 — Business Rules

> Documents program **`CASNCTD9`** (`CASNCTD1` is *Not present in provided source — requires further input*).
> Every rule below is taken from the `PROCEDURE DIVISION` or DB2 SQL of the program. Rules that depend on external copybooks are labeled where relevant.

## Business & processing rules

1. **Contract number must be resolvable.** The program calls `CASGETCC`; if `CASGETCC-RETURN-CODE ≠ '0'`, it displays an error, sets dump code `0999`, and abends.

2. **Contract number must be a known value.** `HMS-3BYTE-CONTRACT-NUM` is mapped by `EVALUATE` to a base context code and audit user name. Any unrecognized contract (`WHEN OTHER`) displays "UNKNOWN HMS-3BYTE-CONTRACT-NUM", sets dump code `0999`, and abends. (Recognized values: `320, 300, 326, 341, 535, 313, 319, 317, 590, 330, 358, 359, 645`.)

3. **State/client-specific context routing.** The context written to DB2 depends on both the contract and, for multi-context clients, `CLM-HMS-CLIENT-ID`:
   - Contracts `326, 590, 359, 645`: first 6 characters of `CLM-HMS-CLIENT-ID` overlay the context code.
   - Contract `320` (NY): `CTSCEN→CTSCASEX-NY`, `CTSCCN→CTSCASNYC`, `CTSECN→CTSESTNY`, `CTSEEN→CTSESTEX-NY`, `CTSCON→CTSCASNYOP1`, `CTSEON→CTSESTNYOP1`, else `CTSCASNY`.
   - Contract `313` (FL): `CTSCAS→CTSCASFL`, `CTSEST→CTSESTFL`, `CTSTRS→CTSTRSFL`, `CTSMST→CTSCASMT-FL`, else `CTSCASFL`.

4. **NY RX-encounter exclusion.** At startup the program reads `CTSPROD.SEC.ARTSPRF` where `NAME_CD = 'NY_RX_ENCOUNTER_EXCLUSION'` and `UPPER(VALUE_TXT) = 'TRUE'`, loading the returned `CONTEXT_CD` values into memory (max 50). During insert, if a claim's `CLM-CLAIM-TYPE = '12'` (RX) **and** its context is in that list, the **insert is skipped** and the skip counter is incremented. (Change `0028`; applies to the new-claim path only.)

5. **Update-vs-insert decision.** For each claim the program performs a lookup joining `ARTCCLM` and `ARTCLKP` (by context, ICN, claim status, and case id):
   - Found (`SQLCODE +0`) → **update** the existing `ARTCCLM` row.
   - Not found (`SQLCODE +100`) → **insert** new `ARTCCLM` (+ `ARTCLKP`) rows.

6. **Duplicate-claim guard.** If the lookup returns `SQLCODE -811` (more than one matching row), the program treats it as a data error, displays the offending ICN / previous ICN, and abends. (There must not be multiple `CLAIM_ID`s for the same ICN.)

7. **Primary-key generation.** New claim ids come from `ARTCTPK` per context (`PK_TYPE_CD = 'CLM'`): `PK_NEXT_NUM` is incremented by 1, then `PK_NEXT_NUM - 1` is used as the new `CLAIM_ID`. If no `ARTCTPK` row exists for the context (`SQLCODE +100`), a new one is inserted (`PK_NEXT_NUM = +2`, `PK_DSC = 'CASE TRACKING SYSTEM CLAIM'`) and a warning is displayed.

8. **Optimistic-concurrency check on `ARTCTPK`.** After re-selecting the counter row, if `LAST_UPDATE_NM` on the row does not equal the program's own `WS-LAST-UPDATE-NM`, the program concludes another application updated the table in the current unit of work, displays "UNCOMMITTED INTERVENTION TO ARTCTPK TABLE", and abends.

9. **Claim-type governs service-code target.** `CLM-CLAIM-TYPE = '12'` routes `CLM-SVC-CODE` to `NDCCD_RF` (NDC drug code); any other claim type routes it to `ICD9P_RF` (procedure code), whose length is capped at 10.

10. **Diagnosis-code decimal normalization.** For primary and secondary diagnosis codes, if there are exactly 3 characters before the `.`, the decimal point is removed and the two segments are recombined; if there is a leading space, the code is left-shifted one position. (Change `0010`.)

11. **Create-source decode.** `CLM-CREATE-SOURCE = '00'` → `CREATE_SOURCE_NM = 'STANDARD MEDICAID'`; `'01'` → `'DSS'`. Other values leave the field unchanged. (Change `0005`.)

12. **Alternate client code for contract 535.** When `HMS-3BYTE-CONTRACT-NUM = '535'`, `ALT_CLIENT_CD = '535'`; otherwise spaces. (Change `0016`, OH CareSource.)

13. **RX-written-date nullability.** When `CLM-RX-WRITTEN-DATE` is spaces, zeros, or low-values, `RX_WRITTEN_DT` is written as SQL NULL (indicator `-1`); otherwise the value is written (indicator `+1`). (Change `0027`, NY contexts.)

14. **Date reformatting.** Remit, service-from, and service-to dates are reformatted from `YYYYMMDD` to `YYYY-MM-DD` unconditionally (no date validation is present).

15. **Commit frequency / checkpointing.** After every `SQL-COMMIT-FREQ = 300` uncommitted operations the program commits, writes a checkpoint record to the control file, rolls the per-commit counters into totals, and resets the timeout counter.

16. **Restart / skip-already-processed.** At startup the control file (`DB2CNTLO`) is read to compute the number of previously committed records (`WS-CNTL-RECS-OUT-TOT`); the program then reads (skips) `WS-CNTL-RECS-OUT-TOT + 1` input records before beginning mainline processing so a rerun does not reprocess committed data.
    - If the control record's `CNTL-PROC-FLAG = 'N'`, the message "BYPASS DB2 CONTROL FILE PROCESSING" is displayed.

17. **Empty / fully-processed input handling.** If, during the skip loop, end-of-file is reached:
    - with `REC-READ-CTR = 0` → "PCFCASE CLAIMS FILE IS EMPTY";
    - otherwise → "ALL … INPUT RECORDS HAVE BEEN PROCESSED PREVIOUSLY".
    In both cases dump code `0998` is set and control passes to the error exit. Per comment `0011`, RC `0998` denotes **good completion when there is no data** in the input file.

18. **Process-monitor reporting.** On completion the program updates `MISC.P_MONITOR` (rows where `CLIENT_CD = contract`, `PROCESS_NM LIKE 'CLKP_LOAD_DURATION_%'`) with `END_DTM`, `TASK_STEP_TXT = 'LOAD'`, `STATUS_TXT` (`SUCCESS` on normal end, `FAILURE` on abend), and per-context `DATA_CNT`.

## Validation conditions

| Validation | Where | Outcome if it fails |
|------------|-------|---------------------|
| `CASGETCC-RETURN-CODE = '0'` | `0000-MAIN` | Abend `0999`. |
| Contract number recognized | `EVALUATE` in `0000-MAIN` | Abend `0999`. |
| Cursor open on `ARTSPRF` succeeds (`SQLCODE +0`) | `0600` | Abend (error exit). |
| Lookup returns at most one row (not `-811`) | `1000-MAINLINE` | Abend. |
| `ARTCTPK.LAST_UPDATE_NM` unchanged by others | `1200-INSERT` | Abend. |
| Commit succeeds (`SQLCODE +0`) | `1900` | Abend. |

## DB2 return-code handling (all statements)

| `SQLCODE` | Interpretation | Program response |
|-----------|----------------|------------------|
| `+0` | success | continue / count |
| `+100` | row not found | context-dependent: insert claim, insert `ARTCTPK`, or (on `P_MONITOR`) log "row non-existent" |
| `-811` | multiple rows on singleton select | display + abend |
| `-904` | resource unavailable | retry (see below) |
| `-911` | deadlock/timeout (rollback done) | retry (see below) |
| `-913` | deadlock/timeout (no rollback) | retry (see below) |
| any other | unexpected error | display + abend |

### Lock/timeout retry rule (`-904 / -911 / -913`)

- If **nothing is uncommitted** in the current unit of work (`SQL-NOT-COMMITED-YET-CTR = 0`): increment `TIME-OUT-CTR`, display attempt count, optionally `ROLLBACK` (when `TIME-OUT-CTR < 5`), and `GO TO 1000-MAINLINE-EXIT` to retry the record.
- If there **is** uncommitted work: `GO TO Z9999-ERROR-EXIT` (abend and roll back the whole unit of work).
- The mainline loop terminates when `TIME-OUT-CTR >= 5`, and the program goes to the error exit.

## Return codes / abend (dump) codes

| Code | Trigger | Meaning |
|------|---------|---------|
| `0999` | contract retrieval failure / unknown contract | Fatal configuration error → abend. |
| `0998` | input empty or all records already processed | Signaled via abend routine; documented in code as **good completion** for no-data. |
| `3645` (default `DUMP-CODE`) | any `Z9999-ERROR-EXIT` reached without a specific code (e.g., SQL failures) | Generic fatal error → abend. |

Normal completion path issues `GOBACK` (no abend) after a successful final commit and `SUCCESS` monitor update.

## Open/closed & flag-based rules present in source

- **`CNTL-PROC-FLAG`** (`'-'` vs `'N'`): `'-'` marks a valid checkpoint record used for restart counting and is the value written at each commit; `'N'` causes a "bypass control file processing" message.
- **`RELATE_IND = '0'`** and **`IS_AUTO_CHECKED = 'N'`**: constants written on every new `ARTCLKP` link row.
- **`PK_TYPE_CD = 'CLM'`**: the only primary-key type this program manages in `ARTCTPK`.
- No explicit "claim open/closed" status rule is present beyond `CLMST_RF` being carried through and used as a lookup key — *any open/closed business meaning of `CLMST_RF` is not defined in provided source.*
