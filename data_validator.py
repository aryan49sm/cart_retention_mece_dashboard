#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DataValidator:
    REQUIRED_COLUMNS = {
        "user_id", "cart_abandoned_date", "avg_order_value", 
        "sessions_last_30d", "num_cart_items", "engagement_score", 
        "profitability_score"
    }
    
    @staticmethod
    def validate_input_file(filepath):
        try:
            df = pd.read_csv(filepath, dtype={"user_id": str})
        except Exception as e:
            raise ValueError(f"Failed to read input file: {e}")
        
        missing_cols = DataValidator.REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Input missing required columns: {missing_cols}")
        
        return df
    
    @staticmethod
    def parse_date_column(series, column_name, allow_na=True):
        parsed = pd.to_datetime(series, dayfirst=True, errors='coerce')
        mask_na = parsed.isna() & series.notna()
        
        if mask_na.any():
            parsed2 = pd.to_datetime(series[mask_na], dayfirst=False, errors='coerce')
            parsed.loc[mask_na] = parsed2
        
        if not allow_na:
            fail_mask = parsed.isna() & series.notna()
            if fail_mask.any():
                sample_vals = series[fail_mask].unique()[:5].tolist()
                raise ValueError(f"Failed to parse {column_name}: {sample_vals}")
        else:
            fail_mask = parsed.isna() & series.notna()
            if fail_mask.any():
                problematic = []
                for v in series[fail_mask].unique()[:5]:
                    s = str(v).strip()
                    if s and s.lower() not in ("nan", "none", "null"):
                        problematic.append(v)
                if problematic:
                    raise ValueError(f"Failed to parse {column_name}: {problematic}")
        
        return parsed
    
    @staticmethod
    def validate_date_window(start_date, end_date, data_min, data_max):
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        if (end_date - start_date).days != 6:
            raise ValueError("Window must be exactly 7 days (inclusive)")
        
        if start_date < data_min or end_date > data_max:
            raise ValueError(
                f"Window [{start_date} to {end_date}] outside data range "
                f"[{data_min} to {data_max}]"
            )
    
    @staticmethod
    def prepare_dataframe(df):
        df = df.copy()
        
        df["cart_abandoned_date"] = DataValidator.parse_date_column(
            df["cart_abandoned_date"], "cart_abandoned_date", allow_na=False
        )
        
        if "last_order_date" in df.columns:
            df["last_order_date"] = DataValidator.parse_date_column(
                df["last_order_date"], "last_order_date", allow_na=True
            )
        else:
            df["last_order_date"] = pd.NaT
        
        return df