from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from reranker_engine import load_database, submodular_rerank

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

# If the file cannot be found after the dataset is loaded, it will return an error
def get_candidates():
    try:
        return load_database(str(DATA_FILE))
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Dataset not found: {DATA_FILE.name}"
        )

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
    ## Uses the first 30 posts , to be changed
    candidates = get_candidates()[:30]

    if mode == "balanced":
        posts = submodular_rerank(
            candidates,
            QUERY_WORDS,
            lambda_stance=weight,
            lambda_topic=0.3,
            k=10,
        )
    else:
        posts = candidates[:10] ## Standard mode uses first 10 posts without reranking. To be changed as well

    return {"posts": posts}
