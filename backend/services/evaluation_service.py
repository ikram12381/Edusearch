# Version "API" de evaluation/evaluate.py : calcule Précision@k, Rappel@k et
# NDCG@k pour le système hybride et pour chaque composante isolée, mais en
# appelant directement les services internes (pas de requête HTTP vers
# soi-même), pour pouvoir être exposée par /api/evaluation et consommée par
# la page "Search Evaluation" du frontend.
#
# evaluation/evaluate.py reste le script de référence pour une analyse
# hors-ligne en ligne de commande (mêmes requêtes de test) ; ce module est
# sa contrepartie "temps réel" pour l'application.

import json
import math
import os
import time

from services import elastic_service, ranking_service, graph_service
from config import CANDIDATE_POOL_SIZE

_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cours.json")
with open(_data_path, encoding="utf-8") as f:
    _all_courses = json.load(f)
_courses_by_id = {c["doc_id"]: c for c in _all_courses}

TEST_SET = [
    {"query": "cours de python pour débutant",
     "pertinents": ["Cours_PythonBases", "Cours_CoderPourTous", "Cours_DataScienceDeAZ"]},
    {"query": "apprendre à coder sans expérience",
     "pertinents": ["Cours_CoderPourTous", "Cours_PythonBases", "Cours_WebBases", "Cours_CSSModerne"]},
    {"query": "réseaux de neurones et intelligence artificielle",
     "pertinents": [
         "Cours_IntroDeepLearning", "Cours_IntroML", "Cours_DeepLearningPyTorch",
         "Cours_CNNVision", "Cours_RNNSeriesTemp", "Cours_DLTensorFlow", "Cours_PanoramaIA",
     ]},
    {"query": "développement web pour débutant",
     "pertinents": ["Cours_WebBases", "Cours_CSSModerne"]},
    {
        # Le catalogue contient depuis peu "Panorama de l'intelligence
        # artificielle" (titre correspondant mot pour mot) : la recherche
        # lexicale seule le retrouve désormais aussi. Le graphe reste
        # néanmoins indispensable pour ramener les cours de ML/DeepLearning/
        # NLP, sous-domaines de IntelligenceArtificielle, qui eux ne
        # contiennent pas l'expression exacte.
        "query": "intelligence artificielle",
        "pertinents": [
            "Cours_IntroML", "Cours_IntroDeepLearning", "Cours_DeepLearningPyTorch", "Cours_NLPIntro",
            "Cours_PanoramaIA", "Cours_EthiqueIA", "Cours_IAGenerative",
            "Cours_CNNVision", "Cours_RNNSeriesTemp", "Cours_DLTensorFlow", "Cours_TransformersLLM",
            "Cours_MLScikitLearn", "Cours_FeatureEngineering", "Cours_MLOpsIntro", "Cours_EnsembleMethods",
            "Cours_NLPSpacyNLTK", "Cours_Chatbots", "Cours_LLMUsages",
        ],
    },
    {"query": "bases de données SQL",
     "pertinents": ["Cours_SQLBases", "Cours_PostgresAvance", "Cours_ModelisationBD"]},
    {"query": "sécurité informatique pour débutant", "pertinents": ["Cours_CyberSecuriteBases"]},
    {"query": "déployer une application avec des conteneurs",
     "pertinents": ["Cours_DockerKubernetes", "Cours_DevOpsIntro", "Cours_CICD"]},
    # --- Requêtes ajoutées pour élargir/équilibrer le jeu de test (13/09) ---
    # Jugées uniquement à partir du domaine/titre des cours dans le catalogue,
    # sans consulter les résultats retournés par le moteur, pour ne pas biaiser
    # l'évaluation en faveur d'une stratégie en particulier.
    {"query": "cloud computing et hébergement",
     "pertinents": ["Cours_CloudBases", "Cours_AWSBases", "Cours_AzureAdmin",
                     "Cours_GCPEssentials", "Cours_CloudNativeServerless"]},
    {"query": "traitement du langage naturel et chatbots",
     "pertinents": ["Cours_NLPIntro", "Cours_NLPSpacyNLTK", "Cours_Chatbots",
                     "Cours_LLMUsages", "Cours_TransformersLLM"]},
    {"query": "analyse et visualisation de données avec Python",
     "pertinents": ["Cours_DataViz", "Cours_DataScienceDeAZ", "Cours_DataWrangling",
                     "Cours_PandasNumpy", "Cours_DataStorytelling"]},
    {"query": "mathématiques pour le machine learning",
     "pertinents": ["Cours_StatsBase", "Cours_AlgebreLineaire", "Cours_StatsAvancees",
                     "Cours_CalculDiffIntegral", "Cours_Probabilites", "Cours_OptimisationML"]},
    {"query": "cybersécurité et protection des réseaux",
     "pertinents": ["Cours_CyberSecuriteBases", "Cours_SecuriteReseaux",
                     "Cours_Cryptographie", "Cours_EthicalHacking"]},
    {"query": "intégration continue et automatisation DevOps",
     "pertinents": ["Cours_DevOpsIntro", "Cours_DockerKubernetes", "Cours_CICD",
                     "Cours_Terraform", "Cours_Monitoring"]},
    {"query": "big data et traitement de données massives",
     "pertinents": ["Cours_BigDataIntro", "Cours_ApacheSpark", "Cours_ArchitecturesBigData",
                     "Cours_DataEngineeringIntro"]},
]


