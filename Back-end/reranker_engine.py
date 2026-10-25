import json
import numpy as np

def load_database(json_path="mock_database.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_relevance(article, query_keywords):
    text = article.get("text", "").lower()
    # Using fast keyword matching to avoid GPU/memory bottlenecks and ensure instant execution
    matches = sum(1 for kw in query_keywords if kw.lower() in text)
    return float(matches + 1.0) 

def calculate_stance_redundancy(candidate, selected_feed):
    if not selected_feed:
        return 0.0
    cand_stance = candidate.get("stance", 0)
    # Continuous distance penalty: calculates absolute ideological distance on the -1 to 1 scale
    distances = [1 - (abs(cand_stance - item.get("stance", 0)) / 2) for item in selected_feed]
    return sum(distances) / len(selected_feed)

def calculate_topic_redundancy(candidate, selected_feed):
    if not selected_feed:
        return 0.0
    cand_topic = candidate.get("topic", "").lower()
    # Penalizes the candidate if the feed already contains the exact same topic
    same_topic_count = sum(1 for item in selected_feed if item.get("topic", "").lower() == cand_topic)
    return same_topic_count / len(selected_feed)

def submodular_rerank(candidates, query_keywords, lambda_stance=0.5, lambda_topic=0.2, k=5):
    selected_feed = []
    remaining_candidates = list(candidates)

    for _ in range(min(k, len(remaining_candidates))):
        best_score = -float('inf')
        best_article = None
        best_index = -1

        for idx, article in enumerate(remaining_candidates):
            relevance = calculate_relevance(article, query_keywords)
            stance_redundancy = calculate_stance_redundancy(article, selected_feed)
            topic_redundancy = calculate_topic_redundancy(article, selected_feed)
            
            # Dual-Penalty Marginal Gain Formula
            marginal_gain = relevance - (lambda_stance * stance_redundancy) - (lambda_topic * topic_redundancy)

            if marginal_gain > best_score:
                best_score = marginal_gain
                best_article = article
                best_index = idx

        if best_article is not None:
            selected_feed.append(best_article)
            remaining_candidates.pop(best_index)

    return selected_feed

def evaluate_feed(feed, query_keywords):
    stances = [art.get("stance", 0) for art in feed]
    
    # 1. Stance Entropy / Variance
    stance_variance = np.var(stances) if len(stances) > 0 else 0.0
    
    # 2. Marginal Stance Repetition (Max consecutive posts with the same ideological sign)
    max_repetition = 0
    current_repetition = 1
    for i in range(1, len(stances)):
        # Check if consecutive stances share the same polarity (both right, both left, or both center)
        if (stances[i] > 0 and stances[i-1] > 0) or (stances[i] < 0 and stances[i-1] < 0) or (stances[i] == stances[i-1] == 0):
            current_repetition += 1
        else:
            if current_repetition > max_repetition:
                max_repetition = current_repetition
            current_repetition = 1
    max_repetition = max(max_repetition, current_repetition) if len(stances) > 0 else 0

    # 3. Average Relevance
    avg_relevance = np.mean([calculate_relevance(art, query_keywords) for art in feed]) if len(feed) > 0 else 0.0

    return {
        "variance": stance_variance,
        "max_repetition": max_repetition,
        "avg_relevance": avg_relevance
    }

if __name__ == "__main__":
    # 1. Toggle this variable to instantly switch which dataset you are testing
    ACTIVE_DATASET = "youtube"  # Options: "tweet_eval", "allsides", "youtube"
    
    # 2. Master configuration mapping each dataset to its JSON file and relevant keywords
    DATASET_CONFIG = {
        "tweet_eval": {
            "file": "tweet_eval_mock.json",
            "query": ["climate", "warming", "abortion", "rights", "feminism"]
        },
        "allsides": {
            "file": "allsides_mock.json",
            "query": ["election", "policy", "government", "president", "vote"]
        },
        "youtube": {
            "file": "youtube_mock.json", 
            "query": ["hate", "love", "worst", "best", "terrible", "amazing", "fail", "win"]
        }
    }
    
    # 3. Load the specific database and query based on your toggle
    current_config = DATASET_CONFIG[ACTIVE_DATASET]
    try:
        database = load_database(current_config["file"])
        query = current_config["query"]
    except FileNotFoundError:
        print(f"Error: Could not find {current_config['file']}. Did you run the preprocessing script?")
        exit()

    print(f"Evaluating Trade-off Curve on {ACTIVE_DATASET.upper()} Dataset:")
    print(f"Keywords used: {query}\n")
    
    # 4. Loop through increasing diversity weights to calculate the metrics
    for lambda_val in [0.0, 0.2, 0.5, 0.8, 1.0]:
        feed = submodular_rerank(database, query, lambda_stance=lambda_val, lambda_topic=0.3, k=10)
        metrics = evaluate_feed(feed, query)
        
        print(f"Lambda (Diversity Threshold): {lambda_val}")
        print(f" - Average Relevance: {metrics['avg_relevance']:.2f}")
        print(f" - Stance Variance: {metrics['variance']:.2f} (Higher is better)")
        print(f" - Max Consecutive Repetition: {metrics['max_repetition']} (Lower is better)\n")