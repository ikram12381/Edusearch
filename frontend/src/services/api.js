// Service centralisé pour tous les appels au backend FastAPI existant.
// Le reste du frontend ne connaît jamais les URLs/endpoints directement —
// il importe des fonctions d'ici. Un seul endroit à changer si l'API évolue.

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    // Le backend, Elasticsearch ou Fuseki ne répond pas du tout.
    throw new ApiError(
      "Service de recherche temporairement indisponible. Vérifie que le backend, Elasticsearch et Fuseki sont bien lancés.",
      0
    );
  }
  if (!res.ok) {
    throw new ApiError(`Erreur serveur (HTTP ${res.status}).`, res.status);
  }
  return res.json();
}

// --- Recherche hybride / lexicale / vectorielle ---

const SEARCH_ENDPOINTS = {
  hybrid: "/search",
  lexical: "/search/lexical-only",
  semantic: "/search/vector-only",
};

export function searchCourses(query, { mode = "hybrid", top_k = 10, signal } = {}) {
  const path = SEARCH_ENDPOINTS[mode] || SEARCH_ENDPOINTS.hybrid;
  return request(path, {
    method: "POST",
    body: JSON.stringify({ query, top_k }),
    signal,
  });
}

// Lance les trois stratégies en parallèle pour la page "Compare Search"
export async function compareSearch(query, top_k = 5) {
  const [hybrid, lexical, semantic] = await Promise.all([
    searchCourses(query, { mode: "hybrid", top_k }),
    searchCourses(query, { mode: "lexical", top_k }),
    searchCourses(query, { mode: "semantic", top_k }),
  ]);
  return { hybrid, lexical, semantic };
}

// --- Catalogue de cours ---

export function listCourses(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, value);
  });
  const qs = params.toString();
  return request(`/courses${qs ? `?${qs}` : ""}`);
}

export function getCourse(docId) {
  return request(`/courses/${encodeURIComponent(docId)}`);
}

// --- Knowledge Graph ---

export function getCourseGraph(docId) {
  return request(`/course/${encodeURIComponent(docId)}/graph`);
}

export function getDomainGraph() {
  return request("/graph/domains");
}

export function getDomainDetail(domainId) {
  return request(`/graph/domains/${encodeURIComponent(domainId)}`);
}

export function getDomainInference(domainId) {
  return request(`/graph/inference/${encodeURIComponent(domainId)}`);
}

export function getSemanticPath(source, target) {
  return request(`/graph/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`);
}

// --- Évaluation ---

export function getEvaluation(k = 5) {
  return request(`/evaluation?k=${k}`);
}

// --- Configuration (poids de fusion réellement utilisés côté serveur) ---

export function getConfig() {
  return request("/config");
}

export { ApiError };
