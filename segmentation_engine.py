#!/usr/bin/env python3

import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta


class SegmentationEngine:
    
    @staticmethod
    def compute_universe(df, start_date=None, end_date=None):
        if not np.issubdtype(df["cart_abandoned_date"].dtype, np.datetime64):
            df["cart_abandoned_date"] = pd.to_datetime(df["cart_abandoned_date"], errors='coerce')
        
        data_min = df["cart_abandoned_date"].min().date()
        data_max = df["cart_abandoned_date"].max().date()
        
        if end_date is None and start_date is None:
            end_date = data_max
            start_date = end_date - timedelta(days=6)
        elif end_date is not None and start_date is None:
            start_date = end_date - timedelta(days=6)
        elif end_date is None and start_date is not None:
            end_date = start_date + timedelta(days=6)
        
        from data_validator import DataValidator
        DataValidator.validate_date_window(start_date, end_date, data_min, data_max)
        
        df["days_since_abandon"] = (
            pd.to_datetime(end_date).date() - df["cart_abandoned_date"].dt.date
        ).apply(lambda d: d.days)
        
        universe = df[
            (df["days_since_abandon"] >= 0) & (df["days_since_abandon"] <= 6)
        ].copy()
        
        return universe, start_date, end_date
    
    @staticmethod
    def compute_percentiles(universe):
        return {
            "AOV_p20": float(np.percentile(universe["avg_order_value"], 20)),
            "AOV_p50": float(np.percentile(universe["avg_order_value"], 50)),
            "AOV_p80": float(np.percentile(universe["avg_order_value"], 80)),
            "eng_p50": float(np.percentile(universe["engagement_score"], 50)),
            "prof_p50": float(np.percentile(universe["profitability_score"], 50)),
        }
    
    @staticmethod
    def assign_decision_tree_bins(universe, percentiles):
        def aov_bin(value):
            if value <= percentiles["AOV_p20"]:
                return "LowAOV"
            elif value > percentiles["AOV_p80"]:
                return "HighAOV"
            else:
                return "MidAOV"
        
        universe["AOV_bin"] = universe["avg_order_value"].apply(aov_bin)
        universe["Eng_bin"] = np.where(
            universe["engagement_score"] > percentiles["eng_p50"], 
            "HighEng", "LowEng"
        )
        universe["Prof_bin"] = np.where(
            universe["profitability_score"] > percentiles["prof_p50"], 
            "HighProf", "LowProf"
        )
        universe["leaf_segment"] = (
            universe["AOV_bin"] + "_" + 
            universe["Eng_bin"] + "_" + 
            universe["Prof_bin"]
        )
        
        return universe
    
    @staticmethod
    def compute_conversion_scores(universe):
        universe["recency_factor"] = (
            (7.0 - universe["days_since_abandon"]) / 7.0
        ).clip(lower=0.0)
        universe["conversion_potential"] = (
            universe["engagement_score"] * universe["recency_factor"]
        )
        return universe
    
    @staticmethod
    def aggregate_segments(universe):
        segments = {}
        
        for leaf, group in universe.groupby("leaf_segment"):
            segments[leaf] = {
                "users": group["user_id"].tolist(),
                "size": len(group),
                "conversion_potential": float(group["conversion_potential"].mean()) if len(group) > 0 else 0.0,
                "profitability": float(group["profitability_score"].mean()) if len(group) > 0 else 0.0,
                "avg_order_value": float(group["avg_order_value"].mean()) if len(group) > 0 else 0.0
            }
        
        # Ensure all 12 possible combinations exist
        aov_bins = ["HighAOV", "MidAOV", "LowAOV"]
        eng_bins = ["HighEng", "LowEng"]
        prof_bins = ["HighProf", "LowProf"]
        
        for a in aov_bins:
            for e in eng_bins:
                for p in prof_bins:
                    key = f"{a}_{e}_{p}"
                    if key not in segments:
                        segments[key] = {
                            "users": [], "size": 0, "conversion_potential": 0.0,
                            "profitability": 0.0, "avg_order_value": 0.0
                        }
        
        return segments
    
    @staticmethod
    def determine_size_constraints(universe_size):
        # min_size = 500 if universe_size >= 10000 else max(50, int(0.005 * universe_size))
        # max_size = min(20000, int(0.4 * universe_size))
        min_size, max_size = 500, 20000
        return min_size, max_size