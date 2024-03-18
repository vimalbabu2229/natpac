import pandas as pd 
df= pd.DataFrame()

# Function to convert time to seconds
def time_to_seconds(time_obj):
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
 
# Function to convert seconds to human-readable time format
def seconds_to_time(df, columns):
    df[columns] = df[columns].apply(lambda x: pd.to_datetime(x, unit='s').dt.strftime('%H:%M:%S'))

def preprocess_data(input_file_path, output_file_path):
    try:
        # Read the Excel file and drop duplicates
        df = pd.read_excel(input_file_path)
    except FileNotFoundError:
        return "Error: Input file not found."
    #if df.isnull().values.any():
        #     # Print the first three rows with null values
        #     null_rows = df[df.isnull().any(axis=1)].head(3)
        #     print("Null values found in the following rows:")
        #     print(null_rows)
        #     raise ValueError("Error: Null values found in the dataset.")
    
    if not all(df.columns):
        return "Error: Column names are not provided in the header."
    
    df = df.dropna().drop_duplicates()
    
    # Iterate through each column name and apply renaming logic
    for col in df.columns:
        if 'sl no.' in col.casefold():
            df = df.rename(columns={col: 'Sl No.'})
        elif 'departure place' in col.casefold() and 'place' in col.casefold():
            df = df.rename(columns={col: 'Departure Place'})
        elif 'departure time' in col.casefold() and 'time' in col.casefold():
            df = df.rename(columns={col: 'Departure Time'})
        elif 'arrival' in col.casefold() and 'place' in col.casefold():
            df = df.rename(columns={col: 'Arrival Place'})
        elif 'arrival' in col.casefold() and 'time' in col.casefold():
            df = df.rename(columns={col: 'Arrival Time'})
        elif 'Running' in col.casefold() and 'time' in col.casefold():
            df = df.rename(columns={col: 'Running Time'})
             
    # Convert time columns to datetime and then to seconds
    time_columns = ['Departure Time', 'Arrival Time', 'Running Time']
    for col in time_columns:
        df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
        df[col] = df[col].apply(time_to_seconds)
        
    # Convert other columns to appropriate data types
    for col in df.columns:
        if col not in time_columns:  # Exclude time columns
            df[col] = df[col].convert_dtypes()
     
    # Sort the DataFrame by 'Departure Time' column
    sorted_df = df.sort_values('Departure Time', ascending=True).reset_index(drop=True) 
    
    # Save the preprocessed DataFrame to an Excel file
    sorted_df.to_excel(output_file_path, index=False)
    
    return "Preprocessing completed successfully."

def main():
    input_file_path = 'dataset/psl.xlsx'
    output_file_path = 'dataset/processed/psl.xlsx'
    result = preprocess_data(input_file_path, output_file_path)
    if result is not None:
        print(result)
        
main()