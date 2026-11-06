# Script d'évaluation du moteur de recherche.
#
# Principe : on définit un petit jeu de test (requête -> documents
# pertinents attendus, jugés manuellement), puis on interroge l'API
# et on calcule Précision@k, Rappel@k et NDCG@k.
#
# A lancer depuis la racine du projet, backend démarré :
#   python evaluation/evaluate.py

import math
import time
import requests

API_URL = "http://localhost:8000/api/search"
LEXICAL_ONLY_URL = "http://localhost:8000/api/search/lexical-only"
VECTOR_ONLY_URL = "http://localhost:8000/api/search/vector-only"

# --- Jeu de test : à toi de l'enrichir avec tes propres requêtes ---
# Pour chaque requête, la liste des doc_id jugés pertinents par toi.
TEST_SET = [
    {
        "query": "cours de python pour débutant",
        "pertinents": ["Cours_PythonBases", "Cours_CoderPourTous", "Cours_DataScienceDeAZ"],
    },
    {
        "query": "apprendre à coder sans expérience",
        "pertinents": ["Cours_CoderPourTous", "Cours_PythonBases", "Cours_WebBases", "Cours_CSSModerne"],
    },
    {
        "query": "réseaux de neurones et intelligence artificielle",
        "pertinents": [
            "Cours_IntroDeepLearning", "Cours_IntroML", "Cours_DeepLearningPyTorch",
            "Cours_CNNVision", "Cours_RNNSeriesTemp", "Cours_DLTensorFlow", "Cours_PanoramaIA",
        ],
    },
    {
        "query": "développement web pour débutant",
        "pertinents": ["Cours_WebBases", "Cours_CSSModerne"],
    },
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
    {
        "query": "bases de données SQL",
        "pertinents": ["Cours_SQLBases", "Cours_PostgresAvance", "Cours_ModelisationBD"],
    },
    {
        "query": "sécurité informatique pour débutant",
        "pertinents": ["Cours_CyberSecuriteBases"],
    },
    {
        "query": "déployer une application avec des conteneurs",
        "pertinents": ["Cours_DockerKubernetes", "Cours_DevOpsIntro", "Cours_CICD"],
    },
    # --- Requêtes ajoutées pour élargir/équilibrer le jeu de test (13/09) ---
    # Jugées uniquement à partir du domaine/titre des cours dans le catalogue,
    # sans consulter les résultats retournés par le moteur, pour ne pas biaiser
    # l'évaluation en faveur d'une stratégie en particulier. Gardé identique
    # à backend/services/evaluation_service.py (même jeu de test, cf. son
    # commentaire d'en-tête).
    {
        "query": "cloud computing et hébergement",
        "pertinents": [
            "Cours_CloudBases", "Cours_AWSBases", "Cours_AzureAdmin",
            "Cours_GCPEssentials", "Cours_CloudNativeServerless",
        ],
    },
    {
        "query": "traitement du langage naturel et chatbots",
        "pertinents": [
            "Cours_NLPIntro", "Cours_NLPSpacyNLTK", "Cours_Chatbots",
            "Cours_LLMUsages", "Cours_TransformersLLM",
        ],
    },
    {
        "query": "analyse et visualisation de données avec Python",
        "pertinents": [
            "Cours_DataViz", "Cours_DataScienceDeAZ", "Cours_DataWrangling",
            "Cours_PandasNumpy", "Cours_DataStorytelling",
        ],
    },
    {
        "query": "mathématiques pour le machine learning",
        "pertinents": [
            "Cours_StatsBase", "Cours_AlgebreLineaire", "Cours_StatsAvancees",
            "Cours_CalculDiffIntegral", "Cours_Probabilites", "Cours_OptimisationML",
        ],
    },
    {
        "query": "cybersécurité et protection des réseaux",
        "pertinents": [
            "Cours_CyberSecuriteBases", "Cours_SecuriteReseaux",
            "Cours_Cryptographie", "Cours_EthicalHacking",
        ],
    },
    {
        "query": "intégration continue et automatisation DevOps",
        "pertinents": [
            "Cours_DevOpsIntro", "Cours_DockerKubernetes", "Cours_CICD",
            "Cours_Terraform", "Cours_Monitoring",
        ],
    },
    {
        "query": "big data et traitement de données massives",
        "pertinents": [
            "Cours_BigDataIntro", "Cours_ApacheSpark", "Cours_ArchitecturesBigData",
            "Cours_DataEngineeringIntro",
        ],
    },
]


