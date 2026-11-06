from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class ResultItem(BaseModel):
    doc_id: str
    titre: str
    description: str
    domaine: str
    niveau: str
    score_lexical: float
    score_vectoriel: float
    score_graphe: float
    score_expansion_domaine: float = 0.0
    score_final: float
    exclu: bool = False
    raison_exclusion: Optional[str] = None
    trouve_par_expansion_graphe: bool = False
    formateur: Optional[str] = None
    parcours: List[str] = []
    # --- Champs catalogue (repris de cours.json, pour l'affichage direct
    # sans requête supplémentaire côté frontend) ---
    duree_heures: Optional[int] = None
    note: Optional[float] = None
    gratuit: Optional[bool] = None
    # --- Explication de la pertinence ("Why this result?") ---
    matched_concepts: List[str] = []
    related_concepts: List[str] = []


class InterpretationEntite(BaseModel):
    type: str
    score: float
    raison: str


class EntiteDetectee(BaseModel):
    label: str
    ambigu: bool
    type_retenu: str
    types_possibles: List[str]
    interpretations: List[InterpretationEntite] = []
    raison_resolution: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[ResultItem]
    nb_lexical: int
    nb_vectoriel: int
    nb_exclus: int
    entites_detectees: List[EntiteDetectee] = []
    domaines_elargis: List[str] = []


class PrerequisiteStep(BaseModel):
    doc_id: str
    titre: str


class CourseGraphInfo(BaseModel):
    doc_id: str
    chaine_prerequis: List[List[PrerequisiteStep]]
    formateur: Optional[str] = None
    parcours: List[str] = []


# ---------------------------------------------------------------------------
# Catalogue de cours (Explore / Search filters / Course details)
# ---------------------------------------------------------------------------

class CourseListItem(BaseModel):
    doc_id: str
    titre: str
    description: str
    domaine: str
    niveau: str
    duree_heures: int
    note: float
    gratuit: bool


class RelatedCourse(BaseModel):
    doc_id: str
    titre: str
    domaine: str
    niveau: str


class CourseDetail(BaseModel):
    doc_id: str
    titre: str
    description: str
    domaine: str
    niveau: str
    duree_heures: int
    note: float
    gratuit: bool
    formateur: Optional[str] = None
    parcours: List[str] = []
    competences_enseignees: List[str] = []
    prerequis_requis: List[str] = []
    chaine_prerequis: List[List[PrerequisiteStep]] = []
    cours_relies: List[RelatedCourse] = []


# ---------------------------------------------------------------------------
# Knowledge Graph — vue "domaines" pour la page Knowledge Graph
# ---------------------------------------------------------------------------

class DomainNode(BaseModel):
    id: str
    label: str
    nb_cours: int


class DomainEdge(BaseModel):
    source: str
    target: str


class DomainGraphResponse(BaseModel):
    nodes: List[DomainNode]
    edges: List[DomainEdge]


class DomainDetail(BaseModel):
    id: str
    label: str
    cours: List[CourseListItem]
    competences: List[str]


class InferenceNode(BaseModel):
    local_name: str
    label: str


class InferenceChainResponse(BaseModel):
    domaine: str
    chaine: List[InferenceNode]


class PathResponse(BaseModel):
    source: str
    target: str
    trouve: bool
    chemin: List[InferenceNode]


# ---------------------------------------------------------------------------
# Évaluation (Precision@k / Recall@k / NDCG@k) exposée à l'app
# ---------------------------------------------------------------------------

class EvaluationQueryResult(BaseModel):
    query: str
    precision: float
    recall: float
    ndcg: float
    response_time_ms: float


class EvaluationSummary(BaseModel):
    label: str
    precision: float
    recall: float
    ndcg: float
    avg_response_time_ms: float
    par_requete: List[EvaluationQueryResult]


class EvaluationResponse(BaseModel):
    k: int
    hybride: EvaluationSummary
    lexical: EvaluationSummary
    vectoriel: EvaluationSummary


# ---------------------------------------------------------------------------
# Configuration exposée en lecture (poids de fusion, modèle d'embeddings)
# ---------------------------------------------------------------------------

class SearchConfig(BaseModel):
    poids_lexical: float
    poids_vectoriel: float
    poids_graphe: float
    poids_expansion: float
    embedding_model: str
