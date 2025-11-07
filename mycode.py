import streamlit as st
import pandas as pd
import os
from pathlib import Path

st.set_page_config(page_title="CSV File Viewer", page_icon="📊", layout="wide")

st.title("📊 CSV File Viewer")
st.markdown("Browse and view CSV files from your local folder")

# Sidebar for folder selection
st.sidebar.header("Folder Selection")

# Input for folder path
folder_path = st.sidebar.text_input(
    "Enter folder path:",
    placeholder="C:/Users/YourName/Documents/data",
    help="Enter the full path to the folder containing your CSV files"
)

# Normalize the path to handle Windows backslashes
if folder_path:
    folder_path = folder_path.replace('\\', '/')

# Function to get all CSV files in a folder
def get_csv_files(folder):
    try:
        if os.path.exists(folder) and os.path.isdir(folder):
            all_files = os.listdir(folder)
            csv_files = [f for f in all_files if f.lower().endswith('.csv')]
            
            # Debug info in sidebar
            st.sidebar.info(f"Total files in folder: {len(all_files)}")
            if not csv_files and all_files:
                # Show what file types exist
                extensions = set([os.path.splitext(f)[1].lower() for f in all_files if os.path.splitext(f)[1]])
                st.sidebar.warning(f"Found these file types: {', '.join(extensions) if extensions else 'No extensions'}")
            
            return sorted(csv_files)
        else:
            return []
    except Exception as e:
        st.error(f"Error reading folder: {str(e)}")
        return []

# Main content
if folder_path:
    # Validate path exists
    if not os.path.exists(folder_path):
        st.sidebar.error("❌ Path does not exist!")
        st.error(f"The folder path does not exist: `{folder_path}`")
        st.info("Please check your path and try again.")
    elif not os.path.isdir(folder_path):
        st.sidebar.error("❌ Path is not a folder!")
        st.error(f"The path exists but is not a folder: `{folder_path}`")
    else:
        st.sidebar.success("✅ Path is valid!")
    
    csv_files = get_csv_files(folder_path)
    
    if csv_files:
        st.sidebar.success(f"Found {len(csv_files)} CSV file(s)")
        
        # Dropdown to select CSV file
        selected_file = st.sidebar.selectbox(
            "Select a CSV file:",
            csv_files,
            index=0
        )
        
        if selected_file:
            file_path = os.path.join(folder_path, selected_file)
            
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Display file information
                st.subheader(f"📄 {selected_file}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    st.metric("File Size", f"{file_size:.2f} KB")
                
                # Display options
                st.subheader("Display Options")
                show_all = st.checkbox("Show all rows", value=False)
                
                if show_all:
                    st.dataframe(df, use_container_width=True)
                else:
                    num_rows = st.slider("Number of rows to display:", 5, 100, 10)
                    st.dataframe(df.head(num_rows), use_container_width=True)
                
                # Display column information
                with st.expander("📋 Column Information"):
                    col_info = pd.DataFrame({
                        'Column Name': df.columns,
                        'Data Type': df.dtypes.values,
                        'Non-Null Count': df.count().values,
                        'Null Count': df.isnull().sum().values
                    })
                    st.dataframe(col_info, use_container_width=True)
                
                # Display basic statistics
                with st.expander("📊 Statistical Summary"):
                    st.dataframe(df.describe(), use_container_width=True)
                
                # Download button
                st.download_button(
                    label="⬇️ Download CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=selected_file,
                    mime='text/csv',
                )
                
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.info("Make sure the file is a valid CSV format")
    
    elif folder_path:
        st.sidebar.warning("No CSV files found in this folder")
        st.info("👈 Please check the folder path or add CSV files to the folder")
else:
    st.info("👈 Please enter a folder path in the sidebar to get started")
    
    # Instructions
    st.markdown("""
    ### How to use:
    1. Enter the full path to your folder in the sidebar (e.g., `C:/Users/YourName/Documents/data`)
    2. Select a CSV file from the dropdown menu
    3. View and analyze your data
    4. Download the file if needed
    
    ### Tips:
    - Use forward slashes (/) or double backslashes (\\\\) in Windows paths
    - The app will automatically find all CSV files in the specified folder
    - You can view statistics and column information for each file
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with Streamlit 🎈")