def precision_at_k(retrieved: list[str], pertinents: list[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    nb_pertinents = sum(1 for doc in top_k if doc in pertinents)
    return nb_pertinents / len(top_k)


def recall_at_k(retrieved: list[str], pertinents: list[str], k: int) -> float:
    if not pertinents:
        return 0.0
    top_k = retrieved[:k]
    nb_pertinents = sum(1 for doc in top_k if doc in pertinents)
    return nb_pertinents / len(pertinents)


def ndcg_at_k(retrieved: list[str], pertinents: list[str], k: int) -> float:
    """NDCG binaire : pertinent = 1, non pertinent = 0."""
    top_k = retrieved[:k]
    dcg = sum(
        (1 if doc in pertinents else 0) / math.log2(i + 2)
        for i, doc in enumerate(top_k)
    )
    ideal = sorted([1] * min(len(pertinents), k) + [0] * max(0, k - len(pertinents)), reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def _evaluate_endpoint(url: str, k: int, label: str):
    """Interroge un endpoint (hybride ou lexical seul), calcule les
    métriques + le temps de réponse moyen, et affiche un tableau."""
    totals = {"precision": 0.0, "recall": 0.0, "ndcg": 0.0}
    response_times = []

    print(f"\n=== {label} ===")
    print(f"{'Requête':<45} {'P@'+str(k):>8} {'R@'+str(k):>8} {'NDCG@'+str(k):>10} {'temps(ms)':>10}")
    print("-" * 90)

    for case in TEST_SET:
        start = time.perf_counter()
        response = requests.post(url, json={"query": case["query"], "top_k": k})
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.raise_for_status()
        response_times.append(elapsed_ms)

        data = response.json()
        retrieved = [r["doc_id"] for r in data["results"] if not r.get("exclu", False)]

        p = precision_at_k(retrieved, case["pertinents"], k)
        r = recall_at_k(retrieved, case["pertinents"], k)
        n = ndcg_at_k(retrieved, case["pertinents"], k)

        totals["precision"] += p
        totals["recall"] += r
        totals["ndcg"] += n

        print(f"{case['query']:<45} {p:>8.2f} {r:>8.2f} {n:>10.2f} {elapsed_ms:>10.1f}")

    n_cases = len(TEST_SET)
    avg_time = sum(response_times) / len(response_times)
    print("-" * 90)
    print(f"{'MOYENNE':<45} {totals['precision']/n_cases:>8.2f} "
          f"{totals['recall']/n_cases:>8.2f} {totals['ndcg']/n_cases:>10.2f} {avg_time:>10.1f}")

    return {
        "precision": totals["precision"] / n_cases,
        "recall": totals["recall"] / n_cases,
        "ndcg": totals["ndcg"] / n_cases,
        "avg_time_ms": avg_time,
    }


def run_evaluation(k: int = 5):
    """Évalue le système hybride complet, puis chaque composant seul
    (lexical, vectoriel), et affiche la comparaison finale — la preuve
    chiffrée que l'hybride (et notamment l'apport du graphe) est meilleur
    que n'importe quel composant pris isolément. A mettre dans le rapport
    et les slides de soutenance."""
    hybride = _evaluate_endpoint(API_URL, k, "Système HYBRIDE (lexical + vectoriel + graphe)")
    lexical = _evaluate_endpoint(LEXICAL_ONLY_URL, k, "LEXICAL SEUL (baseline BM25)")
    vectoriel = _evaluate_endpoint(VECTOR_ONLY_URL, k, "VECTORIEL SEUL (baseline embeddings)")

    print("\n=== COMPARAISON FINALE ===")
    print(f"{'Métrique':<15} {'Lexical seul':>15} {'Vectoriel seul':>15} {'Hybride':>15}")
    print("-" * 65)
    for metric in ["precision", "recall", "ndcg"]:
        print(f"{metric:<15} {lexical[metric]:>15.2f} {vectoriel[metric]:>15.2f} {hybride[metric]:>15.2f}")
    print(f"{'temps (ms)':<15} {lexical['avg_time_ms']:>15.1f} {vectoriel['avg_time_ms']:>15.1f} "
          f"{hybride['avg_time_ms']:>15.1f}")
    print("\nNote : le système hybride doit être >= au meilleur des deux baselines sur chaque")
    print("métrique. Pour la requête 'intelligence artificielle' (aucun mot-clé exact dans les")
    print("cours pertinents), regarde spécifiquement le P@5/R@5 hybride vs lexical seul : c'est")
    print("la preuve chiffrée de l'apport du Knowledge Graph (expansion de domaine).")


if __name__ == "__main__":
    run_evaluation(k=5)
