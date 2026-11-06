from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search, courses, graph, evaluation, meta

app = FastAPI(title="EduSearch - Moteur de Recherche Hybride E-learning")

# Autorise le frontend React (qui tourne sur un autre port) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(meta.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "API OK. Documentation sur /docs"}
