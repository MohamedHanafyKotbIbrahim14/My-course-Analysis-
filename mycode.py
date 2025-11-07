import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="CSV Viewer", layout="wide")

st.title("📊 CSV File Viewer - LOCAL")
st.caption("This app runs on YOUR computer and reads YOUR local files")

# Sidebar
st.sidebar.header("📁 Folder Settings")

folder_path = st.sidebar.text_input(
    "Enter Folder Path:",
    value="",
    placeholder="C:/Users/mhana/Desktop/folder"
)

if folder_path:
    folder_path = folder_path.strip().replace('\\', '/')

st.sidebar.markdown("---")
st.sidebar.markdown("**Tips:**")
st.sidebar.info("""
- Copy path from Windows Explorer address bar
- Or right-click folder → Copy as path
- Use forward slashes: C:/Users/...
""")

# Main content
if not folder_path:
    st.info("👈 **Step 1:** Enter your folder path in the sidebar")
    st.markdown("""
    ### How to Get Your Folder Path:
    
    **Method 1:**
    1. Open Windows Explorer
    2. Navigate to your folder
    3. Click the address bar at top
    4. Copy the path (Ctrl+C)
    5. Paste in sidebar
    
    **Method 2:**
    1. Hold Shift
    2. Right-click your folder
    3. Click "Copy as path"
    4. Paste in sidebar (it will auto-fix the format)
    """)
    st.stop()

# Validate path
if not os.path.exists(folder_path):
    st.error(f"❌ Folder not found: `{folder_path}`")
    st.warning("**Double-check:**")
    st.write("1. Is the spelling correct?")
    st.write("2. Does the folder still exist?")
    st.write("3. Try copying the path directly from Windows Explorer")
    st.stop()

if not os.path.isdir(folder_path):
    st.error("❌ This path exists but is not a folder")
    st.stop()

# Read folder
try:
    all_items = os.listdir(folder_path)
    st.sidebar.success(f"✅ Folder found!")
    st.sidebar.info(f"Total items: {len(all_items)}")
except Exception as e:
    st.error(f"Cannot read folder: {str(e)}")
    st.stop()

# Filter for CSV files
csv_files = [f for f in all_items if f.lower().endswith('.csv')]

if len(csv_files) == 0:
    st.warning("⚠️ No CSV files found in this folder")
    
    st.subheader("What's in this folder:")
    
    # Group by file type
    file_types = {}
    for item in all_items:
        full_path = os.path.join(folder_path, item)
        if os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower() or "(no extension)"
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(item)
        else:
            if "(folders)" not in file_types:
                file_types["(folders)"] = []
            file_types["(folders)"].append(item)
    
    # Display file types
    for ext, files in sorted(file_types.items()):
        with st.expander(f"{ext} - {len(files)} files"):
            for f in files[:20]:
                st.write(f"• {f}")
            if len(files) > 20:
                st.write(f"... and {len(files)-20} more")
    
    st.info("💡 If your files are Excel, let me know and I'll update the app!")
    st.stop()

# Show CSV files
st.sidebar.success(f"📄 Found {len(csv_files)} CSV files")

selected_file = st.sidebar.selectbox("Select CSV file:", csv_files)

if selected_file:
    file_path = os.path.join(folder_path, selected_file)
    
    # File header
    st.subheader(f"📄 {selected_file}")
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", f"{len(df):,}")
        col2.metric("Columns", len(df.columns))
        col3.metric("File Size", f"{os.path.getsize(file_path)/1024:.1f} KB")
        
        # Display options
        st.markdown("---")
        col_a, col_b = st.columns([1, 3])
        with col_a:
            show_rows = st.number_input("Rows to display:", 5, 1000, 100)
        
        # Show data
        st.dataframe(df.head(show_rows), use_container_width=True, height=400)
        
        # Additional info
        col_x, col_y = st.columns(2)
        
        with col_x:
            with st.expander("📋 Column Info"):
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Type': df.dtypes.values,
                    'Non-Null': df.count().values,
                    'Null': df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True)
        
        with col_y:
            with st.expander("📊 Statistics"):
                st.dataframe(df.describe(), use_container_width=True)
        
        # Download
        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False),
            file_name=selected_file,
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error reading CSV: {str(e)}")
        st.info("Make sure the file is a valid CSV format")
