# Script de génération : étoffe backend/data/cours.json et ontology/elearning.ttl
# avec de nouveaux cours répartis sur davantage de domaines (AI, Big Data,
# Cloud, DevOps, Cybersécurité, Développement Web, Bases de données, Langues,
# Mathématiques...), tout en conservant les 20 cours et toutes les relations
# existantes. Chaque nouveau cours reçoit le même doc_id des deux côtés
# (cours.json <-> RDF), pour que Elasticsearch et le Knowledge Graph restent
# cohérents (cf. cahier des charges, section "Cohérence des données").
#
# Usage : python backend/generate_dataset.py
# Régénère aussi ontology/elearning.rdf (export RDF/XML) à partir du .ttl
# fusionné, via rdflib, pour que les deux formats restent synchronisés.

import json
import os
import random

random.seed(42)

ROOT = os.path.join(os.path.dirname(__file__), "..")
COURS_JSON_PATH = os.path.join(ROOT, "backend", "data", "cours.json")
TTL_PATH = os.path.join(ROOT, "ontology", "elearning.ttl")
RDF_PATH = os.path.join(ROOT, "ontology", "elearning.rdf")

PREFIX = "http://www.projet-pfm.org/elearning#"

# --- Nouveau domaine : Big Data (sous-domaine de Data Science) ---
NEW_DOMAIN_TTL = """
:BigData a owl:NamedIndividual, :Domaine ;
    rdfs:label "Big Data" ;
    :sousDomaineDe :DataScience .
"""

# --- Nouvelles compétences ---
NEW_COMPETENCES = {
    "CompScikitLearn": "Scikit-learn",
    "CompTensorFlow": "TensorFlow / Keras",
    "CompSpark": "Apache Spark",
    "CompNoSQL": "NoSQL / MongoDB",
    "CompPostgres": "PostgreSQL avancé",
    "CompLinux": "Linux / ligne de commande",
    "CompNodeJS": "Node.js",
    "CompVueJS": "Vue.js",
    "CompCSS": "CSS moderne",
    "CompTerraform": "Terraform (Infra as Code)",
    "CompCICD": "CI/CD",
    "CompMonitoring": "Monitoring & observabilité",
    "CompCryptographie": "Cryptographie",
    "CompEthicalHacking": "Ethical Hacking",
    "CompAWS": "AWS",
    "CompAzure": "Microsoft Azure",
    "CompGCP": "Google Cloud Platform",
    "CompAnglaisAffaires": "Anglais des affaires",
    "CompProbabilites": "Probabilités",
    "CompOptimisation": "Optimisation mathématique",
    "CompVisionOrdinateur": "Vision par ordinateur",
    "CompLLM": "Modèles de langage (LLM)",
    "CompMLOps": "MLOps",
}

# --- Nouveaux formateurs ---
NEW_FORMATEURS = {
    "Formateur_Idrissi": "Sara Idrissi",
    "Formateur_Bennis": "Karim Bennis",
    "Formateur_Chraibi": "Nadia Chraibi",
}

# --- Nouveaux parcours ---
NEW_PARCOURS = {
    "Parcours_IA": "Parcours Intelligence Artificielle",
    "Parcours_CloudDevOps": "Parcours Cloud & DevOps",
    "Parcours_Cybersecurite": "Parcours Cybersécurité",
}

FORMATEURS_POOL = [
    "Formateur_Benali", "Formateur_ElAmrani",
    "Formateur_Idrissi", "Formateur_Bennis", "Formateur_Chraibi", None, None,
]

