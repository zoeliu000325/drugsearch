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

# Define the upgraded fuzzy search function
def fuzzy_search_in_multiple_files(search_term, file_paths):
    results = []
    
    # 预处理搜索关键词，去除空格和连接符号，并生成模糊匹配模式
    processed_search_term = re.sub(r'[\s-]', '', search_term.lower())
    search_pattern = ".*?".join(re.escape(char) for char in processed_search_term)  # 添加非贪婪匹配模式

    for file_path in file_paths:
        # 加载 Excel 文件
        excel_data = pd.ExcelFile(file_path)
        
        # 根据文件名设置 Carrier 值
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
        
        # 遍历文件中的每个工作表
        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)
            
            # 确保工作表至少有 A、B、C 三列
            if df.shape[1] >= 3:
                # 对 Column A 中的内容去除空格和连接符号，进行模糊搜索
                matches = df[df.iloc[:, 0].astype(str)
                             .str.replace(r'[\s-]', '', regex=True)
                             .str.contains(search_pattern, case=False, na=False, regex=True)]
                
                # 提取匹配行并添加 Carrier 和工作表名
                for _, row in matches.iterrows():
                    results.append({
                        'Carrier': carrier_name,
                        'Drug Name': row.iloc[0] if not pd.isna(row.iloc[0]) else '',
                        'Tier': row.iloc[1] if not pd.isna(row.iloc[1]) else '',
                        'Requirement or Limits': row.iloc[2] if not pd.isna(row.iloc[2]) else ''
                    })
    
    # 将结果转换为 DataFrame
    result_df = pd.DataFrame(results)
    
    # 将 NaN 替换为空字符串
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
    # 执行搜索并显示结果
    if search_term:
        result_df = fuzzy_search_in_multiple_files(search_term, file_paths)
        if not result_df.empty:
            st.write("Result:")
            st.dataframe(result_df)  # Display results in a table
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a drug name.")
