# EduSearch AI

Hybrid e-learning course search engine combining **lexical search**, **semantic (vector) search** and a **RDF/OWL knowledge graph**, served by FastAPI and a React front end.

> Learn smarter. Search beyond keywords.

## Features

- **Three search modes**: lexical (BM25), semantic (embeddings) and hybrid, with Reciprocal Rank Fusion.
- **Knowledge graph reasoning** (Fuseki / SPARQL): domain expansion through transitive `sousDomaineDe`, entity linking and disambiguation, prerequisite-based exclusion.
- **Explainable results**: "Why this result?" panel with per-component scores and matched / related concepts.
- **Live evaluation**: Precision@k, Recall@k and NDCG@k for lexical vs. vector vs. hybrid.
- **React UI**: Search, Compare Search (3 columns), Explore, Course Details, interactive Knowledge Graph (D3), prerequisite graph, dark mode, favorites.
- 70 courses across 14 domains, with a matching ontology.

## Architecture

```
.
├── docker-compose.yml      # Elasticsearch + Apache Jena Fuseki
├── ontology/               # elearning.ttl / elearning.rdf (RDF/OWL)
├── backend/
│   ├── main.py             # FastAPI entry point
│   ├── config.py           # service URLs, embedding model, fusion weights
│   ├── index_data.py       # indexes data/cours.json into Elasticsearch
│   ├── generate_dataset.py # regenerates cours.json and the ontology
│   ├── routers/            # search, courses, graph, evaluation, meta
│   ├── services/           # elastic, embedding, graph (SPARQL), ranking, evaluation
│   ├── models/schemas.py   # Pydantic schemas
│   └── tests/              # offline unit tests (ranking / fusion)
├── evaluation/evaluate.py  # CLI evaluation (P@5, R@5, NDCG@5)
└── frontend/               # React + Vite
```

## Prerequisites

Docker, Python 3.10+, Node.js 18+.

## Getting started

### 1. Start Elasticsearch and Fuseki

```bash
cp .env.example .env      # optional: set FUSEKI_ADMIN_PASSWORD
docker compose up -d
```

### 2. Load the ontology into Fuseki

Open http://localhost:3030, log in as `admin`, select the `elearning` dataset, then **upload files** → `ontology/elearning.ttl`.

### 3. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python index_data.py            # once: indexes the courses (computes embeddings)
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173. The API URL defaults to `http://localhost:8000/api`; override it with `VITE_API_BASE`.

## Try it

- `python pour débutant`: lexical match.
- `apprendre à coder sans expérience`: semantic match without shared keywords.
- `intelligence artificielle`: no course contains the exact term, but the graph expands it to its sub-domains.
- `deep learning avancé pytorch`: advanced course excluded when prerequisites are not met.

## Evaluation and tests

```bash
# with the backend running
cd evaluation && pip install -r requirements.txt && python evaluate.py

# unit tests (no Elasticsearch / Fuseki needed)
cd backend && pytest tests/ -v
```

## API overview

| Endpoint | Description |
|---|---|
| `POST /api/search` | Hybrid search |
| `POST /api/search/lexical-only` | Lexical baseline |
| `POST /api/search/vector-only` | Semantic baseline |
| `GET /api/courses`, `GET /api/courses/{doc_id}` | Catalogue and course details |
| `GET /api/course/{doc_id}/graph` | Prerequisite chain, instructor, learning path |
| `GET /api/graph/domains`, `GET /api/graph/domains/{id}` | Domain hierarchy |
| `GET /api/evaluation` | Live metrics for the three strategies |
| `GET /api/config` | Fusion weights in use |

## Limitations

- Transitive reasoning uses a SPARQL property path (`:sousDomaineDe+`), not a full OWL reasoner (HermiT, Pellet).
- Dashboard, My Learning, Profile and Login are mocked (no real authentication or progress tracking).
- The evaluation set is small (8 queries); metrics are indicative.

## Troubleshooting

| Problem | Fix |
|---|---|
| Backend cannot reach Elasticsearch | Wait 20-30 s after `docker compose up` |
| Empty graph / SPARQL error | Make sure `elearning.ttl` was uploaded to Fuseki |
| Network error in the UI | Check the backend is running on port 8000 |
