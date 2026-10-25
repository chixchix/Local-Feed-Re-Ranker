import pandas as pd
from datasets import load_dataset


def preprocess_allsides(input_csv_path, output_json_path):
    # 1. Load the Dataset
    # Read the "bias_clean.csv" file into a Pandas DataFrame
    df = pd.read_csv(input_csv_path)
    
    # 2. Rename Columns to Match the Schema
    # Map the actual columns from bias_clean.csv to the required unified schema
    df = df.rename(columns={
        'url': 'id',             # Using URL as the unique ID
        'page_text': 'text',     # Using the body of the article as the text
        'bias': 'raw_stance'     # Renaming bias to stance for the mapping step
    })
    
    # Note: 'topic' is already named correctly in bias_clean.csv, so it doesn't need renaming
    
    # 3. Extract Relevant Columns
    cols_to_keep = ['id', 'text', 'topic', 'raw_stance']
    df = df[cols_to_keep]
    
    # Standardize the Stance Variable to numerical values for the Submodular Optimization loop
    # Maps text labels to: -1 (Left), 0 (Neutral/Center), +1 (Right)
    stance_mapping = {
        'left': -1,
        'leaning-left': -0.5,
        'center': 0,
        'leaning-right': 0.5,
        'right': 1
    }
    df['stance'] = df['raw_stance'].map(stance_mapping)
    
    # Drop the original text-based stance column to keep the schema clean
    df = df.drop(columns=['raw_stance'])
    
    # Clean up: Drop any rows with missing essential data
    df = df.dropna(subset=['text', 'topic', 'stance'])
    
    # 4. Export to JSON
    # Export the cleaned DataFrame to act as the backend mock database
    df.to_json(output_json_path, orient="records", indent=2)
    
    print(f"Data successfully preprocessed and exported to {output_json_path}!")



def preprocess_tweet_eval(output_json_path):
    # 1. Define the list of Hugging Face subsets you want to combine
    topics = ["climate", "abortion", "atheism", "feminist", "hillary"]
    all_dataframes = []

    # Hugging Face labels: 0 (Neutral), 1 (Against / -1), 2 (Favor / +1)
    stance_mapping = {0: 0, 1: -1, 2: 1}

    # 2. Loop through each topic, download it, and format it
    for topic in topics:
        print(f"Downloading stance_{topic}...")
        dataset = load_dataset("cardiffnlp/tweet_eval", f"stance_{topic}")

        df = pd.DataFrame(dataset['train'])
        df = df.rename(columns={'text': 'text', 'label': 'raw_stance'})
        df['stance'] = df['raw_stance'].map(stance_mapping)

        # Automatically tag the post with the current topic in the loop
        df['topic'] = topic 

        # Generate unique IDs that include the topic name
        df['id'] = [f"tweet_{topic}_{i}" for i in range(len(df))]

        # 3. Add the cleaned dataframe to our list
        cols_to_keep = ['id', 'text', 'topic', 'stance']
        all_dataframes.append(df[cols_to_keep])

    # 4. Merge them all together into one master dataset
    final_df = pd.concat(all_dataframes, ignore_index=True)

    # Export the combined, multi-topic dataset
    final_df.to_json("tweet_eval_mock.json", orient="records", indent=2)
    print("Successfully combined all topics into tweet_eval_mock.json!")

def preprocess_youtube_sentiment(output_json_path):
    print("Downloading YouTube Comment Sentiment dataset...")
    # Load the dataset directly from Hugging Face
    dataset = load_dataset("AmaanP314/youtube-comment-sentiment", split="train")
    
    # Convert to Pandas DataFrame
    # Note: We take a sample of 1,000 comments to keep your local Streamlit dashboard fast
    df = pd.DataFrame(dataset).sample(n=1000, random_state=42)
    
    # Map the text sentiment labels to your numerical algorithmic schema
    # Negative = -1, Neutral = 0, Positive = 1
    stance_mapping = {
        'Negative': -1,
        'Neutral': 0,
        'Positive': 1
    }
    
    # Assuming the dataset has a 'Text' and 'Sentiment' column based on standard formatting
    # We rename them to fit your pipeline
    df = df.rename(columns={'CommentText': 'text', 'Sentiment': 'raw_stance'})
    df['stance'] = df['raw_stance'].map(stance_mapping)
    
    # Hardcode a general topic since these are broad YouTube comments
    df['topic'] = "general_video"
    
    # Generate mock IDs
    df['id'] = [f"yt_comment_{i}" for i in range(len(df))]
    
    # Keep only the essential columns
    cols_to_keep = ['id', 'text', 'topic', 'stance']
    df = df.dropna(subset=['text', 'topic', 'stance'])
    final_df = df[cols_to_keep]
    
    # Export to JSON
    final_df.to_json(output_json_path, orient="records", indent=2)
    print(f"YouTube data successfully exported to {output_json_path}!")


 # Execution Block
if __name__ == "__main__":
    # Example usage:
    #preprocess_allsides("bias_clean.csv", "mock_database.json")
    # 1. Run TweetEval
    #preprocess_tweet_eval("tweet_eval_mock.json")
    
    # 2. Run Cinelli (Ensure your downloaded OSF CSV is in the same folder)
    preprocess_youtube_sentiment("youtube_mock.json")