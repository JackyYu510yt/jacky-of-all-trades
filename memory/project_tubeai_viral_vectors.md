---
name: project-tubeai-viral-vectors
description: TubeAI Viral Vectors were scraped into an LLM-consumable knowledge base for later YouTube title/concept ideation
metadata: 
  node_type: memory
  type: project
  originSessionId: 3d5f0b0d-ff46-43c4-b59f-aba0bd134f3f
---

Scraped the full **TubeAI Viral Vectors** dataset (beta.tubeai.app → Database → Viral Vectors) on 2026-06-15 via the live browser ([[reference-chrome-devtools-live-browser]]) and turned it into an LLM knowledge base for later database/ideation work. All files live in `D:\video_creation_stuff\Compiled Binaries\Tinkering\Viral Vectors\`.

**Deliverables (the knowledge base):**
- `VIRAL_VECTORS_GUIDE.md` — master reference an LLM loads first: field dictionary, "why it works" framework, ideation playbook, all 7 clusters explained.
- `viral_vectors.jsonl` — 5,075 enriched word records (one per line): metrics + top_niches breakdown + pairs + synonyms + derived S/A/B/C tier + auto-generated `reasoning` string.
- `clusters.json` — 7 psychological cluster definitions + stats + exemplars.
- `tubeai_graph_data.json` — graph network model: 500 nodes (top by niche_count) + 515 pair_edges + 80 synonym_edges.

**Raw scrape (source of truth):** `tubeai_words_full.json` (5,075 words, 23 fields incl. niche breakdown), `tubeai_pairs_full.json` (co-occurrence lifts), `tubeai_synonyms_full.json` (WordNet). Rebuild pipeline: `build_docs.py` → `generate_guide.py`; graph via `_build_graph.py`.

**Key data semantics:** `avg_outlier` = avg views-vs-channel-baseline multiplier (TubeAI metric, performance). `niche_count` = # niches the word is an outlier in, max 76 (universality). `pairs[].lift` = co-occurrence multiplier (the big wins live here, e.g. blow+mind 128x). 7 clusters: Awe, Conflict, Extreme, Hack, Hidden, Magnitude, Threat.

**How the API worked (for re-scrapes):** `/api/database/words/search?limit=500&sortBy=niche_count&sortOrder=desc` (caps 500/page, paginate via `nextCursor` while `hm`), plus `/words/pairs` and `/words/synonyms` (comma-sep `words=` batches). Responses are `{d: <base64 zlib-deflate JSON>, v}` — decompress in-page with `DecompressionStream('deflate')`. CAUTION: always re-select the tubeai page before fetching — the CDP-selected page drifts to other tabs and relative fetches then hit the wrong origin (silently returned empty once).
