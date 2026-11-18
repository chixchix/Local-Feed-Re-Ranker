import os
import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load lightweight model once
embedder = SentenceTransformer("all-MiniLM-L6-v2")

STOP_WORDS = {"and", "or", "the", "in", "on", "at", "to", "for", "of", "vs", "a", "an"}


def load_database(json_path="mock_database.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_keywords(text):
    """Tokenizes text into clean individual words, stripping punctuation and stop words."""
    words = str(text).lower().replace("-", " ").split()
    clean_words = [
        w.strip(".,!?\"'():;") for w in words if w not in STOP_WORDS and len(w) > 1
    ]
    return list(set(clean_words))


def get_or_create_vocab_cache(candidates, query_words, cache_path="vocab_cache.pt"):
    """Batch-encodes unique words ONCE and caches them to disk for instant lookups."""
    vocab = set(query_words)
    for art in candidates:
        vocab.update(extract_keywords(art.get("text", "")))
    vocab_list = sorted(list(vocab))

    if os.path.exists(cache_path):
        cached = torch.load(cache_path, weights_only=False)
        if set(vocab_list).issubset(set(cached.keys())):
            return cached
        # Only encode missing words if new query words were added
        missing = [w for w in vocab_list if w not in cached]
        if missing:
            new_embs = embedder.encode(missing, batch_size=64, convert_to_tensor=True, show_progress_bar=False)
            for i, w in enumerate(missing):
                cached[w] = new_embs[i]
            torch.save(cached, cache_path)
        return cached

    print(f"Encoding {len(vocab_list)} unique words once (saving to {cache_path})...")
    embs = embedder.encode(vocab_list, batch_size=64, convert_to_tensor=True, show_progress_bar=True)
    vocab_cache = {w: embs[i] for i, w in enumerate(vocab_list)}
    torch.save(vocab_cache, cache_path)
    return vocab_cache


def calculate_word_level_relevance(query_words, doc_words, vocab_cache=None):
    """Calculates word-level semantic relevance using cached tensors if available."""
    if not query_words or not doc_words:
        return 0.0

    if vocab_cache is not None:
        q_valid = [vocab_cache[w] for w in query_words if w in vocab_cache]
        d_valid = [vocab_cache[w] for w in doc_words if w in vocab_cache]
        if not q_valid or not d_valid:
            return 0.0
        q_embs = torch.stack(q_valid)
        doc_embs = torch.stack(d_valid)
    else:
        q_embs = embedder.encode(query_words, convert_to_tensor=True, show_progress_bar=False)
        doc_embs = embedder.encode(doc_words, convert_to_tensor=True, show_progress_bar=False)

    sim_matrix = util.cos_sim(q_embs, doc_embs)
    best_word_matches = sim_matrix.max(dim=1).values
    return max(0.0, float(best_word_matches.mean().item()))


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
    cand_topic = str(candidate.get("topic", "")).lower()
    same_topic_count = sum(
        1
        for item in selected_feed
        if str(item.get("topic", "")).lower() == cand_topic
    )
    return same_topic_count / len(selected_feed)


def submodular_rerank(
    candidates, query_words, lambda_stance=0.5, lambda_topic=0.2, k=5, vocab_cache=None
):
    selected_feed = []
    remaining_candidates = list(candidates)

    if vocab_cache is None:
        vocab_cache = get_or_create_vocab_cache(remaining_candidates, query_words)

    # PRE-COMPUTE relevance once per candidate OUTSIDE the greedy k-loop!
    candidate_pool = []
    for article in remaining_candidates:
        doc_words = extract_keywords(article.get("text", ""))
        rel = calculate_word_level_relevance(query_words, doc_words, vocab_cache)
        article_copy = dict(article)
        article_copy["_cached_relevance"] = rel
        candidate_pool.append({"data": article_copy, "relevance": rel})

    # Submodular Greedy Reranking Loop (Zero transformer calls inside the loop!)
    for _ in range(min(k, len(candidate_pool))):
        best_score = -float("inf")
        best_item = None
        best_index = -1

        for idx, item in enumerate(candidate_pool):
            article = item["data"]
            relevance = item["relevance"]

            stance_redundancy = calculate_stance_redundancy(article, selected_feed)
            topic_redundancy = calculate_topic_redundancy(article, selected_feed)

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


def evaluate_feed(feed, query_words, vocab_cache=None):
    if not feed:
        return {"variance": 0.0, "max_repetition": 0, "avg_relevance": 0.0}

    stances = [art.get("stance", 0) for art in feed]
    stance_variance = float(np.var(stances)) if len(stances) > 0 else 0.0

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

    relevances = [
        art.get(
            "_cached_relevance",
            calculate_word_level_relevance(
                query_words, extract_keywords(art.get("text", "")), vocab_cache
            ),
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
    ACTIVE_DATASET = "allsides"  # "tweet_eval", "allsides", "youtube", or "debater"

    DATASET_CONFIG = {
        "tweet_eval": {
            "file": "tweet_eval_mock.json",
            "query_words": ["climate", "warming", "abortion", "rights", "feminism"],
        },
        "allsides": {
            "file": "allsides_mock.json",
            "query_words": ["election", "policy", "government", "president", "vote"],
        },
        "youtube": {
            "file": "youtube_mock.json",
            "query_words": ["hate", "love", "worst", "best", "terrible", "amazing", "fail", "win"],
        },
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

    # Load or create the embedding cache for this dataset ONCE before the loop
    cache_file = f"{ACTIVE_DATASET}_vocab_cache.pt"
    vocab_cache = get_or_create_vocab_cache(database, query_words, cache_path=cache_file)

    print("=" * 80)
    print(f"EVALUATING WORD-LEVEL TRADE-OFF SURFACE ON {ACTIVE_DATASET.upper()} DATASET")
    print(f"Query words used: {query_words}")
    print("=" * 80 + "\n")

    FIXED_LAMBDA_TOPIC = 0.3
    lambda_stance_range = [0.0,0.2, 0.3,0.4,0.5,0.6, 0.7,0.8,0.9, 1.0]

    print(f"--- [ FIXED TOPIC DIVERSITY WEIGHT (Lambda Topic): {FIXED_LAMBDA_TOPIC} ] ---\n")

    for l_stance in lambda_stance_range:
        feed = submodular_rerank(
            database,
            query_words,
            lambda_stance=l_stance,
            lambda_topic=FIXED_LAMBDA_TOPIC,
            k=10,
            vocab_cache=vocab_cache,
        )
        metrics = evaluate_feed(feed, query_words, vocab_cache=vocab_cache)
        unique_topics = len(set(str(art.get("topic", "")).lower() for art in feed))

        print(
            f"  • Lambda Stance: {l_stance:<4} | Avg Relevance:"
            f" {metrics['avg_relevance']:.4f} | Stance Var:"
            f" {metrics['variance']:.4f} | Max Repetition:"
            f" {metrics['max_repetition']} | Unique Topics: {unique_topics}/10"
        )