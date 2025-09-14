import streamlit as st

def display_project_readme():
    """
    Display comprehensive project documentation covering data generation, 
    MECE segmentation methodology, and technical implementation details.
    """
    
    # Table of Contents
    st.markdown("""
    **Contents:**
    1. [Project Overview](#project-overview)
    2. [Synthetic Data Generation](#synthetic-data-generation)  
    3. [MECE Segmentation Framework](#mece-segmentation-framework)
    4. [Technical Architecture](#technical-architecture)
    5. [Scoring Methodology](#scoring-methodology)
    6. [Validation & Quality Assurance](#validation-quality-assurance)
    """)
    
    st.markdown("---")
    
    # 1. Project Overview
    st.header("1. Project Overview")
    
    st.markdown("""
    This project implements a **Mutually Exclusive, Collectively Exhaustive (MECE)** audience segmentation system 
    for cart abandoner retention campaigns. The solution addresses the core challenge of creating actionable, 
    non-overlapping customer segments that marketers can effectively target with personalized retention strategies.
    
    **Key Objectives:**
    - Generate realistic cart abandonment data with controlled variability
    - Create MECE-compliant segments using decision tree methodology
    - Implement multi-dimensional scoring for segment prioritization
    - Ensure segments meet practical size constraints for campaign execution
    - Provide comprehensive validation and reporting capabilities
    
    **Business Value:**
    The system enables marketing teams to efficiently allocate resources across distinct customer segments, 
    maximizing conversion potential while maintaining statistical significance for A/B testing and campaign measurement.
    """)
    
    # 2. Synthetic Data Generation
    st.header("2. Synthetic Data Generation")
    
    st.markdown("""
    The synthetic dataset simulates realistic cart abandonment patterns across a 30-day period, 
    generating approximately 22,000 user records with sophisticated behavioral modeling.
    """)
    
    # Data generation flowchart
    st.subheader("2.1 Data Generation Architecture")
    
    st.markdown("""
    **Data Generation Pipeline:**
    
    ```
    Parameter Spec → Daily Volume → Class Assignment → Feature Generation → Quality Check
                        │               │                    │                
                        │               ├── Casual (60%)     ├── AOV Dist     
                        │               ├── Regular (30%)    ├── Engagement   
                        │               ├── VIP (6%)         ├── Sessions     
                        │               └── Dormant (4%)     └── Recency      
                        │                                                     
                        ├── Seasonal patterns                                 
                        ├── Random jitter                                     
                        └── Spike events                                                    
    ```
    
    **Key Components:**
    - **Daily Distribution:** Seasonal patterns, random jitter, spike events
    - **Class Assignment:** Casual (60%), Regular (30%), VIP (6%), Dormant (4%)
    - **Feature Generation:** AOV distribution, engagement scoring, session patterns
    - **Special Cohorts:** VIP low engagement, dormant high AOV, regional niches
    """)
    
    st.subheader("2.2 Latent Class Modeling")
    
    st.markdown("""
    The data generation employs a **latent class mixture model** to create realistic user archetypes:
    
    **Casual Users (60% of population):**
    - Lower average order values (log-normal μ=4.0, σ=0.7)
    - Minimal engagement patterns (Beta α=2.0, β=5.0)
    - Infrequent site sessions (Poisson λ=1.8)
    - Represents price-sensitive, occasional shoppers
    
    **Regular Users (30% of population):**
    - Moderate purchasing behavior (log-normal μ=5.0, σ=0.6)
    - Balanced engagement levels (Beta α=3.0, β=3.5)
    - Consistent browsing patterns (Poisson λ=4.0)
    - Core customer base with predictable behavior
    
    **VIP Users (6% of population):**
    - High-value transactions (log-normal μ=6.7, σ=0.7)
    - Strong engagement signals (Beta α=4.0, β=2.0)
    - Frequent site interactions (Poisson λ=8.0)
    - Premium segment requiring specialized retention
    
    **Dormant Users (4% of population):**
    - Variable AOV with low recent activity (Poisson λ=0.6)
    - Declining engagement patterns (Beta α=1.2, β=6.0)
    - Represents at-risk customers requiring reactivation
    """)
    
    st.subheader("2.3 Temporal Dynamics & Seasonality")
    
    st.markdown("""
    **Daily Volume Modeling:**
    The system generates realistic daily abandonment patterns using a multi-stage process:
    
    ```python
    # 1. Base calculation with seasonal tilt and jitter
    tilt = 0.01 * (day_index - 15)  # Linear trend adjustment
    jitter = np_rng.gamma(shape=5.0, scale=0.2)  # Random variance
    expected_count = base_mean * daily_weight * (1.0 + tilt) * jitter
    
    # 2. Gamma-Poisson compound distribution for overdispersion
    gamma_rate = np_rng.gamma(shape=4.0, scale=expected_count/4.0)
    daily_count = np_rng.poisson(gamma_rate)
    
    # 3. Proportional scaling to exact N_total
    scaled_counts = raw_counts * (N_total / sum(raw_counts))
    final_counts = floor(scaled_counts) + fractional_remainder_allocation
    ```
    
    **Spike Event Days:**
    - **Major spikes:** Days 6, 15, 24 (weights: 3.0, 2.5, 2.2)
    - **Medium spikes:** Days 10, 18, 27 (weights: 1.6, 1.5, 1.5)  
    - **Low troughs:** Days 3, 12, 22 (weights: 0.35, 0.4, 0.5)
    
    **Validation Results:**
    This produces sliding 7-day windows with realistic variance (typically 3K-12K users per window 
    depending on spike inclusion).
    """)
    
    st.subheader("2.4 Feature Engineering & Realism")
    
    st.markdown("""
    **Engagement Score Computation:**
    ```python
    # Base engagement from class-specific Beta distribution
    engagement_base = np_rng.beta(class_alpha, class_beta)
    
    # Session influence calculation
    session_normalized = (sessions - session_mean) / session_std
    session_normalized = clamp(session_normalized, -1.0, 1.0)
    session_influence = 0.12 * session_normalized
    
    # Random noise component
    noise = np_rng.normal(0, 0.03)
    
    # Final engagement score
    engagement = clamp(engagement_base + session_influence + noise, 0.0, 1.0)
    engagement = round(engagement, 3)
    ```
    
    **Profitability Score Logic:**
    ```python
    # AOV normalization across entire dataset
    aov_normalized = (aov_value - aov_min) / (aov_max - aov_min)
    
    # Base profitability calculation
    base_profitability = 0.15 + (0.7 * aov_normalized) + class_profit_modifier
    noise = np_rng.normal(0, 0.05)
    
    # Final profitability score
    profitability = clamp(base_profitability + noise, 0.0, 1.0)
    profitability = round(profitability, 3)
    ```
    
    **Edge Case Injection (Exact Implementation):**
    - **Inverted Profiles:** 0.5% of users (high AOV but low profitability 0.05-0.25 range)
    - **AOV Ties:** Exact values at 4990, 9990, 19990 (500 users total)
    - **Outlier AOV:** 12 users with AOV multiplied by 10x their base value
    - **Special Cohorts:** VIP with low engagement, Dormant with high AOV, Regional niches
    """)
    
    # 3. MECE Segmentation Framework
    st.header("3. MECE Segmentation Framework")
    
    st.markdown("""
    The segmentation engine implements a **hierarchical decision tree** approach to ensure 
    Mutual Exclusivity and Collective Exhaustiveness while respecting business constraints.
    """)
    
    # MECE decision tree diagram
    st.subheader("3.1 Decision Tree Architecture")
    
    st.markdown("""
    **MECE Decision Tree Structure:**
    
    ```
                          All Cart Abandoners (N=10,000)
                                     │
                              AOV > p80 Threshold?
                             /                    \\
                        Yes /                      \\ No
                           /                        \\
                  [High AOV Segment]         AOV > p20 Threshold?
                                           /                    \\
                                      Yes /                      \\ No
                                         /                        \\
                            Engagement > p50?              Profitability > p50?
                             /           \\                  /               \\
                        Yes /             \\ No         Yes /                 \\ No
                           /               \\              /                   \\
                  [Medium AOV +       [Medium AOV +   [Low AOV +           [Low AOV +
                   High Engage]        Low Engage]     High Profit]         Low Profit]
    ```
    
    **Final Segments:**
    - **High AOV:** Premium users requiring immediate retention focus
    - **Medium AOV + High Engagement:** Core users with standard retention
    - **Medium AOV + Low Engagement:** At-risk users needing intervention
    - **Low AOV + High Profitability:** Price-sensitive users for discount campaigns
    - **Low AOV + Low Profitability:** Dormant users for re-engagement
    
    **Actual Threshold Logic:**
    - **High AOV:** avg_order_value > 80th percentile
    - **Medium AOV:** 20th percentile < avg_order_value ≤ 80th percentile  
    - **Low AOV:** avg_order_value ≤ 20th percentile
    - **High Engagement:** engagement_score > 50th percentile
    - **High Profitability:** profitability_score > 50th percentile
    
    **Size Validation:**
    Each leaf segment must meet fixed size constraints (500-20,000 users). Undersized segments are merged 
    according to the hierarchical merging strategy.
    """)
    
    st.subheader("3.2 Threshold Determination & Percentile-Based Splits")
    
    st.markdown("""
    **Dynamic Threshold Calculation:**
    Segmentation thresholds are computed at runtime using percentile-based splits on the current universe:
    
    - **AOV Splits:** 20th and 80th percentiles create three tiers (Low/Medium/High)
    - **Engagement Splits:** 50th percentile separates active from passive users  
    - **Profitability Splits:** 50th percentile identifies high-value prospects
    
    **Actual Decision Logic:**
    ```python
    # AOV Classification
    if value <= percentiles["AOV_p20"]:
        return "LowAOV"
    elif value > percentiles["AOV_p80"]:
        return "HighAOV"
    else:
        return "MidAOV"
    
    # Engagement Classification
    "HighEng" if engagement > percentiles["eng_p50"] else "LowEng"
    
    # Profitability Classification  
    "HighProf" if profitability > percentiles["prof_p50"] else "LowProf"
    ```
    
    **Threshold Stability:**
    - Uses NumPy percentile calculation with deterministic results
    - Boundary conditions handled with strict inequality (> vs ≤)
    - Three-tier AOV approach reflects marketing campaign economics
    """)
    
    st.subheader("3.3 Size Constraint Enforcement")
    
    st.markdown("""
    **Fixed Size Limits:**
    ```python
    min_size = 500  # Fixed minimum segment size
    max_size = 20000  # Fixed maximum segment size
    ```
    
    **Merging Strategy Implementation:**
    1. **Profitability Sibling Merging:** Combine HighProf/LowProf segments with same AOV/Engagement
    2. **Engagement Sibling Merging:** Combine HighEng/LowEng segments with same AOV
    3. **Parent Node Creation:** Merge into intermediate "ELSE" categories
    4. **Global Fallback:** Ultimate merge into "Other_ELSE_ELSE" bucket
    
    **Merge Logic Flow:**
    ```python
    while small_segments_exist:
        for undersized_segment in small_segments:
            try_profitability_sibling_merge()
            if still_undersized:
                try_engagement_sibling_merge()
            if still_undersized:
                merge_to_parent_or_global_other()
    ```
    """)
    
    # 4. Technical Architecture
    st.header("4. Technical Architecture")
    
    st.subheader("4.1 System Components")
    
    st.markdown("""
    **System Architecture Overview:**
    
    ```
    Data Layer:
    ├── Synthetic Data Generator
    ├── Parameter Specifications  
    └── Raw CSV Output
    
    Processing Engine:
    ├── Segmentation Engine
    ├── Segment Scorer
    ├── MECE Validator
    └── Size Optimizer
    
    Analytics Layer:
    ├── Performance Metrics
    ├── Merge Tracking
    └── Quality Reports
    
    Presentation Layer:
    ├── Streamlit Dashboard
    ├── Interactive Visualizations
    └── Export Capabilities
    ```
    
    **Data Flow:**
    Parameter Specs → Data Generation → Processing Engine → Analytics → Dashboard
    """)
    
    st.subheader("4.2 Processing Pipeline")
    
    st.markdown("""
    **Stage 1: Universe Definition**
    - Filter users with cart abandonment in specified 7-day window
    - Validate data completeness and quality
    - Compute universe-level statistics for threshold calculation
    
    **Stage 2: Segmentation Execution**
    - Apply hierarchical decision tree logic
    - Generate segment assignments with rule documentation
    - Track all decision paths and branching logic
    
    **Stage 3: Size Optimization**
    - Evaluate segments against minimum/maximum size constraints
    - Execute merging strategy for undersized segments
    - Maintain exhaustiveness throughout optimization process
    
    **Stage 4: Scoring & Ranking**
    - Compute multi-dimensional scores for each segment
    - Apply weighted aggregation for overall ranking
    - Generate performance metrics and business insights
    
    **Stage 5: Validation & Output**
    - Verify MECE compliance across all segments
    - Generate comprehensive audit reports
    - Export actionable segment definitions for marketing execution
    """)
    
    # 5. Scoring Methodology
    st.header("5. Scoring Methodology")
    
    st.markdown("""
    The scoring system evaluates segments across five critical business dimensions, 
    providing marketing teams with data-driven prioritization for campaign allocation.
    """)
    
    st.subheader("5.1 Multi-Dimensional Scoring Framework")
    
    scoring_table = """
    | Dimension | Weight | Formula | Business Rationale |
    |-----------|--------|---------|-------------------|
    | **Conversion Potential** | 30% | engagement × recency_factor | Primary success metric |
    | **Lift vs Control** | 25% | simulated campaign performance | Incremental value measurement |
    | **Profitability** | 20% | revenue potential per user | ROI optimization |
    | **Strategic Fit** | 15% | (profitability × 0.4) + (aov_norm × 0.6) | Long-term value alignment |
    | **Size Score** | 10% | normalized segment size | Campaign efficiency |
    """
    
    st.markdown(scoring_table)
    
    st.subheader("5.2 Conversion Potential Calculation")
    
    st.markdown("""
    ```python
    # Recency factor calculation
    recency_factor = ((7.0 - days_since_abandon) / 7.0).clip(lower=0.0)
    
    # Conversion potential 
    conversion_potential = engagement_score * recency_factor
    ```
    
    **Recency Logic:**
    - Days since cart abandonment: 0-6 days (7-day window)
    - Recent abandoners (day 0) get factor 1.0, older get proportionally less
    - Direct multiplication with engagement score (no percentile transformation)
    
    **Segment-Level Aggregation:**
    Individual user conversion scores are averaged within each segment to provide 
    representative segment-level conversion expectations.
    """)
    
    st.subheader("5.3 Strategic Fit & Lift Calculation")
    
    st.markdown("""
    **Strategic Fit Formula:**
    ```python
    # AOV normalization across universe
    aov_normalized = (segment_aov - universe_aov_min) / (universe_aov_max - universe_aov_min)
    
    # Strategic fit composite score
    strategic_fit = (profitability_score * 0.4) + (aov_normalized * 0.6)
    ```
    
    **Lift vs Control Formula:**
    ```python
    lift_vs_control = (conversion_potential * 0.6) + (profitability * 0.4)
    ```
    
    **Overall Score Calculation:**
    ```python
    WEIGHTS = {
        "conversion": 0.30,    # Primary success metric
        "lift": 0.25,          # Campaign performance improvement  
        "profitability": 0.20, # Revenue potential
        "strategic": 0.15,     # Long-term value alignment
        "size": 0.10           # Campaign efficiency
    }
    
    overall_score = (conversion_potential * 0.30) + 
                   (lift_vs_control * 0.25) + 
                   (profitability * 0.20) + 
                   (strategic_fit * 0.15) + 
                   (size_score * 0.10)
    ```
    
    All scores are clamped to [0.0, 1.0] range using max(0.0, min(1.0, value)).
    """)
    
    # 6. Validation & Quality Assurance
    st.header("6. Validation & Quality Assurance")
    
    st.subheader("6.1 Input Data Validation")
    
    st.markdown("""
    **Data Validator Implementation:**
    The system includes basic input validation through `DataValidator` class:
    
    ```python
    REQUIRED_COLUMNS = {
        "user_id", "cart_abandoned_date", "avg_order_value", 
        "sessions_last_30d", "num_cart_items", "engagement_score", 
        "profitability_score"
    }
    ```
    
    **Validation Checks:**
    - **Column Completeness:** Ensures all required columns are present
    - **Date Parsing:** Handles multiple date formats with fallback logic
    - **Window Validation:** Confirms 7-day window is exactly 6-day span
    - **Data Range:** Validates window falls within available data dates
    
    **Date Processing:**
    - Primary format attempt with `dayfirst=True`
    - Fallback parsing with `dayfirst=False` for failed dates
    - Null value handling for `last_order_date` (first-time customers)
    """)
    
    st.subheader("6.2 Segmentation Integrity")
    
    st.markdown("""
    **MECE Compliance by Design:**
    The decision tree structure ensures MECE compliance through:

    - **Exhaustive Coverage:** All 12 possible `AOV×Engagement×Profitability` combinations created
    - **Mutual Exclusivity:** Strict inequality thresholds prevent overlaps
    - **Size Enforcement:** Merging process maintains exhaustiveness while meeting size constraints
    
    **Boundary Handling:**
    ```python
    # AOV classification with clear boundaries
    if value <= percentiles["AOV_p20"]:        # Low AOV
    elif value > percentiles["AOV_p80"]:       # High AOV  
    else:                                      # Medium AOV
    ```
    
    **Merge Audit Trail:**
    - Complete logging of all merge operations in `merge_log`
    - Original segment definitions preserved in output
    - Rationale tracking for size-based merges
    """)
    
    st.subheader("6.3 Reproducibility & Determinism")
    
    st.markdown("""
    **Controlled Randomness:**
    - Fixed random seed (42) in data generation for reproducible datasets
    - Deterministic percentile calculations using NumPy defaults
    - Consistent sort ordering in segment processing
    
    **Parameter Specifications:**
    - JSON-based parameter control in `param_spec.json`
    - Documented class distributions and feature relationships
    
    **Limitations:**
    The current implementation focuses on core segmentation logic rather than 
    extensive statistical validation. Future enhancements could include:
    - Automated MECE compliance testing
    - Segment size distribution analysis  
    - Cross-validation of scoring calculations
    - Campaign performance simulation
    """)
    
    # Conclusion
    st.markdown("---")
    st.header("Conclusion")
    
    st.markdown("""
    This segmentation system provides a practical tool for creating customer segments from cart abandonment data. 
    It uses a decision tree approach to ensure every customer gets placed in exactly one segment, making it easy 
    for marketing teams to target different groups with specific campaigns.
    
    **What This System Does Well:**
    - **Creates clear segments** that don't overlap with each other
    - **Provides actionable results** with specific campaign recommendations
    - **Uses simple logic** that's easy to understand and explain
    - **Handles size constraints** to ensure segments are big enough for campaigns
    - **Generates comprehensive reports** with all the details you need
    
    **Current Limitations:**
    - **Basic validation only** - focuses on core logic rather than extensive testing
    - **Single-threaded processing** - works well for typical datasets but not optimized for huge volumes
    - **Fixed scoring weights** - uses standard business assumptions rather than custom-tuned weights
    
    **Future Improvements:**
    - Add real data integration instead of just synthetic data
    - Include A/B testing capabilities to measure campaign performance
    - Add more flexible scoring and threshold options
    - Include automated campaign execution integrations
    """)

def show_readme_modal():
    """Show README content in a modal dialog"""
    
    # Back button to close README
    if st.button("← Back to Dashboard", key="readme_back_button", type="secondary"):
        st.session_state.show_readme = False
        st.rerun()
    
    st.markdown("---")
    
    # Display the full README content
    display_project_readme()