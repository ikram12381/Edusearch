# Test unitaire hors-ligne de la logique de fusion des scores.
# On simule (mock) graph_service pour ne PAS dépendre de Fuseki : ça permet
# de vérifier la logique de pondération/exclusion même sans infrastructure
# lancée, et de le montrer en soutenance comme preuve de fiabilité.
#
# Lancer avec : pytest backend/tests/test_ranking_service.py -v

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from services import ranking_service


FAKE_DOCS = {
    "Cours_A": {"titre": "Cours A", "description": "desc A", "domaine": "Informatique", "niveau": "Debutant"},
    "Cours_B": {"titre": "Cours B", "description": "desc B", "domaine": "DeepLearning", "niveau": "Debutant"},
    "Cours_C": {"titre": "Cours C", "description": "desc C", "domaine": "MachineLearning", "niveau": "Debutant"},
}


@patch("services.graph_service.get_course_concepts", return_value={"enseignees": [], "requises": []})
@patch("services.graph_service.get_formateur", return_value=None)
@patch("services.graph_service.get_parcours", return_value=[])
@patch("services.graph_service.user_has_competences")
@patch("services.graph_service.get_prerequisites")
def test_exclusion_par_prerequis_manquant(mock_prereq, mock_has_comp, *_):
    """Avec un VRAI profil utilisateur (liste de compétences, même vide),
    un cours dont les prérequis ne sont pas satisfaits doit être marqué
    exclu=True et passer en fin de liste, même s'il a le meilleur score."""
    mock_prereq.return_value = ["Algèbre linéaire"]
    mock_has_comp.return_value = (False, ["Algèbre linéaire"])

    lexical_hits = [{"_id": "Cours_A", "_score": 10.0}]
    results = ranking_service.fuse_results(
        lexical_hits=lexical_hits,
        vector_hits=[],
        all_docs_by_id=FAKE_DOCS,
        user_competences=[],  # profil connu, mais 0 compétence déclarée
    )

    assert results[0]["doc_id"] == "Cours_A"
    assert results[0]["exclu"] is True
    assert "Algèbre linéaire" in results[0]["raison_exclusion"]


@patch("services.graph_service.get_course_concepts", return_value={"enseignees": [], "requises": []})
@patch("services.graph_service.get_formateur", return_value=None)
@patch("services.graph_service.get_parcours", return_value=[])
@patch("services.graph_service.user_has_competences")
@patch("services.graph_service.get_prerequisites")
def test_pas_de_profil_donc_pas_exclusion(mock_prereq, mock_has_comp, *_):
    """Régression du bug identifié le 13/09 : SANS profil utilisateur
    (user_competences=None, cas de /api/search et de evaluate.py), un cours
    avec prérequis ne doit PAS être exclu -- on n'a aucune base pour juger
    que l'utilisateur ne les possède pas. C'est ce qui plombait le mode
    hybride en évaluation (P@5 pire que lexical/vectoriel seuls)."""
    mock_prereq.return_value = ["Algèbre linéaire"]

    lexical_hits = [{"_id": "Cours_A", "_score": 10.0}]
    results = ranking_service.fuse_results(
        lexical_hits=lexical_hits,
        vector_hits=[],
        all_docs_by_id=FAKE_DOCS,
        # user_competences non fourni -> None -> pas de profil
    )

    assert results[0]["doc_id"] == "Cours_A"
    assert results[0]["exclu"] is False
    assert results[0]["raison_exclusion"] is None
    mock_has_comp.assert_not_called()


