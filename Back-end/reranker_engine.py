import json
import numpy as np

def load_database(json_path="mock_database.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_relevance(article, query_keywords):
    #MAIN IDEA: Match the relevance scores with simple keywords
    text = article.get("text", "").lower()
    matches = sum(1 for kw in query_keywords if kw in text)
    return float(matches + 1) #Base relevance of 1.0

def calculate_redundancy(candidate, selected_feed):
    #If the political stance is already heavly represented in
    #the feed, then the article gets penalized
    if not selected_feed:
        return 0.0
    cand_stance = candidate.get("stance", 0)
    same_stance_count = sum(1 for item in selected_feed if item.get("stance", 0) == cand_stance)
    return same_stance_count / len(selected_feed)

# The function below is a greedy submodular optomization loop to slect top-k diversified articles
def submodular_rerank(candidates, query_keywords, lambda_param=0.5, k=5):
    selected_feed = []
    remaining_candidates = list(candidates)

    #The underscore (_) in the for loop means that we need to repeat this loop k times
    #but we don;t actually need to use the loop inside our math
    for _ in range(min(k, len(remaining_candidates))):
        best_score = -float('inf')
        best_article = None
        best_index = -1

        for idx, article in enumerate(remaining_candidates):
            #1. Calculate Relevance
            relevance = calculate_relevance(article, query_keywords)
            #2. Calculate Ideological Redundancy Penalty
            redundancy = calculate_redundancy(article, selected_feed)
            #3. Submodular Objective Function: f(S ∪ {i}) - f(S)
            marginal_gain = relevance - (lambda_param * redundancy)

            if marginal_gain > best_score:
                best_score = marginal_gain
                best_article = article
                best_index = idx

        if best_article is not None:
            selected_feed.append(best_article)
            remaining_candidates.pop(best_index)

    return selected_feed


"""EXAMPLE TEXTING EXECUTION"""
if __name__ == "__main__":
    database = load_database("mock_database.json")

    #Simulate a user searching for a topic keyword
    query = ["election"]

    #Run re-ranking with a 0.6 diversity weight
    diversified_feed =  submodular_rerank(database, query, lambda_param = 0.6, k = 5)

    print(f"Top {len(diversified_feed)} Re-Ranked Articles:")
    for i, art in enumerate(diversified_feed, 1):
        print(f"{i}. [Stance: {art['stance']}] Topic: {art['topic']} - ID: {art['id']}")