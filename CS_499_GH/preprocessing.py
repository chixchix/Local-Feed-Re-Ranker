import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer


# 1. PATH CONFIGURATION & LOAD DATA
DATA_DIR = "MINDsmall_train"
OUTPUT_DIR = "processed_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading raw TSV files from MINDsmall_train...")

news_cols = [
    'news_id', 'category', 'subcategory', 'title', 
    'abstract', 'url', 'title_entities', 'abstract_entities'
]
news_df = pd.read_csv(
    os.path.join(DATA_DIR, 'news.tsv'), 
    sep='\t', 
    names=news_cols
)

behavior_cols = ['impression_id', 'user_id', 'time', 'history', 'impressions']
behavior_df = pd.read_csv(
    os.path.join(DATA_DIR, 'behaviors.tsv'), 
    sep='\t', 
    names=behavior_cols
)


# 2. CLEAN & PREPARE ARTICLE TEXT
print("Preprocessing article text...")

# Drop unused columns and handle missing values
news_df = news_df[['news_id', 'category', 'subcategory', 'title', 'abstract']].fillna('')

# Filter out empty or extremely short titles
news_df = news_df[news_df['title'].str.len() > 5].copy()

# Combine Title and Abstract for richer semantic context
news_df['full_text'] = news_df['title'] + ". " + news_df['abstract']

# Save clean metadata mapping
news_df.to_parquet(os.path.join(OUTPUT_DIR, 'clean_news.parquet'), index=False)
print(f"Cleaned News Pool: {len(news_df)} articles.")


# 3. GENERATE DENSE EMBEDDINGS (v_i)
print("Generating 768-dim embeddings via SentenceTransformers...")

# Load pre-trained model
embedder = SentenceTransformer('all-mpnet-base-v2')

# Encode all full_text strings into vector array
text_list = news_df['full_text'].tolist()
raw_embeddings = embedder.encode(
    text_list, 
    show_progress_bar=True, 
    batch_size=64, 
    convert_to_numpy=True
)

# L2 Normalize vectors so dot product equals cosine similarity
norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
norms[norms == 0] = 1.0  # Prevent division by zero
normalized_embeddings = raw_embeddings / norms

# Save embedding matrix
np.save(os.path.join(OUTPUT_DIR, 'news_embeddings.npy'), normalized_embeddings)

# Build quick lookup mapping from news_id to array index
news_id_to_idx = {nid: idx for idx, nid in enumerate(news_df['news_id'])}

# ---------------------------------------------------------
# 4. CONSTRUCT USER PROFILES (u) & IMPRESSION POOLS
# ---------------------------------------------------------
print("Building user vector profiles from history logs...")

# Filter behavior rows with history
valid_behaviors = behavior_df.dropna(subset=['history', 'impressions']).copy()

processed_sessions = []

for idx, row in valid_behaviors.iterrows():
    # Get user history IDs
    history_ids = row['history'].split()
    valid_hist_indices = [news_id_to_idx[nid] for nid in history_ids if nid in news_id_to_idx]
    
    if not valid_hist_indices:
        continue
    
    # Compute user profile vector (u) as normalized average of clicked items
    user_vec = np.mean(normalized_embeddings[valid_hist_indices], axis=0)
    user_norm = np.linalg.norm(user_vec)
    if user_norm > 0:
        user_vec = user_vec / user_norm
        
    # Process candidate impressions
    impression_items = row['impressions'].split()
    candidate_indices = []
    
    for item in impression_items:
        nid, label = item.split('-')
        if nid in news_id_to_idx:
            candidate_indices.append(news_id_to_idx[nid])
            
    if candidate_indices:
        processed_sessions.append({
            'impression_id': row['impression_id'],
            'user_id': row['user_id'],
            'user_vector': user_vec,
            'candidate_indices': candidate_indices
        })

# Save processed user sessions as pickle/parquet
sessions_df = pd.DataFrame(processed_sessions)
sessions_df.to_pickle(os.path.join(OUTPUT_DIR, 'user_sessions.pkl'))

print(f"Preprocessing Complete! Saved {len(sessions_df)} ready-to-use user sessions.")