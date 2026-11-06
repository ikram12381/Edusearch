# Ce service interroge le Knowledge Graph (hébergé dans Fuseki) en SPARQL pour :
# 1. exclure les cours dont un prérequis n'est pas satisfait
# 2. relier une entité mentionnée dans la requête (domaine/compétence) à ses
#    voisins dans le graphe (expansion sémantique), en exploitant réellement
#    la transitivité de :sousDomaineDe
# 3. désambiguïser un terme qui correspond à plusieurs types d'entités
# 4. enrichir un cours avec son formateur, son parcours, sa chaîne de prérequis

import re
from collections import deque
from functools import lru_cache
from SPARQLWrapper import SPARQLWrapper, JSON
from config import FUSEKI_SPARQL_ENDPOINT

PREFIX = """PREFIX : <http://www.projet-pfm.org/elearning#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"""


def _run_query(query: str):
    sparql = SPARQLWrapper(FUSEKI_SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def _local_name(uri: str) -> str:
    """http://.../elearning#DeepLearning -> DeepLearning"""
    return uri.split("#")[-1]


# --- Cache par cours (prérequis / concepts / formateur / parcours) ---------
# AVANT ce fix : fuse_results() appelait get_prerequisites/get_course_concepts/
# get_formateur/get_parcours UNE FOIS PAR CANDIDAT (jusqu'à ~70-100 par
# recherche), soit ~280 aller-retours SPARQL réseau vers Fuseki à CHAQUE
# recherche hybride -> c'est le problème N+1 qui explique les ~6800ms mesurés
# (vs 70-90ms pour lexical/vectoriel, qui ne touchent jamais Fuseki).
# warm_course_cache() remplace ça par 4 requêtes SPARQL BATCHÉES (une par type
# de donnée, via VALUES) pour TOUS les candidats d'une recherche d'un coup ;
# les fonctions get_xxx ci-dessous consultent d'abord ce cache et ne
# retombent sur une requête individuelle que si le cours n'a pas été
# préchargé (ex: appel isolé depuis /api/course/{doc_id}/graph).
_prereq_cache: dict[str, list[str]] = {}
_concepts_cache: dict[str, dict] = {}
_formateur_cache: dict[str, "str | None"] = {}
_parcours_cache: dict[str, list[str]] = {}


def warm_course_cache(doc_ids: list[str]) -> None:
    """Précharge en 4 requêtes SPARQL (au lieu de 4 x len(doc_ids)) les
    infos de tous les cours donnés. A appeler une fois, avant la boucle de
    fusion, avec l'ensemble des candidats (lexical + vectoriel + expansion)."""
    missing = sorted({d for d in doc_ids if d not in _prereq_cache})
    if not missing:
        return
    values = " ".join(f":{d}" for d in missing)

    for d in missing:
        _prereq_cache[d] = []
        _concepts_cache[d] = {"enseignees": [], "requises": []}
        _formateur_cache[d] = None
        _parcours_cache[d] = []

    prereq_q = f"""
    {PREFIX}
    SELECT ?cours ?competenceLabel WHERE {{
        VALUES ?cours {{ {values} }}
        {{
            ?cours :aPrerequis ?prereq .
            ?prereq :enseigneCompetence ?comp .
            ?comp rdfs:label ?competenceLabel .
        }} UNION {{
            ?cours :requiertCompetence ?comp .
            ?comp rdfs:label ?competenceLabel .
        }}
    }}
    """
    for b in _run_query(prereq_q)["results"]["bindings"]:
        doc_id = _local_name(b["cours"]["value"])
        _prereq_cache[doc_id].append(b["competenceLabel"]["value"])

    concepts_q = f"""
    {PREFIX}
    SELECT ?cours ?comp ?label ?role WHERE {{
        VALUES ?cours {{ {values} }}
        {{ ?cours :enseigneCompetence ?comp . BIND("enseignee" AS ?role) }}
        UNION
        {{ ?cours :requiertCompetence ?comp . BIND("requise" AS ?role) }}
        ?comp rdfs:label ?label .
    }}
    """
    for b in _run_query(concepts_q)["results"]["bindings"]:
        doc_id = _local_name(b["cours"]["value"])
        item = {"local_name": _local_name(b["comp"]["value"]), "label": b["label"]["value"]}
        key = "enseignees" if b["role"]["value"] == "enseignee" else "requises"
        _concepts_cache[doc_id][key].append(item)

    formateur_q = f"""
    {PREFIX}
    SELECT ?cours ?label WHERE {{
        VALUES ?cours {{ {values} }}
        ?cours :enseignePar ?f .
        ?f rdfs:label ?label .
    }}
    """
    for b in _run_query(formateur_q)["results"]["bindings"]:
        _formateur_cache[_local_name(b["cours"]["value"])] = b["label"]["value"]

    parcours_q = f"""
    {PREFIX}
    SELECT ?cours ?label WHERE {{
        VALUES ?cours {{ {values} }}
        ?cours :faitPartieDe ?p .
        ?p rdfs:label ?label .
    }}
    """
    for b in _run_query(parcours_q)["results"]["bindings"]:
        _parcours_cache[_local_name(b["cours"]["value"])].append(b["label"]["value"])


def get_prerequisites(doc_id: str) -> list[str]:
    """Retourne les libellés des compétences requises par un cours,
    qu'elles soient déclarées comme prérequis explicite ou comme
    compétence requise 'cachée'."""
    if doc_id in _prereq_cache:
        return _prereq_cache[doc_id]
    query = f"""
    {PREFIX}
    SELECT ?competenceLabel WHERE {{
        {{
            :{doc_id} :aPrerequis ?prereq .
            ?prereq :enseigneCompetence ?comp .
            ?comp rdfs:label ?competenceLabel .
        }} UNION {{
            :{doc_id} :requiertCompetence ?comp .
            ?comp rdfs:label ?competenceLabel .
        }}
    }}
    """
    results = _run_query(query)
    return [b["competenceLabel"]["value"] for b in results["results"]["bindings"]]


def get_prerequisite_chain(doc_id: str) -> list[dict]:
    """Reconstruit la chaîne COMPLETE de prérequis (pas seulement le niveau
    direct) en remontant récursivement :aPrerequis. Sert à l'endpoint
    /api/course/{doc_id}/graph pour la visualisation côté frontend.
    On limite la profondeur à 5 pour éviter tout cycle mal formé."""
    chain = []
    seen = set()
    current = doc_id

    for _ in range(5):
        query = f"""
        {PREFIX}
        SELECT ?prereq ?titre WHERE {{
            :{current} :aPrerequis ?prereq .
            ?prereq :aTitre ?titre .
        }}
        """
        results = _run_query(query)["results"]["bindings"]
        if not results:
            break
        level = []
        for b in results:
            prereq_id = _local_name(b["prereq"]["value"])
            if prereq_id in seen:
                continue
            level.append({"doc_id": prereq_id, "titre": b["titre"]["value"]})
            seen.add(prereq_id)
        if not level:
            break
        chain.append(level)
        current = level[0]["doc_id"]

    return chain


def get_related_domains(domaine_local_name: str) -> list[str]:
    """Retourne les noms locaux (ex: 'Informatique', 'DeepLearning') des
    domaines liés — ancêtres ET descendants — en exploitant la fermeture
    TRANSITIVE réelle de :sousDomaineDe via un property path SPARQL 1.1
    (`+`). C'est ce qui manquait dans la version précédente : déclarer
    owl:TransitiveProperty dans l'ontologie ne suffit pas, Fuseki ne fait
    pas d'inférence OWL par défaut — il faut soit calculer la fermeture
    nous-mêmes ici (ce qu'on fait), soit activer un reasoner sur le dataset.
    Usage général (ex: affichage) -- PAS utilisée pour l'expansion de
    requête, voir get_descendant_domains ci-dessous.
    """
    query = f"""
    {PREFIX}
    SELECT DISTINCT ?d WHERE {{
        {{ :{domaine_local_name} :sousDomaineDe+ ?d . }}
        UNION
        {{ ?d :sousDomaineDe+ :{domaine_local_name} . }}
    }}
    """
    results = _run_query(query)
    return [_local_name(b["d"]["value"]) for b in results["results"]["bindings"]]


def get_descendant_domains(domaine_local_name: str) -> list[str]:
    """Retourne UNIQUEMENT les sous-domaines (descendants) d'un domaine,
    via la fermeture transitive de :sousDomaineDe. Utilisée par
    expand_query_domains : chercher un domaine large (ex: 'Intelligence
    Artificielle') doit ramener ses sous-domaines plus spécifiques (ML,
    DeepLearning, NLP), PAS remonter vers ses domaines ANCÊTRES (ex:
    'DataScience', 'Informatique'), qui sont plus larges et regroupent des
    cours sans rapport direct avec la requête. Contrairement à
    get_related_domains (ancêtres + descendants), volontairement à sens
    unique pour ne pas injecter de faux positifs dans le bonus d'expansion."""
    query = f"""
    {PREFIX}
    SELECT DISTINCT ?d WHERE {{
        ?d :sousDomaineDe+ :{domaine_local_name} .
    }}
    """
    results = _run_query(query)
    return [_local_name(b["d"]["value"]) for b in results["results"]["bindings"]]


get_descendant_domains = lru_cache(maxsize=None)(get_descendant_domains)


def get_all_typed_labels() -> list[dict]:
    """Récupère tous les couples (label, type, nom_local) pour Domaine et
    Competence. Sert de base au 'entity linking' — approche volontairement
    simple (matching de labels) adaptée à un PFM, mais RÉELLEMENT branchée
    dans le pipeline de recherche (contrairement à l'ancienne fonction
    get_related_domains qui n'était jamais appelée nulle part)."""
    query = f"""
    {PREFIX}
    SELECT ?entity ?label ?type WHERE {{
        {{ ?entity a :Domaine ; rdfs:label ?label . BIND("Domaine" AS ?type) }}
        UNION
        {{ ?entity a :Competence ; rdfs:label ?label . BIND("Competence" AS ?type) }}
    }}
    """
    results = _run_query(query)["results"]["bindings"]
    return [
        {
            "local_name": _local_name(b["entity"]["value"]),
            "label": b["label"]["value"],
            "type": b["type"]["value"],
        }
        for b in results
    ]


get_all_typed_labels = lru_cache(maxsize=1)(get_all_typed_labels)


# --- Désambiguïsation : scoring par contexte lexical + Knowledge Graph ---
# Mots-index simples indiquant que l'utilisateur parle plutôt d'un Domaine
# (une thématique de cours) ou plutôt d'une Compétence (un savoir-faire
# précis, ce qu'un cours enseigne ou exige en prérequis).
DOMAIN_CONTEXT_WORDS = {
    "domaine", "thematique", "thématique", "cours", "formation",
    "apprendre", "apprentissage", "sujet", "specialite", "spécialité",
}
SKILL_CONTEXT_WORDS = {
    "competence", "compétence", "competences", "compétences", "skill",
    "skills", "maitriser", "maîtriser", "maitrise", "maîtrise", "savoir",
    "savoir-faire", "enseigne", "enseigner", "requiert", "prerequis", "prérequis",
}


def _context_score(query_text: str, entity_type: str) -> float:
    """Score de contexte lexical (0 à 1) : la requête contient-elle des mots
    qui trahissent plutôt une recherche de Domaine ou de Compétence ?
    Départ neutre à 0.5 (aucun indice) ; chaque mot-index DU type considéré
    fait monter le score, chaque mot-index de L'AUTRE type le fait
    descendre — généralisable à n'importe quel terme ambigu (pas seulement
    'Cloud'), puisqu'on ne regarde jamais le terme lui-même, seulement les
    mots qui l'entourent."""
    text = f" {query_text.lower()} "
    own_words = DOMAIN_CONTEXT_WORDS if entity_type == "Domaine" else SKILL_CONTEXT_WORDS
    other_words = SKILL_CONTEXT_WORDS if entity_type == "Domaine" else DOMAIN_CONTEXT_WORDS
    own_hits = sum(1 for w in own_words if w in text)
    other_hits = sum(1 for w in other_words if w in text)
    score = 0.5 + 0.25 * min(own_hits, 2) - 0.2 * min(other_hits, 2)
    return max(0.0, min(1.0, score))


def _knowledge_graph_score(candidate: dict) -> float:
    """Score basé sur la richesse RÉELLE des relations de cette
    interprétation dans le graphe : combien de cours sont concrètement
    reliés à cette entité (comme domaine via :appartientADomaine, ou
    comme compétence via :enseigneCompetence / :requiertCompetence).
    5 cours reliés ou plus -> score maximal 1.0."""
    if candidate["type"] == "Domaine":
        query = f"""
        {PREFIX}
        SELECT (COUNT(DISTINCT ?cours) AS ?n) WHERE {{
            ?cours :appartientADomaine :{candidate['local_name']} .
        }}
        """
    else:
        query = f"""
        {PREFIX}
        SELECT (COUNT(DISTINCT ?cours) AS ?n) WHERE {{
            {{ ?cours :enseigneCompetence :{candidate['local_name']} . }}
            UNION
            {{ ?cours :requiertCompetence :{candidate['local_name']} . }}
        }}
        """
    results = _run_query(query)["results"]["bindings"]
    n = int(results[0]["n"]["value"]) if results and results[0].get("n") else 0
    return min(1.0, n / 5)


def score_entity_interpretation(query_text: str, candidate: dict) -> dict:
    """Combine le score de contexte lexical (70%) et le score de richesse
    dans le Knowledge Graph (30%) pour UNE interprétation candidate
    (ex: 'Cloud' en tant que Domaine). Le contexte est volontairement
    prépondérant : un mot-index explicite ('compétence cloud') doit
    trancher même face à un domaine très riche en cours dans le graphe —
    le score KG sert surtout de départage quand le contexte est neutre
    (aucun mot-index des deux côtés). Retourne {"score": float, "raison":
    str} — la raison est générée dynamiquement selon ce qui a fait pencher
    la balance, pour être affichée telle quelle côté frontend."""
    ctx = _context_score(query_text, candidate["type"])
    kg = _knowledge_graph_score(candidate)
    score = round(0.7 * ctx + 0.3 * kg, 2)

    type_fr = "un domaine/cours" if candidate["type"] == "Domaine" else "une compétence"
    if ctx >= 0.7:
        raison = f"Le contexte de la requête indique une recherche portant sur {type_fr}."
    elif ctx <= 0.3:
        raison = f"Le contexte de la requête ne correspond pas à {type_fr} ; interprétation peu probable."
    elif kg >= 0.6:
        raison = f"'{candidate['label']}' est fortement relié à des cours dans le graphe en tant que {candidate['type'].lower()}."
    else:
        raison = f"'{candidate['label']}' existe aussi comme {candidate['type'].lower()}, sans indice de contexte fort."

    return {"score": score, "raison": raison}


def link_entities_in_query(query_text: str, all_entities: list[dict] = None) -> list[dict]:
    """Entity linking + désambiguïsation.

    Cherche, parmi les labels connus du graphe, ceux qui apparaissent dans
    le texte de la requête (comparaison insensible à la casse). Si un même
    libellé correspond à PLUSIEURS types d'entités (ex: 'Cloud' est à la
    fois un Domaine et une Compétence dans l'ontologie), chaque
    interprétation reçoit un SCORE (contexte lexical de la requête +
    richesse de ses relations dans le Knowledge Graph), et celle au score
    le plus élevé est retenue — la résolution n'est donc jamais un choix
    arbitraire ('on privilégie toujours Domaine'), elle dépend de la
    requête elle-même. Ex: 'cours cloud' résout en Domaine, 'compétence
    cloud' résout en Competence, pour le même terme "Cloud".
    """
    text = query_text.lower()
    query_words = [w for w in text.split() if len(w) >= 3]
    if all_entities is None:
        all_entities = get_all_typed_labels()

    matches_by_label: dict[str, list[dict]] = {}
    for ent in all_entities:
        label_lower = ent["label"].lower()
        # Cas 1 (historique) : le label complet apparaît tel quel dans la
        # requête (ex: requête "cours de deep learning avancé" -> label
        # "Deep Learning").
        # Cas 2 (fix) : un mot de la requête est un préfixe partiel d'un
        # mot du label, ou inversement (ex: requête "DEEP" -> mot "deep"
        # préfixe du mot "deep" dans "Deep Learning"). Sans ce 2e cas,
        # toute requête courte/tronquée sur un label multi-mots ne matchait
        # JAMAIS aucune entité : expand_query_domains() recevait alors une
        # liste vide, expansion_hits restait vide, et TOUS les résultats
        # de la recherche perdaient tout le bonus POIDS_EXPANSION (0.40,
        # le plus gros poids du score final) même quand le cours
        # appartenait exactement au domaine cherché.
        # Filtre aussi les mots courts (< 3 lettres) côté label — sinon des
        # prépositions comme "de"/"la"/"le" dans un label multi-mots
        # ("Bases de données", "Réseaux de neurones"...) matchent par
        # préfixe n'importe quel mot de requête qui commence par les mêmes
        # 2 lettres (ex: "deep".startswith("de")), créant des faux positifs
        # sans rapport avec le sens de la requête.
        label_words = [w for w in label_lower.split() if len(w) >= 3]
        matched = label_lower in text or any(
            lw.startswith(qw) or qw.startswith(lw)
            for lw in label_words
            for qw in query_words
        )
        if matched:
            matches_by_label.setdefault(ent["label"], []).append(ent)

    linked = []
    for label, candidates in matches_by_label.items():
        types_found = {c["type"] for c in candidates}
        ambiguous = len(types_found) > 1

        scored = [
            {**c, **score_entity_interpretation(query_text, c)}
            for c in candidates
        ]
        scored.sort(key=lambda c: c["score"], reverse=True)
        preferred = scored[0]

        raison_resolution = None
        if ambiguous:
            gap = scored[0]["score"] - scored[1]["score"]
            if gap < 0.05:
                raison_resolution = (
                    f"Scores très proches entre les interprétations possibles ; "
                    f"{preferred['type']} retenu par défaut."
                )
            else:
                raison_resolution = preferred["raison"]

        linked.append({
            "label": label,
            "ambiguous": ambiguous,
            "candidates": candidates,
            "interpretation_retenue": preferred,
            "interpretations": scored,
            "raison_resolution": raison_resolution,
        })
    return linked


def expand_query_domains(linked_entities: list[dict]) -> list[str]:
    """A partir des entités liées (résultat de link_entities_in_query),
    retourne l'ensemble élargi des domaines (noms locaux) à utiliser pour
    booster la recherche : le domaine détecté lui-même + ses domaines
    apparentés (parents ET enfants) via la fermeture transitive du graphe.
    """
    expanded = set()
    for ent in linked_entities:
        chosen = ent["interpretation_retenue"]
        if chosen["type"] != "Domaine":
            continue
        domain_local = chosen["local_name"]
        expanded.add(domain_local)
        expanded.update(get_descendant_domains(domain_local))
    return sorted(expanded)


def get_formateur(doc_id: str) -> str | None:
    if doc_id in _formateur_cache:
        return _formateur_cache[doc_id]
    query = f"""
    {PREFIX}
    SELECT ?label WHERE {{
        :{doc_id} :enseignePar ?f .
        ?f rdfs:label ?label .
    }}
    """
    results = _run_query(query)["results"]["bindings"]
    return results[0]["label"]["value"] if results else None


def get_parcours(doc_id: str) -> list[str]:
    if doc_id in _parcours_cache:
        return _parcours_cache[doc_id]
    query = f"""
    {PREFIX}
    SELECT ?label WHERE {{
        :{doc_id} :faitPartieDe ?p .
        ?p rdfs:label ?label .
    }}
    """
    results = _run_query(query)["results"]["bindings"]
    return [b["label"]["value"] for b in results]


def user_has_competences(user_competences: list[str], required: list[str]) -> tuple[bool, list[str]]:
    """Vérifie si l'utilisateur possède les compétences requises.
    Retourne (ok, compétences_manquantes)."""
    missing = [c for c in required if c not in user_competences]
    return (len(missing) == 0, missing)


def get_course_concepts(doc_id: str) -> dict:
    """Retourne les compétences ENSEIGNÉES et REQUISES d'un cours, avec à la
    fois leur nom local (pour les comparer à une entité détectée dans une
    requête) et leur libellé lisible (pour l'affichage). Sert de base au
    calcul de 'matched_concepts' / 'related_concepts' pour la fonctionnalité
    'Why this result?' de la page Search."""
    if doc_id in _concepts_cache:
        return _concepts_cache[doc_id]
    query = f"""
    {PREFIX}
    SELECT ?comp ?label ?role WHERE {{
        {{ :{doc_id} :enseigneCompetence ?comp . BIND("enseignee" AS ?role) }}
        UNION
        {{ :{doc_id} :requiertCompetence ?comp . BIND("requise" AS ?role) }}
        ?comp rdfs:label ?label .
    }}
    """
    results = _run_query(query)["results"]["bindings"]
    enseignees, requises = [], []
    for b in results:
        item = {"local_name": _local_name(b["comp"]["value"]), "label": b["label"]["value"]}
        (enseignees if b["role"]["value"] == "enseignee" else requises).append(item)
    return {"enseignees": enseignees, "requises": requises}


def get_domain_ancestor_chain(domain_local_name: str) -> list[str]:
    """Reconstruit la chaîne ORDONNÉE des domaines ancêtres (parent,
    grand-parent, ...) en suivant :sousDomaineDe UN SAUT À LA FOIS.
    get_related_domains() calcule déjà la fermeture transitive complète en
    une seule requête SPARQL 1.1 (:sousDomaineDe+), mais retourne un
    ensemble non ordonné ; cette fonction reconstruit pas à pas la chaîne
    de déduction elle-même, pour l'afficher concrètement côté frontend
    (section 'Knowledge Graph Inference') et illustrer ce que signifie
    déclarer :sousDomaineDe comme owl:TransitiveProperty dans l'ontologie :
    DeepLearning sousDomaineDe MachineLearning, MachineLearning
    sousDomaineDe IntelligenceArtificielle => DeepLearning sousDomaineDe
    IntelligenceArtificielle (relation déduite, jamais affirmée directement)."""
    chain = [domain_local_name]
    current = domain_local_name
    for _ in range(10):  # garde-fou anti-cycle, comme get_prerequisite_chain
        query = f"""
        {PREFIX}
        SELECT ?parent WHERE {{ :{current} :sousDomaineDe ?parent . }} LIMIT 1
        """
        results = _run_query(query)["results"]["bindings"]
        if not results:
            break
        parent_local = _local_name(results[0]["parent"]["value"])
        if parent_local in chain:
            break
        chain.append(parent_local)
        current = parent_local
    return chain


def find_domain_path(source_local: str, target_local: str) -> list[str] | None:
    """Recherche par chemin dans le graphe (fonctionnalité 'Find semantic
    path') : parcours en largeur (BFS) sur le graphe NON ORIENTÉ des
    arêtes directes :sousDomaineDe (on peut donc remonter vers un parent
    OU descendre vers un enfant à chaque étape), pour trouver le plus
    court chemin entre deux domaines - par exemple DeepLearning ->
    MachineLearning -> IntelligenceArtificielle -> DataScience si
    DataScience n'est pas un ancêtre direct de DeepLearning mais partage
    un ancêtre commun. Retourne None si aucun chemin n'existe (composantes
    du graphe non connectées)."""
    hierarchy = get_domain_hierarchy()
    adjacency: dict[str, set[str]] = {}
    for edge in hierarchy["edges"]:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])

    if source_local == target_local:
        return [source_local]
    if source_local not in adjacency or target_local not in adjacency:
        return None

    queue = deque([[source_local]])
    visited = {source_local}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in sorted(adjacency.get(node, [])):
            if neighbor == target_local:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None


def get_domain_hierarchy() -> dict:
    """Retourne TOUS les domaines (nœuds) et leurs relations DIRECTES
    :sousDomaineDe (arêtes), pour alimenter la visualisation interactive
    de la page 'Knowledge Graph'. Contrairement à get_related_domains(),
    on ne calcule PAS la fermeture transitive ici : on veut le graphe tel
    qu'il est déclaré (arbre de domaines), pas son enveloppe complète."""
    nodes_query = f"""
    {PREFIX}
    SELECT ?d ?label WHERE {{
        ?d a :Domaine ; rdfs:label ?label .
    }}
    """
    edges_query = f"""
    {PREFIX}
    SELECT ?child ?parent WHERE {{
        ?child :sousDomaineDe ?parent .
    }}
    """
    nodes = [
        {"id": _local_name(b["d"]["value"]), "label": b["label"]["value"]}
        for b in _run_query(nodes_query)["results"]["bindings"]
    ]
    edges = [
        {"source": _local_name(b["child"]["value"]), "target": _local_name(b["parent"]["value"])}
        for b in _run_query(edges_query)["results"]["bindings"]
    ]
    return {"nodes": nodes, "edges": edges}
