import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load lightweight model for embedding individual words/synonyms fast on CPU
embedder = SentenceTransformer("all-MiniLM-L6-v2")

STOP_WORDS = {"and", "or", "the", "in", "on", "at", "to", "for", "of", "vs", "a", "an"}


def load_database(json_path="mock_database.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_keywords(text):
    """Tokenizes text into clean individual words, stripping punctuation and stop words."""
    words = text.lower().replace("-", " ").split()
    clean_words = [
        w.strip(".,!?\"'():;") for w in words if w not in STOP_WORDS and len(w) > 1
    ]
    return list(set(clean_words))  # Unique words


def calculate_word_level_relevance(query_words, doc_words):
    """Calculates word-level semantic relevance using Max-Pooling over word embeddings.

    For each query word, finds its highest semantic synonym/match in the document.
    """
    if not query_words or not doc_words:
        return 0.0

    # Encode individual query words and document words as separate vectors
    q_embs = embedder.encode(
        query_words, convert_to_tensor=True, show_progress_bar=False
    )
    doc_embs = embedder.encode(
        doc_words, convert_to_tensor=True, show_progress_bar=False
    )

    # Compute pairwise cosine similarity matrix [len(query_words) x len(doc_words)]
    sim_matrix = util.cos_sim(q_embs, doc_embs)

    # Max-pooling: For each query word, take the score of its best-matching synonym in the doc
    best_word_matches = sim_matrix.max(dim=1).values.tolist()

    # Average best-match scores across all query words
    avg_score = float(np.mean(best_word_matches))
    return max(0.0, avg_score)


def calculate_stance_redundancy(candidate, selected_feed):
    if not selected_feed:
        return 0.0
    cand_stance = candidate.get("stance", 0)
    distances = [
        1 - (abs(cand_stance - item.get("stance", 0)) / 2)
        for item in selected_feed
    ]
    return sum(distances) / len(selected_feed)


def calculate_topic_redundancy(candidate, selected_feed):
    if not selected_feed:
        return 0.0
    cand_topic = candidate.get("topic", "").lower()
    same_topic_count = sum(
        1
        for item in selected_feed
        if item.get("topic", "").lower() == cand_topic
    )
    return same_topic_count / len(selected_feed)


def submodular_rerank(
    candidates, query_words, lambda_stance=0.5, lambda_topic=0.2, k=5
):
    selected_feed = []
    remaining_candidates = list(candidates)

    # Pre-tokenize candidate texts into word lists
    candidate_word_lists = [
        extract_keywords(art.get("text", "")) for art in remaining_candidates
    ]

    candidate_pool = [
        {"data": article, "doc_words": candidate_word_lists[i]}
        for i, article in enumerate(remaining_candidates)
    ]

    # Submodular Greedy Reranking Loop
    for _ in range(min(k, len(candidate_pool))):
        best_score = -float("inf")
        best_item = None
        best_index = -1

        for idx, item in enumerate(candidate_pool):
            article = item["data"]
            doc_words = item["doc_words"]

            # Calculate Word-Level Semantic Relevance
            relevance = calculate_word_level_relevance(query_words, doc_words)

            # Calculate Redundancies
            stance_redundancy = calculate_stance_redundancy(
                article, selected_feed
            )
            topic_redundancy = calculate_topic_redundancy(
                article, selected_feed
            )

            # Dual-Penalty Marginal Gain Formula
            marginal_gain = (
                relevance
                - (lambda_stance * stance_redundancy)
                - (lambda_topic * topic_redundancy)
            )

            if marginal_gain > best_score:
                best_score = marginal_gain
                best_item = item
                best_index = idx

        if best_item is not None:
            selected_feed.append(best_item["data"])
            candidate_pool.pop(best_index)

    return selected_feed



def evaluate_feed(feed, query_words):
    if not feed:
        return {"variance": 0.0, "max_repetition": 0, "avg_relevance": 0.0}

    stances = [art.get("stance", 0) for art in feed]

    # 1. Stance Variance
    stance_variance = float(np.var(stances)) if len(stances) > 0 else 0.0

    # 2. Max Consecutive Repetition
    max_repetition = 0
    current_repetition = 1
    for i in range(1, len(stances)):
        if (
            (stances[i] > 0 and stances[i - 1] > 0)
            or (stances[i] < 0 and stances[i - 1] < 0)
            or (stances[i] == stances[i - 1] == 0)
        ):
            current_repetition += 1
        else:
            if current_repetition > max_repetition:
                max_repetition = current_repetition
            current_repetition = 1
    max_repetition = max(max_repetition, current_repetition)

    # 3. Average Word-Level Semantic Relevance
    relevances = [
        calculate_word_level_relevance(
            query_words, extract_keywords(art.get("text", ""))
        )
        for art in feed
    ]
    avg_relevance = float(np.mean(relevances))

    return {
        "variance": stance_variance,
        "max_repetition": max_repetition,
        "avg_relevance": avg_relevance,
    }


if __name__ == "__main__":
    # Choose dataset: "tweet_eval", "allsides", "youtube", or "debater"
    # **CHANGE THE DATASET IN THE LINE BELOW
    ACTIVE_DATASET = "debater"

    # UPDATED CONFIG: Queries broken down into explicit lists of individual target words
    DATASET_CONFIG = {
        "tweet_eval": {
            "file": "tweet_eval_mock.json",
            "query_words": ["climate", "warming", "abortion", "rights", "feminism",],
        },
        "allsides": {
            "file": "allsides_mock.json",
            "query_words": ["election", "policy", "government", "president", "vote",],
        },
        "youtube": {
            "file": "youtube_mock.json",
            "query_words": ["hate", "love", "worst", "best", "terrible", "amazing", "fail", "win",],
        },
        # --- NEW DEBATER CONFIGURATION ---
        "debater": {
            "file": "debater_mock.json",
            "query_words": ["assisted", "suicide", "health", "moral", "rights", "ethics"],
        },
    }

    current_config = DATASET_CONFIG[ACTIVE_DATASET]
    try:
        database = load_database(current_config["file"])
        query_words = current_config["query_words"]
    except FileNotFoundError:
        print(f"Error: Could not find {current_config['file']}.")
        exit()

    print(
        "================================================================================"
    )
    print(
        f"EVALUATING WORD-LEVEL TRADE-OFF SURFACE ON {ACTIVE_DATASET.upper()}"
        " DATASET"
    )
    print(f"Query words used: {query_words}")
    print(
        "========================================================================\n"
    )

    # Fixed Topic Weight, varying Stance Weight
    FIXED_LAMBDA_TOPIC = 0.3
    lambda_stance_range = [0.0, 0.3, 0.7, 1.0]

    print(f"--- [ FIXED TOPIC DIVERSITY WEIGHT (Lambda Topic): {FIXED_LAMBDA_TOPIC} ] ---\n")

    for l_stance in lambda_stance_range:
        feed = submodular_rerank(
            database,
            query_words,
            lambda_stance=l_stance,
            lambda_topic=FIXED_LAMBDA_TOPIC,
            k=10,
        )
        metrics = evaluate_feed(feed, query_words)

        unique_topics = len(
            set(art.get("topic", "").lower() for art in feed)
        )

        print(
            f"  • Lambda Stance: {l_stance:<4} | Avg Relevance:"
            f" {metrics['avg_relevance']:.4f} | Stance Var:"
            f" {metrics['variance']:.4f} | Max Repetition:"
            f" {metrics['max_repetition']} | Unique Topics: {unique_topics}/10"
        )