def _precision_at_k(retrieved, pertinents, k):
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    return sum(1 for d in top_k if d in pertinents) / len(top_k)


def _recall_at_k(retrieved, pertinents, k):
    if not pertinents:
        return 0.0
    top_k = retrieved[:k]
    return sum(1 for d in top_k if d in pertinents) / len(pertinents)


def _ndcg_at_k(retrieved, pertinents, k):
    top_k = retrieved[:k]
    dcg = sum((1 if d in pertinents else 0) / math.log2(i + 2) for i, d in enumerate(top_k))
    ideal = sorted([1] * min(len(pertinents), k) + [0] * max(0, k - len(pertinents)), reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def _hybrid_doc_ids(query: str, k: int) -> list[str]:
    pool = max(k, CANDIDATE_POOL_SIZE)
    lexical_hits = elastic_service.lexical_search(query, pool)
    vector_hits = elastic_service.vector_search(query, pool)
    linked_entities = graph_service.link_entities_in_query(query)
    expanded_domains = graph_service.expand_query_domains(linked_entities)
    expansion_hits = elastic_service.search_by_domains(expanded_domains, pool)

    # Cf. routers/search.py : précharge en 4 requêtes batchées plutôt que de
    # laisser fuse_results() interroger Fuseki une fois par candidat.
    candidate_ids = {h["_id"] for h in lexical_hits} | {h["_id"] for h in vector_hits} | {h["_id"] for h in expansion_hits}
    graph_service.warm_course_cache(list(candidate_ids))

    fused = ranking_service.fuse_results(
        lexical_hits=lexical_hits,
        vector_hits=vector_hits,
        all_docs_by_id=_courses_by_id,
        expansion_hits=expansion_hits,
        expanded_domains=expanded_domains,
    )
    return [r["doc_id"] for r in fused[:k] if not r["exclu"]]


def _lexical_doc_ids(query: str, k: int) -> list[str]:
    return [h["_id"] for h in elastic_service.lexical_search(query, k)][:k]


def _vector_doc_ids(query: str, k: int) -> list[str]:
    return [h["_id"] for h in elastic_service.vector_search(query, k)][:k]


def _run_for_strategy(label: str, retrieve_fn, k: int) -> dict:
    per_query = []
    totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    times = []
    for case in TEST_SET:
        start = time.perf_counter()
        retrieved = retrieve_fn(case["query"], k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)

        p = _precision_at_k(retrieved, case["pertinents"], k)
        r = _recall_at_k(retrieved, case["pertinents"], k)
        n = _ndcg_at_k(retrieved, case["pertinents"], k)
        totals["precision"] += p
        totals["recall"] += r
        totals["ndcg"] += n

        per_query.append({
            "query": case["query"], "precision": round(p, 3), "recall": round(r, 3),
            "ndcg": round(n, 3), "response_time_ms": round(elapsed_ms, 1),
        })

    n_cases = len(TEST_SET)
    return {
        "label": label,
        "precision": round(totals["precision"] / n_cases, 3),
        "recall": round(totals["recall"] / n_cases, 3),
        "ndcg": round(totals["ndcg"] / n_cases, 3),
        "avg_response_time_ms": round(sum(times) / len(times), 1),
        "par_requete": per_query,
    }


def run_evaluation(k: int = 5) -> dict:
    """Calcule les métriques pour le système hybride ET pour chaque
    composante isolée (lexical seul, vectoriel seul), pour la page
    'Search Evaluation' du frontend. Nécessite Elasticsearch et Fuseki
    actifs (mêmes dépendances que /api/search)."""
    return {
        "k": k,
        "hybride": _run_for_strategy("Hybride (lexical + vectoriel + graphe)", _hybrid_doc_ids, k),
        "lexical": _run_for_strategy("Lexical seul (BM25)", _lexical_doc_ids, k),
        "vectoriel": _run_for_strategy("Vectoriel seul (embeddings)", _vector_doc_ids, k),
    }
