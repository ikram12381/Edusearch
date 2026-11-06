# Ce service transforme un texte (titre + description d'un cours,
# ou la requête de l'utilisateur) en un vecteur numérique qui
# représente son SENS. Deux textes proches en sens auront des
# vecteurs proches (mesuré par similarité cosinus).

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME

# Le modèle est chargé une seule fois au démarrage du serveur
# (le charger à chaque requête serait beaucoup trop lent).
_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def get_embedding(text: str) -> list[float]:
    """Transforme un texte en vecteur (liste de floats)."""
    vector = _model.encode(text, normalize_embeddings=True)
    return vector.tolist()
