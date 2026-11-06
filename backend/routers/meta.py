# Expose en lecture seule la configuration de fusion du moteur (poids
# lexical/vectoriel/graphe/expansion, modèle d'embeddings), pour que le
# frontend affiche les VRAIS poids utilisés côté serveur ("Search
# strategy" sur la page Search) plutôt que de les dupliquer en dur.

from fastapi import APIRouter
from models.schemas import SearchConfig
import config

router = APIRouter()


@router.get("/config", response_model=SearchConfig)
async def get_config():
    return SearchConfig(
        poids_lexical=config.POIDS_LEXICAL,
        poids_vectoriel=config.POIDS_VECTORIEL,
        poids_graphe=config.POIDS_GRAPHE,
        poids_expansion=config.POIDS_EXPANSION,
        embedding_model=config.EMBEDDING_MODEL_NAME,
    )
