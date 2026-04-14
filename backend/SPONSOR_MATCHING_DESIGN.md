# Sponsor Matching — Design Note

## Overview
Given a club profile (name, mission, university, preferred industries, support types),
return the **top 5** best-fit sponsors with structured reasoning.

## Pipeline

```
Club Profile
    │
    ▼
Embed club text (OpenAI text-embedding-3-small)
    │
    ▼
pgvector cosine search  →  top 15 candidates
    │
    ▼
Rule-based boost (industry overlap, support type overlap)
    │
    ▼
LLM rerank + explain (GPT-4o-mini, temperature=0)
  - input: club context + 15 candidate blurbs
  - output: ordered top 5 with score + reasons + suggested activation
    │
    ▼
Return MatchSponsorsResponse
```

## Why not RAG?
- We have ~30 curated sponsors in Postgres, not a dynamic corpus.
- Vector search over 30 rows is instant; no chunking/retrieval pipeline needed.
- The LLM rerank step is what makes matches *smart* — it reads full club context
  alongside sponsor descriptions and produces human-quality reasoning.
- RAG adds complexity (document loaders, chunk strategies) with zero benefit at this scale.

## What changed from v1?
1. **Vector search expanded** from top 5 → top 15 to give the reranker more candidates.
2. **Rule-based boost** adds 0-15% bonus for explicit field overlap (industries, support types).
3. **LLM rerank** (GPT-4o-mini) picks final top 5 with reasons and activation ideas.
4. **MatchSponsorsResult schema** extended with `reasons[]` and `suggested_activation`.

## Stability
Same club input → deterministic vector search → LLM rerank with temperature=0
→ stable top 5 across runs (minor ordering variance possible).

## Enrichment (optional, not in v1)
If team agrees: fetch sponsor `website_url`, summarize with LLM, cache in DB.
Only if ToS-safe and team approves.