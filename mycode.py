import streamlit as st
import pandas as pd
import os

# Page config
st.set_page_config(page_title="CSV Viewer", layout="wide")

# Title
st.title("📊 CSV File Viewer")

# Sidebar
st.sidebar.header("Settings")

# Folder path input
folder_path = st.sidebar.text_input(
    "Folder Path:", 
    value="",
    placeholder="Paste your folder path here"
)

# Convert Windows backslashes
if folder_path:
    folder_path = folder_path.strip().replace('\\', '/')

st.sidebar.markdown("---")

# Main area
if not folder_path:
    st.info("👈 Enter your folder path in the sidebar")
    st.markdown("""
    ### Instructions:
    1. Paste your folder path in the sidebar
    2. Example: `C:/Users/mhana/Desktop/folder`
    3. Select a CSV file from the list
    """)
    st.stop()

# Check if folder exists
if not os.path.exists(folder_path):
    st.error(f"❌ Folder not found: {folder_path}")
    st.stop()

if not os.path.isdir(folder_path):
    st.error(f"❌ Not a folder: {folder_path}")
    st.stop()

# Get all files
try:
    all_items = os.listdir(folder_path)
    st.sidebar.success(f"✅ Found {len(all_items)} items")
except Exception as e:
    st.error(f"Error reading folder: {e}")
    st.stop()

# Filter CSV files
csv_files = [f for f in all_items if f.lower().endswith('.csv')]

if len(csv_files) == 0:
    st.warning("⚠️ No CSV files found in this folder")
    
    # Show what's in the folder
    st.subheader("Files in folder:")
    file_types = {}
    for item in all_items[:20]:  # Show first 20
        ext = os.path.splitext(item)[1] or "(no extension)"
        if ext not in file_types:
            file_types[ext] = []
        file_types[ext].append(item)
    
    for ext, files in file_types.items():
        st.write(f"**{ext}:** {len(files)} files")
        for f in files[:3]:
            st.write(f"  - {f}")
    
    st.stop()

# Show CSV count
st.sidebar.success(f"📄 {len(csv_files)} CSV files found")

# Select file
selected_file = st.sidebar.selectbox("Select CSV file:", csv_files)

if selected_file:
    st.subheader(f"File: {selected_file}")
    
    file_path = os.path.join(folder_path, selected_file)
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Size", f"{os.path.getsize(file_path)/1024:.1f} KB")
        
        # Show data
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download button
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            file_name=selected_file,
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
