import pandas as pd
import streamlit as st
from pathlib import Path

# 获取当前工作目录，而不是使用 __file__
current_dir = Path.cwd()

# 定义相对路径的 Excel 文件路径列表
file_paths = [
    current_dir / "BC3.xlsx",
    current_dir / "HN.xlsx",
    current_dir / "KAISER.xlsx",
    current_dir / "BS.xlsx"
]

# 检查文件是否存在
#for file_path in file_paths:
    #if not file_path.exists():
        #st.error(f"File not found: {file_path}")
    #else:
        #st.write(f"File found: {file_path}")

# Informational content
information_text = """
1 = Preferred Generics  
2 = Preferred Brand/High Cost Generics  
3 = Non-Preferred Brand Drugs  
4 = High Cost Drugs  
5 = Preventive Drugs  
7 = Brand Reference Only, Generic is Available  
PV = Preventive Drugs  
AL = Age Limit  
PA = Prior Authorization  
QL = Quantity Limit  
ST = Step Therapy  
AC = Anti-Cancer  
LA = Limited Access  
SP = Specialty Drug  
RX/OTC = Prescription & Over-the-Counter
"""

# Define the fuzzy search function
def fuzzy_search_in_multiple_files(search_term, file_paths):
    results = []
    
    for file_path in file_paths:
        # Load the Excel file
        excel_data = pd.ExcelFile(file_path)
        
        # Set Carrier value based on file name
        if "BC3.xlsx" in file_path.name:
            carrier_name = "BC"
        elif "HN.xlsx" in file_path.name:
            carrier_name = "HN"
        elif "KAISER.xlsx" in file_path.name:
            carrier_name = "KAISER"
        elif "BS.xlsx" in file_path.name:
            carrier_name = "BS"
        else:
            carrier_name = "Unknown"
        
        # Iterate over each sheet in the file
        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)
            
            # Ensure the sheet has at least A, B, C columns
            if df.shape[1] >= 3:
                # Perform a case-insensitive fuzzy search in Column A
                matches = df[df.iloc[:, 0].astype(str).str.contains(search_term, case=False, na=False)]
                
                # Extract matching rows and add Carrier and Sheet Name
                for _, row in matches.iterrows():
                    results.append({
                        'Carrier': carrier_name,
                        'Drug Name': row.iloc[0] if not pd.isna(row.iloc[0]) else '',
                        'Tier': row.iloc[1] if not pd.isna(row.iloc[1]) else '',
                        'Requirement or Limits': row.iloc[2] if not pd.isna(row.iloc[2]) else ''
                    })
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(results)
    
    # Replace NaN with empty strings
    result_df.fillna('', inplace=True)
    return result_df

# Streamlit app
st.title("Drug Information Search")

# Display informational content
st.text_area("Drug Tier Information", information_text, height=200)

# Input search term
search_term = st.text_input("Enter drug name:")

# Search button
if st.button("Search"):
    # Perform search and display results
    if search_term:
        result_df = fuzzy_search_in_multiple_files(search_term, file_paths)
        if not result_df.empty:
            st.write("Result:")
            st.dataframe(result_df)  # Display results in a table
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a drug name.")