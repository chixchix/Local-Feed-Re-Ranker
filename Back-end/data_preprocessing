import pandas as pd

def preprocess_allsides(input_csv_path, output_json_path):
    # 1. Load the Dataset
    # Read the AllSides CSV file into a Pandas DataFrame
    df = pd.read_csv(input_csv_path)
    
    # 2. Rename Columns
    # Ensure the column names match your standardized schema
    # Note: Adjust the original column names (keys) to match your specific downloaded CSV
    df = df.rename(columns={
        'id_column': 'id',
        'raw_text_or_headline': 'text',
        'topic_category': 'topic',
        'bias_label': 'raw_stance'
    })
    
    # 3. Extract Relevant Columns
    # Filter the DataFrame to keep only the required fields
    cols_to_keep = ['id', 'text', 'topic', 'raw_stance']
    
    # Include engagement metrics if they are available in your dataset
    if 'engagement_metric' in df.columns:
        df = df.rename(columns={'engagement_metric': 'engagement'})
        cols_to_keep.append('engagement')
        
    df = df[cols_to_keep]
    
    # Standardize the Stance Variable to numerical values
    # -1 (Left), 0 (Neutral), +1 (Right)
    stance_mapping = {
        'Left': -1,
        'Center': 0,
        'Neutral': 0,
        'Right': 1
    }
    df['stance'] = df['raw_stance'].map(stance_mapping)
    
    # Drop the original text-based stance column to keep the schema clean
    df = df.drop(columns=['raw_stance'])
    
    # (Optional) Drop any rows with missing essential data
    df = df.dropna(subset=['text', 'topic', 'stance'])
    
    # 4. Export to JSON
    # Export the cleaned DataFrame to a single file, such as mock_database.json
    df.to_json(output_json_path, orient="records", indent=2)
    
    print(f"Data successfully preprocessed and exported to {output_json_path}!")

# Example usage:
# preprocess_allsides("allsides_raw_data.csv", "mock_database.json")