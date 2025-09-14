import streamlit as st
import sys
import os
from datetime import datetime, date, timedelta
from components.csv_display import display_segments_summary, display_user_segment_mapping
from components.readme_display import show_readme_modal

# Add parent directory to path to import segmentation modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import custom components
from utils.data_processing import (
    validate_date_range, 
    check_output_exists, 
    run_segmentation_analysis,
    get_available_output_directories,
    load_segments_data,
    get_segment_summary_stats,
    get_performance_metrics,
    is_simple_csv_directory,
    get_output_directory_path
)

from components.mece_display import display_mece_report
from components.tree_visualization import create_segmentation_tree
from components.simple_csv_viewer import display_simple_dashboard, display_simple_csv_viewer

def main():
    st.set_page_config(
        page_title="Cart Abandoner Segmentation Dashboard",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🛒 Cart Abandoner Retention Strategy Dashboard")
    st.markdown("Interactive analysis of cart abandoner segments with MECE compliance validation")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Previous Analysis")
        
        # Clear refresh flag if it exists
        if st.session_state.get('refresh_dropdown', False):
            st.session_state.refresh_dropdown = False
        
        # Show available outputs
        available_outputs = get_available_output_directories()
        if available_outputs:
            selected_output = st.selectbox(
                "Load Previous Analysis",
                [""] + available_outputs,
                format_func=lambda x: "Select analysis..." if x == "" else x
            )
            
            if selected_output:
                st.session_state.current_output_directory = selected_output
                st.success(f"Loaded: {selected_output}")
        
        st.markdown("---")
        
        # Date range selection for new analysis
        st.subheader("New Analysis Period")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date(2025, 9, 14),
                min_value=date(2025, 9, 1),
                max_value=date(2025, 9, 30)
            )
        
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=date(2025, 9, 20),
                min_value=date(2025, 9, 1),
                max_value=date(2025, 9, 30)
            )
        
        # Validate date range
        is_valid, message = validate_date_range(start_date, end_date)
        
        if is_valid:
            st.success(message)
            
            # Check if output already exists
            exists, output_dir, missing_files = check_output_exists(start_date, end_date)
            
            if exists:
                st.info("Analysis already exists for this date range")
            else:
                # Show what will be created instead of showing missing files error
                expected_output_dir = get_output_directory_path(start_date, end_date)
                st.info(f"Will create new analysis: {expected_output_dir}")
        else:
            st.error(message)
        
        # Analysis button
        if st.button("Run New Segmentation Analysis", disabled=not is_valid):
            with st.spinner("Running segmentation analysis..."):
                success, output_dir, error = run_segmentation_analysis(start_date, end_date)
                
                if success:
                    st.session_state.current_output_directory = output_dir
                    st.session_state.refresh_dropdown = True  # Force dropdown refresh
                    st.success("Analysis completed!")
                    st.rerun()
                else:
                    st.error(f"Analysis failed: {error}")
        
        st.markdown("---")
        
        # README Documentation Button
        # st.subheader("Project Documentation")
        if st.button("📖 View README", key="readme_button", type="secondary"):
            st.session_state.show_readme = True
            st.rerun()
    
    # Check if README should be displayed
    if st.session_state.get('show_readme', False):
        show_readme_modal()
        return
    
    # Main content area
    if 'current_output_directory' in st.session_state:
        output_directory = st.session_state.current_output_directory
        
        # Display current analysis info
        st.info(f"Currently viewing: **{output_directory}**")
        
        # Check if this is a simple CSV directory
        if is_simple_csv_directory(output_directory):
            # Show simple CSV viewer for raw data
            display_simple_dashboard(output_directory)
        else:
            # Show full analysis dashboard for processed results
            # Create tabs - Optimized 3-tab structure
            tab1, tab2, tab3 = st.tabs([
                " Segments Analysis", 
                "MECE Compliance", 
                "Segmentation Tree"
            ])
            
            with tab1:
                st.header("Segments Analysis")
                display_segments_summary(output_directory)
                st.markdown("---")
                display_user_segment_mapping(output_directory)
            
            with tab2:
                st.header("MECE Compliance")
                display_mece_report(output_directory)
            
            with tab3:
                st.header("Segmentation Decision Tree")
                create_segmentation_tree(output_directory)
    
    else:
        # Welcome screen

        # col1, col2 = st.columns(2)
        
        # with col1:
            st.markdown("""
            ### 📝 About this dashboard:
            - **Segment Analysis**: View detailed cart abandoner segments with scoring
            - **MECE Validation**: Ensure segments are Mutually Exclusive and Collectively Exhaustive
            - **Interactive Visualization**: Explore segmentation decision trees and merge processes
            - **Performance Metrics**: Analyze conversion potential and profitability
            """)
        
        # with col2:
            st.markdown("""
            ### 📘 Getting started:
            1. **Load existing analysis** from the sidebar, or
            2. **Select a 7-day date range** in September 2025
            3. **Run new segmentation analysis**
            4. **Explore results** in the interactive tabs
            """)
        
        # Show available analyses
        # available_outputs = get_available_output_directories()
        # if available_outputs:
        #     st.markdown("### Available Analyses")
            
        #     for output in available_outputs[:5]:  # Show latest 5
        #         col1, col2 = st.columns([3, 1])
        #         with col1:
        #             st.write(f"📊 {output}")
        #         with col2:
        #             if st.button(f"Load", key=f"load_{output}"):
        #                 st.session_state.current_output_directory = output
        #                 st.rerun()
        # else:
        #     st.info("No previous analyses found. Create your first analysis using the sidebar!")

if __name__ == "__main__":
    main()