# Chaque entrée : (slug, titre, domaine, niveau, description, duree, competences_enseignees,
#                   prerequis_doc_id_ou_None, competence_requise_ou_None, parcours_ou_None)
NEW_COURSES = [
    # --- Informatique / Python ---
    ("PythonIntermediaire", "Python intermédiaire : structures de données et POO", "Informatique", "Intermediaire",
     "Approfondissez Python avec les listes, dictionnaires, la programmation orientée objet et les bonnes pratiques.",
     14, [], "Cours_PythonBases", None, None),
    ("AutomatisationPython", "Automatisation de tâches avec Python", "Informatique", "Intermediaire",
     "Automatisez des tâches répétitives (fichiers, emails, web scraping) grâce à des scripts Python.",
     10, [], "Cours_PythonBases", None, None),
    ("Algorithmique", "Algorithmique et structures de données", "Informatique", "Intermediaire",
     "Complexité algorithmique, tris, arbres, graphes : les fondamentaux pour concevoir des programmes efficaces.",
     16, [], "Cours_PythonBases", None, None),
    ("LinuxBases", "Introduction à Linux et à la ligne de commande", "Informatique", "Debutant",
     "Manipuler un système Linux, naviguer en ligne de commande, gérer fichiers et permissions.",
     8, ["CompLinux"], None, None, None),
    ("PythonScriptingAvance", "Python pour l'automatisation et le scripting avancé", "Informatique", "Avance",
     "Scripts robustes, gestion d'erreurs, packaging et publication de modules Python réutilisables.",
     16, [], "PythonIntermediaire", None, None),

    # --- Data Science ---
    ("DataScienceDeAZ", "Data Science avec Python : de A à Z", "DataScience", "Debutant",
     "Panorama complet du métier de data scientist : collecte, nettoyage, analyse et restitution des données.",
     18, [], None, None, "Parcours_DataScientist"),
    ("DataWrangling", "Nettoyage et préparation de données (Data Wrangling)", "DataScience", "Intermediaire",
     "Techniques de nettoyage, transformation et fiabilisation des jeux de données réels, souvent imparfaits.",
     12, [], "Cours_PythonBases", None, "Parcours_DataScientist"),
    ("PandasNumpy", "Pandas et NumPy pour l'analyse de données", "DataScience", "Intermediaire",
     "Manipulez efficacement des données tabulaires et numériques avec les bibliothèques Python de référence.",
     11, [], "Cours_PythonBases", None, "Parcours_DataScientist"),
    ("DataStorytelling", "Storytelling et communication de données", "DataScience", "Intermediaire",
     "Transformez une analyse de données en récit clair et convaincant pour des décideurs non techniques.",
     8, [], None, None, "Parcours_DataScientist"),
    ("DataEngineeringIntro", "Introduction au Data Engineering", "DataScience", "Intermediaire",
     "Pipelines de données, ETL/ELT et bonnes pratiques pour alimenter des projets de data science à l'échelle.",
     14, [], "Cours_SQLBases", None, "Parcours_DataScientist"),

    # --- Big Data ---
    ("BigDataIntro", "Introduction au Big Data", "BigData", "Debutant",
     "Comprendre les enjeux du Big Data (volume, vélocité, variété) et l'écosystème Hadoop.",
     10, [], None, None, None),
    ("ApacheSpark", "Apache Spark pour le traitement de données massives", "BigData", "Intermediaire",
     "Traitement distribué de données à grande échelle avec Apache Spark (RDD, DataFrames, Spark SQL).",
     16, ["CompSpark"], "BigDataIntro", None, None),
    ("ArchitecturesBigData", "Architectures Big Data modernes (Data Lake, Data Warehouse)", "BigData", "Avance",
     "Concevoir des architectures de données modernes pour l'analytique et le machine learning à grande échelle.",
     18, [], "ApacheSpark", None, None),

    # --- Intelligence Artificielle (domaine parent) ---
    ("PanoramaIA", "Panorama de l'intelligence artificielle", "IntelligenceArtificielle", "Debutant",
     "Une vue d'ensemble accessible de l'IA : apprentissage automatique, réseaux de neurones, applications concrètes.",
     8, [], None, None, "Parcours_IA"),
    ("EthiqueIA", "Éthique et IA responsable", "IntelligenceArtificielle", "Debutant",
     "Biais algorithmiques, transparence, impacts sociétaux : les enjeux éthiques du déploiement de l'IA.",
     6, [], None, None, "Parcours_IA"),
    ("IAGenerative", "IA générative : principes et applications", "IntelligenceArtificielle", "Intermediaire",
     "Modèles génératifs (texte, image) : comment ils fonctionnent et comment les utiliser en pratique.",
     12, [], "Cours_IntroML", None, "Parcours_IA"),

    # --- Machine Learning ---
    ("MLScikitLearn", "Machine Learning avec Scikit-learn", "MachineLearning", "Intermediaire",
     "Implémentez régression, classification et clustering avec la bibliothèque Scikit-learn.",
     16, ["CompScikitLearn"], "Cours_IntroML", None, "Parcours_DataScientist"),
    ("FeatureEngineering", "Feature Engineering et sélection de variables", "MachineLearning", "Intermediaire",
     "Créez et sélectionnez les meilleures variables pour améliorer la performance de vos modèles.",
     10, [], "Cours_IntroML", None, "Parcours_DataScientist"),
    ("MLOpsIntro", "Machine Learning en production (MLOps)", "MachineLearning", "Avance",
     "Déployer, versionner et monitorer des modèles de machine learning en environnement de production.",
     18, ["CompMLOps"], "MLScikitLearn", None, "Parcours_IA"),
    ("EnsembleMethods", "Random Forests et méthodes d'ensemble", "MachineLearning", "Intermediaire",
     "Combinez plusieurs modèles (bagging, boosting) pour améliorer la robustesse de vos prédictions.",
     10, [], "Cours_IntroML", None, "Parcours_DataScientist"),

    # --- Deep Learning ---
    ("CNNVision", "Réseaux de neurones convolutifs (CNN) pour la vision par ordinateur", "DeepLearning", "Intermediaire",
     "Comprendre et implémenter des CNN pour la classification et la détection d'images.",
     16, ["CompVisionOrdinateur"], "Cours_IntroDeepLearning", None, "Parcours_IA"),
    ("RNNSeriesTemp", "Réseaux de neurones récurrents (RNN) et séries temporelles", "DeepLearning", "Intermediaire",
     "Modéliser des séquences et séries temporelles avec des RNN, LSTM et GRU.",
     14, [], "Cours_IntroDeepLearning", None, "Parcours_IA"),
    ("DLTensorFlow", "Deep Learning avec TensorFlow et Keras", "DeepLearning", "Intermediaire",
     "Construisez et entraînez des réseaux de neurones avec TensorFlow/Keras, de bout en bout.",
     18, ["CompTensorFlow"], "Cours_IntroDeepLearning", None, "Parcours_IA"),
    ("TransformersLLM", "Transformers et modèles de langage", "DeepLearning", "Avance",
     "L'architecture Transformer et son rôle central dans les grands modèles de langage modernes.",
     20, ["CompLLM"], "CNNVision", None, "Parcours_IA"),

    # --- NLP ---
    ("NLPSpacyNLTK", "Traitement du langage naturel avec spaCy et NLTK", "NLP", "Intermediaire",
     "Tokenisation, lemmatisation, reconnaissance d'entités : le NLP appliqué avec des bibliothèques Python.",
     12, [], "Cours_NLPIntro", None, "Parcours_IA"),
    ("Chatbots", "Chatbots et agents conversationnels", "NLP", "Intermediaire",
     "Concevoir des agents conversationnels : compréhension d'intention, dialogue, intégration.",
     10, [], "Cours_NLPIntro", None, None),
    ("LLMUsages", "Grands modèles de langage (LLM) : principes et usages", "NLP", "Avance",
     "Fonctionnement, forces et limites des LLM, et comment les intégrer dans une application réelle.",
     14, ["CompLLM"], "Cours_NLPIntro", None, "Parcours_IA"),

    # --- Développement Web ---
    ("CSSModerne", "CSS moderne : Flexbox, Grid et responsive design", "DeveloppementWeb", "Debutant",
     "Maîtrisez la mise en page moderne du web avec Flexbox et CSS Grid, pour des interfaces responsives.",
     8, ["CompCSS"], "Cours_WebBases", None, "Parcours_DevWeb"),
    ("NodeJS", "Node.js et développement backend JavaScript", "DeveloppementWeb", "Intermediaire",
     "Créez des serveurs et APIs avec Node.js, dans la continuité de JavaScript côté client.",
     16, ["CompNodeJS"], "Cours_JSAvance", None, "Parcours_DevWeb"),
    ("VueJS", "Vue.js : construire des interfaces réactives", "DeveloppementWeb", "Intermediaire",
     "Composants, réactivité et gestion d'état avec le framework Vue.js.",
     14, ["CompVueJS"], "Cours_WebBases", None, "Parcours_DevWeb"),
    ("ExpressAPI", "APIs REST avec Express.js", "DeveloppementWeb", "Intermediaire",
     "Concevez des APIs REST robustes et documentées avec Express.js sur Node.js.",
     12, [], "NodeJS", None, "Parcours_DevWeb"),
    ("MERNStack", "Développement full-stack avec le stack MERN", "DeveloppementWeb", "Avance",
     "MongoDB, Express, React et Node.js : construisez une application web complète de bout en bout.",
     24, [], "NodeJS", None, "Parcours_DevWeb"),

    # --- Cloud ---
    ("AWSBases", "AWS pour débutants : les fondamentaux", "Cloud", "Debutant",
     "Les services essentiels d'Amazon Web Services : EC2, S3, IAM, et les bases de l'architecture cloud.",
     12, ["CompAWS"], "Cours_CloudBases", None, "Parcours_CloudDevOps"),
    ("AzureAdmin", "Microsoft Azure : administration et services", "Cloud", "Intermediaire",
     "Administrer des ressources Azure et déployer des applications dans le cloud Microsoft.",
     14, ["CompAzure"], "Cours_CloudBases", None, "Parcours_CloudDevOps"),
    ("GCPEssentials", "Google Cloud Platform (GCP) essentials", "Cloud", "Debutant",
     "Panorama des services Google Cloud Platform pour le calcul, le stockage et les données.",
     10, ["CompGCP"], "Cours_CloudBases", None, "Parcours_CloudDevOps"),
    ("CloudNativeServerless", "Architectures cloud natives et serverless", "Cloud", "Avance",
     "Concevoir des applications scalables avec des architectures serverless et cloud natives.",
     16, [], "AWSBases", None, "Parcours_CloudDevOps"),

    # --- DevOps ---
    ("CICD", "Intégration continue et déploiement continu (CI/CD)", "DevOps", "Intermediaire",
     "Mettre en place des pipelines CI/CD pour automatiser tests, build et déploiement.",
     12, ["CompCICD"], "Cours_DevOpsIntro", None, "Parcours_CloudDevOps"),
    ("Terraform", "Infrastructure as Code avec Terraform", "DevOps", "Avance",
     "Déclarez et gérez votre infrastructure cloud comme du code avec Terraform.",
     14, ["CompTerraform"], "Cours_DockerKubernetes", None, "Parcours_CloudDevOps"),
    ("Monitoring", "Monitoring et observabilité des systèmes", "DevOps", "Avance",
     "Surveillez vos systèmes en production avec Prometheus et Grafana : métriques, alertes, tableaux de bord.",
     12, ["CompMonitoring"], "Cours_DockerKubernetes", None, "Parcours_CloudDevOps"),

    # --- Bases de données ---
    ("MongoDB", "Bases de données NoSQL avec MongoDB", "BasesDeDonnees", "Intermediaire",
     "Modélisation orientée documents, requêtes et agrégations avec MongoDB.",
     10, ["CompNoSQL"], "Cours_SQLBases", None, None),
    ("ModelisationBD", "Modélisation de bases de données relationnelles", "BasesDeDonnees", "Intermediaire",
     "Concevoir un schéma relationnel normalisé, robuste et performant.",
     10, [], "Cours_SQLBases", None, None),
    ("PostgresAvance", "Administration et optimisation PostgreSQL", "BasesDeDonnees", "Avance",
     "Index, requêtes complexes, tuning et administration avancée de PostgreSQL.",
     14, ["CompPostgres"], "Cours_SQLBases", None, None),

    # --- Cybersécurité ---
    ("SecuriteReseaux", "Sécurité des réseaux et pare-feu", "CyberSecurite", "Intermediaire",
     "Protéger une infrastructure réseau : pare-feu, VPN, segmentation et détection d'intrusion.",
     12, [], "Cours_CyberSecuriteBases", None, "Parcours_Cybersecurite",),
    ("Cryptographie", "Cryptographie appliquée", "CyberSecurite", "Intermediaire",
     "Chiffrement symétrique/asymétrique, signatures et protocoles cryptographiques utilisés en pratique.",
     10, ["CompCryptographie"], "Cours_CyberSecuriteBases", None, "Parcours_Cybersecurite"),
    ("EthicalHacking", "Ethical Hacking et tests d'intrusion", "CyberSecurite", "Avance",
     "Méthodologie de pentest : reconnaissance, exploitation et rapport, dans un cadre légal et éthique.",
     18, ["CompEthicalHacking"], "SecuriteReseaux", None, "Parcours_Cybersecurite"),

    # --- Langues ---
    ("AnglaisAffaires", "Anglais des affaires pour l'IT", "Langues", "Intermediaire",
     "Communiquer à l'écrit et à l'oral en anglais professionnel dans un contexte tech.",
     10, ["CompAnglaisAffaires"], "Cours_AnglaisTech", None, None),
    ("PrepaTOEIC", "Préparation au TOEIC", "Langues", "Debutant",
     "Méthodologie et entraînement intensif pour réussir le test TOEIC.",
     12, [], None, None, None),

    # --- Mathématiques ---
    ("CalculDiffIntegral", "Calcul différentiel et intégral pour la data science", "Mathematiques", "Intermediaire",
     "Dérivées, intégrales et leur usage concret en machine learning et optimisation.",
     12, [], "Cours_StatsBase", None, "Parcours_DataScientist"),
    ("Probabilites", "Probabilités appliquées", "Mathematiques", "Intermediaire",
     "Variables aléatoires, lois de probabilité et raisonnement probabiliste pour la data science.",
     10, ["CompProbabilites"], "Cours_StatsBase", None, "Parcours_DataScientist"),
    ("OptimisationML", "Optimisation mathématique pour le machine learning", "Mathematiques", "Avance",
     "Descente de gradient et méthodes d'optimisation au cœur de l'entraînement des modèles.",
     12, ["CompOptimisation"], "Cours_AlgebreLineaire", None, "Parcours_DataScientist"),
]


