import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import msal
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Course Analysis Tool - OneDrive", layout="wide")

st.title("📊 Advanced Course Analysis Tool - OneDrive Edition")

# Microsoft Graph API Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/Files.Read.All"]

# For local development
REDIRECT_URI = "http://localhost:8501"

# Check if credentials are loaded
if not CLIENT_ID or not TENANT_ID or not CLIENT_SECRET:
    st.error("❌ Missing credentials! Please create a `.env` file with CLIENT_ID, TENANT_ID, and CLIENT_SECRET")
    st.stop()

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'selected_folder_id' not in st.session_state:
    st.session_state.selected_folder_id = None
if 'csv_files' not in st.session_state:
    st.session_state.csv_files = []

def get_auth_url():
    """Generate Microsoft login URL"""
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return auth_url

def get_token_from_code(auth_code):
    """Exchange authorization code for access token"""
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    return result

def get_user_info(access_token):
    """Get user information from Microsoft Graph"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def list_onedrive_folders(access_token, folder_id=None):
    """List folders in OneDrive"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    if folder_id:
        url = f'https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children'
    else:
        url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        items = response.json().get('value', [])
        folders = [item for item in items if 'folder' in item]
        return folders
    return []

def list_csv_files(access_token, folder_id=None):
    """List CSV files in a OneDrive folder"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    if folder_id:
        url = f'https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children'
    else:
        url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        items = response.json().get('value', [])
        csv_files = [item for item in items if item['name'].lower().endswith('.csv')]
        return csv_files
    return []

def download_file_content(access_token, file_id):
    """Download file content from OneDrive"""
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.content
    return None

def process_dataframe(df):
    """Process and clean the dataframe"""
    # Skip first row if it's header info
    if 'Student ID' in df.columns and len(df) > 0 and str(df.iloc[0, 0]).startswith('ACTL'):
        df = df.iloc[1:].reset_index(drop=True)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # COLUMN D (index 3): ALWAYS contains Final Mark + Grade
    final_col = df.iloc[:, 3]
    df['Final_Mark'] = final_col.astype(str).str.extract('(\d+)').astype(float)
    df['Grade'] = final_col.astype(str).str.extract('([A-Z]{2,3})')[0]
    
    # Clean Student ID
    df['Student ID'] = df.iloc[:, 0].astype(str).str.strip()
    
    return df

def get_grade_distribution(df):
    """Calculate grade distribution percentages"""
    grade_counts = df['Grade'].value_counts()
    total = len(df[df['Grade'].notna()])
    
    grade_order = ['HD', 'DN', 'CR', 'PS', 'FL']
    distribution = {}
    
    for grade in grade_order:
        count = grade_counts.get(grade, 0)
        percentage = (count / total * 100) if total > 0 else 0
        distribution[grade] = {'count': count, 'percentage': percentage}
    
    return distribution

def get_assessment_columns(df):
    """Get all assessment columns: Column D + Column E onwards"""
    col_d_name = df.columns[3]
    assessment_cols = [col_d_name]
    
    for i in range(4, len(df.columns)):
        col_name = df.columns[i]
        if col_name not in ['Final_Mark', 'Grade', 'Student ID']:
            assessment_cols.append(col_name)
    
    return assessment_cols

# --- SIDEBAR: Authentication ---
st.sidebar.header("🔐 OneDrive Connection")

# Check for authorization code in URL
query_params = st.query_params
if 'code' in query_params and not st.session_state.access_token:
    with st.spinner("Authenticating..."):
        auth_code = query_params['code']
        result = get_token_from_code(auth_code)
        
        if 'access_token' in result:
            st.session_state.access_token = result['access_token']
            st.session_state.user_info = get_user_info(result['access_token'])
            # Clear the code from URL
            st.query_params.clear()
            st.rerun()
        else:
            st.sidebar.error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")

# Show connection status
if st.session_state.access_token:
    if st.session_state.user_info:
        st.sidebar.success(f"✅ Connected as: {st.session_state.user_info.get('userPrincipalName', 'User')}")
    else:
        st.sidebar.success("✅ Connected to OneDrive")
    
    if st.sidebar.button("🔓 Disconnect"):
        st.session_state.access_token = None
        st.session_state.user_info = None
        st.session_state.selected_folder_id = None
        st.session_state.csv_files = []
        st.rerun()
else:
    st.sidebar.info("🔒 Not connected to OneDrive")
    
    if st.sidebar.button("🔐 Connect to OneDrive"):
        auth_url = get_auth_url()
        st.sidebar.markdown(f"[Click here to sign in with Microsoft]({auth_url})")
        st.sidebar.info("After signing in, you'll be redirected back to this app")

st.sidebar.markdown("---")

# --- MAIN APP ---
if not st.session_state.access_token:
    st.info("👈 **Please connect to OneDrive** in the sidebar to access your files")
    st.markdown("""
    ### How to use this tool:
    1. Click **"Connect to OneDrive"** in the sidebar
    2. Sign in with your Microsoft account
    3. Grant permission to read your files
    4. Browse your OneDrive folders
    5. Select 2 CSV files to compare
    6. View comprehensive analysis and visualizations
    
    ### Features:
    - 📊 Statistical analysis
    - 📈 Distribution charts
    - 🔴 Scatter plots for common students
    - 📋 Detailed comparison tables
    - ⬇️ Download results
    """)
    st.stop()

# --- BROWSE ONEDRIVE ---
st.sidebar.subheader("📁 Browse OneDrive")

# List folders
folders = list_onedrive_folders(st.session_state.access_token)
folder_options = {"Root": None}
for folder in folders:
    folder_options[folder['name']] = folder['id']

selected_folder_name = st.sidebar.selectbox(
    "Select folder:",
    options=list(folder_options.keys()),
    key="folder_select"
)

selected_folder_id = folder_options[selected_folder_name]

if selected_folder_id != st.session_state.selected_folder_id:
    st.session_state.selected_folder_id = selected_folder_id
    st.session_state.csv_files = list_csv_files(st.session_state.access_token, selected_folder_id)

# Show CSV files
if len(st.session_state.csv_files) > 0:
    st.sidebar.success(f"📄 Found {len(st.session_state.csv_files)} CSV files")
    
    csv_file_options = {file['name']: file['id'] for file in st.session_state.csv_files}
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Select Files to Compare")
    
    file1_name = st.sidebar.selectbox("File 1:", options=list(csv_file_options.keys()), key="file1_select")
    file2_name = st.sidebar.selectbox("File 2:", options=list(csv_file_options.keys()), key="file2_select", 
                                     index=min(1, len(csv_file_options)-1))
    
    if st.sidebar.button("📊 Load and Analyze Files"):
        with st.spinner("Downloading files from OneDrive..."):
            # Download files
            file1_content = download_file_content(st.session_state.access_token, csv_file_options[file1_name])
            file2_content = download_file_content(st.session_state.access_token, csv_file_options[file2_name])
            
            if file1_content and file2_content:
                st.session_state.file1_df = pd.read_csv(pd.io.common.BytesIO(file1_content))
                st.session_state.file2_df = pd.read_csv(pd.io.common.BytesIO(file2_content))
                st.session_state.file1_name = file1_name
                st.session_state.file2_name = file2_name
                st.session_state.files_loaded = True
                st.success("✅ Files loaded successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to download files")
else:
    st.sidebar.warning(f"⚠️ No CSV files found in '{selected_folder_name}'")
    st.info(f"No CSV files found in the selected folder. Please select a different folder or upload CSV files to your OneDrive.")

# --- ANALYSIS SECTION ---
if 'files_loaded' in st.session_state and st.session_state.files_loaded:
    try:
        df1_orig = process_dataframe(st.session_state.file1_df.copy())
        df2_orig = process_dataframe(st.session_state.file2_df.copy())
        
        file1 = st.session_state.file1_name
        file2 = st.session_state.file2_name
        
        # Get available assessment columns
        assessment_cols_file1 = get_assessment_columns(df1_orig)
        assessment_cols_file2 = get_assessment_columns(df2_orig)
        
        # Column selection
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Select Columns to Compare")
        
        st.sidebar.markdown(f"**File 1:** {file1}")
        selected_col1 = st.sidebar.selectbox("Select column:", assessment_cols_file1, key="col1")
        
        st.sidebar.markdown(f"**File 2:** {file2}")
        selected_col2 = st.sidebar.selectbox("Select column:", assessment_cols_file2, key="col2")
        
        # Map columns
        col_d_name_file1 = df1_orig.columns[3]
        col_d_name_file2 = df2_orig.columns[3]
        
        if selected_col1 == col_d_name_file1:
            col1_name = 'Final_Mark'
        else:
            col1_name = selected_col1
            df1_orig[selected_col1] = pd.to_numeric(df1_orig[selected_col1], errors='coerce')
        
        if selected_col2 == col_d_name_file2:
            col2_name = 'Final_Mark'
        else:
            col2_name = selected_col2
            df2_orig[selected_col2] = pd.to_numeric(df2_orig[selected_col2], errors='coerce')
        
        display_col1 = selected_col1
        display_col2 = selected_col2
        
        # Find common students
        common_ids = set(df1_orig['Student ID']) & set(df2_orig['Student ID'])
        
        st.header("📈 Analysis & Comparison")
        
        # Student Overview
        st.subheader("👥 Student Overview")
        overview_col1, overview_col2, overview_col3 = st.columns(3)
        overview_col1.metric("📄 Students in File 1", len(df1_orig))
        overview_col2.metric("📄 Students in File 2", len(df2_orig))
        overview_col3.metric("🔗 Students in BOTH", len(common_ids))
        
        # Distribution Analysis
        st.subheader("📊 Distribution Analysis - ALL Students")
        st.info("These distributions show ALL students from each file")
        
        fig_dist, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # File 1 Distribution
        data1_full = df1_orig[col1_name].dropna()
        data1_common = df1_orig[df1_orig['Student ID'].isin(common_ids)][col1_name].dropna()
        
        axes[0, 0].hist(data1_full, bins=20, color='lightblue', alpha=0.7, edgecolor='black', label='All Students')
        axes[0, 0].hist(data1_common, bins=20, color='red', alpha=0.6, edgecolor='black', label='Common Students')
        axes[0, 0].axvline(data1_full.mean(), color='blue', linestyle='--', linewidth=2, label=f'Mean (All): {data1_full.mean():.1f}')
        axes[0, 0].axvline(data1_common.mean(), color='darkred', linestyle='--', linewidth=2, label=f'Mean (Common): {data1_common.mean():.1f}')
        axes[0, 0].set_xlabel(display_col1, fontweight='bold')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title(f'{file1} - {display_col1}\nTotal: {len(data1_full)} | Common: {len(data1_common)}', fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # File 2 Distribution
        data2_full = df2_orig[col2_name].dropna()
        data2_common = df2_orig[df2_orig['Student ID'].isin(common_ids)][col2_name].dropna()
        
        axes[0, 1].hist(data2_full, bins=20, color='lightcoral', alpha=0.7, edgecolor='black', label='All Students')
        axes[0, 1].hist(data2_common, bins=20, color='red', alpha=0.6, edgecolor='black', label='Common Students')
        axes[0, 1].axvline(data2_full.mean(), color='coral', linestyle='--', linewidth=2, label=f'Mean (All): {data2_full.mean():.1f}')
        axes[0, 1].axvline(data2_common.mean(), color='darkred', linestyle='--', linewidth=2, label=f'Mean (Common): {data2_common.mean():.1f}')
        axes[0, 1].set_xlabel(display_col2, fontweight='bold')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title(f'{file2} - {display_col2}\nTotal: {len(data2_full)} | Common: {len(data2_common)}', fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Box Plot
        fig_dist.delaxes(axes[1, 1])
        axes[1, 0] = plt.subplot(2, 1, 2)
        
        box_data = [data1_full, data1_common, data2_full, data2_common]
        box_labels = [f'File 1\nAll\n(n={len(data1_full)})', f'File 1\nCommon\n(n={len(data1_common)})',
                     f'File 2\nAll\n(n={len(data2_full)})', f'File 2\nCommon\n(n={len(data2_common)})']
        box_colors = ['lightblue', 'red', 'lightcoral', 'darkred']
        
        bp = axes[1, 0].boxplot(box_data, labels=box_labels, patch_artist=True, widths=0.6)
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        axes[1, 0].set_ylabel('Score', fontweight='bold')
        axes[1, 0].set_title('Box Plot Comparison', fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        st.pyplot(fig_dist)
        
        st.markdown("---")
        
        # Filter Selection
        st.subheader("🔍 Analysis Filter")
        filter_option = st.radio(
            "Analyze which students?",
            ["🌍 ALL Students", "🎯 ONLY Students in BOTH Files"],
            index=0,
            horizontal=True
        )
        show_only_common = (filter_option == "🎯 ONLY Students in BOTH Files")
        
        st.markdown("---")
        
        # Apply Filter
        if show_only_common:
            df1 = df1_orig[df1_orig['Student ID'].isin(common_ids)].copy()
            df2 = df2_orig[df2_orig['Student ID'].isin(common_ids)].copy()
            st.success(f"🎯 Analyzing COMMON students only: {len(common_ids)} students")
        else:
            df1 = df1_orig.copy()
            df2 = df2_orig.copy()
            st.info(f"🌍 Analyzing ALL students | File 1: {len(df1)} | File 2: {len(df2)} | Common: {len(common_ids)}")
        
        # Statistical Summary
        st.subheader(f"📊 Statistical Summary - {'COMMON' if show_only_common else 'ALL'} Students")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown(f"### 📄 {file1}")
            stats1 = df1[col1_name].describe()
            stats_df1 = pd.DataFrame({
                'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [f"{stats1['count']:.0f}", f"{stats1['mean']:.2f}", f"{stats1['std']:.2f}",
                         f"{stats1['min']:.2f}", f"{stats1['25%']:.2f}", f"{stats1['50%']:.2f}",
                         f"{stats1['75%']:.2f}", f"{stats1['max']:.2f}"]
            })
            st.dataframe(stats_df1, use_container_width=True, hide_index=True)
            
            st.markdown("**📊 Grade Distribution**")
            dist1 = get_grade_distribution(df1)
            grade_df1 = pd.DataFrame([
                {'Grade': grade, 'Count': data['count'], 'Percentage': f"{data['percentage']:.1f}%"}
                for grade, data in dist1.items()
            ])
            st.dataframe(grade_df1, use_container_width=True, hide_index=True)
        
        with col_right:
            st.markdown(f"### 📄 {file2}")
            stats2 = df2[col2_name].describe()
            stats_df2 = pd.DataFrame({
                'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [f"{stats2['count']:.0f}", f"{stats2['mean']:.2f}", f"{stats2['std']:.2f}",
                         f"{stats2['min']:.2f}", f"{stats2['25%']:.2f}", f"{stats2['50%']:.2f}",
                         f"{stats2['75%']:.2f}", f"{stats2['max']:.2f}"]
            })
            st.dataframe(stats_df2, use_container_width=True, hide_index=True)
            
            st.markdown("**📊 Grade Distribution**")
            dist2 = get_grade_distribution(df2)
            grade_df2 = pd.DataFrame([
                {'Grade': grade, 'Count': data['count'], 'Percentage': f"{data['percentage']:.1f}%"}
                for grade, data in dist2.items()
            ])
            st.dataframe(grade_df2, use_container_width=True, hide_index=True)
        
        # Scatter Plot (only for common students)
        if show_only_common and len(common_ids) > 0:
            st.subheader(f"📈 Scatter Plot: {display_col1} vs {display_col2}")
            
            plot_df1 = df1[['Student ID', col1_name]].copy()
            plot_df1.columns = ['Student ID', 'Metric1']
            plot_df2 = df2[['Student ID', col2_name]].copy()
            plot_df2.columns = ['Student ID', 'Metric2']
            plot_df = plot_df1.merge(plot_df2, on='Student ID', how='inner').dropna()
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            if len(plot_df) > 0:
                ax.scatter(plot_df['Metric1'], plot_df['Metric2'], 
                          c='red', alpha=0.7, s=100, label=f'Common Students (n={len(plot_df)})')
                
                min_val = 0
                max_val = max(plot_df['Metric1'].max(), plot_df['Metric2'].max())
                ax.plot([min_val, max_val], [min_val, max_val], 
                       'k--', alpha=0.3, linewidth=1, label='Equal Performance Line')
                
                ax.set_xlabel(f'{display_col1} - {file1}', fontsize=12, fontweight='bold')
                ax.set_ylabel(f'{display_col2} - {file2}', fontsize=12, fontweight='bold')
                ax.set_title(f'{display_col1} vs {display_col2}\n(Students in BOTH files)', fontsize=14, fontweight='bold')
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
            
            # Comparison Table
            st.subheader("📋 Detailed Comparison")
            
            common_df1 = df1_orig[df1_orig['Student ID'].isin(common_ids)][['Student ID', col1_name]].copy()
            common_df2 = df2_orig[df2_orig['Student ID'].isin(common_ids)][['Student ID', col2_name]].copy()
            
            comparison_df = common_df1.merge(common_df2, on='Student ID')
            comparison_df.columns = ['Student ID', f'{display_col1} (File1)', f'{display_col2} (File2)']
            comparison_df['Difference'] = comparison_df[f'{display_col2} (File2)'] - comparison_df[f'{display_col1} (File1)']
            comparison_df['Change'] = comparison_df['Difference'].apply(
                lambda x: '📈 Higher' if x > 5 else ('📉 Lower' if x < -5 else '➡️ Similar')
            )
            comparison_df = comparison_df.sort_values('Difference', ascending=False).reset_index(drop=True)
            
            st.dataframe(comparison_df, use_container_width=True)
            
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Higher in File 2", f"{(comparison_df['Difference'] > 5).sum()} students")
            col_b.metric("Lower in File 2", f"{(comparison_df['Difference'] < -5).sum()} students")
            col_c.metric("Similar", f"{(abs(comparison_df['Difference']) <= 5).sum()} students")
            
            csv = comparison_df.to_csv(index=False)
            st.download_button("⬇️ Download Comparison Table", csv, "comparison_table.csv", "text/csv")
    
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        st.exception(e)
