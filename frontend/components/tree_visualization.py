"""
Clean, modular tree visualization component for cart abandoner segmentation.
Contains only essential functions with standard Python practices.
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from pyvis.network import Network

class TreeVisualizationConfig:
    """Configuration constants for tree visualization."""
    
    # Canvas settings
    HEIGHT = "700px"
    WIDTH = "100%"
    BACKGROUND_COLOR = "#000000"  # Pure black background
    FONT_COLOR = "#ffffff"
    
    # Physics settings
    PHYSICS_OPTIONS = """
    var options = {
      "physics": {
        "enabled": true,
        "hierarchicalRepulsion": {
          "centralGravity": 0.4,
          "springLength": 120,
          "springConstant": 0.1,
          "nodeDistance": 180,
          "damping": 0.25
        },
        "maxVelocity": 15,
        "solver": "hierarchicalRepulsion",
        "stabilization": {"iterations": 80}
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "levelSeparation": 120,
          "nodeSpacing": 120,
          "treeSpacing": 150,
          "blockShifting": true,
          "edgeMinimization": true,
          "parentCentralization": true,
          "direction": "UD",
          "sortMethod": "directed"
        }
      },
      "nodes": {
        "borderWidth": 2,
        "shadow": {"enabled": true, "color": "rgba(0,0,0,0.3)", "size": 5},
        "font": {"size": 12, "face": "Arial Bold", "color": "#ffffff", "strokeWidth": 1, "strokeColor": "#000000"}
      },
      "edges": {
        "color": "#999999",
        "width": 2,
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}},
        "smooth": {"enabled": true, "type": "continuous", "roundness": 0.2}
      },
      "interaction": {"hover": true, "dragNodes": true, "zoomView": true}
    }
    """
    
    # Color scheme (updated for 5 levels)
    COLORS = {
        "root": "#e74c3c",
        "aov_high": "#16a085",  # Changed to teal to distinguish from purple profitability
        "aov_mid": "#3498db",
        "aov_low": "#f39c12",
        "engagement_high": "#f1c40f",
        "engagement_low": "#e67e22",
        "engagement_else": "#95a5a6",
        "profitability_high": "#9b59b6",
        "profitability_low": "#34495e",
        "profitability_else": "#7f8c8d",
        "active_segment": "#2ecc71",
        "merged_component": "#e91e63"
    }
    
    # Node sizes (updated for 5 levels)
    NODE_SIZES = {
        "root": 50,
        "aov": 40,
        "engagement": 35,
        "profitability": 30,
        "segment": 25
    }


class SegmentDataAnalyzer:
    """Handles analysis and categorization of segment data."""
    
    @staticmethod
    def load_segment_data(output_directory):
        """Load and validate segment data from CSV file."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            csv_path = os.path.join(project_root, output_directory, "segments_summary.csv")
            
            if not os.path.exists(csv_path):
                return None, None, f"Data file not found: {csv_path}"
            
            df = pd.read_csv(csv_path)
            active_segments = df[df['segment_id'] != ''].copy()
            merged_segments = df[df['segment_id'] == ''].copy()
            
            if len(active_segments) == 0:
                return None, None, "No active segments found in data"
            
            return active_segments, merged_segments, None
            
        except Exception as e:
            return None, None, f"Error loading data: {str(e)}"
    
    @staticmethod
    def load_mece_report(output_directory):
        """Load MECE report to get dynamic percentiles and thresholds."""
        try:
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            mece_path = os.path.join(project_root, output_directory, "mece_report.json")
            
            if not os.path.exists(mece_path):
                return None, f"MECE report not found: {mece_path}"
            
            with open(mece_path, 'r') as f:
                mece_data = json.load(f)
            
            return mece_data, None
            
        except Exception as e:
            return None, f"Error loading MECE report: {str(e)}"
    
    @staticmethod
    def get_dynamic_thresholds(mece_data):
        """Extract dynamic thresholds from MECE report."""
        percentiles = mece_data.get('percentiles', {})
        
        return {
            'aov_low_max': percentiles.get('AOV_p20', 50.0),
            'aov_high_min': percentiles.get('AOV_p80', 200.0),
            'engagement_threshold': percentiles.get('eng_p50', 0.303),
            'profitability_threshold': percentiles.get('prof_p50', 0.122)
        }
    
    @staticmethod
    def parse_segment_hierarchy(segment_name):
        """Parse segment name to extract AOV, Engagement, and Profitability info."""
        # Initialize with defaults
        aov_level = 'unknown'
        eng_level = 'unknown'
        prof_level = 'unknown'
        
        # Parse AOV
        if 'HighAOV' in segment_name:
            aov_level = 'high'
        elif 'MidAOV' in segment_name:
            aov_level = 'mid'
        elif 'LowAOV' in segment_name:
            aov_level = 'low'
        
        # Parse Engagement
        if 'HighEng' in segment_name:
            eng_level = 'high'
        elif 'LowEng' in segment_name:
            eng_level = 'low'
        elif '_ELSE' in segment_name:
            eng_level = 'else'  # Combined category
        
        # Parse Profitability
        if 'HighProf' in segment_name:
            prof_level = 'high'
        elif 'LowProf' in segment_name:
            prof_level = 'low'
        elif 'ELSE' in segment_name:
            prof_level = 'else'  # Combined category
        
        return aov_level, eng_level, prof_level
    
    @staticmethod
    def build_complete_hierarchy(active_segments, merged_segments):
        """Build complete 5-level hierarchy including merged segment details."""
        hierarchy = {}
        
        # Process active segments first
        for _, segment in active_segments.iterrows():
            segment_name = segment.get('segment_name', '')
            aov, eng, prof = SegmentDataAnalyzer.parse_segment_hierarchy(segment_name)
            
            # Build hierarchy path
            if aov not in hierarchy:
                hierarchy[aov] = {}
            if eng not in hierarchy[aov]:
                hierarchy[aov][eng] = {}
            if prof not in hierarchy[aov][eng]:
                hierarchy[aov][eng][prof] = {
                    'active_segments': [],
                    'merged_components': [],
                    'total_users': 0
                }
            
            hierarchy[aov][eng][prof]['active_segments'].append(segment)
            hierarchy[aov][eng][prof]['total_users'] += segment.get('size', 0)
            
            # Find which merged segments this active segment contains
            if pd.notna(segment.get('notes', '')):
                notes = segment.get('notes', '')
                if 'Created by merging:' in notes:
                    merged_list = notes.replace('Created by merging: ', '').split(', ')
                    hierarchy[aov][eng][prof]['merged_components'].extend(merged_list)
        
        # Add information about standalone merged segments
        for _, merged_seg in merged_segments.iterrows():
            segment_name = merged_seg.get('segment_name', '')
            aov, eng, prof = SegmentDataAnalyzer.parse_segment_hierarchy(segment_name)
            
            # These are the granular segments that were merged
            if aov in hierarchy and eng in hierarchy[aov] and prof in hierarchy[aov][eng]:
                continue  # Already processed as part of active segment
            
            # Create entry for merged-only segments
            if aov not in hierarchy:
                hierarchy[aov] = {}
            if eng not in hierarchy[aov]:
                hierarchy[aov][eng] = {}
            if prof not in hierarchy[aov][eng]:
                hierarchy[aov][eng][prof] = {
                    'active_segments': [],
                    'merged_components': [],
                    'total_users': 0
                }
            
            hierarchy[aov][eng][prof]['merged_components'].append(segment_name)
        
        return hierarchy


