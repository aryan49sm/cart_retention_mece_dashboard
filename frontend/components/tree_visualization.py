import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import pandas as pd
from datetime import datetime

def create_segmentation_tree(output_directory):
    """
    Create an interactive tree visualization of the segmentation process.
    
    Args:
        output_directory (str): Path to the output directory containing results
    """
    
    try:
        # Get absolute path to project root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
        project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
        csv_path = os.path.join(project_root, output_directory, "segments_summary.csv")
        
        if not os.path.exists(csv_path):
            st.error("Segments data not found")
            return
        
        df = pd.read_csv(csv_path)
        active_segments = df[df['segment_id'] != ''].copy()
        
        if len(active_segments) == 0:
            st.warning("No active segments to visualize")
            return
        
        st.subheader("🌳 Segmentation Decision Tree")
        
        # Create the tree structure
        fig = create_decision_tree_plotly(active_segments)
        st.plotly_chart(fig, use_container_width=True)
        
        # Add segment flow diagram
        st.markdown("---")
        create_segment_flow_diagram(active_segments)
        
    except Exception as e:
        st.error(f"Error creating tree visualization: {str(e)}")

def create_decision_tree_plotly(segments_df):
    """
    Create a Plotly decision tree visualization.
    
    Args:
        segments_df (pd.DataFrame): DataFrame with segment information
    
    Returns:
        plotly.graph_objects.Figure: The tree visualization
    """
    
    # Define the hierarchical structure (AOV -> Engagement -> Profitability)
    # We'll create a simplified tree based on segment names
    
    nodes = []
    edges = []
    node_colors = []
    node_sizes = []
    node_text = []
    
    # Root node
    nodes.append((0, 0))  # (x, y)
    node_text.append("All Users<br>Cart Abandoners")
    node_colors.append("lightblue")
    node_sizes.append(50)
    
    # Parse segment names to build tree structure
    # Assuming segment names follow pattern: "High AOV, High Engagement, High Profitability"
    
    # Create AOV level (level 1)
    aov_levels = ["High AOV", "Medium AOV", "Low AOV"]
    aov_positions = [(-2, -1), (0, -1), (2, -1)]
    
    for i, (aov, pos) in enumerate(zip(aov_levels, aov_positions)):
        nodes.append(pos)
        node_text.append(f"{aov}<br>Branch")
        node_colors.append("lightgreen")
        node_sizes.append(40)
        
        # Add edge from root
        edges.append(((0, 0), pos))
    
    # Create Engagement level (level 2) 
    engagement_levels = ["High Engagement", "Medium Engagement", "Low Engagement"]
    eng_base_y = -2
    
    for i, aov_pos in enumerate(aov_positions):
        for j, eng in enumerate(engagement_levels):
            x_offset = -0.8 + (j * 0.8)
            pos = (aov_pos[0] + x_offset, eng_base_y)
            nodes.append(pos)
            node_text.append(f"{eng}<br>Sub-branch")
            node_colors.append("lightyellow")
            node_sizes.append(30)
            
            # Add edge from AOV level
            edges.append((aov_pos, pos))
    
    # Add actual segments at the bottom (level 3)
    segment_y = -3
    segments_added = 0
    
    for idx, segment in segments_df.iterrows():
        if segments_added >= 15:  # Limit to prevent overcrowding
            break
            
        x_pos = -4 + (segments_added * 0.6)
        pos = (x_pos, segment_y)
        nodes.append(pos)
        
        # Format segment info
        segment_info = f"{segment['segment_name']}<br>"
        segment_info += f"Size: {segment['size']:,}<br>"
        segment_info += f"Score: {segment['overall_score']:.3f}"
        
        node_text.append(segment_info)
        
        # Color based on score
        score = segment['overall_score']
        if score >= 0.7:
            color = "green"
        elif score >= 0.4:
            color = "orange"
        else:
            color = "red"
        
        node_colors.append(color)
        node_sizes.append(25 + (score * 25))  # Size based on score
        
        # Connect to a parent node (simplified connection)
        parent_idx = 1 + (segments_added % 3)  # Connect to AOV level nodes
        if parent_idx < len(nodes) - 1:
            edges.append((nodes[parent_idx], pos))
        
        segments_added += 1
    
    # Create the plot
    fig = go.Figure()
    
    # Add edges
    for edge in edges:
        fig.add_trace(go.Scatter(
            x=[edge[0][0], edge[1][0]],
            y=[edge[0][1], edge[1][1]],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add nodes
    x_coords = [node[0] for node in nodes]
    y_coords = [node[1] for node in nodes]
    
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='black')
        ),
        text=node_text,
        textposition="middle center",
        textfont=dict(size=10),
        showlegend=False,
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Segmentation Decision Tree",
        showlegend=False,
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

