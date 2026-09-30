# CASNCTD9 — Modernization Notes

> Documents program **`CASNCTD9`** (`CASNCTD1` is *Not present in provided source — requires further input*).
> Recommendations are grounded in the observed behavior of the provided source only. External copybooks, DCLGENs, subprograms, and JCL are *not analyzed* and would be required before a full migration design.

## Recommended high-level strategy

CASNCTD9 is a classic **file-to-database upsert (load) batch job** with checkpoint/restart, per-tenant key generation, and run monitoring. A pragmatic modernization is to re-implement it as an **idempotent ETL/ELT pipeline** (or a batch service) that:

1. Ingests the claims extract,
2. Derives the tenant/context routing key,
3. Performs an **upsert** into the claim store,
4. Maintains the claim-to-case link,
5. Emits run metrics/status,
6. Supports safe reruns.

Because the logic is well-bounded and table-oriented, a **strangler-fig** approach is feasible: keep the DB2 tables initially, replace the COBOL program with a modern job that issues the same logical operations, then migrate the schema later.

## Likely source systems, outputs, and downstream consumers (from source)

| Role | Concrete artifact in source | Modern reading |
|------|-----------------------------|----------------|
| Upstream source | PCFCASE claims file ("NCTCLMS1 300 FILE"), delivered as a GDG generation | A periodic claims **extract/feed** (file drop, object storage, or streaming topic). |
| System of record | DB2 `ARTCCLM` (claims), `ARTCLKP` (claim↔case link), `ARTCTPK` (per-context keys) | Relational **claim store** with a link/junction table and a key-allocation concern. |
| Config source | `CTSPROD.SEC.ARTSPRF` preferences | A **feature-flag/configuration** service or table. |
| Run monitoring | `MISC.P_MONITOR` | A **job-observability**/metrics store or dashboard. |
| Restart state | `DB2CNTLO` control file | A **checkpoint/offset** store. |
| Downstream consumers | Case-management users and reporting that read `ARTCCLM`/`ARTCLKP` (implied by "Case Tracking System") | Case-management app + analytics. *Exact consumers not defined in provided source.* |

## Candidate modern equivalents for legacy concepts

| Legacy concept (in source) | Modern equivalent |
|----------------------------|-------------------|
| Sequential input file `NCTC-IN` (fixed 316-byte, copybook `NCTCLMS9`) | A typed schema (Avro/Protobuf/JSON Schema) with an explicit field contract; ingest via a file/object reader or a stream consumer. |
| Copybook field prefixes / `REPLACING` | A generated DTO/record class from the schema. |
| DB2 embedded SQL (`SELECT`/`UPDATE`/`INSERT`) | Parameterized queries via a data-access layer/ORM, or set-based SQL `MERGE`/`UPSERT`. |
| DB2 cursor `ARTSPRF-CSR` (preferences) | A cached configuration lookup loaded at startup. |
| `ARTCTPK` "increment then read-back" key generation | Database **identity/sequence** columns, or UUIDs — removes the manual counter table and its optimistic-concurrency check. |
| `WS-CONTEXT-CD` derivation (contract + client id) | A small **routing/mapping** component or lookup table (tenant/context resolver). |
| Flags & context codes (`CNTL-PROC-FLAG`, `RELATE_IND`, `IS_AUTO_CHECKED`, `PK_TYPE_CD='CLM'`) | Explicit enums/booleans in the schema; constants moved to configuration. |
| Commit every 300 + control-file checkpoint | Framework-managed **chunked transactions** with a persisted **checkpoint/offset** (e.g., Spring Batch, or a stream consumer's committed offset). |
| Restart-by-skipping N records | Idempotent upsert keyed by natural keys, making reruns inherently safe (no manual skip needed). |
| Lock/timeout retry (`-904/-911/-913`, `TIME-OUT-CTR`) | Built-in **retry with backoff** on transient DB errors. |
| `DISPLAY` counters | Structured logging + metrics (counts per context, inserts/updates, skips). |
| `DSNTIAR` / `ILBOABN0` abends with dump codes | Exception handling + non-zero exit codes / alerting; map `0998` (no-data) to a benign success signal. |
| `P_MONITOR` updates | Job telemetry (start/end, status, per-tenant volume) to an observability platform. |

## Suggested modern design patterns

- **ETL/upsert pipeline** — The core is a per-record upsert. A single set-based `MERGE` (or bulk load into a staging table + merge) would replace the row-at-a-time `SELECT`→`UPDATE`/`INSERT`, greatly improving throughput while preserving the update-vs-insert rule (see business-rules.md #5).
- **Batch orchestration** — Use a batch framework (e.g., Spring Batch, or a workflow orchestrator like Airflow/Argo/Step Functions) to provide chunked commits, checkpoint/restart, retry, and metrics — replacing the hand-rolled control-file and retry logic.
- **Idempotency by natural key** — Keying the upsert on `(context, ICN, claim status, case)` removes the need for the "skip N processed records" restart mechanism.
- **Configuration/feature flags** — Move the NY RX-encounter exclusion (and the contract→context maps) into a configuration service/table rather than code and a preferences read.
- **Event-driven option** — If the upstream feed can be per-claim events, a **stream consumer** (Kafka/Kinesis) with per-partition offset commits maps naturally onto the current commit/checkpoint model and enables near-real-time updates instead of periodic batches.
- **Data-warehouse/table schema** — For analytics, land claims in a warehouse (columnar) with the context code as a partition/tenant dimension; the per-context counts already computed by the program map directly to load-metrics facts.

## Migration considerations / risks (grounded in source)

- **Tenant/context routing is business-critical and intricate** — the contract→context and client-id→sub-context mappings (NY, FL, and the 6-char overlay clients) must be ported exactly; they determine which rows are written and how they are counted.
- **Data typing is currently opaque** — input field types/lengths come from copybook `NCTCLMS9` (not provided). A faithful schema must be reverse-engineered from that copybook before migration.
- **Diagnosis-code and date normalization** (decimal-point handling, `YYYYMMDD`→`YYYY-MM-DD`, ICD9P length cap of 10, NDC vs ICD routing) encode real formatting rules that downstream consumers likely depend on — preserve them.
- **Nullability rules** (e.g., `RX_WRITTEN_DT` null indicator) must be represented explicitly in the target schema.
- **Concurrency assumptions** — the manual `ARTCTPK` counter and its "last-update-name intervention" check exist because multiple applications share these tables; a modern key strategy must still guarantee uniqueness under concurrent writers.
- **The `0998` "no data = good completion"** convention must be reproduced so schedulers don't treat empty feeds as failures.

*No modernization recommendation here should be taken as a statement of fact about systems not present in the provided source.*
