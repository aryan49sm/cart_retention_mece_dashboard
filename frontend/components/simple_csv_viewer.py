import streamlit as st
import pandas as pd
import os

def display_simple_csv_viewer(output_directory):
    """
    Display a simple CSV viewer for raw data folders like 'output'.
    
    Args:
        output_directory (str): Directory containing CSV files
    """
    
    st.subheader("📄 Raw Data Viewer")
    st.info("This folder contains raw data files. Select a CSV file to view its contents.")
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    base_path = os.path.join(project_root, output_directory)
    
    if not os.path.exists(base_path):
        st.error(f"Directory not found: {output_directory}")
        return
    
    # Find CSV files
    csv_files = []
    for file in os.listdir(base_path):
        if file.endswith('.csv'):
            csv_files.append(file)
    
    if not csv_files:
        st.warning("No CSV files found in this directory")
        return
    
    # File selector
    selected_file = st.selectbox(
        "Select CSV file to view:",
        csv_files,
        index=0 if 'simulated_cart_abandons.csv' not in csv_files else csv_files.index('simulated_cart_abandons.csv')
    )
    
    if selected_file:
        file_path = os.path.join(base_path, selected_file)
        
        try:
            # Load the CSV
            df = pd.read_csv(file_path)
            
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{len(df):,}")
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("File Size", f"{os.path.getsize(file_path) / 1024:.1f} KB")
            
            # Display column info
            st.subheader("📊 Column Information")
            col_info = []
            for col in df.columns:
                col_type = str(df[col].dtype)
                non_null = df[col].count()
                null_count = len(df) - non_null
                
                col_info.append({
                    'Column': col,
                    'Type': col_type,
                    'Non-Null': f"{non_null:,}",
                    'Null': f"{null_count:,}"
                })
            
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, use_container_width=True, hide_index=True)
            
            # Display sample data
            st.subheader("🔍 Data Preview")
            
            # Show first few rows
            preview_rows = st.slider("Number of rows to preview", 5, min(100, len(df)), 10)
            st.dataframe(df.head(preview_rows), use_container_width=True)
            
            # Display summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.subheader("📈 Numeric Columns Summary")
                summary_stats = df[numeric_cols].describe()
                st.dataframe(summary_stats, use_container_width=True)
            
            # Download option
            st.subheader("📥 Download")
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {selected_file}",
                data=csv_data,
                file_name=selected_file,
                mime="text/csv"
            )
            
            # Show data types and memory usage
            with st.expander("🔧 Technical Details"):
                st.write("**Data Types:**")
                dtype_info = pd.DataFrame({
                    'Column': df.dtypes.index,
                    'Data Type': df.dtypes.values
                })
                st.dataframe(dtype_info, hide_index=True)
                
                # Memory usage
                memory_usage = df.memory_usage(deep=True).sum()
                st.write(f"**Memory Usage:** {memory_usage / 1024 / 1024:.2f} MB")
        
        except Exception as e:
            st.error(f"Error loading CSV file: {str(e)}")

def display_simple_dashboard(output_directory):
    """
    Display a simple dashboard for raw data directories.
    
    Args:
        output_directory (str): Directory name
    """
    
    st.markdown(f"## 📁 {output_directory.upper()} Directory")
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    base_path = os.path.join(project_root, output_directory)
    
    if os.path.exists(base_path):
        files = os.listdir(base_path)
        
        st.subheader("📋 Directory Contents")
        
        file_info = []
        for file in files:
            file_path = os.path.join(base_path, file)
            if os.path.isfile(file_path):
                size_kb = os.path.getsize(file_path) / 1024
                file_type = file.split('.')[-1].upper() if '.' in file else 'Unknown'
                
                file_info.append({
                    'File Name': file,
                    'Type': file_type,
                    'Size (KB)': f"{size_kb:.1f}"
                })
        
        if file_info:
            files_df = pd.DataFrame(file_info)
            st.dataframe(files_df, use_container_width=True, hide_index=True)
        
        # CSV viewer
        display_simple_csv_viewer(output_directory)
    
    else:
        st.error(f"Directory not found: {output_directory}")