def build_courses_json(existing):
    existing_by_id = {c["doc_id"]: c for c in existing}
    new_list = []
    for (slug, titre, domaine, niveau, desc, duree, comps, prereq, req_comp, parcours) in NEW_COURSES:
        doc_id = f"Cours_{slug}"
        if doc_id in existing_by_id:
            continue
        note = round(random.uniform(4.0, 4.9), 1)
        gratuit = (niveau == "Debutant" and random.random() < 0.55)
        new_list.append({
            "doc_id": doc_id,
            "titre": titre,
            "description": desc,
            "domaine": domaine,
            "niveau": niveau,
            "duree_heures": duree,
            "note": note,
            "gratuit": gratuit,
        })
    return existing + new_list


def build_ttl_additions():
    lines = []
    lines.append("\n#################################################################")
    lines.append("#  EXTENSION DU DATASET (généré par backend/generate_dataset.py)")
    lines.append("#  Nouveau domaine, nouvelles compétences/formateurs/parcours,")
    lines.append("#  et nouveaux cours -- mêmes doc_id que dans cours.json.")
    lines.append("#################################################################")
    lines.append(NEW_DOMAIN_TTL.strip())

    lines.append("\n# --- Nouvelles compétences ---")
    for local, label in NEW_COMPETENCES.items():
        lines.append(f':{local} a owl:NamedIndividual, :Competence ; rdfs:label "{label}" .')

    lines.append("\n# --- Nouveaux formateurs ---")
    for local, label in NEW_FORMATEURS.items():
        lines.append(f':{local} a owl:NamedIndividual, :Formateur ; rdfs:label "{label}" .')

    lines.append("\n# --- Nouveaux parcours ---")
    for local, label in NEW_PARCOURS.items():
        lines.append(f':{local} a owl:NamedIndividual, :Parcours ; rdfs:label "{label}" .')

    lines.append("\n# --- Nouveaux cours ---")
    for (slug, titre, domaine, niveau, desc, duree, comps, prereq, req_comp, parcours) in NEW_COURSES:
        doc_id = f"Cours_{slug}"
        titre_escaped = titre.replace('"', "'")
        block = [f":{doc_id} a owl:NamedIndividual, :Cours ;"]
        block.append(f'    :aTitre "{titre_escaped}" ;')
        block.append(f"    :aNiveau :{niveau} ;")
        block.append(f"    :appartientADomaine :{domaine} ;")
        if prereq:
            block.append(f"    :aPrerequis :{prereq} ;")
        if req_comp:
            block.append(f"    :requiertCompetence :{req_comp} ;")
        for comp in comps:
            block.append(f"    :enseigneCompetence :{comp} ;")
        formateur = random.choice(FORMATEURS_POOL)
        if formateur:
            block.append(f"    :enseignePar :{formateur} ;")
        if parcours:
            block.append(f"    :faitPartieDe :{parcours} ;")
        note = round(random.uniform(4.0, 4.9), 1)
        gratuit = (niveau == "Debutant" and random.random() < 0.55)
        block.append(f"    :aDuree {duree} ;")
        block.append(f'    :aNote "{note}"^^xsd:float ;')
        block.append(f"    :estGratuit {str(gratuit).lower()} .")
        lines.append("\n".join(block))
        lines.append("")

    return "\n".join(lines)


