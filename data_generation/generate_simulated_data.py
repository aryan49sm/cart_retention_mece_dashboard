#!/usr/bin/env python3
"""
generate_simulated_data_allow_null_lastorder.py

Reads a parameter-spec JSON
and produces:
 - simulated_cart_abandons.csv
 - generation_report.json

Usage:
    python generate_simulated_data.py param_spec.json --outdir ./output
"""
import json
import argparse
import os
import math
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def generate_from_spec(spec, outdir):
    seed = int(spec["meta"].get("seed", 42))
    np_rng = np.random.RandomState(seed)
    random.seed(seed)

    N = int(spec["meta"].get("N_total", 22000))
    first_time_rate = float(spec["meta"].get("first_time_rate", 0.12))

    # date mapping - default 30-day month mapping
    start_date = datetime(2025, 9, 1)
    days = list(range(1, 31))

    # day-level params
    base_mean = float(spec["day_level"].get("base_mean_per_day_value", max(1.0, N / 30.0)))
    weights = np.array(spec["day_level"]["daily_weights"]["weights"], dtype=float)
    tilt_coeff = float(spec["day_level"]["daily_weights"].get("seasonal_tilt_coefficient", 0.01))
    jitter_shape = float(spec["day_level"]["daily_weights"].get("jitter_gamma_shape", 5.0))
    jitter_scale = float(spec["day_level"]["daily_weights"].get("jitter_gamma_scale", 0.2))
    neg_bin_k = float(spec["day_level"]["daily_weights"].get("neg_bin_dispersion_k", 4.0))

    # expected counts with tilt and jitter
    tilt = np.array([tilt_coeff * (d - 15) for d in days])
    jitter = np_rng.gamma(shape=jitter_shape, scale=jitter_scale, size=len(days))
    expected = base_mean * weights * (1.0 + tilt) * jitter
    expected = np.clip(expected, 1.0, None)

    raw_counts = []
    for m in expected:
        g = np_rng.gamma(shape=neg_bin_k, scale=(m / neg_bin_k))
        c = np_rng.poisson(g)
        raw_counts.append(int(c))
    raw_counts = np.array(raw_counts, dtype=int)

    # scale to exact N_total
    sum_raw = int(raw_counts.sum())
    if sum_raw <= 0:
        raw_counts = np.full(len(days), int(round(N / len(days))), dtype=int)
        sum_raw = int(raw_counts.sum())

    scaled = raw_counts.astype(float) * (float(N) / float(sum_raw))
    floor_counts = np.floor(scaled).astype(int)
    remainder = N - int(floor_counts.sum())
    frac = scaled - np.floor(scaled)
    order = np.argsort(-frac)
    for idx in order[:remainder]:
        floor_counts[idx] += 1
    daily_counts = floor_counts
    assert int(daily_counts.sum()) == N, "Daily counts must sum to N_total"

    # classes
    classes_spec = spec["latent_classes"]["classes"]
    class_labels = [c["label"] for c in classes_spec]
    class_props = {c["label"]: float(c["proportion"]) for c in classes_spec}
    base_class_counts = {label: int(math.floor(class_props[label] * N)) for label in class_labels}
    diff = N - sum(base_class_counts.values())
    sorted_labels = sorted(class_labels, key=lambda l: -class_props[l])
    i = 0
    while diff > 0:
        base_class_counts[sorted_labels[i % len(sorted_labels)]] += 1
        diff -= 1
        i += 1

    # reserve special cohorts from classes
    # special cohorts come under spec['special_cohorts']['cohorts']
    special_cohorts_obj = spec.get("special_cohorts", {}) or {}
    cohorts_list = special_cohorts_obj.get("cohorts", []) or []
    reserved = {lbl: 0 for lbl in class_labels}
    for cohort in cohorts_list:
        assigned = cohort["assigned_class"]
        reserved[assigned] = reserved.get(assigned, 0) + int(cohort["count"])
    for lbl in class_labels:
        base_class_counts[lbl] = max(0, base_class_counts[lbl] - reserved.get(lbl, 0))

    # build class list and shuffle
    class_list = []
    for lbl, cnt in base_class_counts.items():
        class_list.extend([lbl] * cnt)
    for lbl in class_labels:
        class_list.extend([lbl] * reserved.get(lbl, 0))
    if len(class_list) != N:
        while len(class_list) < N:
            class_list.append(sorted_labels[-1])
        if len(class_list) > N:
            class_list = class_list[:N]
    np_rng.shuffle(class_list)

    # build rows
    rows = []
    uid_width = len(str(N))
    def uid(i): return f"U{str(i+1).zfill(uid_width)}"
    idx_counter = 0
    for day_idx, ccount in enumerate(daily_counts, start=1):
        date_str = (start_date + timedelta(days=day_idx - 1)).strftime("%Y-%m-%d")
        for _ in range(int(ccount)):
            rows.append({
                "user_id": uid(idx_counter),
                "cart_day_index": day_idx,
                "cart_abandoned_date": date_str,
                "class_label": class_list[idx_counter]
            })
            idx_counter += 1
    assert len(rows) == N
    df = pd.DataFrame(rows)

    # assign special cohort indices
    indices_by_class = {lbl: df.index[df["class_label"] == lbl].tolist() for lbl in class_labels}
    used_special_idx = set()
    special_detail_indices = []
    for cohort in cohorts_list:
        assigned = cohort["assigned_class"]
        kcount = int(cohort["count"])
        available = [i for i in indices_by_class[assigned] if i not in used_special_idx]
        if len(available) < kcount:
            chosen = list(np_rng.choice(indices_by_class[assigned], size=kcount, replace=True))
        else:
            chosen = list(np_rng.choice(available, size=kcount, replace=False))
        for ci in chosen:
            used_special_idx.add(ci)
        special_detail_indices.append({"cohort_id": cohort["id"], "indices": chosen})

    # numeric features
    class_param_map = {c["label"]: c for c in classes_spec}
    aov_arr = np.zeros(N, dtype=float)
    sess_arr = np.zeros(N, dtype=int)
    items_arr = np.zeros(N, dtype=int)
    for i in range(N):
        cl = df.at[i, "class_label"]
        params = class_param_map[cl]
        mu = float(params["AOV_log_space"]["mu"])
        sigma = float(params["AOV_log_space"]["sigma"])
        val = np_rng.lognormal(mean=mu, sigma=sigma)
        val = max(50.0, val)
        aov_arr[i] = val
        lam = float(params["sessions_poisson_lambda"])
        sess = int(np_rng.poisson(lam))
        sess_arr[i] = max(0, sess)
        items_arr[i] = max(1, int(np_rng.poisson(2.0)))

    # inject ties and outliers
    tie_info = spec.get("injections", {}).get("aov_tie_values", {})
    tie_vals = tie_info.get("values", [])
    tie_total = int(tie_info.get("count_total", 0))
    if tie_total > 0 and len(tie_vals) > 0:
        tie_indices = list(np_rng.choice(N, size=tie_total, replace=False))
        for j, idx in enumerate(tie_indices):
            aov_arr[idx] = float(tie_vals[j % len(tie_vals)])
    else:
        tie_indices = []

    outlier_count = int(spec.get("injections", {}).get("aov_outliers_count", 0))
    available_for_outliers = [i for i in range(N) if i not in set(tie_indices)]
    if outlier_count > 0:
        if len(available_for_outliers) >= outlier_count:
            outlier_indices = list(np_rng.choice(available_for_outliers, size=outlier_count, replace=False))
        else:
            outlier_indices = list(np_rng.choice(range(N), size=outlier_count, replace=False))
        for idx in outlier_indices:
            aov_arr[idx] = max(50.0, aov_arr[idx] * 10.0)
    else:
        outlier_indices = []

    # finalize AOV rounding & clamp
    aov_arr = np.round(aov_arr / 10.0) * 10.0
    aov_arr = np.clip(aov_arr, 50.0, None)

    aov_min = float(aov_arr.min())
    aov_max = float(aov_arr.max())
    aov_norm = np.zeros(N) if (aov_max - aov_min) <= 0 else (aov_arr - aov_min) / (aov_max - aov_min)

    # resample items with influence
    for i in range(N):
        extra = 1 if aov_norm[i] > 0.7 else 0
        items_arr[i] = max(1, int(np_rng.poisson(2.0)) + extra)
        if np_rng.rand() < 0.005:
            items_arr[i] += int(np_rng.poisson(6))

    # engagement (no missing)
    eng_base = np.zeros(N, dtype=float)
    for i in range(N):
        cl = df.at[i, "class_label"]
        beta_spec = class_param_map[cl].get("engagement_beta", {})
        a = float(beta_spec.get("alpha", 2.0))
        b = float(beta_spec.get("beta", 5.0))
        eng_base[i] = np_rng.beta(a, b)
    sess_mean = float(sess_arr.mean()) if N > 0 else 0.0
    sess_std = float(sess_arr.std(ddof=0)) if N > 0 else 0.0
    if sess_std <= 0:
        sess_norm = np.zeros(N)
    else:
        sess_norm = (sess_arr - sess_mean) / sess_std
        sess_norm = np.clip(sess_norm, -1.0, 1.0)
    engagement = eng_base + 0.12 * sess_norm + np_rng.normal(0, 0.03, size=N)
    engagement = np.clip(engagement, 0.0, 1.0)
    engagement = np.round(engagement, 3)

    # profitability (no missing)
    profit_mod_arr = np.array([float(class_param_map[df.at[i, "class_label"]]["class_profit_modifier"]) for i in range(N)])
    profitability = 0.15 + 0.7 * aov_norm + profit_mod_arr + np_rng.normal(0, 0.05, size=N)
    profitability = np.clip(profitability, 0.0, 1.0)
    profitability = np.round(profitability, 3)

    # inverted low-profit-high-AOV ~0.5%
    invert_count = max(1, int(round(0.005 * N)))
    high_aov_indices = np.where(aov_norm > 0.8)[0]
    if len(high_aov_indices) >= invert_count:
        invert_idxs = list(np_rng.choice(high_aov_indices, size=invert_count, replace=False))
    else:
        invert_idxs = list(np_rng.choice(range(N), size=invert_count, replace=False))
    for idx in invert_idxs:
        profitability[idx] = float(round(max(0.02, np_rng.uniform(0.05, 0.25)), 3))

    # build overrides map for cohorts by id
    cohort_overrides = {c.get("id"): c.get("overrides", {}) for c in cohorts_list}
    # apply special cohort overrides
    for cohort in special_detail_indices:
        cid = cohort["cohort_id"]
        indices = cohort["indices"]
        overrides = cohort_overrides.get(cid, {})
        if cid == "VIP_LowEng_LowProf":
            # apply specified engagement_beta and profitability_range if present
            eb = overrides.get("engagement_beta", {"alpha": 1.0, "beta": 8.0})
            pr = overrides.get("profitability_range", [0.05, 0.30])
            a = float(eb.get("alpha", 1.0))
            b = float(eb.get("beta", 8.0))
            lo, hi = float(pr[0]), float(pr[1])
            for idx in indices:
                engagement[idx] = float(round(np_rng.beta(a, b), 3))
                profitability[idx] = float(round(np_rng.uniform(lo, hi), 3))
        elif cid == "Dormant_HighAOV":
            # sample AOV from override AOV_log_space if provided; also adjust engagement if override present
            aov_space = overrides.get("AOV_log_space")
            eb = overrides.get("engagement_beta", {"alpha": 1.0, "beta": 8.0})
            a = float(eb.get("alpha", 1.0))
            b = float(eb.get("beta", 8.0))
            for idx in indices:
                if aov_space:
                    mu = float(aov_space.get("mu", 6.5))
                    sigma = float(aov_space.get("sigma", 0.6))
                else:
                    mu = float(class_param_map["VIP"]["AOV_log_space"]["mu"])  # fallback
                    sigma = float(class_param_map["VIP"]["AOV_log_space"]["sigma"])  # fallback
                val = np_rng.lognormal(mu, sigma)
                val = max(50.0, val)
                val = float(round(val / 10.0) * 10.0)
                aov_arr[idx] = val
                engagement[idx] = float(round(np_rng.beta(a, b), 3))
        elif cid == "Regional_Niche":
            # Slightly higher AOV bias; region assignment handled later
            for idx in indices:
                aov_arr[idx] = float(round((aov_arr[idx] * 1.2) / 10.0) * 10.0)

    # recompute AOV_norm & profitability if changed
    aov_min = float(aov_arr.min())
    aov_max = float(aov_arr.max())
    aov_norm = np.zeros(N) if (aov_max - aov_min) <= 0 else (aov_arr - aov_min) / (aov_max - aov_min)
    for i in range(N):
        profitability[i] = 0.15 + 0.7 * aov_norm[i] + float(class_param_map[df.at[i, "class_label"]]["class_profit_modifier"]) + np_rng.normal(0, 0.05)
    profitability = np.clip(profitability, 0.0, 1.0)
    profitability = np.round(profitability, 3)
    for cohort in special_detail_indices:
        if cohort["cohort_id"] == "VIP_LowEng_LowProf":
            pr = cohort_overrides.get("VIP_LowEng_LowProf", {}).get("profitability_range", [0.05, 0.30])
            lo, hi = float(pr[0]), float(pr[1])
            for idx in cohort["indices"]:
                profitability[idx] = float(round(np_rng.uniform(lo, hi), 3))

    # last_order_date: allow NULL only for first-time users (first_time_rate)
    lod_list = [None] * N
    first_time_flags = [False] * N
    for i in range(N):
        if np_rng.rand() < first_time_rate:
            # first-time customer -> last_order_date = None
            first_time_flags[i] = True
            lod_list[i] = None
        else:
            r = np_rng.rand()
            if r < 0.50:
                days_before = int(np_rng.randint(1, 91))
            elif r < 0.80:
                days_before = int(np_rng.randint(91, 366))
            else:
                days_before = int(np_rng.randint(366, 721))
            cart_date = datetime.strptime(df.at[i, "cart_abandoned_date"], "%Y-%m-%d")
            lod_dt = cart_date - timedelta(days=days_before)
            lod_list[i] = lod_dt.strftime("%Y-%m-%d")

    # regions
    region_list = ["RegionA", "RegionB", "RegionC", "RegionD", "RegionE"]
    region_probs = [0.4, 0.25, 0.18, 0.12, 0.05]
    region_assign = list(np_rng.choice(region_list, size=N, p=region_probs))
    for cohort in special_detail_indices:
        if cohort["cohort_id"] == "Regional_Niche":
            for idx in cohort["indices"]:
                region_assign[idx] = "NicheRegionX"

    # compose dataframe
    df["avg_order_value"] = np.round(aov_arr, 2)
    df["sessions_last_30d"] = sess_arr.astype(int)
    df["num_cart_items"] = items_arr.astype(int)
    df["engagement_score"] = [float(x) for x in engagement]
    df["profitability_score"] = [float(x) for x in profitability]
    df["last_order_date"] = lod_list
    df["region"] = region_assign

    out_cols = spec["meta"].get("output_columns", [
        "user_id", "cart_abandoned_date", "last_order_date", "avg_order_value",
        "sessions_last_30d", "num_cart_items", "engagement_score", "profitability_score",
        "class_label", "region"
    ])
    for c in out_cols:
        if c not in df.columns:
            df[c] = None
    df_out = df[out_cols].copy()

    # ensure engagement & profitability rounded neatly
    df_out["engagement_score"] = df_out["engagement_score"].apply(lambda x: float(round(x, 3)))
    df_out["profitability_score"] = df_out["profitability_score"].apply(lambda x: float(round(x, 3)))

    # build report
    missing_last_order_count = int(sum(1 for v in lod_list if v is None))
    report = {
        "seed": int(seed),
        "N_total": int(N),
        "daily_counts": {str(i+1): int(c) for i, c in enumerate(daily_counts)},
        "class_counts": {lbl: int((df_out['class_label'] == lbl).sum()) for lbl in class_labels},
        "special_cohort_counts": {c["cohort_id"]: len(c["indices"]) for c in special_detail_indices},
        "injected_outlier_user_ids": [df_out.at[idx, "user_id"] for idx in outlier_indices] if outlier_indices else [],
        "injected_tie_values_counts": {str(val): int((df_out["avg_order_value"] == val).sum()) for val in tie_vals} if tie_vals else {},
        "missing_value_counts": {
            "engagement_score": 0,
            "profitability_score": 0,
            "last_order_date": int(missing_last_order_count)
        },
        "first_time_customer_count": int(missing_last_order_count),
        "percentiles": {
            "AOV_p20": float(df_out["avg_order_value"].quantile(0.20)),
            "AOV_p50": float(df_out["avg_order_value"].quantile(0.50)),
            "AOV_p80": float(df_out["avg_order_value"].quantile(0.80)),
            "eng_p50": float(df_out["engagement_score"].quantile(0.50)),
            "prof_p50": float(df_out["profitability_score"].quantile(0.50))
        },
        "special_details_sample_ids": {c["cohort_id"]: [df_out.at[idx, "user_id"] for idx in c["indices"][:5]] for c in special_detail_indices}
    }

    # save outputs
    ensure_dir(outdir)
    csv_path = os.path.join(outdir, "simulated_cart_abandons.csv")
    report_path = os.path.join(outdir, "generation_report.json")
    df_out.to_csv(csv_path, index=False)
    with open(report_path, "w") as fh:
        json.dump(report, fh, indent=2)

    summary = {
        "csv_path": csv_path,
        "report_path": report_path,
        "rows_written": int(len(df_out)),
        "class_counts": report["class_counts"],
        "daily_counts_sum": int(sum(daily_counts)),
        "first_time_customers": int(missing_last_order_count)
    }
    return summary

def main():
    parser = argparse.ArgumentParser(description="Generate simulated cart-abandon dataset (last_order_date NULL for first-time users only).")
    parser.add_argument("spec", help="Path to parameter-spec JSON file")
    parser.add_argument("--outdir", default=".", help="Output directory for CSV and report JSON")
    args = parser.parse_args()

    if not os.path.exists(args.spec):
        raise FileNotFoundError(f"Spec JSON not found: {args.spec}")

    with open(args.spec, "r") as f:
        spec = json.load(f)

    print("Generating dataset (last_order_date NULL allowed for first-time users) using spec:", args.spec)
    summary = generate_from_spec(spec, args.outdir)
    print("Wrote CSV to:", summary["csv_path"])
    print("Wrote report to:", summary["report_path"])
    print("Rows written:", summary["rows_written"])
    print("Daily counts sum:", summary["daily_counts_sum"])
    print("Class counts:", summary["class_counts"])
    print("First-time customers (last_order_date NULL):", summary["first_time_customers"])

if __name__ == "__main__":
    main()
