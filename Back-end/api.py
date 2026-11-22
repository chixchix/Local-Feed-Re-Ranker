from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from functools import lru_cache

from reranker_double import (
    load_database,
    submodular_rerank,
    get_or_create_vocab_cache,
)

# Creates FastAPI app to allow requests from the front-end
app = FastAPI()

# Allows the frontend to make requests to the backend , the origins are the local servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# Takes the debater_mock dataset file and uses query words to rank posts based on the stance and topic_diversity , // testing
DATA_FILE = BASE_DIR / "debater_mock.json"
QUERY_WORDS = [
    "assisted", "suicide", "health",
    "moral", "rights", "ethics"
]

# Loads the candidate posts from the dataset
## If the file cannot be found after the dataset is loaded, it will return an error
def get_candidates():
    try:
        return load_database(str(DATA_FILE))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dataset not found: {DATA_FILE.name}"
        ) from exc

# Helper function that builds a diverse candidate pool from opposing stances
# Selects 15 posts from each of the opposing stances
def get_diverse_candidates():
    all_posts = get_candidates()

    left_posts = [
        post for post in all_posts
        if float(post["stance"]) == -1.0
    ][:15]

    right_posts = [
        post for post in all_posts
        if float(post["stance"]) == 1.0
    ][:15]

    return left_posts + right_posts


# Load and keep the candidate pool and embeddings in memory
@lru_cache(maxsize=1)
def get_balanced_resources():
    candidates = get_diverse_candidates()

    cache_path = BASE_DIR / "debater_vocab_cache.pt"

    vocab_cache = get_or_create_vocab_cache(
        candidates,
        QUERY_WORDS,
        cache_path=str(cache_path),
    )

    return candidates, vocab_cache

# API ENDPOINT
## Returns the standard feed or balanced feed based on the selected mode
@app.get("/feed")
def get_feed(
    mode: str = "standard",
    weight: float = Query(default=0.5, ge=0.0, le=1.0),
):
    if mode not in ("standard", "balanced"):
        raise HTTPException(
            status_code=400,
            detail="Mode must be standard or balanced"
        )

    # Temporary small candidate pool for initial integration

    if mode == "balanced":
        candidates, vocab_cache = get_balanced_resources()

        posts = submodular_rerank(
            candidates,
            QUERY_WORDS,
            lambda_stance=weight,
            lambda_topic=0.3,
            k=10,
            vocab_cache=vocab_cache,
        )
    else:
        candidates = get_candidates()[:10]
        posts = candidates

    return {"posts": posts}
