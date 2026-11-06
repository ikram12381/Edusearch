# Endpoints dédiés à la page "Knowledge Graph" du frontend : la hiérarchie
# des domaines (nœuds + arêtes :sousDomaineDe, telle que déclarée dans
# l'ontologie) et le détail d'un domaine (cours qu'il contient, compétences
# associées). Le frontend n'a jamais à connaître SPARQL : il consomme un
# JSON simple nœuds/arêtes.

import json
import os
from fastapi import APIRouter, HTTPException
from models.schemas import (
    DomainGraphResponse, DomainNode, DomainEdge, DomainDetail, CourseListItem,
    InferenceChainResponse, InferenceNode, PathResponse,
)
from services import graph_service

router = APIRouter()

_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cours.json")
with open(_data_path, encoding="utf-8") as f:
    _all_courses = json.load(f)


@router.get("/graph/domains", response_model=DomainGraphResponse)
async def domain_graph():
    """Graphe des domaines : nœuds = domaines de l'ontologie (avec leur
    nombre de cours), arêtes = relations :sousDomaineDe directes. Alimente
    la visualisation D3 interactive de la page Knowledge Graph."""
    hierarchy = graph_service.get_domain_hierarchy()
    nb_cours_by_domain = {}
    for c in _all_courses:
        nb_cours_by_domain[c["domaine"]] = nb_cours_by_domain.get(c["domaine"], 0) + 1

    nodes = [
        DomainNode(id=n["id"], label=n["label"], nb_cours=nb_cours_by_domain.get(n["id"], 0))
        for n in hierarchy["nodes"]
    ]
    edges = [DomainEdge(**e) for e in hierarchy["edges"]]
    return DomainGraphResponse(nodes=nodes, edges=edges)


@router.get("/graph/domains/{domain_id}", response_model=DomainDetail)
async def domain_detail(domain_id: str):
    """Détail d'un domaine cliqué dans le graphe : ses cours et les
    compétences (enseignées ou requises) associées à ces cours."""
    matching_labels = [n["label"] for n in graph_service.get_domain_hierarchy()["nodes"] if n["id"] == domain_id]
    if not matching_labels:
        raise HTTPException(status_code=404, detail="Domaine inconnu")

    cours_du_domaine = [c for c in _all_courses if c["domaine"] == domain_id]
    competences = set()
    for c in cours_du_domaine:
        concepts = graph_service.get_course_concepts(c["doc_id"])
        for item in concepts["enseignees"] + concepts["requises"]:
            competences.add(item["label"])

    return DomainDetail(
        id=domain_id,
        label=matching_labels[0],
        cours=[CourseListItem(**c) for c in cours_du_domaine],
        competences=sorted(competences),
    )


def _labels_by_local() -> dict[str, str]:
    hierarchy = graph_service.get_domain_hierarchy()
    return {n["id"]: n["label"] for n in hierarchy["nodes"]}


@router.get("/graph/inference/{domain_id}", response_model=InferenceChainResponse)
async def domain_inference_chain(domain_id: str):
    """Chaîne d'ancêtres d'un domaine, ÉTAPE PAR ÉTAPE, pour illustrer
    concrètement l'inférence rendue possible par owl:TransitiveProperty
    sur :sousDomaineDe (le raisonneur n'affirme jamais directement
    'DeepLearning sousDomaineDe IntelligenceArtificielle' dans l'ontologie
    : c'est une relation DÉDUITE à partir de la chaîne de relations directes).
    Alimente la section 'Knowledge Graph Inference' du frontend."""
    labels = _labels_by_local()
    if domain_id not in labels:
        raise HTTPException(status_code=404, detail="Domaine inconnu")

    chain_ids = graph_service.get_domain_ancestor_chain(domain_id)
    chaine = [InferenceNode(local_name=cid, label=labels.get(cid, cid)) for cid in chain_ids]
    return InferenceChainResponse(domaine=domain_id, chaine=chaine)


@router.get("/graph/path", response_model=PathResponse)
async def semantic_path(source: str, target: str):
    """Recherche par chemin dans le graphe ('Find semantic path') : plus
    court chemin entre deux domaines via les relations :sousDomaineDe,
    calculé par parcours en largeur (BFS) sur le graphe non orienté."""
    labels = _labels_by_local()
    if source not in labels or target not in labels:
        raise HTTPException(status_code=404, detail="Domaine source ou destination inconnu")

    path_ids = graph_service.find_domain_path(source, target)
    trouve = path_ids is not None
    chemin = [InferenceNode(local_name=pid, label=labels.get(pid, pid)) for pid in (path_ids or [])]
    return PathResponse(source=source, target=target, trouve=trouve, chemin=chemin)
