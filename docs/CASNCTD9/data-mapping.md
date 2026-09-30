# CASNCTD9 — Data Mapping & Transformations

> Documents program **`CASNCTD9`** (`CASNCTD1` is *Not present in provided source — requires further input*).
> Transformation logic is taken directly from the `PROCEDURE DIVISION`. Where the underlying copybook definition is needed to be certain, it is *External dependency not analyzed in provided source*.

## 1. Context-code derivation (source → target)

The **context code** (`WS-CONTEXT-CD`) is the routing key written to every target row. It is derived in two stages.

### Stage 1 — contract number → base context + audit name (`0000-MAIN`, `EVALUATE HMS-3BYTE-CONTRACT-NUM`)

- `HMS-3BYTE-CONTRACT-NUM` -> `WS-CONTEXT-CD` : mapped by lookup table below; also sets `WS-LAST-UPDATE-NM`.

| Contract | `WS-CONTEXT-CD` | `WS-LAST-UPDATE-NM` |
|----------|-----------------|----------------------|
| `320` | `CTSCASNY` | `WNYCDF40` |
| `300` | `CTSCASTST` | `WTTCDF40` (TEST) |
| `326` | `CTSCASCO` | `WCOCDF40` |
| `341` | `CTSCASOH` | `WOHCDF40` |
| `535` | `CTSCASOH` | `WCXCDF40` |
| `313` | `CTSCASFL` | `WFLCDF40` |
| `319` | `CTSCASCT` | `WCTCDF40` |
| `317` | `CTSWRCCA` | `WCACDF40` |
| `590` | `CTSCASAL` | `WALCDF40` |
| `330` | `CTSCASAR` | `WARCDF40` |
| `358` | `CTSCASNV` | `WNVCDF40` |
| `359` | `CTSCASNM` | `WNMCDF40` |
| `645` | `CTSCASWV` | `WWVCDF40` |
| any other | — | error → abend `0999` |

### Stage 2 — refine context for multi-context clients (`1000-MAINLINE`)

- `CLM-HMS-CLIENT-ID` -> `WS-CONTEXT-CD` : for multi-context contracts the client id overrides/augments the base context.

**Contracts `326`, `590`, `359`, `645`:** first 6 chars of `CLM-HMS-CLIENT-ID` are moved into `WS-CONTEXT-CD(1:6)` (via `WS-CONTEXT-CD6`).

**Contract `320` (NY)** — `EVALUATE CLM-HMS-CLIENT-ID`:

| `CLM-HMS-CLIENT-ID` | `WS-CONTEXT-CD` | Comment in code |
|---------------------|-----------------|-----------------|
| `CTSCEN` | `CTSCASEX-NY` | Casualty / Exchange / New York |
| `CTSCCN` | `CTSCASNYC` | Casualty / City / New York |
| `CTSECN` | `CTSESTNY` | Estate / City / New York City |
| `CTSEEN` | `CTSESTEX-NY` | Estate / Exchange / New York |
| `CTSCON` | `CTSCASNYOP1` | Casualty / Option 1 / New York |
| `CTSEON` | `CTSESTNYOP1` | Exchange / Option 1 / New York |
| other | `CTSCASNY` | Casualty New York (default) |

**Contract `313` (FL)** — `EVALUATE CLM-HMS-CLIENT-ID`:

| `CLM-HMS-CLIENT-ID` | `WS-CONTEXT-CD` | Comment in code |
|---------------------|-----------------|-----------------|
| `CTSCAS` | `CTSCASFL` | Casualty |
| `CTSEST` | `CTSESTFL` | Estate |
| `CTSTRS` | `CTSTRSFL` | Trust |
| `CTSMST` | `CTSCASMT-FL` | Mass Tort |
| other | `CTSCASFL` | Casualty (default) |

After derivation, `WS-CONTEXT-CD` is `UNSTRING`-ed (delimited by all spaces) to obtain its trimmed text (`WS-UNSTRING-T`) and length (`WS-UNSTRING-L`), which populate the VARCHAR host variables `CCLM-CONTEXT-CD`, `CTPK-CONTEXT-CD`, `CLKP-CONTEXT-CD`.

## 2. Field-by-field mapping (input → `ARTCCLM`)

Format: `source_field -> target_field : transformation`