class PyVisTreeBuilder:
    """Handles PyVis network creation and configuration."""
    
    def __init__(self):
        self.config = TreeVisualizationConfig()
        self.analyzer = SegmentDataAnalyzer()
    
    def create_network(self):
        
        net = Network(
            height=self.config.HEIGHT,
            width=self.config.WIDTH,
            bgcolor=self.config.BACKGROUND_COLOR,
            font_color=self.config.FONT_COLOR,
            directed=True,
            layout=True
        )
        
        net.set_options(self.config.PHYSICS_OPTIONS)
        return net
    
    def add_root_node(self, net, total_users, active_count, merged_count):
        """Add root node to the network."""
        net.add_node(
            "root",
            label="Customer Universe",
            title=f"Total: {total_users:,} users\nActive: {active_count} segments\nMerged: {merged_count} segments",
            color=self.config.COLORS["root"],
            size=self.config.NODE_SIZES["root"],
            level=0,
            font={"size": 14, "bold": True}
        )
    
    def add_aov_nodes(self, net, aov_categories):
        """Add AOV branch nodes to the network."""
        for aov_type, aov_info in aov_categories.items():
            if aov_info['segment_count'] == 0:
                continue
                
            aov_id = f"{aov_type}_aov"
            net.add_node(
                aov_id,
                label=f"{aov_info['display_name']}\n{aov_info['user_count']:,} users",
                title=f"Range: {aov_info['range']}\nSegments: {aov_info['segment_count']}\nUsers: {aov_info['user_count']:,}",
                color=self.config.COLORS[f"aov_{aov_type}"],
                size=self.config.NODE_SIZES["aov"],
                level=1,
                font={"size": 12}
            )
            net.add_edge("root", aov_id, width=3)
    
    def add_engagement_nodes(self, net, aov_categories):
        """Add engagement nodes for each AOV category."""
        for aov_type, aov_info in aov_categories.items():
            if aov_info['segment_count'] == 0:
                continue
                
            aov_id = f"{aov_type}_aov"
            eng_categories = self.analyzer.categorize_by_engagement(aov_info['data'])
            
            for eng_type, eng_info in eng_categories.items():
                if eng_info['segment_count'] == 0:
                    continue
                    
                eng_id = f"{aov_id}_{eng_type}_eng"
                net.add_node(
                    eng_id,
                    label=f"{eng_info['display_name']}\n{eng_info['user_count']:,} users",
                    title=f"Engagement: {eng_type}\nSegments: {eng_info['segment_count']}\nUsers: {eng_info['user_count']:,}",
                    color=self.config.COLORS[f"engagement_{eng_type}"],
                    size=self.config.NODE_SIZES["engagement"],
                    level=2,
                    font={"size": 11}
                )
                net.add_edge(aov_id, eng_id, width=2)
                
                # Add individual segments
                self.add_segment_nodes(net, eng_id, eng_info['data'])
    
    def add_segment_nodes(self, net, parent_id, segments_df):
        """Add individual segment nodes."""
        for _, segment in segments_df.iterrows():
            seg_id = f"seg_{segment['segment_id']}"
            
            label = f"{segment['segment_id']}\n{segment['size']:,} users"
            title = f"Segment: {segment['segment_id']}\nUsers: {segment['size']:,}\nScore: {segment.get('overall_score', 0):.3f}"
            
            net.add_node(
                seg_id,
                label=label,
                title=title,
                color=self.config.COLORS["active_segment"],
                size=self.config.NODE_SIZES["segment"],
                level=3,
                font={"size": 10}
            )
            net.add_edge(parent_id, seg_id, width=1)
    
    def build_tree(self, output_directory):
        """Build complete 5-level tree visualization with proper hierarchy."""
        # Load data
        active_segments, merged_segments, error = self.analyzer.load_segment_data(output_directory)
        if error:
            return None, error
        
        # Load dynamic thresholds
        mece_data, mece_error = self.analyzer.load_mece_report(output_directory)
        if mece_error:
            # Use default values if MECE report unavailable
            thresholds = {
                'aov_low_max': 50.0,
                'aov_high_min': 200.0,
                'engagement_threshold': 0.303,
                'profitability_threshold': 0.122
            }
        else:
            thresholds = self.analyzer.get_dynamic_thresholds(mece_data)
        
        # Create network
        net = self.create_network()
        if not net:
            return None, "PyVis not available"
        
        # Build complete hierarchy
        hierarchy = self.analyzer.build_complete_hierarchy(active_segments, merged_segments)
        total_users = active_segments['size'].sum()
        
        # Add root node
        self.add_root_node(net, total_users, len(active_segments), len(merged_segments))
        
        # Build 5-level tree: Root → AOV → Engagement → Profitability → Segments
        for aov_type, aov_data in hierarchy.items():
            if aov_type == 'unknown':
                continue
                
            # Level 2: AOV nodes with dynamic ranges
            aov_id = f"{aov_type}_aov"
            aov_users = sum(
                sum(prof_data['total_users'] for prof_data in eng_data.values())
                for eng_data in aov_data.values()
            )
            
            aov_display = {'high': 'High AOV', 'mid': 'Medium AOV', 'low': 'Low AOV'}[aov_type]
            
            # Dynamic AOV ranges based on MECE report
            if aov_type == 'high':
                aov_range = f">${thresholds['aov_high_min']:.0f}+"
            elif aov_type == 'mid':
                aov_range = f"${thresholds['aov_low_max']:.0f}-${thresholds['aov_high_min']:.0f}"
            else:  # low
                aov_range = f"≤${thresholds['aov_low_max']:.0f}"
            
            net.add_node(
                aov_id,
                label=f"{aov_display}\n{aov_users:,} users",
                title=f"Range: {aov_range}\nTotal users: {aov_users:,}",
                color=self.config.COLORS[f"aov_{aov_type}"],
                size=self.config.NODE_SIZES["aov"],
                level=1,
                font={"size": 12}
            )
            net.add_edge("root", aov_id, width=3)
            
            # Level 3: Engagement nodes
            for eng_type, eng_data in aov_data.items():
                if eng_type == 'unknown':
                    continue
                    
                eng_id = f"{aov_id}_{eng_type}_eng"
                eng_users = sum(prof_data['total_users'] for prof_data in eng_data.values())
                
                if eng_users == 0:
                    continue
                
                eng_display = {
                    'high': 'High Engagement',
                    'low': 'Low Engagement', 
                    'else': 'Combined Engagement'
                }[eng_type]
                
                # Dynamic engagement threshold info
                if eng_type == 'high':
                    eng_threshold_info = f"Score >{thresholds['engagement_threshold']:.3f}"
                elif eng_type == 'low':
                    eng_threshold_info = f"Score ≤{thresholds['engagement_threshold']:.3f}"
                else:
                    eng_threshold_info = "Merged categories"
                
                net.add_node(
                    eng_id,
                    label=f"{eng_display}\n{eng_users:,} users",
                    title=f"Engagement: {eng_type}\nThreshold: {eng_threshold_info}\nUsers: {eng_users:,}",
                    color=self.config.COLORS[f"engagement_{eng_type}"],
                    size=self.config.NODE_SIZES["engagement"],
                    level=2,
                    font={"size": 11}
                )
                net.add_edge(aov_id, eng_id, width=2)
                
                # Level 4: Profitability nodes
                for prof_type, prof_data in eng_data.items():
                    if prof_type == 'unknown' or prof_data['total_users'] == 0:
                        continue
                        
                    prof_id = f"{eng_id}_{prof_type}_prof"
                    
                    prof_display = {
                        'high': 'High Profitability',
                        'low': 'Low Profitability',
                        'else': 'Combined Profitability'
                    }[prof_type]
                    
                    # Dynamic profitability threshold info
                    if prof_type == 'high':
                        prof_threshold_info = f"Score >{thresholds['profitability_threshold']:.3f}"
                    elif prof_type == 'low':
                        prof_threshold_info = f"Score ≤{thresholds['profitability_threshold']:.3f}"
                    else:
                        prof_threshold_info = "Merged categories"
                    
                    # Show merge information in title
                    merge_info = ""
                    if prof_data['merged_components']:
                        merge_info = f"\nContains: {', '.join(prof_data['merged_components'][:3])}{'...' if len(prof_data['merged_components']) > 3 else ''}"
                    
                    net.add_node(
                        prof_id,
                        label=f"{prof_display}\n{prof_data['total_users']:,} users",
                        title=f"Profitability: {prof_type}\nThreshold: {prof_threshold_info}\nUsers: {prof_data['total_users']:,}{merge_info}",
                        color=self.config.COLORS[f"profitability_{prof_type}"],
                        size=self.config.NODE_SIZES["profitability"],
                        level=3,
                        font={"size": 10}
                    )
                    net.add_edge(eng_id, prof_id, width=2)
                    
                    # Level 5: Individual active segments
                    for segment in prof_data['active_segments']:
                        seg_id = f"seg_{segment['segment_id']}"
                        
                        # Show if this segment contains merged components
                        merge_count = len(prof_data['merged_components'])
                        label = f"{segment['segment_id']}\n{segment['size']:,} users"
                        if merge_count > 0:
                            label += f"\n(+{merge_count} merged)"
                        
                        # Enhanced tooltip with proper segment name
                        title = f"Segment: {segment['segment_id']}\nName: {segment.get('segment_name', 'N/A')}\nUsers: {segment['size']:,}\nScore: {segment.get('overall_score', 0):.3f}"
                        if merge_count > 0:
                            title += f"\nContains {merge_count} merged segments"
                        
                        net.add_node(
                            seg_id,
                            label=label,
                            title=title,
                            color=self.config.COLORS["active_segment"],
                            size=self.config.NODE_SIZES["segment"],
                            level=4,
                            font={"size": 9}
                        )
                        net.add_edge(prof_id, seg_id, width=1)
        
        # Generate HTML and inject custom CSS to remove white padding
        html_content = net.generate_html()
        html_content = self.inject_custom_css(html_content)
        return html_content, None
    
    def inject_custom_css(self, html_content):
        """Inject custom CSS to remove white padding."""
        custom_css = """
        <style>
        body { 
            margin: 0 !important; 
            padding: 0 !important; 
            background-color: #000000 !important; 
            overflow: hidden !important; 
        }
        #mynetworkid { 
            border: none !important; 
            margin: 0 !important; 
            padding: 0 !important; 
        }
        </style>
        """
        # Inject CSS right after <head>
        html_content = html_content.replace('<head>', f'<head>{custom_css}')
        return html_content


