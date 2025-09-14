#!/usr/bin/env python3

import os
import json
import pandas as pd
from segment_scorer import SegmentScorer


class OutputGenerator:
    
    @staticmethod
    def ensure_directory(path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def create_segment_summary(scored_segments, segments, merge_log, split_log, percentiles, min_size):
        # Create segment ID mapping based on overall score ranking
        sorted_keys = sorted(
            scored_segments.keys(),
            key=lambda k: (-scored_segments[k]["overall_score"], -scored_segments[k]["size"], k)
        )
        
        segment_id_map = {key: f"S{i:03d}" for i, key in enumerate(sorted_keys, start=1)}
        
        # Track merges and splits
        merged_to_map = {}
        for merge in merge_log:
            destination = merge.get("to")
            for source in merge.get("from", []):
                merged_to_map[source] = destination
        
        split_from_map = {}
        for split in split_log:
            original = split.get("original")
            for created in split.get("created", []):
                split_from_map[created] = original
        
        rows = []
        final_segments = set(sorted_keys)
        
        # Add active segments
        for segment_key in sorted_keys:
            segment_data = scored_segments[segment_key]
            segment_id = segment_id_map[segment_key]
            rules = SegmentScorer.generate_segment_rules(segment_key, percentiles)
            
            is_valid = "Yes" if segment_data["size"] >= min_size else "No"
            notes = ""
            
            # Check if created from merges
            merge_sources = [
                m for m in merge_log if m.get("to") == segment_key
            ]
            if merge_sources:
                source_list = []
                for merge in merge_sources:
                    source_list.extend(merge.get("from", []))
                notes = "Created by merging: " + ", ".join(source_list)
            
            # Check if created from splits
            if segment_key in split_from_map:
                if notes:
                    notes += " ; "
                notes += f"Created by splitting {split_from_map[segment_key]}"
            
            rows.append({
                "segment_id": segment_id,
                "segment_name": segment_key,
                "rules_applied": rules,
                "size": segment_data["size"],
                "conversion_potential": SegmentScorer._format_float(segment_data["conversion_potential"]),
                "profitability": SegmentScorer._format_float(segment_data["profitability"]),
                "lift_vs_control": SegmentScorer._format_float(segment_data["lift_vs_control"]),
                "size_score": SegmentScorer._format_float(segment_data["size_score"]),
                "strategic_fit": SegmentScorer._format_float(segment_data["strategic_fit"]),
                "overall_score": SegmentScorer._format_float(segment_data["overall_score"]),
                "valid_flag": is_valid,
                "merged_into": "",
                "notes": notes
            })
        
        # Add merged segments
        all_merged_sources = set()
        for merge in merge_log:
            for source in merge.get("from", []):
                all_merged_sources.add(source)
        
        for source_segment in sorted(all_merged_sources):
            if source_segment in final_segments:
                continue
            
            destination = merged_to_map.get(source_segment, "")
            
            rows.append({
                "segment_id": "",
                "segment_name": source_segment,
                "rules_applied": SegmentScorer.generate_segment_rules(source_segment, percentiles),
                "size": segments.get(source_segment, {}).get("size", 0),
                "conversion_potential": SegmentScorer._format_float(
                    segments.get(source_segment, {}).get("conversion_potential", 0.0)
                ),
                "profitability": SegmentScorer._format_float(
                    segments.get(source_segment, {}).get("profitability", 0.0)
                ),
                "lift_vs_control": 0.0,
                "size_score": 0.0,
                "strategic_fit": 0.0,
                "overall_score": 0.0,
                "valid_flag": "No",
                "merged_into": destination,
                "notes": f"Merged into {destination}" if destination else "Merged"
            })
        
        return pd.DataFrame(rows), segment_id_map
    
    @staticmethod
    def create_user_segment_mapping(segments, universe_df, segment_id_map):
        user_to_segment = {}
        
        for segment_key, segment_data in segments.items():
            segment_id = segment_id_map.get(segment_key)
            for user_id in segment_data.get("users", []):
                user_to_segment[user_id] = {
                    "segment_id": segment_id,
                    "segment_name": segment_key
                }
        
        user_mapping = universe_df[["user_id"]].copy()
        user_mapping["segment_id"] = user_mapping["user_id"].map(
            lambda u: user_to_segment.get(u, {}).get("segment_id", "UNASSIGNED")
        )
        user_mapping["segment_name"] = user_mapping["user_id"].map(
            lambda u: user_to_segment.get(u, {}).get("segment_name", "UNASSIGNED")
        )
        
        return user_mapping
    
    @staticmethod
    def create_mece_report(start_date, end_date, universe_df, percentiles, segments, 
                          merge_log, split_log, min_size, max_size, user_mapping):
        
        merge_and_split_log = []
        merge_and_split_log.extend(merge_log or [])
        merge_and_split_log.extend(split_log or [])
        
        if not merge_and_split_log:
            merge_and_split_log = [{"note": "No merges or splits performed"}]
        
        duplicate_count = int(user_mapping["user_id"].duplicated().sum())
        total_assigned = int(user_mapping.shape[0])
        
        mece_report = {
            "window_start": str(start_date),
            "window_end": str(end_date),
            "universe_size": int(len(universe_df)),
            "min_segment_size": int(min_size),
            "max_segment_size": int(max_size),
            "percentiles": percentiles,
            "segment_counts": {k: int(v["size"]) for k, v in segments.items()},
            "merge_and_split_log": merge_and_split_log,
            "mece_validation": {
                "duplicate_users": duplicate_count,
                "exhaustiveness_check": bool(total_assigned == len(universe_df)),
                "total_users_assigned": total_assigned
            }
        }
        
        return mece_report
    
    @staticmethod
    def save_all_outputs(segments_summary, user_mapping, mece_report, output_dir):
        OutputGenerator.ensure_directory(output_dir)
        
        segments_summary.to_csv(
            os.path.join(output_dir, "segments_summary.csv"), 
            index=False
        )
        
        user_mapping.to_csv(
            os.path.join(output_dir, "user_segment_map.csv"), 
            index=False
        )
        
        with open(os.path.join(output_dir, "mece_report.json"), "w") as f:
            json.dump(mece_report, f, indent=2)
        
        return {
            "segments_summary_path": os.path.join(output_dir, "segments_summary.csv"),
            "user_mapping_path": os.path.join(output_dir, "user_segment_map.csv"),
            "mece_report_path": os.path.join(output_dir, "mece_report.json")
        }