- `CLM-ICN` -> `CCLM-ICN-NUM` (`ICN_NUM`) : trimmed of trailing spaces via UNSTRING; length captured for VARCHAR.
- `CLM-FORMER-ICN` -> `CCLM-PREV-ICN-NUM` (`PREV_ICN_NUM`) : UNSTRING trim + length.
- `CLM-RECIPIENT-ID-NUM` -> `CCLM-RECIP-MA-NUM` (`RECIP_MA_NUM`) : UNSTRING trim + length. *(An older 16-char truncation block is commented out and inactive.)*
- `CLM-PROVIDER-NUM` -> `CCLM-PROVIDER-ID` (`PROVIDER_ID`) : UNSTRING trim + length.
- `CLM-CLAIM-STATUS` -> `CCLM-CLMST-RF` (`CLMST_RF`) : moved directly; VARCHAR length hard-set to `1`.
- `CLM-TRANSACTION-TYPE` -> `CCLM-TRNTP-RF` (`TRNTP_RF`) : moved directly; length hard-set to `1`.
- `CLM-CLAIM-TYPE` -> `CCLM-CLMTP-RF` (`CLMTP_RF`) : UNSTRING trim + length.
- `CLM-UNITS-OF-SERVICE` -> `CCLM-UNITS-NUM` (`UNITS_NUM`) : UNSTRING trim + length.
- `CLM-CHARGE-AMT` -> `CCLM-CHARGE-AMT` (`CHARGE_AMT`) : moved through numeric edited field `WS-DE-EDIT` (`S9(7)V99`) to de-edit into a numeric value.
- `CLM-PAID-AMT` -> `CCLM-PAID-AMT` (`PAID_AMT`) : same de-edit through `WS-DE-EDIT`.
- `CLM-DOR-A` -> `CCLM-REMIT-DT` (`REMIT_DT`) : date reformat (see §3).
- `CLM-SERVICE-DATE-FROM-A` -> `CCLM-SERVICE-FROM-DT` (`SERVICE_FROM_DT`) : date reformat.
- `CLM-SERVICE-DATE-TO-A` -> `CCLM-SERVICE-TO-DT` (`SERVICE_TO_DT`) : date reformat.
- `CLM-SVC-CODE` -> `CCLM-NDCCD-RF` **or** `CCLM-ICD9P-RF` : conditional routing (see §4).
- `CLM-PRIMARY-DIAG-CODE` -> `CCLM-ICD9D-RF` (`ICD9D_RF`) : diagnosis normalization (see §5).
- `CLM-SECOND-DIAG-CODE` -> `CCLM-ICD9D-2ND-RF` (`ICD9D_2ND_RF`) : diagnosis normalization (see §5).
- `CLM-CREATE-SOURCE` -> `CCLM-CREATE-SOURCE-NM` (`CREATE_SOURCE_NM`) : decode `'00'`/`'01'` (see §6).
- `CLM-CDE-ICD-VERSION` -> `CCLM-ICD-VERSION` (`ICD_VERSION`) : UNSTRING trim + length.
- `CLM-AGENCY-CODE` -> `CCLM-AGENCY-CD` (`AGENCY_CD`) : UNSTRING trim + length.
- `CLM-COUNTY-CD` -> `CCLM-COUNTY-CD` (`COUNTY_CD`) : moved directly.
- (contract test) -> `CCLM-ALT-CLIENT-CD` (`ALT_CLIENT_CD`) : `'535'` if contract `535`, else spaces (see §7).
- `CLM-RX-WRITTEN-DATE` -> `RX_WRITTEN_DT` : null-indicator handling (see §8).
- `CLM-HMS-CASE-KEY` -> `CLKP-CASE-ID` (`ARTCLKP.CASE_ID`) : moved directly (used on insert path).
- `WS-LAST-UPDATE-NM` -> `CCLM/CLKP/CTPK LAST_UPDATE_NM` : moved directly; length hard-set to `8`.
- `CURRENT TIMESTAMP` -> `LAST_UPDATE_DTM` (all tables) : DB2 timestamp at execution.

## 3. Date handling / normalization

`CLM-DOR-A`, `CLM-SERVICE-DATE-FROM-A`, `CLM-SERVICE-DATE-TO-A` are 8-character `YYYYMMDD` strings, reformatted to a 10-character `YYYY-MM-DD` string by inserting `-` separators:

- positions `(1:4)` (year) -> target `(1:4)`
- literal `-` -> target `(5:1)`
- positions `(5:2)` (month) -> target `(6:2)`
- literal `-` -> target `(8:1)`
- positions `(7:2)` (day) -> target `(9:2)`

No validity checking of the date values is performed — *validation of these dates is not present in provided source* (the fields are reformatted unconditionally).

## 4. Service-code routing (decision table)

Driven by `CLM-CLAIM-TYPE`:

| Condition | Action |
|-----------|--------|
| `CLM-CLAIM-TYPE = '12'` (RX/pharmacy) | `CLM-SVC-CODE` -> `CCLM-NDCCD-RF` (NDC drug code), UNSTRING trim + length. |
| otherwise | `CLM-SVC-CODE` -> `CCLM-ICD9P-RF` (procedure code), UNSTRING trim + length; if resulting length `> 10`, force length to `10` (change `0020`, column-width fit). |