def create_segment_flow_diagram(segments_df):
    """
    Create a flow diagram showing segment distribution and performance.
    
    Args:
        segments_df (pd.DataFrame): DataFrame with segment information
    """
    
    st.subheader("📊 Segment Performance Flow")
    
    # Create a horizontal bar chart showing segment sizes and scores
    fig = go.Figure()
    
    # Sort segments by size
    segments_sorted = segments_df.sort_values('size', ascending=True)
    
    # Add bar for segment sizes
    fig.add_trace(go.Bar(
        y=segments_sorted['segment_name'],
        x=segments_sorted['size'],
        name='Segment Size',
        orientation='h',
        marker_color='lightblue',
        text=segments_sorted['size'].apply(lambda x: f"{x:,}"),
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title="Segment Size Distribution",
        xaxis_title="Number of Users",
        yaxis_title="Segments",
        height=max(400, len(segments_sorted) * 40),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Score comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: Size vs Score
        fig_scatter = px.scatter(
            segments_df,
            x='size',
            y='overall_score',
            size='conversion_potential',
            color='profitability',
            hover_name='segment_name',
            title="Segment Size vs Overall Score",
            color_continuous_scale='RdYlGn'
        )
        fig_scatter.update_xaxis(title="Segment Size")
        fig_scatter.update_yaxis(title="Overall Score")
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Box plot of scores
        fig_box = go.Figure()
        
        fig_box.add_trace(go.Box(
            y=segments_df['overall_score'],
            name='Overall Score',
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8
        ))
        
        fig_box.update_layout(
            title="Score Distribution",
            yaxis_title="Overall Score"
        )
        st.plotly_chart(fig_box, use_container_width=True)

def create_merge_process_animation(output_directory):
    """
    Create an animated visualization showing the merge process.
    
    Args:
        output_directory (str): Path to the output directory
    """
    
    st.subheader("🔄 Merge Process Visualization")
    
    try:
        # Get absolute path to project root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
        project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
        csv_path = os.path.join(project_root, output_directory, "segments_summary.csv")
        
        df = pd.read_csv(csv_path)
        
        active_segments = df[df['segment_id'] != '']
        merged_segments = df[df['segment_id'] == '']
        
        if len(merged_segments) == 0:
            st.info("No segments were merged in this analysis")
            return
        
        # Create before/after comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Before Merging:**")
            # Show original count (estimated)
            total_original = len(active_segments) + len(merged_segments)
            st.metric("Original Segments", total_original)
            
            # List merged segments
            if len(merged_segments) > 0:
                st.write("**Segments that were merged:**")
                for _, segment in merged_segments.iterrows():
                    st.write(f"• {segment['segment_name']} ({segment['size']:,} users)")
                    if pd.notna(segment['merged_into']):
                        st.write(f"  → Merged into: {segment['merged_into']}")
        
        with col2:
            st.write("**After Merging:**")
            st.metric("Final Segments", len(active_segments))
            st.metric("Segments Merged", len(merged_segments))
            
            # Calculate efficiency gain
            efficiency = (len(merged_segments) / total_original) * 100
            st.metric("Optimization", f"{efficiency:.1f}%")
        
        # Sankey diagram for merge flow
        if len(merged_segments) > 0:
            create_merge_sankey(active_segments, merged_segments)
    
    except Exception as e:
        st.error(f"Error creating merge visualization: {str(e)}")

def create_merge_sankey(active_segments, merged_segments):
    """
    Create a Sankey diagram showing the merge flow.
    
    Args:
        active_segments (pd.DataFrame): Active segments
        merged_segments (pd.DataFrame): Merged segments
    """
    
    try:
        # Prepare data for Sankey
        source = []
        target = []
        value = []
        labels = []
        
        # Add all segment names to labels
        all_segments = list(merged_segments['segment_name']) + list(active_segments['segment_name'])
        unique_targets = merged_segments['merged_into'].dropna().unique()
        
        labels = all_segments + [f"{target} (Final)" for target in unique_targets]
        
        # Create flows
        for _, merged in merged_segments.iterrows():
            if pd.notna(merged['merged_into']):
                source_idx = labels.index(merged['segment_name'])
                target_name = f"{merged['merged_into']} (Final)"
                
                if target_name in labels:
                    target_idx = labels.index(target_name)
                    source.append(source_idx)
                    target.append(target_idx)
                    value.append(merged['size'])
        
        if source:  # Only create if we have data
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels,
                    color="blue"
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value
                )
            )])
            
            fig.update_layout(
                title_text="Segment Merge Flow",
                font_size=10,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Could not create Sankey diagram: {str(e)}")