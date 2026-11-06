# C'est le coeur "intelligent" du projet : on combine les résultats
# des recherches lexicale + vectorielle + expansion de domaine par le
# graphe en une seule liste triée, et on utilise le graphe pour :
# - exclure les cours dont un prérequis n'est pas satisfait
# - AJOUTER des candidats trouvés uniquement grâce à la structure du
#   Knowledge Graph (sous-domaines), ce qui n'existait pas dans la
#   version précédente (la fonction d'expansion existait mais n'était
#   jamais appelée par le pipeline de recherche)

from config import POIDS_LEXICAL, POIDS_VECTORIEL, POIDS_GRAPHE, POIDS_EXPANSION, RRF_K
from services import graph_service


def _normalize_scores(hits: list, score_key: str = "_score") -> dict:
    """Remet les scores ES entre 0 et 1 pour pouvoir les combiner
    équitablement avec le score de similarité vectorielle (déjà 0-1).
    Utilisée par /api/search/lexical-only (score BM25 brut affiché seul,
    pas de fusion). N'est PLUS utilisée dans fuse_results (voir _rank_map /
    _rrf_score ci-dessous : la fusion combine des RANGS, pas des scores
    bruts -- cf. leur docstring pour le pourquoi)."""
    if not hits:
        return {}
    scores = [h[score_key] for h in hits]
    max_score = max(scores) if max(scores) > 0 else 1
    return {h["_id"]: h[score_key] / max_score for h in hits}


def _rank_map(hits: list, score_key: str = "_score") -> dict:
    """doc_id -> rang (0 = meilleur résultat), pour une liste de hits déjà
    triée ou à trier par score décroissant."""
    ordered = sorted(hits, key=lambda h: h[score_key], reverse=True)
    return {h["_id"]: i for i, h in enumerate(ordered)}


def _rrf_score(rank: int, k: int = RRF_K) -> float:
    """Score de fusion par rang (Reciprocal Rank Fusion), normé entre 0
    (rang très lointain) et 1 (rang 0 = meilleur résultat du retriever).

    Pourquoi RRF et pas juste normaliser le score brut par le max du lot
    (ancienne approche) : ici, vector_search() est interrogée avec un pool
    (CANDIDATE_POOL_SIZE=100) plus grand que tout le catalogue (70 cours),
    donc elle retourne LITTÉRALEMENT tous les cours, chacun avec un vrai
    score de similarité cosinus jamais nul. Diviser par le max donnait donc
    un score non négligeable même au cours le MOINS pertinent du
    catalogue -- ce qui diluait le signal et empêchait l'hybride de se
    distinguer du vectoriel seul (mesuré : hybride < vectoriel seul sur
    Rappel@5/NDCG@5). Un score basé sur le RANG, lui, s'effondre vite au-
    delà des tout premiers résultats, quel que soit l'écart de score brut
    entre 1er et dernier -- c'est la technique standard pour fusionner des
    retrievers dont les scores bruts ne sont pas sur la même échelle
    (BM25 vs cosinus vs bonus binaire du graphe).
    RRF_K est volontairement petit (voir config.py) : la formule standard
    (k=60) est calibrée pour des corpus de milliers de documents ; avec un
    catalogue de 70 cours, k=60 ne différencierait quasiment pas les rangs
    entre eux."""
    return (k + 1) / (k + 1 + rank)


