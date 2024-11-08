import pandas as pd
import streamlit as st
from pathlib import Path
import re
from typing import List, Dict
import pickle
import os

# 配置常量
CACHE_FILE = "drug_data_cache.pkl"
SEARCH_MIN_LENGTH = 2

# 信息文本
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

@st.cache_data
def get_file_paths() -> List[Path]:
    """获取Excel文件路径"""
    current_dir = Path.cwd()
    return [
        current_dir / "BC3.xlsx",
        current_dir / "HN.xlsx",
        current_dir / "KAISER.xlsx",
        current_dir / "BS1.xlsx"
    ]

def get_carrier_name(file_path: Path) -> str:
    """根据文件名获取运营商名称"""
    carrier_map = {
        "BC3.xlsx": "BC",
        "HN.xlsx": "HN",
        "KAISER.xlsx": "KAISER",
        "BS1.xlsx": "BS"
    }
    return carrier_map.get(file_path.name, "Unknown")

@st.cache_data
def load_data(file_paths: List[Path]) -> pd.DataFrame:
    """加载并缓存Excel数据"""
    # 尝试从缓存文件加载
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            pass  # 如果加载失败，继续处理Excel文件
    
    data = []
    for file_path in file_paths:
        if not file_path.exists():
            st.error(f"File not found: {file_path}")
            continue
            
        try:
            excel_data = pd.ExcelFile(file_path)
            carrier_name = get_carrier_name(file_path)
            
            for sheet_name in excel_data.sheet_names:
                df = excel_data.parse(sheet_name)
                if df.shape[1] >= 3:
                    # 只保留需要的列并重命名
                    df = df.iloc[:, :3]
                    df.columns = ['Drug Name', 'Tier', 'Requirement or Limits']
                    df['Carrier'] = carrier_name
                    df['Sheet Name'] = sheet_name
                    # 预处理药品名称
                    df['Drug Name_processed'] = df['Drug Name'].str.replace(r'[\s-]', '', regex=True).str.lower()
                    data.append(df)
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")
            continue
    
    if not data:
        st.error("No data could be loaded from any file")
        return pd.DataFrame()
        
    combined_df = pd.concat(data, ignore_index=True)
    combined_df.fillna('', inplace=True)
    
    # 保存到缓存文件
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(combined_df, f)
    except:
        pass
        
    return combined_df

@st.cache_data
def fuzzy_search_in_dataframe(search_term: str, df: pd.DataFrame) -> pd.DataFrame:
    if not search_term or len(search_term) < SEARCH_MIN_LENGTH:
        return pd.DataFrame()
        
    # Preprocess the search term and split into terms
    search_terms = re.findall(r'[a-zA-Z]+|\d+', search_term.lower())
    
    # Preprocess the 'Drug Name' column if not already done
    if 'Drug Name_processed' not in df.columns:
        df['Drug Name_processed'] = df['Drug Name'].str.lower().str.replace(r'\W+', '', regex=True)
    
    # Filter rows that contain all search terms
    mask = df['Drug Name_processed'].apply(lambda x: all(term in x for term in search_terms))
    matches = df[mask]
    
    # Return the required columns
    return matches[['Carrier', 'Drug Name', 'Tier', 'Requirement or Limits', 'Sheet Name']]

def main():
    st.title("Drug Information Search")
    
    # 显示信息文本
    with st.expander("Drug Tier Information", expanded=False):
        st.text(information_text)
    
    # 加载数据
    file_paths = get_file_paths()
    with st.spinner('Loading data...'):
        data_df = load_data(file_paths)
    
    # 搜索界面
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Enter drug name:", key="drug_search")
    with col2:
        search_button = st.button("Search", use_container_width=True)
    
    # 执行搜索
    if search_button or search_term:
        if len(search_term) < SEARCH_MIN_LENGTH:
            st.warning("Please enter at least 2 characters.")
            return
            
        with st.spinner('Searching...'):
            result_df = fuzzy_search_in_dataframe(search_term, data_df)
            
        if not result_df.empty:
            st.success(f"Found {len(result_df)} results")
            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No results found.")

if __name__ == "__main__":
    main()