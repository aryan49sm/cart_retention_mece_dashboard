import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import math

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
        
        st.subheader("🌳 Interactive Segmentation Decision Tree")
        
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["🌳 Decision Tree", "📊 Performance Matrix", "🔄 Segment Flow"])
        
        with tab1:
            fig = create_modern_decision_tree(active_segments)
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            create_performance_matrix(active_segments)
            
        with tab3:
            create_segment_flow_visualization(active_segments)
        
    except Exception as e:
        st.error(f"Error creating tree visualization: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def create_modern_decision_tree(segments_df):
    """
    Create a modern, beautiful decision tree visualization.
    
    Args:
        segments_df (pd.DataFrame): DataFrame with segment information
    
    Returns:
        plotly.graph_objects.Figure: The tree visualization
    """
    
    # Parse segment rules to understand the decision criteria
    segments_data = []
    
    for idx, segment in segments_df.iterrows():
        segment_info = {
            'id': segment['segment_id'],
            'name': segment['segment_name'],
            'size': segment['size'],
            'score': segment['overall_score'],
            'conversion_potential': segment.get('conversion_potential', 0.5),
            'profitability': segment.get('profitability', 0.5),
            'rules': segment.get('segment_rules', '')
        }
        segments_data.append(segment_info)
    
    # Create tree layout
    fig = go.Figure()
    
    # Define color palette
    colors = {
        'high': '#2E8B57',      # Sea Green
        'medium': '#FF8C00',    # Dark Orange  
        'low': '#DC143C',       # Crimson
        'root': '#4169E1',      # Royal Blue
        'branch': '#9370DB'     # Medium Purple
    }
    
    # Root node
    fig.add_trace(go.Scatter(
        x=[0], y=[4],
        mode='markers+text',
        marker=dict(size=80, color=colors['root'], 
                   line=dict(width=3, color='white'),
                   symbol='circle'),
        text=['Cart Abandoners<br>Universe'],
        textposition="middle center",
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate='<b>Cart Abandoners Universe</b><br>' +
                     f'Total Users: {segments_df["size"].sum():,}<br>' +
                     '<extra></extra>'
    ))
    
    # Level 1: AOV Branches
    aov_branches = ['High AOV', 'Medium AOV', 'Low AOV']
    aov_positions = [(-3, 2.5), (0, 2.5), (3, 2.5)]
    aov_colors = [colors['high'], colors['medium'], colors['low']]
    
    for i, (branch, pos, color) in enumerate(zip(aov_branches, aov_positions, aov_colors)):
        # Add branch node
        fig.add_trace(go.Scatter(
            x=[pos[0]], y=[pos[1]],
            mode='markers+text',
            marker=dict(size=60, color=color,
                       line=dict(width=2, color='white'),
                       symbol='diamond'),
            text=[f'{branch}<br>Branch'],
            textposition="middle center", 
            textfont=dict(size=10, color='white', family='Arial'),
            showlegend=False,
            hovertemplate=f'<b>{branch} Branch</b><br>' +
                         'Decision Node<br>' +
                         '<extra></extra>'
        ))
        
        # Add connecting line from root
        fig.add_trace(go.Scatter(
            x=[0, pos[0]], y=[4, pos[1]],
            mode='lines',
            line=dict(color='#708090', width=3, dash='solid'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Level 2: Segment Leaves
    num_segments = len(segments_data)
    if num_segments > 0:
        # Distribute segments across the width
        segment_width = 8  # Total width for segments
        segment_spacing = segment_width / max(num_segments - 1, 1) if num_segments > 1 else 0
        start_x = -segment_width / 2
        
        for i, segment in enumerate(segments_data):
            x_pos = start_x + (i * segment_spacing)
            y_pos = 1
            
            # Color based on overall score
            score = segment['score']
            if score >= 0.7:
                color = colors['high']
                label = 'High Performer'
            elif score >= 0.4:
                color = colors['medium'] 
                label = 'Medium Performer'
            else:
                color = colors['low']
                label = 'Low Performer'
            
            # Size based on segment size (normalized)
            max_size = max([s['size'] for s in segments_data])
            normalized_size = 30 + (segment['size'] / max_size) * 40
            
            # Add segment node
            fig.add_trace(go.Scatter(
                x=[x_pos], y=[y_pos],
                mode='markers+text',
                marker=dict(size=normalized_size, color=color,
                           line=dict(width=2, color='white'),
                           symbol='hexagon'),
                text=[f"{segment['id']}<br>{segment['size']:,}"],
                textposition="middle center",
                textfont=dict(size=8, color='white', family='Arial'),
                showlegend=False,
                hovertemplate=f"<b>{segment['name']}</b><br>" +
                             f"ID: {segment['id']}<br>" +
                             f"Size: {segment['size']:,} users<br>" +
                             f"Score: {segment['score']:.3f}<br>" +
                             f"Performance: {label}<br>" +
                             f"<extra></extra>"
            ))
            
            # Connect to appropriate AOV branch (simplified logic)
            parent_idx = i % 3  # Distribute across 3 AOV branches
            parent_pos = aov_positions[parent_idx]
            
            fig.add_trace(go.Scatter(
                x=[parent_pos[0], x_pos], y=[parent_pos[1], y_pos],
                mode='lines',
                line=dict(color='#B0C4DE', width=2, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add legend manually using annotations
    fig.add_annotation(
        x=0.02, y=0.98,
        xref="paper", yref="paper",
        text="<b>Performance Levels:</b><br>" +
             "<span style='color:#2E8B57'>●</span> High (0.7+)<br>" +
             "<span style='color:#FF8C00'>●</span> Medium (0.4-0.7)<br>" +
             "<span style='color:#DC143C'>●</span> Low (<0.4)",
        showarrow=False,
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=10)
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Segmentation Decision Tree - Interactive View",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'family': 'Arial Black'}
        },
        showlegend=False,
        height=700,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-5, 5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 5]),
        plot_bgcolor='rgba(248,249,250,0.8)',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_performance_matrix(segments_df):
    """
    Create a performance matrix visualization showing segment relationships.
    
    Args:
        segments_df (pd.DataFrame): DataFrame with segment information
    """
    
    st.subheader("📊 Segment Performance Matrix")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: Size vs Score
        fig_scatter = px.scatter(
            segments_df,
            x='size',
            y='overall_score',
            size='conversion_potential' if 'conversion_potential' in segments_df.columns else 'size',
            color='profitability' if 'profitability' in segments_df.columns else 'overall_score',
            hover_name='segment_name',
            title="Segment Size vs Performance Score",
            color_continuous_scale='RdYlGn',
            labels={
                'size': 'Segment Size (Users)',
                'overall_score': 'Overall Performance Score'
            }
        )
        
        fig_scatter.update_layout(
            height=400,
            xaxis_title="Segment Size (Users)",
            yaxis_title="Overall Performance Score",
            plot_bgcolor='rgba(248,249,250,0.8)'
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Performance distribution
        fig_dist = go.Figure()
        
        # Add histogram
        fig_dist.add_trace(go.Histogram(
            x=segments_df['overall_score'],
            nbinsx=10,
            marker_color='rgba(55, 83, 109, 0.7)',
            marker_line=dict(color='white', width=2),
            name='Score Distribution'
        ))
        
        fig_dist.update_layout(
            title="Performance Score Distribution",
            xaxis_title="Overall Score",
            yaxis_title="Number of Segments",
            height=400,
            plot_bgcolor='rgba(248,249,250,0.8)',
            showlegend=False
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # Segment comparison table
    st.subheader("📋 Segment Performance Comparison")
    
    # Create a styled dataframe
    display_df = segments_df[['segment_id', 'segment_name', 'size', 'overall_score']].copy()
    display_df['size'] = display_df['size'].apply(lambda x: f"{x:,}")
    display_df['overall_score'] = display_df['overall_score'].apply(lambda x: f"{x:.3f}")
    display_df.columns = ['Segment ID', 'Segment Name', 'Size', 'Score']
    
    st.dataframe(display_df, use_container_width=True)

def create_segment_flow_visualization(segments_df):
    """
    Create a flow visualization showing segment progression and relationships.
    
    Args:
        segments_df (pd.DataFrame): DataFrame with segment information
    """
    
    st.subheader("🔄 Segment Flow & Progression")
    
    # Create a waterfall-style chart showing segment sizes
    segments_sorted = segments_df.sort_values('overall_score', ascending=False)
    
    fig = go.Figure()
    
    # Create cumulative flow
    cumulative_size = 0
    colors = ['#2E8B57', '#32CD32', '#FFD700', '#FF8C00', '#FF6347', '#DC143C']
    
    for i, (idx, segment) in enumerate(segments_sorted.iterrows()):
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Bar(
            x=[segment['segment_id']],
            y=[segment['size']],
            name=f"{segment['segment_id']} ({segment['size']:,})",
            marker_color=color,
            text=f"{segment['size']:,}",
            textposition='auto',
            hovertemplate=f"<b>{segment['segment_name']}</b><br>" +
                         f"Size: {segment['size']:,}<br>" +
                         f"Score: {segment['overall_score']:.3f}<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Segment Size Distribution (Ranked by Performance)",
        xaxis_title="Segment ID",
        yaxis_title="Number of Users",
        height=500,
        plot_bgcolor='rgba(248,249,250,0.8)',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Flow metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = segments_df['size'].sum()
        st.metric("Total Users", f"{total_users:,}")
    
    with col2:
        avg_score = segments_df['overall_score'].mean()
        st.metric("Avg Score", f"{avg_score:.3f}")
    
    with col3:
        top_segment = segments_sorted.iloc[0]
        st.metric("Top Segment", f"{top_segment['segment_id']}")
    
    with col4:
        score_range = segments_df['overall_score'].max() - segments_df['overall_score'].min()
        st.metric("Score Range", f"{score_range:.3f}")

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
        
        st.write(f"**Active Segments:** {len(active_segments)}")
        st.write(f"**Merged Segments:** {len(merged_segments)}")
        
        # Show merge impact
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Active Segments")
            active_chart = px.bar(
                active_segments,
                x='segment_id',
                y='size',
                color='overall_score',
                title="Active Segment Sizes",
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(active_chart, use_container_width=True)
        
        with col2:
            st.subheader("Merged Segments")
            if len(merged_segments) > 0:
                merged_chart = px.bar(
                    merged_segments.head(10),  # Show top 10 merged
                    x=range(len(merged_segments.head(10))),
                    y='size',
                    title="Merged Segment Sizes (Top 10)",
                    color_discrete_sequence=['#FF6B6B']
                )
                merged_chart.update_layout(xaxis_title="Merged Segment Index")
                st.plotly_chart(merged_chart, use_container_width=True)
            else:
                st.info("No merged segments to display")
        
    except Exception as e:
        st.error(f"Error creating merge visualization: {str(e)}")

# Legacy function for backward compatibility
def create_segment_flow_diagram(segments_df):
    """Legacy function - redirects to new visualization"""
    create_segment_flow_visualization(segments_df)