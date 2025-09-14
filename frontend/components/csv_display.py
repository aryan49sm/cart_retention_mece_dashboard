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
        
        # Display summary metrics
        total_segments = len(df[df['segment_id'] != ''])
        total_users = df[df['segment_id'] != '']['size'].sum()
        avg_score = df[df['segment_id'] != '']['overall_score'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Segments", total_segments)
        with col2:
            st.metric("Total Users", f"{total_users:,}")
        with col3:
            st.metric("Avg Overall Score", f"{avg_score:.3f}")
        
        st.markdown("---")
        
        # Separate active and merged segments
        # Active segments have valid segment_id (not empty/null)
        active_segments = df[
            (df['segment_id'].notna()) & 
            (df['segment_id'] != '') & 
            (df['segment_id'].str.strip() != '')
        ].copy()
        
        # Merged segments have empty segment_id
        merged_segments = df[
            (df['segment_id'].isna()) | 
            (df['segment_id'] == '') | 
            (df['segment_id'].str.strip() == '')
        ].copy()
        
        # Display active segments
        st.subheader("🎯 Active Segments")
        
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
        
        # Display merged segments if any
        if len(merged_segments) > 0:
            st.markdown("---")
            st.subheader("🔀 Merged Segments")
            st.caption("These segments were merged due to size constraints")
            
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
        
        # Segment performance visualization
        if len(active_segments) > 0:
            st.markdown("---")
            st.subheader("📊 Segment Performance Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Size distribution
                import plotly.express as px
                
                size_data = active_segments['size'].astype(int)
                segment_names = active_segments['segment_name']
                
                fig_size = px.bar(
                    x=segment_names,
                    y=size_data,
                    title="Segment Size Distribution",
                    labels={'x': 'Segment', 'y': 'Number of Users'}
                )
                fig_size.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_size, use_container_width=True)
            
            with col2:
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
                    st.info("✅ Enhanced with class_label and region data from main dataset")
                else:
                    st.info("📄 Displaying basic segment distribution (class_label and region not available)")
            except Exception as e:
                st.warning(f"Could not load enhanced data: {str(e)}")
                enhanced_df = df.copy()
        
        st.subheader("👥 User Distribution Summary")
        
        # Basic segment distribution
        segment_distribution = enhanced_df['segment_name'].value_counts()
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Segment Distribution", "🏷️ Class Labels", "🌍 Regional Analysis"])
        
        with tab1:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Segment Distribution:**")
                for segment, count in segment_distribution.head(10).items():
                    percentage = (count / len(enhanced_df)) * 100
                    st.write(f"• {segment}: {count:,} users ({percentage:.1f}%)")
            
            with col2:
                # Pie chart of segment distribution
                import plotly.express as px
                
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
                st.markdown("**Segment vs Class Label Analysis:**")
                
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
                st.markdown("**Segment vs Region Analysis:**")
                
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