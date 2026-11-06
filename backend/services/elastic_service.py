# Ce service gère tout ce qui touche à Elasticsearch :
# - créer l'index avec le bon mapping (y compris le champ vectoriel)
# - indexer les cours
# - faire la recherche lexicale (mots-clés)
# - faire la recherche vectorielle (kNN sur les embeddings)

from elasticsearch import Elasticsearch
from config import ELASTICSEARCH_URL, ELASTICSEARCH_INDEX, EMBEDDING_DIMENSIONS
from services.embedding_service import get_embedding

es = Elasticsearch(ELASTICSEARCH_URL)


def create_index():
    """Crée l'index avec un mapping adapté : champs texte classiques
    + un champ 'embedding' de type dense_vector pour la recherche kNN."""
    if es.indices.exists(index=ELASTICSEARCH_INDEX):
        es.indices.delete(index=ELASTICSEARCH_INDEX)

    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "titre": {"type": "text"},
                "description": {"type": "text"},
                "domaine": {"type": "keyword"},
                "niveau": {"type": "keyword"},
                "duree_heures": {"type": "integer"},
                "note": {"type": "float"},
                "gratuit": {"type": "boolean"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMENSIONS,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }
    }
    es.indices.create(index=ELASTICSEARCH_INDEX, body=mapping)


def index_course(course: dict):
    """Indexe un cours : calcule son embedding à partir du titre +
    description, puis l'envoie à Elasticsearch."""
    text_for_embedding = f"{course['titre']}. {course['description']}"
    embedding = get_embedding(text_for_embedding)

    doc = {**course, "embedding": embedding}
    es.index(index=ELASTICSEARCH_INDEX, id=course["doc_id"], document=doc)


def lexical_search(query: str, top_k: int = 10):
    """Recherche classique par mots-clés (BM25) sur titre + description."""
    body = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["titre^2", "description"],  # le titre compte double
            }
        },
    }
    res = es.search(index=ELASTICSEARCH_INDEX, body=body)
    return res["hits"]["hits"]


def vector_search(query: str, top_k: int = 10):
    """Recherche par similarité de sens : transforme la requête en
    vecteur, puis cherche les documents dont le vecteur est le plus proche."""
    query_vector = get_embedding(query)
    body = {
        "knn": {
            "field": "embedding",
            "query_vector": query_vector,
            "k": top_k,
            # Elasticsearch exige num_candidates >= k pour le kNN
            # approximatif ; ce champ était figé à 50, ce qui aurait cassé
            # (ou tronqué silencieusement) toute recherche avec top_k > 50.
            "num_candidates": max(top_k * 2, 100),
        },
        "size": top_k,
    }
    res = es.search(index=ELASTICSEARCH_INDEX, body=body)
    return res["hits"]["hits"]


def search_by_domains(domains: list[str], top_k: int = 10):
    """Récupère les cours dont le champ 'domaine' fait partie d'un ensemble
    élargi calculé par le Knowledge Graph (voir graph_service.expand_query_domains).

    C'est ce qui permet au graphe d'apporter de VRAIS candidats supplémentaires
    à la recherche (pas juste un filtre), par exemple : la requête "intelligence
    artificielle" ne contient littéralement aucun mot-clé des descriptions de
    "Introduction au Machine Learning" ou "Introduction au deep learning" — mais
    le graphe sait que MachineLearning et DeepLearning sont des sous-domaines de
    IntelligenceArtificielle, donc ces cours sont ajoutés aux candidats."""
    if not domains:
        return []
    body = {
        "size": top_k,
        "query": {"terms": {"domaine": domains}},
    }
    res = es.search(index=ELASTICSEARCH_INDEX, body=body)
    return res["hits"]["hits"]