## 5. Diagnosis-code normalization (primary and secondary)

Applied identically to `CLM-PRIMARY-DIAG-CODE` → `ICD9D_RF` and `CLM-SECOND-DIAG-CODE` → `ICD9D_2ND_RF` (change `0010`):

1. Copy the diagnosis code to a 7-byte work field `WK-DIAG-CODE`.
2. Count characters **before** the first `.` (decimal point) using `INSPECT … TALLYING … BEFORE INITIAL '.'` into `COUNT-M`.
3. **Decision table:**

| Condition (`COUNT-M`) | Action |
|-----------------------|--------|
| `= 3` (3 chars before the dot) | Split into two 3-char halves (`WS-DIAG-CODE-41`/`-42`), recombine without the dot into `WS-DIAG-CODE-N` (6 chars), then UNSTRING into the target reference field + length. |
| `> 0` and `≠ 3` | If the first character is a space, left-shift the code by one position and blank position 7; then UNSTRING the (possibly shifted) code into the target + length. |
| `= 0` (no dot / leading positions) | UNSTRING the code as-is into the target + length. |

Effect: removes the embedded decimal point when the integer portion is 3 digits and left-justifies codes that have a leading space. *(The full ICD formatting intent beyond the visible code is Transformation not fully visible in provided source.)*

## 6. Create-source decode (decision table)

`CLM-CREATE-SOURCE` -> `CCLM-CREATE-SOURCE-NM` (change `0005`):

| `CLM-CREATE-SOURCE` | `CREATE_SOURCE_NM` |
|---------------------|--------------------|
| `'00'` | `STANDARD MEDICAID` |
| `'01'` | `DSS` |
| other | (no move — field left unchanged for this record) |

## 7. Alternate-client code (decision table)

| Condition | `CCLM-ALT-CLIENT-CD` (`ALT_CLIENT_CD`) |
|-----------|----------------------------------------|
| `HMS-3BYTE-CONTRACT-NUM = '535'` | `'535'` |
| otherwise | spaces |

## 8. RX-written-date null handling (decision table)

`CLM-RX-WRITTEN-DATE` -> `RX_WRITTEN_DT` with a DB2 null indicator (change `0027`), on both the update and insert paths:

| Condition | `RX-WRITTEN-DT-VALUE` | `RX-WRITTEN-DT-INDICATOR` | DB2 effect |
|-----------|----------------------|---------------------------|------------|
| `CLM-RX-WRITTEN-DATE` = SPACES **or** ZEROS **or** LOW-VALUES | spaces | `-1` | column set to NULL |
| otherwise | `CLM-RX-WRITTEN-DATE` | `+1` | column set to the value |

## 9. Derived / computed values

| Derived value | How computed |
|---------------|--------------|
| `CLAIM_ID` (insert) | `ARTCTPK.PK_NEXT_NUM` is incremented by 1, then `PK_NEXT_NUM - 1` is selected and used as the new `CLAIM_ID` for both `ARTCCLM` and `ARTCLKP`. |
| `WS-CONTEXT-CD-1..7` + counts | On successful insert, the current context is recorded into the first empty of seven "seen-context" slots; the matching slot's counter (`WS-CONTEXT-CD-n-CNT`) is incremented — used to report per-context volumes to `P_MONITOR` and the counter display. |
| Restart skip count | `WS-CNTL-RECS-OUT-TOT` accumulated from control-file records; `CRP-IN = WS-CNTL-RECS-OUT-TOT + 1` records are read/skipped before mainline processing. |
| `LAST_UPDATE_DTM`, `CREATE`/monitor timestamps | DB2 `CURRENT TIMESTAMP`. |

## 10. Existing-claim lookup (drives UPDATE vs INSERT)

Singleton `SELECT L.CLAIM_ID FROM ARTCCLM C, ARTCLKP L` joined on `CONTEXT_CD` + `CLAIM_ID`, filtered by `C.CONTEXT_CD = context`, `C.ICN_NUM = ICN`, `C.CLMST_RF = claim status`, `L.CONTEXT_CD = context`, `L.CASE_ID = case id`.

| `SQLCODE` | Meaning | Action |
|-----------|---------|--------|
| `+0` | claim found | `1100-UPDATE-ARTCCLM` |
| `+100` | not found | `1200-INSERT-ARTCCLM` |
| `-811` | more than one row | display error → abend |
| `-904` / `-911` / `-913` | resource unavailable / deadlock / timeout | retry logic (see business-rules.md) |
| other | unexpected | display error → abend |