@patch("services.graph_service.get_course_concepts", return_value={"enseignees": [], "requises": []})
@patch("services.graph_service.get_formateur", return_value=None)
@patch("services.graph_service.get_parcours", return_value=[])
@patch("services.graph_service.user_has_competences", return_value=(True, []))
@patch("services.graph_service.get_prerequisites", return_value=[])
def test_expansion_domaine_ajoute_un_candidat_absent_du_lexical_et_vectoriel(*_):
    """Un cours trouvé UNIQUEMENT via l'expansion de domaine du graphe (pas
    par le lexical ni le vectoriel) doit quand même apparaître dans les
    résultats, avec trouve_par_expansion_graphe=True."""
    expansion_hits = [{"_id": "Cours_C", "_score": 1.0}]

    results = ranking_service.fuse_results(
        lexical_hits=[],
        vector_hits=[],
        all_docs_by_id=FAKE_DOCS,
        expansion_hits=expansion_hits,
        expanded_domains=["MachineLearning", "IntelligenceArtificielle"],
    )

    doc_ids = [r["doc_id"] for r in results]
    assert "Cours_C" in doc_ids
    result_c = next(r for r in results if r["doc_id"] == "Cours_C")
    assert result_c["trouve_par_expansion_graphe"] is True
    assert result_c["score_expansion_domaine"] == 1.0


@patch("services.graph_service.get_course_concepts", return_value={"enseignees": [], "requises": []})
@patch("services.graph_service.get_formateur", return_value=None)
@patch("services.graph_service.get_parcours", return_value=[])
@patch("services.graph_service.user_has_competences", return_value=(True, []))
@patch("services.graph_service.get_prerequisites", return_value=[])
def test_tri_par_score_final_decroissant(*_):
    """Les cours non exclus doivent être triés par score_final décroissant."""
    lexical_hits = [{"_id": "Cours_A", "_score": 5.0}, {"_id": "Cours_B", "_score": 10.0}]

    results = ranking_service.fuse_results(
        lexical_hits=lexical_hits,
        vector_hits=[],
        all_docs_by_id=FAKE_DOCS,
    )

    scores = [r["score_final"] for r in results]
    assert scores == sorted(scores, reverse=True)


@patch("services.graph_service.get_formateur", return_value=None)
@patch("services.graph_service.get_parcours", return_value=[])
@patch("services.graph_service.user_has_competences", return_value=(True, []))
@patch("services.graph_service.get_prerequisites", return_value=[])
@patch("services.graph_service.get_course_concepts")
def test_matched_et_related_concepts_et_champs_catalogue(mock_concepts, *_):
    """Vérifie le calcul de matched_concepts/related_concepts ('Why this
    result?') et le passage des champs catalogue (durée/note/gratuit)."""
    mock_concepts.return_value = {
        "enseignees": [{"local_name": "CompReseauxNeurones", "label": "Réseaux de neurones"}],
        "requises": [],
    }
    docs = {
        "Cours_B": {
            "titre": "Cours B", "description": "desc B", "domaine": "DeepLearning",
            "niveau": "Debutant", "duree_heures": 18, "note": 4.8, "gratuit": False,
        },
    }
    linked_entities = [{
        "label": "Deep Learning",
        "ambiguous": False,
        "candidates": [{"local_name": "DeepLearning", "label": "Deep Learning", "type": "Domaine"}],
        "interpretation_retenue": {"local_name": "DeepLearning", "label": "Deep Learning", "type": "Domaine"},
    }]
    label_by_local = {"DeepLearning": "Deep Learning", "MachineLearning": "Machine Learning"}

    results = ranking_service.fuse_results(
        lexical_hits=[{"_id": "Cours_B", "_score": 5.0}],
        vector_hits=[],
        all_docs_by_id=docs,
        expanded_domains=["DeepLearning", "MachineLearning"],
        linked_entities=linked_entities,
        label_by_local=label_by_local,
    )

    r = results[0]
    assert r["duree_heures"] == 18 and r["note"] == 4.8 and r["gratuit"] is False
    assert "Deep Learning" in r["matched_concepts"]
    assert "Machine Learning" in r["related_concepts"]


if __name__ == "__main__":
    test_exclusion_par_prerequis_manquant()
    test_expansion_domaine_ajoute_un_candidat_absent_du_lexical_et_vectoriel()
    test_tri_par_score_final_decroissant()
    print("Tous les tests sont passés.")
