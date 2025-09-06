# IPS Compliance System – Context Documentation (PostgreSQL, Latest Version Only, Persist Strategy)

## Purpose
We are building an AI-powered compliance knowledge system to ingest Investment Policy Statements (IPS),
extract guidelines, and make them queryable both deterministically (SQL) and semantically (vector search).

This system supports:
- Compliance monitoring
- Cross-fund comparison
- Auditable storage of rules
- Intelligent Q&A for portfolio managers

We always abide by the latest version of the IPS for each portfolio.  
No document versioning or history is maintained.

## Persist Strategy (Replace-on-Reingestion)
When the same IPS document (doc_id) is supplied again:
1. Portfolio → Upsert (insert if new, update name if changed).
2. Document → Upsert (replace metadata like date/name if changed).
3. Guidelines → Delete all rows for this doc_id, then insert the new set.
4. Embeddings → Delete all embeddings for those rules, then insert new ones.

This ensures:
- Only the latest rules for each document are kept.
- No duplicate guidelines or embeddings exist.

## PostgreSQL Schema
(see schema.sql in package)
