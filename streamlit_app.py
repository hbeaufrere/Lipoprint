"""Streamlit web app for gel electrophoresis densitometry analysis."""
import streamlit as st
import numpy as np
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
from PIL import Image

from image_processor import GelImageProcessor, DensitometryAnalyzer
from export_handler import AnalysisExporter


# Page configuration
st.set_page_config(
    page_title="Gel Densitometry Analysis",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🧬 Gel Electrophoresis Densitometry Analysis</h1>',
            unsafe_allow_html=True)

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'current_tube' not in st.session_state:
    st.session_state.current_tube = 0
if 'bands_detected' not in st.session_state:
    st.session_state.bands_detected = False


def load_and_process_image(uploaded_file):
    """Load image and extract tubes. Supports TIF and JPEG."""
    # Determine file extension
    file_ext = '.tif' if uploaded_file.name.lower().endswith(('.tif', '.tiff')) else '.jpg'

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        processor = GelImageProcessor(tmp_path)
        processor.extract_tubes(num_tubes=12, tubes_per_row=20)  # First 12 of 20 tubes per row
        st.session_state.processor = processor
        st.session_state.current_tube = 0
        st.session_state.bands_detected = False
        return processor
    except Exception as e:
        st.error(f"Failed to load image: {str(e)}")
        return None


def trim_band_top_25percent(left, right):
    """Trim the top 25% of a band region, returning new left boundary."""
    band_height = right - left
    trim_amount = int(band_height * 0.25)
    return left + trim_amount


def display_densitometry_plot(profile, peaks, background, bands, colors, slider_boundaries=None):
    """Create an interactive Plotly figure for densitometry."""
    x = np.arange(len(profile))

    # Category colors
    category_colors = {
        'VLDL': '#FF6B6B',
        'IDL': '#FFA07A',
        'LDL': '#FFD700',
        'HDL': '#4ECDC4'
    }

    fig = go.Figure()

    # Plot profile
    fig.add_trace(go.Scatter(
        x=x, y=profile,
        mode='lines',
        name='Densitometry Profile',
        line=dict(color='black', width=2.5),
        hovertemplate='Position: %{x}<br>OD: %{y:.4f}<extra></extra>'
    ))

    # Plot background line
    fig.add_hline(
        y=background,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Background: {background:.4f}",
        annotation_position="right"
    )

    # Plot peaks
    if len(peaks) > 0:
        fig.add_trace(go.Scatter(
            x=peaks, y=profile[peaks],
            mode='markers',
            name='Detected Peaks',
            marker=dict(color='red', size=8),
            hovertemplate='Peak at: %{x}<br>OD: %{y:.4f}<extra></extra>'
        ))

    # Plot bands with colored AUC areas
    if bands:
        for i, band in enumerate(bands):
            left = band['left']
            right = band['right']

            # Trim top 25% of each band
            left_trimmed = trim_band_top_25percent(left, right)

            # Use category name if available, otherwise use generic band name
            band_name = band.get('category', f'Band {i+1}')
            color = category_colors.get(band_name, colors[i % len(colors)])

            # Use trimmed region for AUC calculation and display
            band_x = x[left_trimmed:right+1]
            band_y = profile[left_trimmed:right+1]

            # Add filled area with category color (AUC - Area Under Curve)
            fig.add_trace(go.Scatter(
                x=band_x, y=band_y,
                fill='tozeroy',  # Fill to y=0 axis
                fillcolor=color,
                opacity=0.35,
                line=dict(color=color, width=2.5),
                name=band_name,
                hovertemplate=f'<b>{band_name}</b><br>Position: %{{x}}<br>OD: %{{y:.4f}}<extra></extra>',
                showlegend=True
            ))

            # Add boundary lines (on trimmed boundaries)
            fig.add_vline(x=left_trimmed, line_dash="dash", line_color=color, line_width=2, opacity=0.7)
            fig.add_vline(x=right, line_dash="dash", line_color=color, line_width=2, opacity=0.7)

    # Plot temporary slider boundaries (when adjusting)
    if slider_boundaries:
        for category, (start, end) in slider_boundaries.items():
            color = category_colors.get(category, 'gray')
            # Add thicker, more visible lines to show current slider positions
            fig.add_vline(x=start, line_dash="dot", line_color=color, line_width=4, opacity=0.8)
            fig.add_vline(x=end, line_dash="dot", line_color=color, line_width=4, opacity=0.8)

    fig.update_layout(
        title='Gel Densitometry Profile',
        xaxis_title='Position (pixels)',
        yaxis_title='Optical Density',
        hovermode='x unified',
        height=600,
        template='plotly_white',
        font=dict(size=12)
    )

    return fig


