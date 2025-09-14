#!/usr/bin/env python3

import pandas as pd
import numpy as np


class SegmentScorer:
    
    WEIGHTS = {
        "conversion": 0.30,
        "lift": 0.25,
        "profitability": 0.20,
        "size": 0.10,
        "strategic": 0.15
    }
    
    @staticmethod
    def compute_final_scores(segments, universe_df):
        universe_aov_min = float(universe_df["avg_order_value"].min())
        universe_aov_max = float(universe_df["avg_order_value"].max())
        
        segment_sizes = [v["size"] for v in segments.values()]
        size_min = min(segment_sizes) if segment_sizes else 0
        size_max = max(segment_sizes) if segment_sizes else 0
        
        scored_segments = {}
        
        for segment_key, segment_data in sorted(segments.items()):
            scored_segment = {
                "segment_name": segment_key,
                "size": segment_data["size"],
                "conversion_potential": float(segment_data["conversion_potential"]) if segment_data["size"] > 0 else 0.0,
                "profitability": float(segment_data["profitability"]) if segment_data["size"] > 0 else 0.0
            }
            
            # Compute AOV normalization
            if universe_aov_max > universe_aov_min and segment_data["size"] > 0:
                aov_norm = (segment_data["avg_order_value"] - universe_aov_min) / (universe_aov_max - universe_aov_min)
            else:
                aov_norm = 0.5
            
            # Compute size score
            if size_max != size_min:
                size_score = (segment_data["size"] - size_min) / (size_max - size_min)
            else:
                size_score = 0.5
            
            # Compute component scores
            lift_score = SegmentScorer._clamp01(
                scored_segment["conversion_potential"] * 0.6 + 
                scored_segment["profitability"] * 0.4
            )
            
            strategic_score = SegmentScorer._clamp01(
                0.4 * scored_segment["profitability"] + 0.6 * aov_norm
            )
            
            overall_score = SegmentScorer._clamp01(
                SegmentScorer.WEIGHTS["conversion"] * scored_segment["conversion_potential"] +
                SegmentScorer.WEIGHTS["lift"] * lift_score +
                SegmentScorer.WEIGHTS["profitability"] * scored_segment["profitability"] +
                SegmentScorer.WEIGHTS["size"] * size_score +
                SegmentScorer.WEIGHTS["strategic"] * strategic_score
            )
            
            scored_segment.update({
                "size_score": float(size_score),
                "lift_vs_control": float(lift_score),
                "strategic_fit": float(strategic_score),
                "overall_score": float(overall_score)
            })
            
            scored_segments[segment_key] = scored_segment
        
        return scored_segments
    
    @staticmethod
    def generate_segment_rules(segment_key, percentiles):
        base_key = segment_key
        split_suffix = ""
        
        if "_SPLIT_" in segment_key or "_SPLIT_Q" in segment_key:
            split_idx = segment_key.find("_SPLIT")
            base_key = segment_key[:split_idx]
            split_suffix = segment_key[split_idx+1:]
        
        parts = base_key.split("_")
        aov_part = parts[0] if len(parts) > 0 else "ELSE"
        eng_part = parts[1] if len(parts) > 1 else "ELSE"
        prof_part = parts[2] if len(parts) > 2 else "ELSE"
        
        # AOV rules
        if aov_part == "LowAOV":
            aov_rule = f"avg_order_value <= {percentiles['AOV_p20']:.2f}"
        elif aov_part == "HighAOV":
            aov_rule = f"avg_order_value > {percentiles['AOV_p80']:.2f}"
        elif aov_part == "MidAOV":
            aov_rule = f"{percentiles['AOV_p20']:.2f} < avg_order_value <= {percentiles['AOV_p80']:.2f}"
        else:
            aov_rule = "AOV: ELSE"
        
        # Engagement rules
        if eng_part == "HighEng":
            eng_rule = f"engagement_score > {percentiles['eng_p50']:.3f}"
        elif eng_part == "LowEng":
            eng_rule = f"engagement_score <= {percentiles['eng_p50']:.3f}"
        else:
            eng_rule = "Engagement: ELSE"
        
        # Profitability rules
        if prof_part == "HighProf":
            prof_rule = f"profitability_score > {percentiles['prof_p50']:.3f}"
        elif prof_part == "LowProf":
            prof_rule = f"profitability_score <= {percentiles['prof_p50']:.3f}"
        else:
            prof_rule = "Profitability: ELSE"
        
        rule = f"{aov_rule} & {eng_rule} & {prof_rule}"
        
        if split_suffix:
            rule = f"{rule} & split={split_suffix}"
        
        return rule
    
    @staticmethod
    def _clamp01(value):
        return float(max(0.0, min(1.0, float(value))))
    
    @staticmethod
    def _format_float(value, decimals=3):
        try:
            return round(float(value), decimals)
        except:
            return 0.0