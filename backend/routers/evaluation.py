# Expose le protocole d'évaluation (Précision@k / Rappel@k / NDCG@k,
# système hybride vs. chaque composante isolée) à la page "Search
# Evaluation" du frontend, sans avoir à lancer evaluation/evaluate.py
# séparément en ligne de commande.

from fastapi import APIRouter
from models.schemas import EvaluationResponse
from services import evaluation_service

router = APIRouter()


@router.get("/evaluation", response_model=EvaluationResponse)
async def get_evaluation(k: int = 5):
    return evaluation_service.run_evaluation(k=k)
