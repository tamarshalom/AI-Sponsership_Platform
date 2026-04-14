# Sponsor Matching Design (v2)

## Overview

Given a `ClubProfile`, return the top sponsor matches with:
- semantic similarity score,
- short reasons,
- one suggested activation idea.

## Pipeline

1. **Embed club context** with OpenAI embeddings (`text-embedding-3-small`).
2. **Vector retrieve top-K** sponsors from Postgres/pgvector (`embedding <=> query` cosine distance).
3. **Rule boost** candidates using explicit overlap:
   - preferred industries overlap
   - requested support type overlap
4. **LLM rerank** top candidates (model from `settings.openai_model`, temperature 0):
   - picks final top-N
   - returns `reasons[]` and `suggested_activation`
5. **Fallback safety**:
   - if rerank fails or API key is missing, return boosted vector ranking.

## Why this helps

- Vector search ensures semantic recall.
- Rule boost preserves deterministic signal for obvious field overlap.
- LLM rerank improves final ordering + explainability.
- Fallback keeps endpoint reliable under API failures.
