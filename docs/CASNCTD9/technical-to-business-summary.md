# CASNCTD9 — Technical-to-Business Summary

> Documents program **`CASNCTD9`** (`CASNCTD1` is *Not present in provided source — requires further input*).
> Plain-English summary for non-mainframe readers, grounded only in the provided source.

## What the program does

`CASNCTD9` is a scheduled **batch load program**. Each run reads a file of case-related **claims** (the "PCFCASE claims file") and applies those claims to the **Case Tracking System** database in DB2. For every claim it decides whether that claim already exists in the database:

- If it **already exists**, the program **updates** the stored claim with the latest values.
- If it is **new**, the program **inserts** the claim and also creates a **link record** that ties the claim to its case, assigning a fresh internal claim id.

It processes one client/state at a time — the specific client is identified by a **contract number** the program looks up at startup — and it labels every row it writes with a **context code** that encodes the client, state, and line of business (for example, Casualty vs. Estate vs. Trust for New York or Florida).

## Why it exists

The program keeps the Case Tracking System's claim tables **in sync** with the incoming claims extract so that downstream case-management users and processes see current claim data (status, amounts, dates, diagnosis/procedure/drug codes, provider and recipient identifiers, etc.). It exists to **automate the bulk maintenance** of these claim and claim-to-case link tables, including generating the internal claim keys and recording who/when each row was last updated.

The header comment states it was **cloned from an earlier program (CASNCTD7) specifically for New York**, and over years of change history it was extended to support many additional states and sub-contexts.

## What data it reads and writes

**Reads**
- The **claims extract file** (fixed-length records) — the main input.
- A small **control file** to know how many records earlier runs already committed, so a restart does not double-process.
- A DB2 **preferences table** to learn which New York contexts should exclude pharmacy (RX) "encounter" claims.
- The **claim, claim-lookup, and primary-key tables** in DB2 to check for existing claims and to obtain the next claim id.

**Writes**
- The **claim table** (`ARTCCLM`) — insert or update.
- The **claim-lookup/link table** (`ARTCLKP`) — insert for new claims.
- The **primary-key table** (`ARTCTPK`) — to advance the per-context claim-id counter.
- A **process-monitor table** (`MISC.P_MONITOR`) — end time, status, and per-context row counts.
- The **control file** — checkpoint records at each commit.
- The **job log** — banners, informational/warning/error messages, and end-of-run counters.

## Which decisions it makes

- **Which client/state** a run is for (from the contract number) and **which context code** each claim belongs to (refined by the claim's client id for multi-context states like NY and FL).
- **Update vs. insert** for each claim, based on whether a matching claim already exists.
- **Whether to skip** a pharmacy (RX) claim, when the client's context is on the New York RX-encounter exclusion list.
- **How to format and normalize** values: dates to `YYYY-MM-DD`, monetary amounts to numeric, diagnosis codes (decimal-point handling), and routing the service code to either an NDC drug code or an ICD procedure code depending on claim type.
- **How to recover** from database lock/timeout conditions (retry up to five times) and **when to fail** the run (unknown contract, duplicate claim, commit failure, or unexpected SQL error) — in which case it rolls back, records `FAILURE`, and abends.
- **When to commit** (every 300 operations) and **where to resume** after an interrupted run (via the control file).

## How it contributes to the business process

`CASNCTD9` is the **data-integration step** that turns a periodic claims feed into current, queryable claim records inside the Case Tracking System, correctly attributed to the right client, state, and line of business. By maintaining the claim-to-case links and per-context claim keys, it enables case managers and downstream reporting/monitoring (the `P_MONITOR` table records each run's success and volumes) to rely on **up-to-date, consistently coded claim data**. Its restart/checkpoint and retry logic make the nightly/periodic load **safe to rerun** without duplicating work, which is essential for a dependable production batch pipeline.

*Business meaning beyond what the code states (e.g., the precise definition of each status/flag, or the exact upstream/downstream systems) is not defined in the provided source.*