def main():
    with open(COURS_JSON_PATH, encoding="utf-8") as f:
        existing_courses = json.load(f)

    already_extended = any(c["doc_id"] == "Cours_PythonIntermediaire" for c in existing_courses)
    if already_extended:
        print("Le dataset semble déjà étendu (Cours_PythonIntermediaire présent) : rien à faire.")
        return

    all_courses = build_courses_json(existing_courses)
    with open(COURS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    print(f"cours.json : {len(existing_courses)} -> {len(all_courses)} cours.")

    with open(TTL_PATH, encoding="utf-8") as f:
        ttl_content = f.read()
    ttl_content += "\n" + build_ttl_additions()
    with open(TTL_PATH, "w", encoding="utf-8") as f:
        f.write(ttl_content)
    print(f"Ontologie mise à jour : {TTL_PATH}")

    # Régénère le RDF/XML à partir du Turtle fusionné, pour rester synchronisé
    try:
        from rdflib import Graph
        g = Graph()
        g.parse(TTL_PATH, format="turtle")
        g.serialize(destination=RDF_PATH, format="xml")
        print(f"Export RDF/XML régénéré : {RDF_PATH} ({len(g)} triplets)")
    except ImportError:
        print("rdflib non installé : ontology/elearning.rdf n'a pas été régénéré "
              "(pip install rdflib puis relancer ce script, ou régénérer depuis Protégé).")


if __name__ == "__main__":
    main()
