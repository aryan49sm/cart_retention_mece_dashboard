import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import json
import os
import sys

# Add parent directory to path to import our segmentation modules
sys.path.append('..')
from segment_and_score_clean import SegmentationAPI

# Page configuration
st.set_page_config(
    page_title="Cart Abandoner Segmentation Dashboard", 
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("🛒 Cart Abandoner Retention Strategy Dashboard")
st.markdown("---")

# Sidebar for controls
st.sidebar.header("Analysis Configuration")

# Date range validation
MIN_DATE = date(2025, 9, 1)
MAX_DATE = date(2025, 9, 30)

def validate_date_range(start_date, end_date):
    """Validate that the date range is exactly 7 days and within bounds."""
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    if (end_date - start_date).days != 6:
        return False, "Date range must be exactly 7 days (inclusive)"
    
    if start_date < MIN_DATE or end_date > MAX_DATE:
        return False, f"Dates must be between {MIN_DATE} and {MAX_DATE}"
    
    return True, "Valid date range"

# Date input controls
st.sidebar.subheader("📅 Analysis Window")
st.sidebar.markdown("Select a 7-day window for cart abandonment analysis")

# Default to latest available dates
default_end_date = MAX_DATE
default_start_date = default_end_date - timedelta(days=6)

start_date = st.sidebar.date_input(
    "Start Date",
    value=default_start_date,
    min_value=MIN_DATE,
    max_value=MAX_DATE - timedelta(days=6),
    help="First day of the 7-day analysis window"
)

end_date = st.sidebar.date_input(
    "End Date", 
    value=default_end_date,
    min_value=MIN_DATE + timedelta(days=6),
    max_value=MAX_DATE,
    help="Last day of the 7-day analysis window"
)

# Validate date range
is_valid, validation_message = validate_date_range(start_date, end_date)

if not is_valid:
    st.sidebar.error(f"❌ {validation_message}")
else:
    st.sidebar.success(f"✅ {validation_message}")

# Analysis options
st.sidebar.subheader("⚙️ Analysis Options")
split_oversize = st.sidebar.checkbox(
    "Split Oversized Segments",
    value=False,
    help="Automatically split segments larger than maximum size"
)

# Run analysis button
run_analysis = st.sidebar.button(
    "🚀 Run Segmentation Analysis",
    disabled=not is_valid,
    type="primary"
)

# Main content area
if not run_analysis and not st.session_state.get('analysis_complete', False):
    # Welcome screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👈 Configure your analysis settings in the sidebar and click 'Run Segmentation Analysis' to begin")
        
        # Show sample data info
        st.subheader("📊 Available Data Overview")
        st.markdown("""
        **Data Range**: September 1-30, 2025  
        **Analysis Window**: 7-day sliding windows  
        **Features**: AOV, Engagement Score, Profitability Score, Sessions, Cart Items
        """)

# Store results in session state for persistence
if 'segmentation_results' not in st.session_state:
    st.session_state.segmentation_results = None

if run_analysis and is_valid:
    with st.spinner("🔄 Running segmentation analysis..."):
        # Run the segmentation
        result = SegmentationAPI.run_segmentation(
            input_file="../output/simulated_cart_abandons.csv",
            start_date=start_date,
            end_date=end_date,
            split_oversize=split_oversize
        )
        
        # Store results
        st.session_state.segmentation_results = result
        st.session_state.analysis_complete = True
        
        if result["status"] == "success":
            st.sidebar.success("✅ Analysis completed successfully!")
        else:
            st.sidebar.error(f"❌ Analysis failed: {result['error_message']}")

# Display results if available
if st.session_state.get('segmentation_results') and st.session_state.segmentation_results["status"] == "success":
    results = st.session_state.segmentation_results
    
    # Results summary
    st.header("📈 Analysis Results")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Analysis Window", f"{results['window_start']} to {results['window_end']}")
    with col2:
        st.metric("Universe Size", f"{results['universe_size']:,} users")
    with col3:
        st.metric("Segments Created", results['num_segments'])
    with col4:
        st.metric("Merges Performed", results['summary_stats']['merges_performed'])
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Segments Overview", "📋 Detailed Report", "🌳 Tree Visualization", "📚 Documentation"])
    
    with tab1:
        st.subheader("Segment Summary")
        # This will be implemented in the next step
        st.info("Segment summary table will be displayed here")
    
    with tab2:
        st.subheader("MECE Report Details")
        # This will be implemented in the next step
        st.info("Detailed MECE report will be displayed here")
    
    with tab3:
        st.subheader("Interactive Tree Visualization")
        # This will be implemented in the next step
        st.info("Animated tree visualization will be displayed here")
    
    with tab4:
        st.subheader("Processing Pipeline Documentation")
        st.info("Complete end-to-end pipeline documentation will be added here later")

elif st.session_state.get('segmentation_results') and st.session_state.segmentation_results["status"] == "error":
    st.error(f"❌ Analysis Error: {st.session_state.segmentation_results['error_message']}")
    st.session_state.analysis_complete = False