#!/usr/bin/env python3

import pandas as pd
import numpy as np
import math


class SegmentOptimizer:
    
    @staticmethod
    def merge_small_segments(segments, universe_df, min_size):
        segments = dict(segments)
        merge_log = []
        universe_idx = universe_df.set_index("user_id")
        
        while True:
            small_segments = [
                k for k, v in segments.items() 
                if v["size"] < min_size and k != "Other_ELSE_ELSE"
            ]
            
            if not small_segments:
                break
            
            merged_any = False
            for segment_key in sorted(small_segments):
                if segment_key not in segments:
                    continue
                
                parts = segment_key.split("_")
                if len(parts) < 3:
                    continue
                
                aov_part, eng_part, prof_part = parts[0], parts[1], parts[2]
                
                if prof_part in ("HighProf", "LowProf"):
                    # Try merging with profitability sibling
                    sibling_prof = "LowProf" if prof_part == "HighProf" else "HighProf"
                    sibling_key = f"{aov_part}_{eng_part}_{sibling_prof}"
                    parent_key = f"{aov_part}_{eng_part}_ELSE"
                    
                    sources = [k for k in [segment_key, sibling_key] if k in segments]
                    before_counts = {s: segments[s]["size"] for s in sources}
                    
                    segments = SegmentOptimizer._merge_segments(segments, parent_key, sources)
                    merge_log.append({
                        "action": "merge_profit_sibling",
                        "from": sources,
                        "from_counts": before_counts,
                        "to": parent_key,
                        "to_count": segments[parent_key]["size"]
                    })
                    merged_any = True
                    
                elif prof_part == "ELSE" and eng_part != "ELSE":
                    # Merge to AOV parent
                    parent_key = f"{aov_part}_ELSE_ELSE"
                    sources = [k for k in segments.keys() if k.startswith(f"{aov_part}_")]
                    before_counts = {s: segments[s]["size"] for s in sources}
                    
                    segments = SegmentOptimizer._merge_segments(segments, parent_key, sources)
                    merge_log.append({
                        "action": "merge_to_aov_parent",
                        "from": sources,
                        "from_counts": before_counts,
                        "to": parent_key,
                        "to_count": segments[parent_key]["size"]
                    })
                    merged_any = True
                    
                elif eng_part == "ELSE" and aov_part != "Other":
                    # Merge to global other
                    parent_key = "Other_ELSE_ELSE"
                    sources = [k for k in segments.keys() if k.startswith(f"{aov_part}_")]
                    before_counts = {s: segments[s]["size"] for s in sources}
                    
                    segments = SegmentOptimizer._merge_segments(segments, parent_key, sources)
                    merge_log.append({
                        "action": "merge_to_global_other",
                        "from": sources,
                        "from_counts": before_counts,
                        "to": parent_key,
                        "to_count": segments[parent_key]["size"]
                    })
                    merged_any = True
                    
                else:
                    # Fallback to global other
                    parent_key = "Other_ELSE_ELSE"
                    sources = [segment_key]
                    before_counts = {s: segments[s]["size"] for s in sources}
                    
                    segments = SegmentOptimizer._merge_segments(segments, parent_key, sources)
                    merge_log.append({
                        "action": "merge_fallback_to_global",
                        "from": sources,
                        "from_counts": before_counts,
                        "to": parent_key,
                        "to_count": segments[parent_key]["size"]
                    })
                    merged_any = True
                
                if merged_any:
                    segments = SegmentOptimizer._recompute_stats(segments, universe_idx)
                    break
            
            if not merged_any:
                break
        
        return segments, merge_log
    
    @staticmethod
    def split_large_segments(segments, universe_df, max_size):
        new_segments = {}
        split_log = []
        universe_idx = universe_df.set_index("user_id")
        
        for segment_key, segment_data in segments.items():
            size = segment_data.get("size", 0)
            
            if size <= max_size or size == 0:
                new_segments[segment_key] = segment_data
                continue
            
            users = segment_data["users"]
            user_data = universe_idx.loc[users]
            
            # Determine number of splits needed
            num_splits = int(math.ceil(size / float(max_size)))
            
            # Check if we can split by sessions
            unique_sessions = user_data["sessions_last_30d"].nunique()
            
            if unique_sessions <= 1:
                # Split by index
                chunks = [
                    users[i:i+max_size] 
                    for i in range(0, len(users), max_size)
                ]
                created_segments = []
                
                for idx, user_list in enumerate(chunks, start=1):
                    new_key = f"{segment_key}_SPLIT_{idx}"
                    new_segments[new_key] = {
                        "users": user_list,
                        "size": len(user_list),
                        "conversion_potential": 0.0,
                        "profitability": 0.0,
                        "avg_order_value": 0.0
                    }
                    created_segments.append(new_key)
                
                split_log.append({
                    "action": "split_by_index",
                    "original": segment_key,
                    "created": created_segments,
                    "counts": [new_segments[x]["size"] for x in created_segments]
                })
            else:
                # Split by sessions quantiles
                quantiles = [i / float(num_splits) for i in range(1, num_splits)]
                cut_values = np.quantile(
                    user_data["sessions_last_30d"].values, quantiles
                ) if quantiles else []
                
                buckets = [[] for _ in range(num_splits)]
                
                for user_id in users:
                    sessions = user_data.at[user_id, "sessions_last_30d"]
                    bucket_idx = 0
                    
                    for idx, cut_val in enumerate(cut_values):
                        if sessions <= cut_val:
                            bucket_idx = idx
                            break
                        bucket_idx = idx + 1
                    
                    buckets[bucket_idx].append(user_id)
                
                created_segments = []
                for idx, user_list in enumerate(buckets, start=1):
                    new_key = f"{segment_key}_SPLIT_Q{idx}"
                    new_segments[new_key] = {
                        "users": user_list,
                        "size": len(user_list),
                        "conversion_potential": 0.0,
                        "profitability": 0.0,
                        "avg_order_value": 0.0
                    }
                    created_segments.append(new_key)
                
                split_log.append({
                    "action": "split_by_sessions_quantile",
                    "original": segment_key,
                    "created": created_segments,
                    "counts": [new_segments[x]["size"] for x in created_segments]
                })
        
        new_segments = SegmentOptimizer._recompute_stats(new_segments, universe_idx)
        return new_segments, split_log
    
    @staticmethod
    def _merge_segments(segments, destination_key, source_keys):
        merged_users = []
        
        for key in source_keys:
            if key in segments:
                merged_users.extend(segments[key]["users"])
                if key != destination_key:
                    segments.pop(key, None)
        
        segments[destination_key] = {
            "users": merged_users,
            "size": len(merged_users),
            "conversion_potential": 0.0,
            "profitability": 0.0,
            "avg_order_value": 0.0
        }
        
        return segments
    
    @staticmethod
    def _recompute_stats(segments, universe_idx):
        for segment_key, segment_data in segments.items():
            users = segment_data.get("users", [])
            
            if not users:
                segment_data.update({
                    "size": 0, "conversion_potential": 0.0,
                    "profitability": 0.0, "avg_order_value": 0.0
                })
                continue
            
            user_subset = universe_idx.loc[users]
            segment_data.update({
                "size": len(user_subset),
                "conversion_potential": float(user_subset["conversion_potential"].mean()),
                "profitability": float(user_subset["profitability_score"].mean()),
                "avg_order_value": float(user_subset["avg_order_value"].mean())
            })
        
        return segments