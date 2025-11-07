import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="CSV Comparison Tool", layout="wide")

st.title("📊 Course Analysis & Comparison Tool")

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

# Main content
if not folder_path:
    st.info("👈 Enter your folder path in the sidebar")
    st.stop()

# Validate path
if not os.path.exists(folder_path):
    st.error(f"❌ Folder not found: {folder_path}")
    st.stop()

if not os.path.isdir(folder_path):
    st.error("❌ Not a folder")
    st.stop()

# Get CSV files
try:
    all_items = os.listdir(folder_path)
    csv_files = [f for f in all_items if f.lower().endswith('.csv')]
except Exception as e:
    st.error(f"Cannot read folder: {e}")
    st.stop()

if len(csv_files) == 0:
    st.warning("⚠️ No CSV files found")
    st.stop()

st.sidebar.success(f"✅ Found {len(csv_files)} CSV files")

# Select TWO files
st.sidebar.subheader("Select Files to Compare")
file1 = st.sidebar.selectbox("📄 File 1:", csv_files, key="file1")
file2 = st.sidebar.selectbox("📄 File 2:", csv_files, key="file2", index=min(1, len(csv_files)-1))

if file1 and file2:
    st.header("📈 Analysis & Comparison")
    
    # Read both files
    try:
        df1 = pd.read_csv(os.path.join(folder_path, file1))
        df2 = pd.read_csv(os.path.join(folder_path, file2))
        
        # Skip first row (header info) if it's not actual data
        if 'Student ID' in df1.columns and df1.iloc[0, 0] == df1.columns[0]:
            df1 = df1.iloc[1:].reset_index(drop=True)
        if 'Student ID' in df2.columns and df2.iloc[0, 0] == df2.columns[0]:
            df2 = df2.iloc[1:].reset_index(drop=True)
        
        # Clean column names
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Extract numeric final marks
        def extract_final_mark(df):
            # Find the column with "FINAL" in it
            final_col = [col for col in df.columns if 'FINAL' in col.upper()][0]
            
            # Extract numeric part (e.g., "78 DN" -> 78)
            df['Final_Mark'] = df[final_col].astype(str).str.extract('(\d+)').astype(float)
            
            # Clean Student ID
            df['Student ID'] = df['Student ID'].astype(str).str.strip()
            
            return df
        
        df1 = extract_final_mark(df1)
        df2 = extract_final_mark(df2)
        
        # Find common students
        common_ids = set(df1['Student ID']) & set(df2['Student ID'])
        
        st.info(f"🔍 Found **{len(common_ids)}** students in both files")
        
        # --- STATISTICAL SUMMARY ---
        st.subheader("📊 Statistical Summary - Final Marks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{file1}**")
            stats1 = df1['Final_Mark'].describe()
            stats_df1 = pd.DataFrame({
                'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [
                    f"{stats1['count']:.0f}",
                    f"{stats1['mean']:.2f}",
                    f"{stats1['std']:.2f}",
                    f"{stats1['min']:.2f}",
                    f"{stats1['25%']:.2f}",
                    f"{stats1['50%']:.2f}",
                    f"{stats1['75%']:.2f}",
                    f"{stats1['max']:.2f}"
                ]
            })
            st.dataframe(stats_df1, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown(f"**{file2}**")
            stats2 = df2['Final_Mark'].describe()
            stats_df2 = pd.DataFrame({
                'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [
                    f"{stats2['count']:.0f}",
                    f"{stats2['mean']:.2f}",
                    f"{stats2['std']:.2f}",
                    f"{stats2['min']:.2f}",
                    f"{stats2['25%']:.2f}",
                    f"{stats2['50%']:.2f}",
                    f"{stats2['75%']:.2f}",
                    f"{stats2['max']:.2f}"
                ]
            })
            st.dataframe(stats_df2, use_container_width=True, hide_index=True)
        
        # --- SCATTER PLOT ---
        st.subheader("📈 Scatter Plot Comparison")
        
        # Prepare data for plotting
        # All students from file 1
        plot_df = df1[['Student ID', 'Final_Mark']].copy()
        plot_df.columns = ['Student ID', 'File1_Mark']
        
        # Merge with file 2
        df2_plot = df2[['Student ID', 'Final_Mark']].copy()
        df2_plot.columns = ['Student ID', 'File2_Mark']
        
        plot_df = plot_df.merge(df2_plot, on='Student ID', how='outer')
        
        # Mark common students
        plot_df['Is_Common'] = plot_df['Student ID'].isin(common_ids)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot non-common students
        non_common = plot_df[~plot_df['Is_Common']]
        ax.scatter(non_common['File1_Mark'], non_common['File2_Mark'], 
                  c='blue', alpha=0.5, s=50, label='Different Students')
        
        # Plot common students in RED
        common = plot_df[plot_df['Is_Common']]
        ax.scatter(common['File1_Mark'], common['File2_Mark'], 
                  c='red', alpha=0.7, s=100, label=f'Same Students (n={len(common)})')
        
        # Add diagonal line (if mark was same)
        min_val = 0
        max_val = 100
        ax.plot([min_val, max_val], [min_val, max_val], 
               'k--', alpha=0.3, linewidth=1, label='Equal Performance Line')
        
        ax.set_xlabel(f'{file1} - Final Mark', fontsize=12)
        ax.set_ylabel(f'{file2} - Final Mark', fontsize=12)
        ax.set_title('Final Mark Comparison\n(Red = Same Student ID in Both Files)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 105)
        ax.set_ylim(0, 105)
        
        st.pyplot(fig)
        
        # --- DISTRIBUTION PLOT ---
        st.subheader("📊 Distribution Comparison")
        
        fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram for File 1
        ax1.hist(df1['Final_Mark'].dropna(), bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        ax1.axvline(df1['Final_Mark'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df1["Final_Mark"].mean():.1f}')
        ax1.set_xlabel('Final Mark')
        ax1.set_ylabel('Frequency')
        ax1.set_title(file1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Histogram for File 2
        ax2.hist(df2['Final_Mark'].dropna(), bins=20, color='lightcoral', edgecolor='black', alpha=0.7)
        ax2.axvline(df2['Final_Mark'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df2["Final_Mark"].mean():.1f}')
        ax2.set_xlabel('Final Mark')
        ax2.set_ylabel('Frequency')
        ax2.set_title(file2)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig2)
        
        # --- DETAILED COMPARISON TABLE ---
        st.subheader("📋 Students in Both Files - Detailed Comparison")
        
        if len(common_ids) > 0:
            comparison_df = common[['Student ID', 'File1_Mark', 'File2_Mark']].copy()
            comparison_df['Difference'] = comparison_df['File2_Mark'] - comparison_df['File1_Mark']
            comparison_df['Change'] = comparison_df['Difference'].apply(
                lambda x: '📈 Improved' if x > 0 else ('📉 Declined' if x < 0 else '➡️ Same')
            )
            comparison_df = comparison_df.sort_values('Difference', ascending=False).reset_index(drop=True)
            
            st.dataframe(comparison_df, use_container_width=True)
            
            # Summary stats for common students
            st.markdown("**Performance Change Summary:**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Improved", f"{(comparison_df['Difference'] > 0).sum()} students")
            col_b.metric("Declined", f"{(comparison_df['Difference'] < 0).sum()} students")
            col_c.metric("Same", f"{(comparison_df['Difference'] == 0).sum()} students")
        else:
            st.warning("No common students found in both files")
        
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        st.exception(e)
