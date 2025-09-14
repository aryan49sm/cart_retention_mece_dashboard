import plotly.express as px
import streamlit as st
import pandas as pd
import os

def display_segments_summary(output_directory):
    """
    Display the segments_summary.csv file in a formatted table.
    
    Args:
        output_directory (str): Path to the output directory containing segments_summary.csv
    """
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    csv_path = os.path.join(project_root, output_directory, "segments_summary.csv")
    
    if not os.path.exists(csv_path):
        st.error(f"Segments summary file not found: {csv_path}")
        return
    
    try:
        # Load the segments summary
        df = pd.read_csv(csv_path)
        
        # Filter active segments using consistent logic
        active_segments = df[
            (df['segment_id'].notna()) & 
            (df['segment_id'] != '') & 
            (df['segment_id'].str.strip() != '')
        ].copy()
        
        # Calculate metrics
        total_segments = len(active_segments)
        total_users = int(active_segments['size'].sum()) if len(active_segments) > 0 else 0
        avg_score = float(active_segments['overall_score'].mean()) if len(active_segments) > 0 else 0
        
        # Display key metrics in 3 columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Segments", total_segments)
        with col2:
            st.metric("Total Users", f"{total_users:,}")
        with col3:
            st.metric("Avg Score", f"{avg_score:.3f}")
        
        st.markdown("---")
        
        # Merged segments calculation for reference
        merged_segments = df[
            (df['segment_id'].isna()) | 
            (df['segment_id'] == '') | 
            (df['segment_id'].str.strip() == '')
        ].copy()
        
        # Display active segments
        st.subheader("Active Segments")
        
        # Expandable help section for Active Segments
        with st.expander("ℹ️ Column Explanations - Active Segments", expanded=False):
            st.markdown("""
            **Key Columns Overview:**
            
            • **segment_id**: Unique identifier (S001, S002, etc.) for operational segments  
            • **segment_name**: Descriptive name combining AOV, engagement, and profitability rules  
            • **rules_applied**: Specific business logic conditions defining this segment  
            • **size**: Number of users classified into this segment  
            
            **Performance Scores (0.0 - 1.0 scale):**
            
            • **conversion_potential**: Expected likelihood to convert (based on historical patterns)  
            • **profitability**: Revenue potential per user (calculated from AOV and margin data)  
            • **lift_vs_control**: Performance improvement over baseline/control group  
            • **size_score**: Segment size viability (larger segments score higher for campaign efficiency)  
            • **strategic_fit**: Alignment with business priorities and marketing capabilities  
            • **overall_score**: Weighted combination of all above metrics (primary ranking metric)  
            
            **Status & Metadata:**
            
            • **valid_flag**: "Yes" for active segments, "No" for merged ones  
            • **merged_into**: Shows target segment ID if this segment was consolidated (None for active segments)  
            • **notes**: Additional context about segment creation or merging decisions (None if no special notes)
            
            """)
        
        # Detailed formula explanations for numeric columns
        with st.expander("🧮 Detailed Calculation Formulas & Logic", expanded=False):
            st.markdown("""
            **Formula Documentation - Exact Implementation Details**
            
            **1. Conversion Potential (0.0 - 1.0)**
            ```
            Formula: engagement_score × recency_factor
            
            Where:
            • recency_factor = (7.0 - days_since_abandon) / 7.0, clipped to ≥ 0.0
            • engagement_score = original engagement score from dataset
            ```
            
            **Logic & Intuition:**
            - Combines user engagement patterns with cart abandonment recency
            - Recent abandoners (lower days_since_abandon) get higher recency_factor
            - Highly engaged users with recent abandons have highest conversion potential
            - Example: User with engagement=0.8, abandoned 2 days ago → (7-2)/7 = 0.714 → 0.8 × 0.714 = 0.571
            
            **2. Profitability (0.0 - 1.0)**
            ```
            Formula: Direct profitability_score from dataset (segment average)
            ```
            
            **Logic & Intuition:**
            - Uses pre-calculated profitability scores based on user behavior and AOV patterns
            - Represents expected revenue potential per user in the segment
            - Higher scores indicate users likely to generate more profit upon conversion
            
            **3. Lift vs Control (0.0 - 1.0)**
            ```
            Formula: (conversion_potential × 0.6) + (profitability × 0.4)
            
            Weights breakdown:
            • Conversion likelihood: 60% weight (primary factor)
            • Profitability impact: 40% weight (secondary factor)
            ```
            
            **Logic & Intuition:**
            - Estimates performance improvement over baseline/control group
            - Prioritizes conversion likelihood but considers profit impact
            - Segments with both high conversion and profitability score highest
            
            **4. Size Score (0.0 - 1.0)**
            ```
            Formula: (segment_size - min_size) / (max_size - min_size)
            
            Where:
            • min_size = smallest segment size across all segments
            • max_size = largest segment size across all segments
            ```
            
            **Logic & Intuition:**
            - Normalized segment size relative to all other segments
            - Larger segments score higher due to campaign efficiency benefits
            - Enables cost-effective marketing with better statistical significance
            - If all segments same size, defaults to 0.5
            
            **5. Strategic Fit (0.0 - 1.0)**
            ```
            Formula: (profitability × 0.4) + (aov_normalized × 0.6)
            
            Where:
            • aov_normalized = (segment_aov - universe_aov_min) / (universe_aov_max - universe_aov_min)
            • universe_aov_min/max = minimum/maximum AOV across entire dataset
            ```
            
            **Logic & Intuition:**
            - Measures alignment with business priorities and marketing capabilities
            - High-AOV segments score higher (60% weight) as they're strategically valuable
            - Profitability adds 40% weight to ensure revenue focus
            - Balances strategic value (AOV) with immediate profitability
            
            **6. Overall Score (0.0 - 1.0)**
            ```
            Formula: Weighted sum of all component scores
            
            overall_score = (conversion_potential × 0.30) +
                          (lift_vs_control × 0.25) +
                          (profitability × 0.20) +
                          (strategic_fit × 0.15) +
                          (size_score × 0.10)
            ```
            
            **Weight Rationale:**
            - **Conversion (30%)**: Primary business goal - getting users to convert
            - **Lift (25%)**: Performance improvement over baseline campaigns
            - **Profitability (20%)**: Revenue generation potential
            - **Strategic Fit (15%)**: Long-term business value alignment
            - **Size (10%)**: Campaign efficiency and statistical significance
            
            **Technical Notes:**
            - All values are clamped between 0.0 and 1.0 using max(0.0, min(1.0, value))
            - Segment-level scores are averages of individual user scores within each segment
            - Empty segments (size=0) default to 0.0 for all metrics
            """)
        
        if len(active_segments) > 0:
            # Format the dataframe for better display
            display_df = active_segments.copy()
            
            # Round numeric columns
            numeric_cols = ['conversion_potential', 'profitability', 'lift_vs_control', 
                          'size_score', 'strategic_fit', 'overall_score']
            for col in numeric_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(3)
            
            # Format size with commas
            display_df['size'] = display_df['size'].apply(lambda x: f"{x:,}")
            
            # Display dataframe without color coding
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Add download button
            csv_data = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Active Segments CSV",
                data=csv_data,
                file_name=f"active_segments_{output_directory.split('_')[-2]}_{output_directory.split('_')[-1]}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No active segments found")
        
        # Display merged segments if any - DISPLAY ONLY, not included in calculations
        if len(merged_segments) > 0:
            st.markdown("---")
            st.subheader("Merged Segments")
            st.caption("These segments were merged due to size constraints (not included in above metrics)")
            
            # Expandable help section for Merged Segments
            with st.expander("ℹ️ Column Explanations - Merged Segments", expanded=False):
                st.markdown("""
                **Why Segments Get Merged:**
                
                Segments with insufficient users (i.e., < 500) are automatically merged into larger, 
                related segments to ensure statistical significance and campaign viability.
                
                **Column Details:**
                
                • **segment_name**: Original segment name before merging  
                • **rules_applied**: The specific business logic that defined this segment  
                • **valid_flag**: Always "No" for merged segments (indicates inactive status)  
                • **merged_into**: Target segment ID where these users were consolidated  
                • **notes**: Explanation of merging decision and which segments were combined  
                
                **Understanding None Values:**
                
                • **merged_into**: Will be None only if segment wasn't merged (should not happen here)  
                • **notes**: Will be None if no additional context was needed for the merge decision            
                """)
            
            # Format merged segments - show only specified columns
            display_merged = merged_segments.copy()
            
            # Select only the required columns
            required_columns = ['segment_name', 'rules_applied', 'valid_flag', 'merged_into', 'notes']
            available_columns = [col for col in required_columns if col in display_merged.columns]
            
            if available_columns:
                display_merged_filtered = display_merged[available_columns]
                
                st.dataframe(
                    display_merged_filtered,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Required columns not found in merged segments data")
        
        # Segment performance visualization - ONLY for active segments
        if len(active_segments) > 0:
            st.markdown("---")
            st.subheader("Segment Performance Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Size distribution
                size_data = active_segments['size'].astype(int)
                segment_names = active_segments['segment_name']
                
                with st.expander("ℹ️ Segment Size Distribution", expanded=False):
                    st.markdown("""
                    This bar chart displays the number of users in each segment. Each bar represents a segment, with the height showing the total user count for that segment.
                    """)
                        
                fig_size = px.bar(
                    x=segment_names,
                    y=size_data,
                    title="Segment Size Distribution",
                    labels={'x': 'Segment', 'y': 'Number of Users'}
                )
                fig_size.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_size, use_container_width=True)
            
            with col2:
                
                with st.expander("ℹ️ Conversion Potential vs Profitability", expanded=False):
                    st.markdown("""
                    This scatter plot compares conversion potential (x-axis) against profitability (y-axis) for each segment. The bubble size represents the number of users in each segment, while the color indicates the overall performance score.
                    """)
                    
                # Score comparison
                fig_scores = px.scatter(
                    active_segments,
                    x='conversion_potential',
                    y='profitability',
                    size='size',
                    color='overall_score',
                    hover_name='segment_name',
                    title="Conversion Potential vs Profitability",
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_scores, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading segments summary: {str(e)}")

def display_user_segment_mapping(output_directory):
    """
    Display summary statistics from user_segment_map.csv with enhanced insights
    
    Args:
        output_directory (str): Path to the output directory containing user_segment_map.csv
    """
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    csv_path = os.path.join(project_root, output_directory, "user_segment_map.csv")
    
    if not os.path.exists(csv_path):
        st.warning(f"User segment mapping file not found: {csv_path}")
        return
    
    try:
        # Load user mapping
        df = pd.read_csv(csv_path)
        
        # Try to load the main data to get class_label and region information
        main_data_path = os.path.join(project_root, "output", "simulated_cart_abandons.csv")
        enhanced_df = df.copy()
        
        if os.path.exists(main_data_path):
            try:
                main_df = pd.read_csv(main_data_path)
                # Merge to get class_label and region
                if 'class_label' in main_df.columns and 'region' in main_df.columns:
                    enhanced_df = df.merge(
                        main_df[['user_id', 'class_label', 'region']], 
                        on='user_id', 
                        how='left'
                    )
                else:
                    st.info("Displaying basic segment distribution (class_label and region not available)")
            except Exception as e:
                st.warning(f"Could not load enhanced data: {str(e)}")
                enhanced_df = df.copy()
        
        st.subheader("User Distribution Summary")
        
        # Basic segment distribution
        segment_distribution = enhanced_df['segment_name'].value_counts()
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Segment Distribution", "Class Labels", "Regional Analysis"])
        
        with tab1:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Segment Distribution:**")
                for segment, count in segment_distribution.head(10).items():
                    percentage = (count / len(enhanced_df)) * 100
                    st.write(f"• {segment}: {count:,} users ({percentage:.1f}%)")
            
            with col2:
                # Expandable explanation for pie chart
                with st.expander("ℹ️ Understanding Pie Chart", expanded=False):
                    st.markdown("""
                    This pie chart displays the proportional distribution of users across different segments in your dataset. Each colored slice represents a segment, with the size of the slice corresponding to the number of users in that segment relative to the total user base.
                    """)
                
                # Pie chart of segment distribution
                fig_dist = px.pie(
                    values=segment_distribution.values,
                    names=segment_distribution.index,
                    title="User Distribution by Segment"
                )
                st.plotly_chart(fig_dist, use_container_width=True)
        
        with tab2:
            if 'class_label' in enhanced_df.columns:
                # Class label analysis
                class_distribution = enhanced_df['class_label'].value_counts()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Class Label Distribution:**")
                    for class_label, count in class_distribution.items():
                        percentage = (count / len(enhanced_df)) * 100
                        st.write(f"• {class_label}: {count:,} users ({percentage:.1f}%)")
                
                with col2:
                    # Expandable explanation for class label pie chart
                    with st.expander("ℹ️ Understanding Class Label Chart", expanded=False):
                        st.markdown("""
                        This pie chart shows the distribution of users by their original class labels from the source dataset. Each slice represents a different customer classification, helping you understand the composition of your cart abandoner dataset.
                        """)
                    
                    # Class label pie chart
                    fig_class = px.pie(
                        values=class_distribution.values,
                        names=class_distribution.index,
                        title="Distribution by Class Label",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_class, use_container_width=True)
                
                # Cross-analysis: Segments by Class Label
                st.markdown("---")
                
                # Expandable explanation for heatmap
                with st.expander("ℹ️ Understanding Segment vs Class Label Heatmap", expanded=False):
                    st.markdown("""
                    This heatmap displays the cross-tabulation between your new segments and original class labels. The color intensity indicates the number of users in each segment-class combination, with darker colors representing higher user counts.
                    """)
                
                cross_table = pd.crosstab(enhanced_df['segment_name'], enhanced_df['class_label'])
                
                # Heatmap
                fig_heatmap = px.imshow(
                    cross_table.values,
                    x=cross_table.columns,
                    y=cross_table.index,
                    title="Segment vs Class Label Heatmap",
                    labels=dict(x="Class Label", y="Segment", color="Count"),
                    text_auto=True
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
            else:
                st.info("Class label data not available for this analysis")
        
        with tab3:
            if 'region' in enhanced_df.columns:
                # Regional analysis
                region_distribution = enhanced_df['region'].value_counts()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Regional Distribution:**")
                    for region, count in region_distribution.items():
                        percentage = (count / len(enhanced_df)) * 100
                        st.write(f"• {region}: {count:,} users ({percentage:.1f}%)")
                
                with col2:
                    # Expandable explanation for regional bar chart
                    with st.expander("ℹ️ Understanding Regional Distribution", expanded=False):
                        st.markdown("""
                        This bar chart shows the geographical distribution of cart abandoners across different regions. Each bar represents a region, with the height indicating the number of users and the color intensity reflecting the user count.
                        """)
                    
                    # Regional bar chart
                    fig_region = px.bar(
                        x=region_distribution.index,
                        y=region_distribution.values,
                        title="Distribution by Region",
                        labels={'x': 'Region', 'y': 'Number of Users'},
                        color=region_distribution.values,
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_region, use_container_width=True)
                
                # Cross-analysis: Segments by Region
                st.markdown("---")
                
                # Expandable explanation for stacked bar chart
                with st.expander("ℹ️ Understanding Segment Distribution by Region", expanded=False):
                    st.markdown("""
                    This stacked bar chart displays how each segment is distributed across different regions. Each bar represents a region, and the colored segments within each bar show the proportion of different user segments in that region.
                    """)
                
                cross_table_region = pd.crosstab(enhanced_df['segment_name'], enhanced_df['region'])
                
                # Stacked bar chart
                fig_stacked = px.bar(
                    cross_table_region,
                    title="Segment Distribution by Region",
                    labels={'value': 'Number of Users', 'index': 'Segment'},
                    barmode='stack'
                )
                st.plotly_chart(fig_stacked, use_container_width=True)
                
            else:
                st.info("Regional data not available for this analysis")
        
        # Download options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Basic Segment Mapping"):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"user_segment_mapping_{output_directory.split('_')[-2]}_{output_directory.split('_')[-1]}.csv",
                    mime="text/csv",
                    key="download_basic_mapping"
                )
        
        with col2:
            if 'class_label' in enhanced_df.columns or 'region' in enhanced_df.columns:
                if st.button("📥 Download Enhanced Mapping"):
                    enhanced_csv_data = enhanced_df.to_csv(index=False)
                    st.download_button(
                        label="Download Enhanced CSV",
                        data=enhanced_csv_data,
                        file_name=f"enhanced_user_mapping_{output_directory.split('_')[-2]}_{output_directory.split('_')[-1]}.csv",
                        mime="text/csv",
                        key="download_enhanced_mapping"
                    )
        
    except Exception as e:
        st.error(f"Error loading user segment mapping: {str(e)}")