def main():
    """Main Streamlit app."""

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.write("---")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload Gel Image",
            type=['tif', 'tiff', 'jpg', 'jpeg'],
            help="Select a gel electrophoresis image (TIF or JPEG)"
        )

        if uploaded_file is not None:
            processor = load_and_process_image(uploaded_file)

            if processor is not None:
                st.success(f"✅ Image loaded successfully!")
                st.info(f"Found {len(processor.tubes)} tubes ready for analysis")

    # Main content
    if st.session_state.processor is None:
        st.info("👆 Please upload a TIF image to get started", icon="ℹ️")
        return

    processor = st.session_state.processor

    # Tube selection
    col1, col2 = st.columns([3, 1])

    with col1:
        tube_idx = st.selectbox(
            "Select Tube to Analyze",
            range(12),
            format_func=lambda x: f"Tube {x + 1}",
            key="tube_selector"
        )
        st.session_state.current_tube = tube_idx

    with col2:
        st.write("")  # Spacing
        st.write("")
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()

    # Get profile for selected tube
    try:
        profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
        background = processor.detect_background(profile)

        # Create analyzer
        analyzer = DensitometryAnalyzer(profile, background)
        st.session_state.analyzer = analyzer

    except Exception as e:
        st.error(f"Error analyzing tube: {str(e)}")
        return

    # Manual band definition with 4 lipid categories
    st.write("---")
    st.write("### 🧬 Define Lipoprotein Bands (VLDL, IDL, LDL, HDL)")

    profile_length = len(profile)

    # Category definitions: VLDL, IDL, LDL, HDL
    categories = ['VLDL', 'IDL', 'LDL', 'HDL']
    category_colors = {
        'VLDL': '#FF6B6B',  # Red
        'IDL': '#FFA07A',   # Light coral
        'LDL': '#FFD700',   # Gold
        'HDL': '#4ECDC4'    # Teal
    }

    # Create sliders for category boundaries
    col1, col2, col3, col4 = st.columns(4)

    boundaries = {}

    with col1:
        st.write("**VLDL**")
        vldl_start = st.slider("VLDL start", 0, profile_length - 1, 0, key="vldl_start")
        vldl_end = st.slider("VLDL end", vldl_start + 1, profile_length - 1, int(profile_length * 0.25), key="vldl_end")
        boundaries['VLDL'] = (vldl_start, vldl_end)

    with col2:
        st.write("**IDL**")
        idl_start = st.slider("IDL start", vldl_end, profile_length - 1, int(profile_length * 0.25), key="idl_start")
        idl_end = st.slider("IDL end", idl_start + 1, profile_length - 1, int(profile_length * 0.5), key="idl_end")
        boundaries['IDL'] = (idl_start, idl_end)

    with col3:
        st.write("**LDL**")
        ldl_start = st.slider("LDL start", idl_end, profile_length - 1, int(profile_length * 0.5), key="ldl_start")
        ldl_end = st.slider("LDL end", ldl_start + 1, profile_length - 1, int(profile_length * 0.75), key="ldl_end")
        boundaries['LDL'] = (ldl_start, ldl_end)

    with col4:
        st.write("**HDL**")
        hdl_start = st.slider("HDL start", ldl_end, profile_length - 1, int(profile_length * 0.75), key="hdl_start")
        hdl_end = st.slider("HDL end", hdl_start + 1, profile_length, profile_length, key="hdl_end")
        boundaries['HDL'] = (hdl_start, min(hdl_end, profile_length - 1))

    # Apply category boundaries to bands
    col_apply = st.columns(1)[0]
    with col_apply:
        if st.button("✅ Apply Band Definitions", key="apply_categories"):
            analyzer.bands = []
            for category in categories:
                start, end = boundaries[category]
                if start < end:
                    analyzer.bands.append({
                        'left': start,
                        'right': end,
                        'category': category
                    })
            st.session_state.bands_detected = True
            st.success(f"✅ Defined {len(analyzer.bands)} bands!")
            st.rerun()

    # Clear button
    if st.button("🧹 Clear All Bands", key="clear_bands"):
        analyzer.bands = []
        st.session_state.bands_detected = False
        st.rerun()

    st.write("---")

    # Display graph and stats
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#A8D8EA']

    # Create Plotly figure with slider boundaries
    fig = display_densitometry_plot(profile, analyzer.peaks, background,
                                   analyzer.bands, colors, slider_boundaries=boundaries)

    # Display graph full width
    st.write("### 📈 Densitometry Profile")
    st.plotly_chart(fig, use_container_width=True)

    # Display gel tube image horizontally below the graph
    st.write("### 🧫 Gel Tube Image with Band Boundaries")
    try:
        tube_info = processor.tubes[st.session_state.current_tube]
        tube_region = tube_info['region']

        # Enhance contrast for better visualization
        tube_normalized = tube_region.astype(float)
        tube_min = np.percentile(tube_normalized, 5)
        tube_max = np.percentile(tube_normalized, 95)
        tube_display = np.clip((tube_normalized - tube_min) / (tube_max - tube_min + 0.001) * 255, 0, 255).astype(np.uint8)

        # Get dimensions
        tube_height, tube_width = tube_display.shape  # (depth, width)

        # Calculate the 25% offset and crop the image to start from 25%
        trim_offset = int(tube_height * 0.25)
        tube_display_trimmed = tube_display[trim_offset:, :]  # Crop to remove top 25%

        # Transpose the image so depth becomes the horizontal axis
        tube_display_transposed = np.transpose(tube_display_trimmed)  # Now (width, depth)

        # Create horizontal figure - larger for better visibility
        fig_width = 14
        fig_height = 2.5

        fig_tube = plt.figure(figsize=(fig_width, fig_height))
        ax_tube = fig_tube.add_subplot(111)

        # Display the transposed image with contrast enhancement
        im = ax_tube.imshow(tube_display_transposed, cmap='gray', aspect='auto', origin='upper', interpolation='nearest')
        plt.colorbar(im, ax=ax_tube, label='Intensity')

        # Draw band boundaries on gel image
        if analyzer.bands:
            for i, band in enumerate(analyzer.bands):
                left = band['left']
                right = band['right']

                # Trim top 25% of each band
                left_trimmed = trim_band_top_25percent(left, right)

                # Adjust for the 25% crop we applied to the image
                left_adj = left_trimmed - trim_offset
                right_adj = right - trim_offset

                band_name = band.get('category', f'Band {i+1}')

                category_colors = {
                    'VLDL': '#FF6B6B',
                    'IDL': '#FFA07A',
                    'LDL': '#FFD700',
                    'HDL': '#4ECDC4'
                }
                color = category_colors.get(band_name, colors[i % len(colors)])

                # Draw horizontal lines for band boundaries (only if in visible range)
                if -10 <= left_adj <= tube_display_transposed.shape[1] + 10:
                    ax_tube.axhline(y=left_adj, color=color, linestyle='--', linewidth=2, alpha=0.7)
                if -10 <= right_adj <= tube_display_transposed.shape[1] + 10:
                    ax_tube.axhline(y=right_adj, color=color, linestyle='--', linewidth=2, alpha=0.7)

        # Also draw slider positions to preview
        if boundaries:
            for category, (start, end) in boundaries.items():
                # Adjust for the 25% crop
                start_adj = start - trim_offset
                end_adj = end - trim_offset

                category_colors = {
                    'VLDL': '#FF6B6B',
                    'IDL': '#FFA07A',
                    'LDL': '#FFD700',
                    'HDL': '#4ECDC4'
                }
                color = category_colors.get(category, 'gray')
                if -10 <= start_adj <= tube_display_transposed.shape[1] + 10:
                    ax_tube.axhline(y=start_adj, color=color, linestyle=':', linewidth=1, alpha=0.4)
                if -10 <= end_adj <= tube_display_transposed.shape[1] + 10:
                    ax_tube.axhline(y=end_adj, color=color, linestyle=':', linewidth=1, alpha=0.4)

        # Set x-axis to show the trimmed region (25% to 100%)
        ax_tube.set_xlabel(f'Depth (pixels: {trim_offset} to {tube_height})')
        ax_tube.set_ylabel('Width')
        ax_tube.set_title(f'Tube {st.session_state.current_tube + 1} - Horizontal View (Top 25% Trimmed)')

        st.pyplot(fig_tube, use_container_width=True)
        plt.close(fig_tube)
    except Exception as e:
        st.warning(f"Could not display tube image: {str(e)}")

    # Profile statistics below
    col_stats = st.columns(4)
    with col_stats[0]:
        st.metric("Background OD", f"{background:.4f}")
    with col_stats[1]:
        st.metric("Peak OD", f"{np.max(profile):.4f}")
    with col_stats[2]:
        st.metric("Profile Length", f"{len(profile)} px")
    with col_stats[3]:
        st.metric("Detected Bands", len(analyzer.bands))

    # Band analysis
    if analyzer.bands:
        st.write("---")
        st.write("### 📋 Lipoprotein Composition Analysis")

        band_aucs, percentages = analyzer.calculate_band_percentages()
        total_auc = sum(band_aucs)

        # Display as table
        band_data = []
        for i, (band, auc, pct) in enumerate(zip(analyzer.bands, band_aucs, percentages)):
            band_name = band.get('category', f'Band {i+1}')
            band_data.append({
                'Lipoprotein': band_name,
                'Position': f"{band['left']}-{band['right']} px",
                'AUC': f"{auc:.2f}",
                'Percentage': f"{pct:.2f}%"
            })

        st.dataframe(
            band_data,
            use_container_width=True,
            hide_index=True
        )

        # Visual representation
        st.write("#### Lipoprotein Distribution")

        # Get category names and colors
        category_colors_map = {
            'VLDL': '#FF6B6B',
            'IDL': '#FFA07A',
            'LDL': '#FFD700',
            'HDL': '#4ECDC4'
        }

        band_names = [band.get('category', f"Band {i+1}") for i, band in enumerate(analyzer.bands)]
        bar_colors = [category_colors_map.get(name, colors[i % len(colors)]) for i, name in enumerate(band_names)]

        fig_bar = go.Figure(data=[
            go.Bar(
                x=band_names,
                y=percentages,
                marker_color=bar_colors,
                text=[f"{p:.1f}%" for p in percentages],
                textposition='auto',
                hovertemplate='%{x}<br>%{y:.2f}%<extra></extra>'
            )
        ])

        fig_bar.update_layout(
            title='Lipoprotein Percentage Composition',
            xaxis_title='Lipoprotein',
            yaxis_title='Percentage (%)',
            height=400,
            template='plotly_white',
            showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)

        # Lipoprotein profile percentage table - PROMINENT DISPLAY
        st.write("---")

        # Create a prominent table with percentages
        table_data = []
        for i, (band, pct) in enumerate(zip(analyzer.bands, percentages)):
            band_name = band.get('category', f'Band {i+1}')
            table_data.append([band_name, f"{pct:.1f}%"])

        # Display as DataFrame for clear table format
        import pandas as pd
        df_percentages = pd.DataFrame(table_data, columns=['Lipoprotein', 'Percentage'])

        st.write("### 📊 Lipoprotein profile (%)")
        st.dataframe(df_percentages, use_container_width=False, hide_index=True)

        # Also display as metrics in columns for visual prominence
        st.write("")
        metric_cols = st.columns(len(analyzer.bands))
        for idx, (band, pct) in enumerate(zip(analyzer.bands, percentages)):
            band_name = band.get('category', f'Band {idx+1}')
            category_colors_map = {'VLDL': '#FF6B6B', 'IDL': '#FFA07A', 'LDL': '#FFD700', 'HDL': '#4ECDC4'}
            with metric_cols[idx]:
                st.metric(band_name, f"{pct:.1f}%")

    # Export section
    st.write("---")
    st.write("### 💾 Export Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export as CSV", key="export_csv"):
            try:
                exporter = AnalysisExporter(processor, analyzer, tube_idx)
                csv_path = "/tmp/analysis.csv"
                exporter.export_to_csv(csv_path)

                with open(csv_path, 'r') as f:
                    csv_data = f.read()

                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"tube_{tube_idx + 1}_analysis.csv",
                    mime="text/csv",
                    key="download_csv"
                )
                st.success("✅ CSV ready for download!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")

    with col2:
        if st.button("📥 Export as JSON", key="export_json"):
            try:
                exporter = AnalysisExporter(processor, analyzer, tube_idx)
                json_path = "/tmp/analysis.json"
                exporter.export_to_json(json_path)

                with open(json_path, 'r') as f:
                    json_data = f.read()

                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"tube_{tube_idx + 1}_analysis.json",
                    mime="application/json",
                    key="download_json"
                )
                st.success("✅ JSON ready for download!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")

    with col3:
        if st.button("📥 Export Summary", key="export_summary"):
            try:
                exporter = AnalysisExporter(processor, analyzer, tube_idx)
                summary_path = "/tmp/summary.txt"
                exporter.export_summary(summary_path)

                with open(summary_path, 'r') as f:
                    summary_data = f.read()

                st.download_button(
                    label="📥 Download Summary",
                    data=summary_data,
                    file_name=f"tube_{tube_idx + 1}_summary.txt",
                    mime="text/plain",
                    key="download_summary"
                )
                st.success("✅ Summary ready for download!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")

    # Footer
    st.write("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;">
    <p>Gel Electrophoresis Densitometry Analysis Tool</p>
    <p>Powered by Python • Streamlit • NumPy/SciPy</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
