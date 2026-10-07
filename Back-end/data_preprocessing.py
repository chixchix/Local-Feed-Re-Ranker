import pandas as pd

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
        'Left': -1,
        'Lean Left': -1,
        'Center': 0,
        'Lean Right': 1,
        'Right': 1
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

# Example usage:
# preprocess_allsides("bias_clean.csv", "mock_database.json")