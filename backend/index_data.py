# A lancer UNE FOIS (ou à chaque fois que tu modifies cours.json) pour
# remplir Elasticsearch avec les cours + leurs embeddings.
#
# Commande : python index_data.py

import json
from services import elastic_service

with open("data/cours.json", encoding="utf-8") as f:
    courses = json.load(f)

print(f"Création de l'index '{elastic_service.ELASTICSEARCH_INDEX if hasattr(elastic_service, 'ELASTICSEARCH_INDEX') else 'cours'}'...")
elastic_service.create_index()

print(f"Indexation de {len(courses)} cours (calcul des embeddings, patience)...")
for i, course in enumerate(courses, 1):
    elastic_service.index_course(course)
    print(f"  [{i}/{len(courses)}] {course['titre']}")

print("Terminé ! Les cours sont indexés dans Elasticsearch.")
