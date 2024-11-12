import pandas as pd
import streamlit as st
from pathlib import Path
import re
from typing import List
import pickle
import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import tempfile

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
    current_dir = Path.cwd()
    return [
        current_dir / "BC3.xlsx",
        current_dir / "HN.xlsx",
        current_dir / "KAISER.xlsx",
        current_dir / "BS1.xlsx"
    ]

def get_carrier_name(file_path: Path) -> str:
    carrier_map = {
        "BC3.xlsx": "BC",
        "HN.xlsx": "HN",
        "KAISER.xlsx": "KAISER",
        "BS1.xlsx": "BS"
    }
    return carrier_map.get(file_path.name, "Unknown")

@st.cache_data
def load_data(file_paths: List[Path]) -> pd.DataFrame:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    
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
                    df = df.iloc[:, :3]
                    df.columns = ['Drug Name', 'Tier', 'Requirement or Limits']
                    df['Carrier'] = carrier_name
                    df['Sheet Name'] = sheet_name
                    df['Drug Name_processed'] = df['Drug Name'].str.replace(r'[\s-]', '', regex=True).str.lower()
                    df['Tier'] = df['Tier'].astype(str)  # 确保 Tier 列为字符串类型
                    data.append(df)
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")
            continue
    
    if not data:
        st.error("No data could be loaded from any file")
        return pd.DataFrame()
        
    combined_df = pd.concat(data, ignore_index=True)
    combined_df.fillna('', inplace=True)
    
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
        
    search_terms = re.findall(r'[a-zA-Z]+|\d+', search_term.lower())
    
    if 'Drug Name_processed' not in df.columns:
        df['Drug Name_processed'] = df['Drug Name'].str.lower().str.replace(r'\W+', '', regex=True)
    
    mask = df['Drug Name_processed'].apply(lambda x: all(term in x for term in search_terms))
    matches = df[mask]
    
    return matches[['Carrier', 'Tier', 'Requirement or Limits', 'Drug Name']]

def send_email(to_address, subject, body, attachment_path):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'kcalinsurance2024@gmail.com'  # 你的邮箱地址
    smtp_password = 'ihld ikcc nhow ldot'  # 使用应用专用密码或调整密码配置

    from_address = 'kcalinsurance2024@gmail.com'  # 发件人地址
    
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = 'drug search result'
    msg.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(attachment_path)}",
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_address, to_address, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Main Function
def main():
    st.title("Drug Information Search")
    
    with st.expander("Drug Tier Information", expanded=False):
        st.text(information_text)
    
    file_paths = get_file_paths()
    with st.spinner('Loading data...'):
        data_df = load_data(file_paths)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Enter drug name:", key="drug_search")
    with col2:
        search_button = st.button("Search", use_container_width=True)
    
    if search_button or search_term:
        if len(search_term) < SEARCH_MIN_LENGTH:
            st.warning("Please enter at least 2 characters.")
            return
            
        with st.spinner('Searching...'):
            result_df = fuzzy_search_in_dataframe(search_term, data_df)
            
        if not result_df.empty:
            st.success(f"Found {len(result_df)} results")
            st.session_state["latest_result"] = result_df
            st.dataframe(result_df, use_container_width=True, hide_index=True)
        else:
            st.info("No results found.")

    if "cumulative_results" not in st.session_state:
        st.session_state["cumulative_results"] = pd.DataFrame(columns=["Carrier", "Tier", "Requirement or Limits", "Drug Name"])

    st.write("Manage Results:")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Add"):
            if "latest_result" in st.session_state and not st.session_state["latest_result"].empty:
                blank_rows = pd.DataFrame([["", "", "", ""]] * 3, columns=st.session_state["cumulative_results"].columns)
                st.session_state["cumulative_results"] = pd.concat(
                    [st.session_state["cumulative_results"], st.session_state["latest_result"], blank_rows],
                    ignore_index=True
                )
                st.success("Added")
            else:
                st.warning("No search result to add.")
    
    with col_b:
        if st.button("Remove"):
            if not st.session_state["cumulative_results"].empty:
                if "latest_result" in st.session_state and not st.session_state["latest_result"].empty:
                    rows_to_remove = len(st.session_state["latest_result"]) + 3
                    st.session_state["cumulative_results"] = st.session_state["cumulative_results"].iloc[:-rows_to_remove]
                    st.info("Removed last added search result, including blank rows.")
                else:
                    st.warning("No search result to remove.")
            else:
                st.warning("No results to remove.")
    
    email = st.text_input("Enter email:", key="email_input")
    with col_c:
        if st.button("Send"):
            if email and not st.session_state["cumulative_results"].empty:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
                    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                        st.session_state["cumulative_results"].to_excel(writer, index=False, sheet_name="Cumulative Results")
                        workbook = writer.book
                        worksheet = writer.sheets["Cumulative Results"]
                        font_style = Font(name="Times New Roman")
                        for row in worksheet.iter_rows():
                            for cell in row:
                                cell.font = font_style
                        for cell in worksheet["B"]:
                            cell.alignment = Alignment(horizontal="center")
                    
                    temp_file_path = temp_file.name
                    print(temp_file_path)
                subject = "Cumulative Drug Information Results"
                body = "Please find the attached Excel file with cumulative drug information search results."
                
                if send_email(email, subject, body, temp_file_path):
                    st.success(f"Results sent to {email}")
                else:
                    st.error("Failed to send the email.")
                
                os.remove(temp_file_path)
            else:
                st.warning("Please enter an email and ensure there are results to send.")

if __name__ == "__main__":
    main()