def create_segmentation_tree(output_directory):
    """
    Main function to create the segmentation tree visualization.
    This is the only public interface used by the frontend.
    """
    # Load dynamic thresholds from MECE report
    analyzer = SegmentDataAnalyzer()
    mece_data, mece_error = analyzer.load_mece_report(output_directory)
    
    if mece_error:
        st.warning(f"Could not load dynamic thresholds from {output_directory}: {mece_error}. Using default values.")
    else:
        thresholds = analyzer.get_dynamic_thresholds(mece_data)
    # Business logic description with dynamic values in expandable section
    with st.expander("ℹ️ Understanding the 5-Level Decision Tree", expanded=False):
        st.markdown(f"""
        **Purpose**: This decision tree systematically segments cart abandoners using a data-driven 5-level hierarchy with thresholds dynamically loaded from MECE reports.
        
        **Dynamic Thresholds**: Values auto-update based on your dataset's percentiles:
        - AOV Low: ≤${thresholds['aov_low_max']:.0f} (20th percentile)
        - AOV High: >${thresholds['aov_high_min']:.0f} (80th percentile)  
        - Engagement: >{thresholds['engagement_threshold']:.3f} (50th percentile)
        - Profitability: >{thresholds['profitability_threshold']:.3f} (50th percentile)
        
        **Tree Structure**:
        - **Level 1: Customer Universe** - All cart abandoners in the dataset (root node)
        - **Level 2: AOV Segmentation** - Primary split by purchasing power:
          - High AOV: >${thresholds['aov_high_min']:.0f} (Premium customers with strong buying power)
          - Medium AOV: ${thresholds['aov_low_max']:.0f}-${thresholds['aov_high_min']:.0f} (Standard customers, core market)
          - Low AOV: ≤${thresholds['aov_low_max']:.0f} (Budget-conscious, volume-focused)
          - Combined: Merged categories for statistical significance
        - **Level 3: Engagement Classification** - Secondary split by user activity:
          - High Engagement: Score >{thresholds['engagement_threshold']:.3f} (Active users, frequent interactions)
          - Low Engagement: Score ≤{thresholds['engagement_threshold']:.3f} (Passive users, minimal activity)
          - Combined: Merged categories for statistical significance
        - **Level 4: Profitability Potential** - Tertiary split by revenue opportunity:
          - High Profitability: Score >{thresholds['profitability_threshold']:.3f} (High-margin customers)
          - Low Profitability: Score ≤{thresholds['profitability_threshold']:.3f} (Cost-sensitive strategies)
          - Combined: Merged for campaign efficiency
        - **Level 5: Final Segments** - Actionable segments with specific retention strategies
        
        **Interactive Features**:
        - **Drag**: Rearrange nodes by clicking and dragging
        - **Zoom**: Use mouse wheel or pinch gestures to zoom in/out
        - **Hover**: View detailed segment information and metrics
        - **Pan**: Click and drag empty space to navigate large trees
        
        **Business Value**: Each segment shows user counts, performance scores, and business rules to guide targeted marketing campaigns with optimal ROI.
        """)
    
    st.markdown("---")
    
    # Load and display tree (reuse analyzer from above)
    active_segments, merged_segments, error = analyzer.load_segment_data(output_directory)
    
    if error:
        st.error(f"Error: {error}")
        return
    
    # Generate tree
    with st.spinner("Generating tree visualization..."):
        tree_builder = PyVisTreeBuilder()
        html_content, error = tree_builder.build_tree(output_directory)
        
        if error:
            st.error(f"Error creating tree: {error}")
            return
        
        if html_content:
            st.components.v1.html(html_content, height=750, scrolling=True)
            
            # Download option
            st.download_button(
                label="📥 Download Interactive Tree (HTML)",
                data=html_content,
                file_name=f"tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
            
            # st.success("Tree visualization loaded successfully!")
            st.info("Tip: Drag nodes to rearrange, zoom with mouse wheel, hover for details")
        else:
            st.error("Failed to generate tree visualization")