import json
import os
from fastapi import APIRouter, HTTPException
from models.schemas import (
    SearchRequest, SearchResponse, ResultItem, EntiteDetectee,
    CourseGraphInfo, PrerequisiteStep,
)
from services import elastic_service, ranking_service, graph_service
from config import CANDIDATE_POOL_SIZE

router = APIRouter()

# Chargement en mémoire des cours (utilisé pour retrouver titre/description
# rapidement lors de la fusion, sans refaire un appel réseau)
_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cours.json")
with open(_data_path, encoding="utf-8") as f:
    _all_courses = json.load(f)
_courses_by_id = {c["doc_id"]: c for c in _all_courses}


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    pool = max(request.top_k, CANDIDATE_POOL_SIZE)
    lexical_hits = elastic_service.lexical_search(request.query, pool)
    vector_hits = elastic_service.vector_search(request.query, pool)

    # --- Entity linking + désambiguïsation sur la requête ---
    all_typed_labels = graph_service.get_all_typed_labels()
    label_by_local = {e["local_name"]: e["label"] for e in all_typed_labels}
    linked_entities = graph_service.link_entities_in_query(request.query, all_typed_labels)
    expanded_domains = graph_service.expand_query_domains(linked_entities)

    # --- Candidats supplémentaires apportés par le graphe ---
    expansion_hits = elastic_service.search_by_domains(expanded_domains, pool)

    # Précharge en 4 requêtes SPARQL batchées les infos (prérequis, concepts,
    # formateur, parcours) de TOUS les candidats d'un coup, plutôt que de
    # laisser fuse_results() interroger Fuseki une fois par candidat (c'était
    # la cause du temps de réponse ~6800ms en mode hybride, cf. évaluation).
    candidate_ids = {h["_id"] for h in lexical_hits} | {h["_id"] for h in vector_hits} | {h["_id"] for h in expansion_hits}
    graph_service.warm_course_cache(list(candidate_ids))

    fused = ranking_service.fuse_results(
        lexical_hits=lexical_hits,
        vector_hits=vector_hits,
        all_docs_by_id=_courses_by_id,
        expansion_hits=expansion_hits,
        expanded_domains=expanded_domains,
        linked_entities=linked_entities,
        label_by_local=label_by_local,
    )

    results = [ResultItem(**r) for r in fused[: request.top_k]]
    nb_exclus = sum(1 for r in fused if r["exclu"])

    entites_detectees = [
        EntiteDetectee(
            label=ent["label"],
            ambigu=ent["ambiguous"],
            type_retenu=ent["interpretation_retenue"]["type"],
            types_possibles=sorted({c["type"] for c in ent["candidates"]}),
            interpretations=[
                {"type": i["type"], "score": i["score"], "raison": i["raison"]}
                for i in ent.get("interpretations", [])
            ],
            raison_resolution=ent.get("raison_resolution"),
        )
        for ent in linked_entities
    ]

    return SearchResponse(
        results=results,
        nb_lexical=len(lexical_hits),
        nb_vectoriel=len(vector_hits),
        nb_exclus=nb_exclus,
        entites_detectees=entites_detectees,
        domaines_elargis=expanded_domains,
    )


@router.post("/search/lexical-only", response_model=SearchResponse)
async def search_lexical_only(request: SearchRequest):
    """Endpoint qui n'utilise QUE la recherche lexicale, sans vectoriel
    ni graphe. Sert de baseline pour prouver, dans evaluation/evaluate.py,
    que le système hybride donne de meilleurs résultats."""
    lexical_hits = elastic_service.lexical_search(request.query, request.top_k)

    # Le score BM25 brut d'Elasticsearch (hit["_score"]) n'est pas borné
    # entre 0 et 1 : il peut dépasser largement 1 (ex: 6.68), contrairement
    # au score utilisé dans le pipeline hybride qui est normalisé par
    # ranking_service._normalize_scores(). Le frontend affichant TOUJOURS
    # score_lexical * 100 comme un pourcentage, un score brut non normalisé
    # donnait des valeurs aberrantes du type "668%". On applique donc la
    # même normalisation (division par le score max du batch) qu'en mode
    # hybride pour rester cohérent.
    normalized_scores = ranking_service._normalize_scores(lexical_hits)

    results = []
    for hit in lexical_hits[: request.top_k]:
        doc = _courses_by_id.get(hit["_id"])
        if not doc:
            continue
        score_lex = normalized_scores.get(hit["_id"], 0.0)
        results.append(ResultItem(
            doc_id=hit["_id"],
            titre=doc["titre"],
            description=doc["description"],
            domaine=doc["domaine"],
            niveau=doc["niveau"],
            score_lexical=round(score_lex, 3),
            score_vectoriel=0.0,
            score_graphe=0.0,
            score_final=round(score_lex, 3),
            exclu=False,
            duree_heures=doc.get("duree_heures"),
            note=doc.get("note"),
            gratuit=doc.get("gratuit"),
        ))

    return SearchResponse(
        results=results,
        nb_lexical=len(lexical_hits),
        nb_vectoriel=0,
        nb_exclus=0,
    )


@router.post("/search/vector-only", response_model=SearchResponse)
async def search_vector_only(request: SearchRequest):
    """Baseline symétrique de lexical-only : QUE la recherche vectorielle,
    sans BM25 ni graphe. Permet de prouver dans evaluate.py que chaque
    composant (lexical, vectoriel, graphe) apporte individuellement quelque
    chose, et pas seulement que 'hybride > lexical'."""
    vector_hits = elastic_service.vector_search(request.query, request.top_k)

    results = []
    for hit in vector_hits[: request.top_k]:
        doc = _courses_by_id.get(hit["_id"])
        if not doc:
            continue
        results.append(ResultItem(
            doc_id=hit["_id"],
            titre=doc["titre"],
            description=doc["description"],
            domaine=doc["domaine"],
            niveau=doc["niveau"],
            score_lexical=0.0,
            score_vectoriel=round(hit["_score"], 3),
            score_graphe=0.0,
            score_final=round(hit["_score"], 3),
            exclu=False,
            duree_heures=doc.get("duree_heures"),
            note=doc.get("note"),
            gratuit=doc.get("gratuit"),
        ))

    return SearchResponse(
        results=results,
        nb_lexical=0,
        nb_vectoriel=len(vector_hits),
        nb_exclus=0,
    )


@router.get("/course/{doc_id}/graph", response_model=CourseGraphInfo)
async def course_graph_info(doc_id: str):
    """Renvoie ce que le Knowledge Graph sait sur un cours : sa chaîne
    complète de prérequis (pas juste le niveau direct), son formateur,
    son parcours. Utilisé par le frontend pour la 'visualisation des
    résultats enrichis' demandée dans les objectifs du projet."""
    if doc_id not in _courses_by_id:
        raise HTTPException(status_code=404, detail="Cours inconnu")

    chain_raw = graph_service.get_prerequisite_chain(doc_id)
    chain = [[PrerequisiteStep(**step) for step in level] for level in chain_raw]

    return CourseGraphInfo(
        doc_id=doc_id,
        chaine_prerequis=chain,
        formateur=graph_service.get_formateur(doc_id),
        parcours=graph_service.get_parcours(doc_id),
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
