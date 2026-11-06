"""Backend configuration: service URLs, embedding model and score-fusion weights."""

ELASTICSEARCH_URL = "http://localhost:9200"
ELASTICSEARCH_INDEX = "cours"

FUSEKI_SPARQL_ENDPOINT = "http://localhost:3030/elearning/sparql"

# Embedding model (lightweight). A heavier alternative: "BAAI/bge-m3".
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# Fusion weights (should sum to ~1).
# - POIDS_LEXICAL:   BM25 keyword match
# - POIDS_VECTORIEL: semantic similarity (embeddings)
# - POIDS_GRAPHE:    prerequisite validation. With no user profile this is a
#                    constant for all non-excluded courses, so it never changes
#                    the relative ranking (exclusion itself is unaffected).
# - POIDS_EXPANSION: bonus for courses found through domain expansion in the
#                    knowledge graph (e.g. "artificial intelligence" ->
#                    MachineLearning / DeepLearning sub-domains).
# Tuned on the small TEST_SET in evaluation_service.py (8 queries): re-check
# Precision@5, Recall@5 and NDCG@5 before changing them further.
POIDS_LEXICAL = 0.15
POIDS_VECTORIEL = 0.35
POIDS_GRAPHE = 0.10
POIDS_EXPANSION = 0.40

# Reciprocal Rank Fusion constant. The textbook k=60 targets corpora of
# thousands of documents; with a 70-course catalogue a small k keeps ranks
# discriminative.
RRF_K = 5

# Candidates retrieved by EACH retriever before fusion. Set above the catalogue
# size so every candidate gets a real lexical/vector score instead of a default 0.
CANDIDATE_POOL_SIZE = 100
