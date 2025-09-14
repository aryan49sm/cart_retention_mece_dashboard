import streamlit as st
import json
import os

def display_mece_report(output_directory):
    """
    Display the MECE compliance report in a formatted view.
    
    Args:
        output_directory (str): Path to the output directory containing mece_report.json
    """
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    json_path = os.path.join(project_root, output_directory, "mece_report.json")
    
    if not os.path.exists(json_path):
        st.error(f"MECE report file not found: {json_path}")
        return
    
    try:
        # Load the MECE report
        with open(json_path, 'r') as f:
            report = json.load(f)
        
        # Display overall compliance status
        st.subheader("🎯 MECE Compliance Overview")
        
        # Main compliance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Extract validation data
        mece_validation = report.get('mece_validation', {})
        universe_size = report.get('universe_size', 0)
        duplicate_users = mece_validation.get('duplicate_users', 0)
        exhaustiveness_check = mece_validation.get('exhaustiveness_check', False)
        total_users_assigned = mece_validation.get('total_users_assigned', 0)
        
        # Calculate MECE compliance
        is_mutually_exclusive = duplicate_users == 0
        is_collectively_exhaustive = exhaustiveness_check and (total_users_assigned == universe_size)
        overall_compliance = is_mutually_exclusive and is_collectively_exhaustive
        
        with col1:
            st.metric(
                "Mutually Exclusive", 
                "✅ PASS" if is_mutually_exclusive else "❌ FAIL",
                delta=None
            )
        
        with col2:
            st.metric(
                "Collectively Exhaustive", 
                "✅ PASS" if is_collectively_exhaustive else "❌ FAIL",
                delta=None
            )
        
        with col3:
            st.metric(
                "Overall MECE", 
                "✅ COMPLIANT" if overall_compliance else "❌ NON-COMPLIANT",
                delta=None
            )
        
        with col4:
            st.metric(
                "Universe Size", 
                f"{universe_size:,}",
                delta=None
            )
        
        # Detailed breakdown
        st.markdown("---")
        
        # Coverage Analysis
        st.subheader("📊 Coverage Analysis")
        
        # Calculate coverage percentage
        coverage_percentage = (total_users_assigned / universe_size * 100) if universe_size > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Total Universe:** {universe_size:,}")
            st.write(f"**Users Assigned:** {total_users_assigned:,}")
            st.write(f"**Coverage:** {coverage_percentage:.2f}%")
            
            # Progress bar for coverage
            st.progress(min(coverage_percentage / 100, 1.0))
        
        with col2:
            if is_collectively_exhaustive:
                st.success("✅ All users segmented")
            else:
                missing_users = universe_size - total_users_assigned
                st.warning(f"⚠️ {missing_users:,} users not segmented")
        
        # Overlap Analysis
        st.markdown("---")
        st.subheader("🔍 Overlap Analysis")
        
        if is_mutually_exclusive:
            st.success("✅ No overlapping users detected")
        else:
            st.error(f"❌ {duplicate_users:,} users appear in multiple segments")
        
        # Segment counts validation
        if 'segment_counts' in report:
            st.markdown("---")
            st.subheader("📊 Segment Distribution")
            
            segment_counts = report['segment_counts']
            total_from_counts = sum(segment_counts.values())
            
            # Verify counts match
            if total_from_counts == total_users_assigned:
                st.success(f"✅ Segment counts verified: {total_from_counts:,} users")
            else:
                st.error(f"❌ Count mismatch: Segments={total_from_counts:,}, Assigned={total_users_assigned:,}")
            
            # Show segment breakdown
            for segment, count in segment_counts.items():
                percentage = (count / total_users_assigned * 100) if total_users_assigned > 0 else 0
                st.write(f"• **{segment}**: {count:,} users ({percentage:.1f}%)")
        
        # Segment Size Analysis
        if 'segment_details' in report:
            st.markdown("---")
            st.subheader("📈 Segment Size Validation")
            
            segments = report['segment_details']
            min_size = report.get('validation_rules', {}).get('min_segment_size', 1000)
            
            # Create a table for segment sizes
            segment_data = []
            for segment_name, details in segments.items():
                size = details.get('size', 0)
                status = "✅ Valid" if size >= min_size else "⚠️ Below minimum"
                segment_data.append({
                    'Segment': segment_name,
                    'Size': f"{size:,}",
                    'Status': status
                })
            
            if segment_data:
                import pandas as pd
                df = pd.DataFrame(segment_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Validation Rules
        st.markdown("---")
        st.subheader("📋 Analysis Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Configuration:**")
            min_size = report.get('min_segment_size', 'Not specified')
            max_size = report.get('max_segment_size', 'Not specified')
            st.write(f"• Min Segment Size: {min_size:,}" if isinstance(min_size, int) else f"• Min Segment Size: {min_size}")
            st.write(f"• Max Segment Size: {max_size:,}" if isinstance(max_size, int) else f"• Max Segment Size: {max_size}")
            
            window_start = report.get('window_start', 'Not specified')
            window_end = report.get('window_end', 'Not specified')
            st.write(f"• Analysis Window: {window_start} to {window_end}")
        
        with col2:
            st.write("**Validation Results:**")
            st.write(f"• Mutually Exclusive: {'✅ PASS' if is_mutually_exclusive else '❌ FAIL'}")
            st.write(f"• Collectively Exhaustive: {'✅ PASS' if is_collectively_exhaustive else '❌ FAIL'}")
            st.write(f"• Overall MECE: {'✅ COMPLIANT' if overall_compliance else '❌ NON-COMPLIANT'}")
        
        # Raw Report Data (Expandable)
        with st.expander("🔧 Raw Report Data"):
            st.json(report)
        
        # Download button
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="📥 Download MECE Report",
            data=report_json,
            file_name=f"mece_report_{output_directory.split('_')[-2]}_{output_directory.split('_')[-1]}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"Error loading MECE report: {str(e)}")

def display_mece_summary_card(output_directory):
    """
    Display a compact MECE summary card for dashboard view.
    
    Args:
        output_directory (str): Path to the output directory containing mece_report.json
    """
    
    # Get absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/components
    project_root = os.path.dirname(os.path.dirname(current_dir))  # go up two levels
    json_path = os.path.join(project_root, output_directory, "mece_report.json")
    
    if not os.path.exists(json_path):
        st.error("MECE report not found")
        return False
    
    try:
        with open(json_path, 'r') as f:
            report = json.load(f)
        
        # Extract key metrics with proper defaults
        universe_size = report.get('universe_size', 0)
        mece_validation = report.get('mece_validation', {})
        
        # Calculate MECE compliance
        duplicate_users = mece_validation.get('duplicate_users', 0)
        exhaustiveness_check = mece_validation.get('exhaustiveness_check', False)
        total_users_assigned = mece_validation.get('total_users_assigned', 0)
        
        is_mutually_exclusive = duplicate_users == 0
        is_collectively_exhaustive = exhaustiveness_check and (total_users_assigned == universe_size)
        is_mece_compliant = is_mutually_exclusive and is_collectively_exhaustive
        
        # Calculate coverage percentage
        coverage_percentage = (total_users_assigned / universe_size * 100) if universe_size > 0 else 0
        overlaps = duplicate_users
        
        # Display status
        if is_mece_compliant:
            st.success("✅ MECE Compliant")
        else:
            st.error("❌ MECE Issues Detected")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Universe", f"{universe_size:,}")
        with col2:
            st.metric("Coverage", f"{coverage_percentage:.1f}%")
        with col3:
            st.metric("Overlaps", overlaps)
        
        return True
        
    except Exception as e:
        st.error(f"MECE summary error: {str(e)}")
        return False