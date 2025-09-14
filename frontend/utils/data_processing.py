import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import json

def get_available_output_directories():
    """
    Get list of available output directories.
    
    Returns:
        list: List of output directory names
    """
    
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/utils
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    
    directories = []
    
    for item in os.listdir(project_root):
        item_path = os.path.join(project_root, item)
        if os.path.isdir(item_path) and (item.startswith("output") or item == "output"):
            directories.append(item)
    
    # Sort by date (newest first), but keep 'output' at the end
    output_dirs = [d for d in directories if d != "output"]
    output_dirs.sort(reverse=True)
    
    if "output" in directories:
        output_dirs.append("output")
    
    return output_dirs

def is_simple_csv_directory(output_directory):
    """
    Check if this is a simple CSV directory (like 'output') that should only show raw CSV.
    
    Args:
        output_directory (str): Directory name
    
    Returns:
        bool: True if it's a simple CSV directory
    """
    
    return output_directory == "output"

def validate_date_range(start_date, end_date):
    """
    Validate that the date range is exactly 7 days and within allowed bounds.
    
    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date
    
    Returns:
        tuple: (is_valid, error_message)
    """
    
    # Check if dates are provided
    if not start_date or not end_date:
        return False, "Both start and end dates must be provided"
    
    # Check date order
    if start_date >= end_date:
        return False, "Start date must be before end date"
    
    # Check for exactly 7 days
    date_diff = (end_date - start_date).days
    if date_diff != 6:  # 6 days difference = 7 day window
        return False, f"Date range must be exactly 7 days. Current range: {date_diff + 1} days"
    
    # Check bounds (September 2025)
    min_date = datetime(2025, 9, 1).date()
    max_date = datetime(2025, 9, 30).date()
    
    if start_date < min_date or end_date > max_date:
        return False, f"Dates must be within September 2025 ({min_date} to {max_date})"
    
    return True, "Valid date range"

def format_date_for_filename(start_date, end_date):
    """
    Format dates for use in filename.
    
    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date
    
    Returns:
        str: Formatted date string for filename
    """
    
    return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

def get_output_directory_path(start_date, end_date):
    """
    Get the expected output directory path for given dates.
    
    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date
    
    Returns:
        str: Output directory name
    """
    
    return f"output_{format_date_for_filename(start_date, end_date)}"

