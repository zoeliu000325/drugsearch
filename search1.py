import pandas as pd
import streamlit as st
from pathlib import Path
import re

# 获取当前工作目录，而不是使用 __file__
current_dir = Path.cwd()

# 定义相对路径的 Excel 文件路径列表
file_paths = [
    current_dir / "BC3.xlsx",
    current_dir / "HN.xlsx",
    current_dir / "KAISER.xlsx",
    current_dir / "BS1.xlsx"
]

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

# Function to load data from Excel files into a single DataFrame
def load_data(file_paths):
    data = []
    for file_path in file_paths:
        excel_data = pd.ExcelFile(file_path)
        
        # 根据文件名设置 Carrier 值
        if "BC3.xlsx" in file_path.name:
            carrier_name = "BC"
        elif "HN.xlsx" in file_path.name:
            carrier_name = "HN"
        elif "KAISER.xlsx" in file_path.name:
            carrier_name = "KAISER"
        elif "BS1.xlsx" in file_path.name:
            carrier_name = "BS"
        else:
            carrier_name = "Unknown"
        
        # 遍历文件中的每个工作表
        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)
            
            # 确保工作表至少有 A、B、C 三列
            if df.shape[1] >= 3:
                df = df.iloc[:, :3]  # Limit to first 3 columns
                df.columns = ['Drug Name', 'Tier', 'Requirement or Limits']
                df['Carrier'] = carrier_name
                df['Sheet Name'] = sheet_name
                data.append(df)
                
    # 合并所有文件的数据
    combined_df = pd.concat(data, ignore_index=True)
    combined_df.fillna('', inplace=True)  # 填充 NaN 值为空字符串
    return combined_df

# Define the upgraded fuzzy search function
def fuzzy_search_in_dataframe(search_term, df):
    # 预处理搜索关键词，去除空格和连接符号，并生成模糊匹配模式
    processed_search_term = re.sub(r'[\s-]', '', search_term.lower())
    search_pattern = ".*?".join(re.escape(char) for char in processed_search_term)  # 添加非贪婪匹配模式

    # 对 Drug Name 列中的内容进行模糊搜索
    matches = df[df['Drug Name'].str.replace(r'[\s-]', '', regex=True)
                 .str.contains(search_pattern, case=False, na=False, regex=True)]
    return matches

# Streamlit app
st.title("Drug Information Search")

# Display informational content
st.text_area("Drug Tier Information", information_text, height=200)

# Load data from files
data_df = load_data(file_paths)

# Input search term
search_term = st.text_input("Enter drug name:")

# Search button
if st.button("Search"):
    # 执行搜索并显示结果
    if search_term:
        result_df = fuzzy_search_in_dataframe(search_term, data_df)
        if not result_df.empty:
            st.write("Result:")
            st.dataframe(result_df)  # Display results in a table
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a drug name.")
