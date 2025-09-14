#!/usr/bin/env python3

import argparse
import os
from datetime import datetime, date

from data_validator import DataValidator
from segmentation_engine import SegmentationEngine
from segment_optimizer import SegmentOptimizer
from segment_scorer import SegmentScorer
from output_generator import OutputGenerator


class SegmentationAPI:
    
    @staticmethod
    def run_segmentation(input_file, start_date=None, end_date=None, split_oversize=False):
        """
        Main segmentation function designed for frontend integration.
        
        Args:
            input_file (str): Path to CSV file with cart abandonment data
            start_date (date, optional): Start of 7-day analysis window
            end_date (date, optional): End of 7-day analysis window  
            split_oversize (bool): Whether to split large segments
            
        Returns:
            dict: Results including file paths and summary statistics
            
        Raises:
            ValueError: For invalid inputs or data issues
            FileNotFoundError: If input file doesn't exist
        """
        
        try:
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            df = DataValidator.validate_input_file(input_file)
            df = DataValidator.prepare_dataframe(df)
            
            universe, start_date, end_date = SegmentationEngine.compute_universe(
                df, start_date, end_date
            )
            
            if len(universe) == 0:
                raise ValueError("No users found in the specified 7-day window")
            
            percentiles = SegmentationEngine.compute_percentiles(universe)
            universe = SegmentationEngine.assign_decision_tree_bins(universe, percentiles)
            universe = SegmentationEngine.compute_conversion_scores(universe)
            
            segments = SegmentationEngine.aggregate_segments(universe)
            
            min_size, max_size = SegmentationEngine.determine_size_constraints(len(universe))
            segments, merge_log = SegmentOptimizer.merge_small_segments(
                segments, universe, min_size
            )
            
            split_log = []
            if split_oversize:
                segments, split_log = SegmentOptimizer.split_large_segments(
                    segments, universe, max_size
                )
            
            scored_segments = SegmentScorer.compute_final_scores(segments, universe)
            
            output_dir = f"output_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
            
            segments_summary, segment_id_map = OutputGenerator.create_segment_summary(
                scored_segments, segments, merge_log, split_log, percentiles, min_size
            )
            
            user_mapping = OutputGenerator.create_user_segment_mapping(
                segments, universe, segment_id_map
            )
            
            mece_report = OutputGenerator.create_mece_report(
                start_date, end_date, universe, percentiles, segments,
                merge_log, split_log, min_size, max_size, user_mapping
            )
            
            file_paths = OutputGenerator.save_all_outputs(
                segments_summary, user_mapping, mece_report, output_dir
            )
            
            return {
                "status": "success",
                "window_start": str(start_date),
                "window_end": str(end_date),
                "universe_size": len(universe),
                "num_segments": len(scored_segments),
                "output_directory": output_dir,
                "files": file_paths,
                "percentiles": percentiles,
                "summary_stats": {
                    "min_segment_size": min_size,
                    "max_segment_size": max_size,
                    "merges_performed": len(merge_log),
                    "splits_performed": len(split_log)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def parse_date_string(date_str):
        """Parse YYYY-MM-DD date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    """Command line interface for segmentation."""
    parser = argparse.ArgumentParser(
        description="Create MECE audience segments from cart abandonment data"
    )
    
    parser.add_argument(
        "--input", "-i", 
        default="output/simulated_cart_abandons.csv",
        help="Input CSV file path"
    )
    parser.add_argument(
        "--end-date", "-e",
        help="End date of 7-day window (YYYY-MM-DD). Defaults to latest data date"
    )
    parser.add_argument(
        "--start-date", "-s", 
        help="Start date of 7-day window (YYYY-MM-DD). Optional"
    )
    parser.add_argument(
        "--split-oversize", 
        action="store_true",
        help="Split segments larger than max size by sessions quantile"
    )
    
    args = parser.parse_args()
    
    start_date = SegmentationAPI.parse_date_string(args.start_date)
    end_date = SegmentationAPI.parse_date_string(args.end_date)
    
    result = SegmentationAPI.run_segmentation(
        args.input, start_date, end_date, args.split_oversize
    )
    
    if result["status"] == "success":
        print("SEGMENTATION COMPLETED SUCCESSFULLY")
        print(f"Analysis Window: {result['window_start']} to {result['window_end']}")
        print(f"Universe Size: {result['universe_size']} users")
        print(f"Segments Created: {result['num_segments']}")
        print(f"Output Directory: {result['output_directory']}")
        print("Generated Files:")
        for file_type, file_path in result["files"].items():
            print(f"  - {file_type}: {file_path}")
    else:
        print(f"SEGMENTATION FAILED: {result['error_message']}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())