def check_output_exists(start_date, end_date):
    """
    Check if output files exist for the given date range.
    
    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date
    
    Returns:
        tuple: (exists, output_directory, missing_files)
    """
    
    output_dir = get_output_directory_path(start_date, end_date)
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/utils
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    output_path = os.path.join(project_root, output_dir)
    
    if not os.path.exists(output_path):
        return False, output_dir, ["Directory does not exist"]
    
    # Check for required files
    required_files = [
        "segments_summary.csv",
        "user_segment_map.csv", 
        "mece_report.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(output_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    exists = len(missing_files) == 0
    return exists, output_dir, missing_files

def run_segmentation_analysis(start_date, end_date):
    """
    Run the segmentation analysis for the given date range.
    
    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date
    
    Returns:
        tuple: (success, output_directory, error_message)
    """
    
    try:
        # Add project root directory to path to import segmentation modules
        # Get the directory containing this file (frontend/utils)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels to get to project root (from frontend/utils to project root)
        project_root = os.path.dirname(os.path.dirname(current_dir))
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Import the segmentation API
        from segment_and_score_clean import SegmentationAPI
        
        # Create API instance
        api = SegmentationAPI()
        
        # Define input file path (absolute path to be safe)
        input_file = os.path.join(project_root, "output", "simulated_cart_abandons.csv")
        
        # Verify input file exists
        if not os.path.exists(input_file):
            return False, None, f"Input file not found: {input_file}"
        
        # Run segmentation with date objects (convert if strings)
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        results = api.run_segmentation(
            input_file=input_file,
            start_date=start_date,
            end_date=end_date
        )
        
        if results.get('status') == 'success':
            output_dir = results.get('output_directory', get_output_directory_path(start_date, end_date))
            return True, output_dir, None
        else:
            error_msg = results.get('error_message', 'Unknown error occurred')
            error_type = results.get('error_type', 'UnknownError')
            return False, None, f"{error_type}: {error_msg}"
    
    except Exception as e:
        return False, None, f"Error running segmentation: {str(e)}"

def load_segments_data(output_directory):
    """
    Load segments data from the output directory.
    
    Args:
        output_directory (str): Output directory name
    
    Returns:
        tuple: (success, data_dict, error_message)
    """
    
    try:
        # Get the absolute path to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/utils
        project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
        base_path = os.path.join(project_root, output_directory)
        
        data = {}
        
        # Load segments summary
        segments_path = os.path.join(base_path, "segments_summary.csv")
        if os.path.exists(segments_path):
            data['segments'] = pd.read_csv(segments_path)
        
        # Load user mapping
        users_path = os.path.join(base_path, "user_segment_map.csv")
        if os.path.exists(users_path):
            data['users'] = pd.read_csv(users_path)
        
        # Load MECE report
        mece_path = os.path.join(base_path, "mece_report.json")
        if os.path.exists(mece_path):
            with open(mece_path, 'r') as f:
                data['mece'] = json.load(f)
        
        return True, data, None
    
    except Exception as e:
        return False, {}, f"Error loading data: {str(e)}"

def get_segment_summary_stats(segments_df):
    """
    Get summary statistics for segments.
    
    Args:
        segments_df (pd.DataFrame): Segments dataframe
    
    Returns:
        dict: Summary statistics
    """
    
    if segments_df is None or len(segments_df) == 0:
        return {}
    
    # Filter only valid segments with segment_id (not empty)
    active_segments = segments_df[
        (segments_df['segment_id'].notna()) & 
        (segments_df['segment_id'] != '') & 
        (segments_df['segment_id'].str.strip() != '')
    ].copy()
    
    # Filter merged segments (empty segment_id)
    merged_segments = segments_df[
        (segments_df['segment_id'].isna()) | 
        (segments_df['segment_id'] == '') | 
        (segments_df['segment_id'].str.strip() == '')
    ].copy()
    
    if len(active_segments) == 0:
        return {
            'total_segments': 0,
            'merged_segments': len(merged_segments),
            'total_users': 0,
            'avg_segment_size': 0,
            'avg_score': 0,
            'min_score': 0,
            'max_score': 0
        }
    
    stats = {
        'total_segments': len(active_segments),
        'merged_segments': len(merged_segments),
        'total_users': int(active_segments['size'].sum()),
        'avg_segment_size': float(active_segments['size'].mean()),
        'avg_score': float(active_segments['overall_score'].mean()),
        'min_score': float(active_segments['overall_score'].min()),
        'max_score': float(active_segments['overall_score'].max())
    }
    
    return stats

def get_performance_metrics(segments_df):
    """
    Calculate performance metrics for segments.
    
    Args:
        segments_df (pd.DataFrame): Segments dataframe
    
    Returns:
        dict: Performance metrics
    """
    
    if segments_df is None or len(segments_df) == 0:
        return {}
    
    # Filter only valid segments with segment_id (not empty)
    active_segments = segments_df[
        (segments_df['segment_id'].notna()) & 
        (segments_df['segment_id'] != '') & 
        (segments_df['segment_id'].str.strip() != '')
    ].copy()
    
    if len(active_segments) == 0:
        return {}
    
    # Calculate weighted averages
    total_size = active_segments['size'].sum()
    
    # Count high, medium, low value segments based on overall_score
    high_value_segments = len(active_segments[active_segments['overall_score'] >= 0.7])
    medium_value_segments = len(active_segments[
        (active_segments['overall_score'] >= 0.4) & 
        (active_segments['overall_score'] < 0.7)
    ])
    low_value_segments = len(active_segments[active_segments['overall_score'] < 0.4])
    
    metrics = {
        'weighted_conversion_potential': float(
            (active_segments['conversion_potential'] * active_segments['size']).sum() / total_size
        ) if total_size > 0 else 0,
        
        'weighted_profitability': float(
            (active_segments['profitability'] * active_segments['size']).sum() / total_size
        ) if total_size > 0 else 0,
        
        'weighted_strategic_fit': float(
            (active_segments['strategic_fit'] * active_segments['size']).sum() / total_size
        ) if total_size > 0 else 0,
        
        'high_value_segments': high_value_segments,
        'medium_value_segments': medium_value_segments,
        'low_value_segments': low_value_segments
    }
    
    return metrics