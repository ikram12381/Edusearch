// Données simulées pour Dashboard / My Learning / Profile — non fournies par
// le backend (qui reste centré sur le moteur de recherche hybride). Les
// doc_id référencés existent réellement dans backend/data/cours.json, pour
// que les cartes puissent renvoyer vers de vraies pages Course Details.

export const MOCK_USER = {
  name: "Assia",
  email: "assia@edusearch.ai",
  level: "Intermédiaire",
};

export const DASHBOARD_STATS = {
  enrolledCourses: 12,
  completedCourses: 5,
  learningHours: 37,
  searchQueries: 128,
};

export const CONTINUE_LEARNING = [
  { doc_id: "Cours_IntroDeepLearning", titre: "Introduction au deep learning", domaine: "DeepLearning", niveau: "Debutant", progress: 72 },
  { doc_id: "Cours_IntroML", titre: "Introduction au Machine Learning", domaine: "MachineLearning", niveau: "Debutant", progress: 45 },
  { doc_id: "Cours_SQLBases", titre: "Les bases de SQL", domaine: "BasesDeDonnees", niveau: "Debutant", progress: 90 },
];

export const MY_LEARNING = {
  inProgress: CONTINUE_LEARNING,
  completed: [
    { doc_id: "Cours_PythonBases", titre: "Python pour débutants", domaine: "Informatique", niveau: "Debutant" },
    { doc_id: "Cours_WebBases", titre: "Les bases du développement web", domaine: "DeveloppementWeb", niveau: "Debutant" },
    { doc_id: "Cours_GitBases", titre: "Git et le contrôle de version", domaine: "Informatique", niveau: "Debutant" },
  ],
};

export const PROFILE_SKILLS = [
  { label: "Python", value: 80 },
  { label: "SQL", value: 90 },
  { label: "Machine Learning", value: 70 },
  { label: "Power BI", value: 60 },
];