def fuse_results(
    lexical_hits: list,
    vector_hits: list,
    all_docs_by_id: dict,
    expansion_hits: list = None,
    expanded_domains: list = None,
    user_competences: list[str] = None,
    linked_entities: list[dict] = None,
    label_by_local: dict = None,
) -> list[dict]:
    """Fusionne lexical + vectoriel + candidats trouvés par expansion de
    domaine (KG), applique le raisonnement du graphe (exclusion par
    prérequis), enrichit avec formateur/parcours, et trie par score final
    décroissant.

    `linked_entities` (sortie de graph_service.link_entities_in_query) et
    `label_by_local` (nom local -> libellé, pour TOUS les domaines/compétences)
    servent uniquement à calculer, pour chaque résultat, les concepts
    'matched' (ce qui, dans la requête, correspond directement à ce cours)
    et 'related' (ce que le graphe rattache à ce cours sans correspondance
    directe) -- affichés dans le panneau 'Why this result?' du frontend."""
    # Distinction cruciale : `None` = aucun profil utilisateur connu (recherche
    # anonyme, évaluation) -> on ne peut/doit rien exclure faute d'info.
    # `[]` = profil connu, utilisateur qui n'a explicitement AUCUNE compétence
    # -> l'exclusion par prérequis doit s'appliquer normalement.
    # Avant ce fix, les deux cas étaient traités pareil (user_competences or [])
    # et TOUT cours ayant un prérequis (58/70 dans le catalogue) était exclu et
    # relégué en fin de classement dès qu'aucun profil n'était transmis -- ce
    # qui est systématiquement le cas pour /api/search (le champ n'existe même
    # pas dans SearchRequest) et pour evaluate.py. Résultat : le mode hybride
    # était pénalisé par une fonctionnalité de personnalisation qui ne recevait
    # jamais de vraies données, et perdait face aux baselines lexical/vectoriel
    # qui n'appliquent pas cette exclusion.
    has_user_profile = user_competences is not None
    user_competences = user_competences or []
    expansion_hits = expansion_hits or []
    expanded_domains = set(expanded_domains or [])
    linked_entities = linked_entities or []
    label_by_local = label_by_local or {}

    linked_domain_locals = {
        ent["interpretation_retenue"]["local_name"]: ent["label"]
        for ent in linked_entities
        if ent["interpretation_retenue"]["type"] == "Domaine"
    }
    linked_competence_locals = {
        ent["interpretation_retenue"]["local_name"]: ent["label"]
        for ent in linked_entities
        if ent["interpretation_retenue"]["type"] == "Competence"
    }

    lexical_rank = _rank_map(lexical_hits)
    vector_rank = _rank_map(vector_hits)
    # Les candidats d'expansion (recherche par domaines élargis) n'ont pas de
    # rang "naturel" pertinent -- search_by_domains() est un simple filtre
    # par égalité de domaine, pas un score de pertinence. On les classe donc
    # par leur proximité sémantique déjà connue (rang vectoriel), pour que
    # les cours d'un sous-domaine réellement proches de la requête pèsent
    # plus, dans le bonus graphe, que ceux qui n'y sont que par appartenance
    # administrative au même domaine.
    expansion_doc_ids = {h["_id"] for h in expansion_hits}
    expansion_ordered = sorted(
        expansion_hits,
        key=lambda h: (vector_rank.get(h["_id"], 10**9), lexical_rank.get(h["_id"], 10**9)),
    )
    expansion_rank = {h["_id"]: i for i, h in enumerate(expansion_ordered)}

    all_ids = sorted(set(lexical_rank.keys()) | set(vector_rank.keys()) | expansion_doc_ids)

    results = []
    for doc_id in all_ids:
        doc = all_docs_by_id.get(doc_id)
        if not doc:
            continue

        score_lex = _rrf_score(lexical_rank[doc_id]) if doc_id in lexical_rank else 0.0
        score_vec = _rrf_score(vector_rank[doc_id]) if doc_id in vector_rank else 0.0

        # Bonus d'expansion : le cours appartient à un domaine élargi par le
        # graphe (lui-même ou un domaine apparenté), OU a été retrouvé via
        # la recherche par domaines élargis.
        #
        # (Retour en arrière : j'avais tenté de ne donner le bonus plein
        # qu'aux cours "trouvés UNIQUEMENT par le graphe" (score_lex==0 ET
        # score_vec==0), en pensant que le bonus était donné à tort à des
        # cours déjà repérés par lexical/vectoriel. Erreur de raisonnement :
        # vector_search() est interrogée avec pool=100 > taille du corpus
        # (70 cours), donc elle retourne TOUJOURS les 70 cours avec un vrai
        # score de similarité cosinus -- jamais exactement 0. La condition
        # "score_vec == 0.0" n'était donc presque JAMAIS vraie, et quasi
        # tous les candidats d'expansion (y compris les sous-domaines de
        # "intelligence artificielle", la raison d'être du graphe) se
        # retrouvaient rabaissés au bonus réduit. Mesuré : ça a fait
        # baisser hybride sur les 3 métriques au lieu de les améliorer.
        #
        # Nouvelle version (RRF) : le bonus n'est plus binaire (1.0/0.0) mais
        # basé sur le rang du cours DANS le sous-groupe des candidats
        # d'expansion (voir expansion_rank ci-dessus, classé par proximité
        # vectorielle). Un cours du domaine élargi qui est AUSSI le plus
        # proche sémantiquement de la requête reçoit un bonus fort ; un cours
        # qui n'a que son domaine en commun avec la requête (ex: un cours
        # avancé sur un domaine "débutant") reçoit un bonus qui s'effondre
        # vite -- contrairement à l'ancien bonus plat qui traitait les deux
        # cas pareil.
        score_expansion = _rrf_score(expansion_rank[doc_id]) if doc_id in expansion_rank else 0.0

        trouve_uniquement_par_graphe = (
            doc_id in expansion_doc_ids and score_lex == 0.0 and score_vec == 0.0
        )

        # --- Raisonnement du graphe : exclusion par prérequis ---
        # On n'exclut que si on connaît réellement le profil de l'utilisateur.
        # Sans profil, impossible de juger s'il "manque" une compétence : on
        # considère le cours comme accessible (ok=True), sans quoi tout cours
        # avec prérequis serait injustement relégué en fin de classement.
        required_competences = graph_service.get_prerequisites(doc_id)
        if has_user_profile:
            ok, missing = graph_service.user_has_competences(user_competences, required_competences)
        else:
            ok, missing = True, []
        score_graphe = 1.0 if ok else 0.0

        score_final = (
            POIDS_LEXICAL * score_lex
            + POIDS_VECTORIEL * score_vec
            + POIDS_GRAPHE * score_graphe
            + POIDS_EXPANSION * score_expansion
        )

        # --- "Why this result?" : concepts détectés dans la requête qui
        # correspondent directement à ce cours (matched), vs. concepts que
        # le graphe rattache à ce cours sans correspondance directe (related) ---
        concepts = graph_service.get_course_concepts(doc_id)
        course_competence_locals = {
            c["local_name"]: c["label"] for c in concepts["enseignees"] + concepts["requises"]
        }
        matched_concepts = set()
        if doc.get("domaine") in linked_domain_locals:
            matched_concepts.add(linked_domain_locals[doc["domaine"]])
        for local, label in course_competence_locals.items():
            if local in linked_competence_locals:
                matched_concepts.add(label)

        related_concepts = set()
        for d in expanded_domains:
            if d != doc.get("domaine") and d in label_by_local:
                related_concepts.add(label_by_local[d])
        for label in course_competence_locals.values():
            if label not in matched_concepts:
                related_concepts.add(label)
        related_concepts -= matched_concepts

        results.append({
            "doc_id": doc_id,
            "titre": doc["titre"],
            "description": doc["description"],
            "domaine": doc["domaine"],
            "niveau": doc["niveau"],
            "score_lexical": round(score_lex, 3),
            "score_vectoriel": round(score_vec, 3),
            "score_graphe": round(score_graphe, 3),
            "score_expansion_domaine": round(score_expansion, 3),
            "score_final": round(score_final, 3),
            "exclu": not ok,
            "raison_exclusion": (
                f"Prérequis manquant(s): {', '.join(missing)}" if not ok else None
            ),
            "trouve_par_expansion_graphe": trouve_uniquement_par_graphe,
            "formateur": graph_service.get_formateur(doc_id),
            "parcours": graph_service.get_parcours(doc_id),
            "duree_heures": doc.get("duree_heures"),
            "note": doc.get("note"),
            "gratuit": doc.get("gratuit"),
            "matched_concepts": sorted(matched_concepts),
            "related_concepts": sorted(related_concepts)[:5],
        })

    # Les cours exclus passent en dernier, le reste trié par score décroissant.
    # En cas d'égalité exacte sur score_final (fréquent avec les bonus
    # graphe/expansion binaires), on départage par le score vectoriel puis
    # lexical bruts, et enfin par doc_id -> classement 100% déterministe et
    # reproductible d'un run à l'autre (contrairement à un simple tri sur
    # une liste construite depuis un set, dont l'ordre initial dépend du
    # hachage aléatoire des chaînes de Python).
    results.sort(key=lambda r: (
        r["exclu"], -r["score_final"], -r["score_vectoriel"], -r["score_lexical"], r["doc_id"],
    ))
    return results
