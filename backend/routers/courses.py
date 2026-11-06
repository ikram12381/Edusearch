# Endpoints de catalogue : lister/filtrer les cours (page Explore, filtres
# de la page Search) et consulter le détail complet d'un cours (page Course
# Details), en combinant backend/data/cours.json (source unique de vérité
# pour les métadonnées) et le Knowledge Graph (formateur, parcours,
# compétences, prérequis, cours reliés).

import json
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from models.schemas import CourseListItem, CourseDetail, RelatedCourse, PrerequisiteStep
from services import graph_service

router = APIRouter()

_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cours.json")
with open(_data_path, encoding="utf-8") as f:
    _all_courses = json.load(f)
_courses_by_id = {c["doc_id"]: c for c in _all_courses}


@router.get("/courses", response_model=list[CourseListItem])
async def list_courses(
    domaine: Optional[str] = None,
    niveau: Optional[str] = None,
    duree_max: Optional[int] = None,
    note_min: Optional[float] = None,
    gratuit: Optional[bool] = None,
    q: Optional[str] = None,
):
    """Catalogue filtré, utilisé par la page Explore Courses et par les
    filtres (Domain / Difficulty / Duration / Rating / Free) de la page
    Search. Filtre simple en mémoire sur cours.json : ne remplace pas la
    recherche hybride (/api/search), qui reste la fonctionnalité centrale."""
    results = _all_courses
    if domaine:
        results = [c for c in results if c["domaine"] == domaine]
    if niveau:
        results = [c for c in results if c["niveau"] == niveau]
    if duree_max is not None:
        results = [c for c in results if c["duree_heures"] <= duree_max]
    if note_min is not None:
        results = [c for c in results if c["note"] >= note_min]
    if gratuit is not None:
        results = [c for c in results if c["gratuit"] == gratuit]
    if q:
        q_lower = q.lower()
        results = [c for c in results if q_lower in c["titre"].lower() or q_lower in c["description"].lower()]
    return [CourseListItem(**c) for c in results]


@router.get("/courses/{doc_id}", response_model=CourseDetail)
async def get_course(doc_id: str):
    """Détail complet d'un cours : métadonnées catalogue + tout ce que le
    Knowledge Graph en sait (formateur, parcours, compétences enseignées,
    prérequis requis, chaîne complète de prérequis, cours reliés par domaine)."""
    doc = _courses_by_id.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Cours inconnu")

    concepts = graph_service.get_course_concepts(doc_id)
    chain_raw = graph_service.get_prerequisite_chain(doc_id)
    chain = [[PrerequisiteStep(**step) for step in level] for level in chain_raw]

    cours_relies = [
        RelatedCourse(doc_id=c["doc_id"], titre=c["titre"], domaine=c["domaine"], niveau=c["niveau"])
        for c in _all_courses
        if c["domaine"] == doc["domaine"] and c["doc_id"] != doc_id
    ][:4]

    return CourseDetail(
        **doc,
        formateur=graph_service.get_formateur(doc_id),
        parcours=graph_service.get_parcours(doc_id),
        competences_enseignees=[c["label"] for c in concepts["enseignees"]],
        prerequis_requis=graph_service.get_prerequisites(doc_id),
        chaine_prerequis=chain,
        cours_relies=cours_relies,
    )
