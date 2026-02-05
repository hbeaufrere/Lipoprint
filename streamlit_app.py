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
        processor.extract_tubes(num_tubes=12, rows=2)
        st.session_state.processor = processor
        st.session_state.current_tube = 0
        st.session_state.bands_detected = False
        return processor
    except Exception as e:
        st.error(f"Failed to load image: {str(e)}")
        return None


def display_densitometry_plot(profile, peaks, background, bands, colors):
    """Create an interactive Plotly figure for densitometry."""
    x = np.arange(len(profile))

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

    # Plot bands
    if bands:
        for i, band in enumerate(bands):
            left = band['left']
            right = band['right']
            color = colors[i % len(colors)]

            band_x = x[left:right+1]
            band_y = profile[left:right+1]

            # Add filled area
            fig.add_trace(go.Scatter(
                x=band_x, y=band_y,
                fill='tonexty',
                fillcolor=color,
                opacity=0.3,
                line=dict(color=color, width=0),
                name=f'Band {i+1}',
                hovertemplate='Band %{fullData.name}<br>Position: %{x}<br>OD: %{y:.4f}<extra></extra>'
            ))

            # Add boundary lines
            fig.add_vline(x=left, line_dash="dash", line_color=color, line_width=2)
            fig.add_vline(x=right, line_dash="dash", line_color=color, line_width=2)

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

    # Control buttons
    st.write("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎯 Auto-Detect Bands", key="detect_peaks"):
            try:
                peaks = analyzer.detect_automatic_peaks(prominence_threshold=0.05)

                # Create bands from peaks
                analyzer.bands = []
                peak_width = 5

                for peak in peaks:
                    left = max(0, peak - peak_width)
                    right = min(len(profile) - 1, peak + peak_width)
                    analyzer.bands.append({'left': left, 'right': right, 'peak': peak})

                st.session_state.bands_detected = True
                st.success(f"✅ Detected {len(analyzer.bands)} bands!")

            except Exception as e:
                st.error(f"Error detecting peaks: {str(e)}")

    with col2:
        manual_bands = st.checkbox(
            "📊 Manually Define Bands",
            key="manual_bands_checkbox"
        )

    with col3:
        if st.button("🧹 Clear Bands", key="clear_bands"):
            analyzer.bands = []
            st.session_state.bands_detected = False
            st.rerun()

    # Manual band definition
    if manual_bands and not st.session_state.bands_detected:
        st.info("Define bands manually by specifying position ranges")

        num_manual_bands = st.number_input(
            "Number of bands to define",
            min_value=1,
            max_value=10,
            value=1,
            key="num_manual_bands"
        )

        analyzer.bands = []

        for i in range(num_manual_bands):
            st.write(f"**Band {i+1}**")
            col1, col2 = st.columns(2)

            with col1:
                left = st.number_input(
                    f"Left boundary (Band {i+1})",
                    min_value=0,
                    max_value=len(profile) - 1,
                    value=max(0, (len(profile) // (num_manual_bands + 1)) * (i + 1) - 5),
                    key=f"left_{i}"
                )

            with col2:
                right = st.number_input(
                    f"Right boundary (Band {i+1})",
                    min_value=0,
                    max_value=len(profile) - 1,
                    value=min(len(profile) - 1, (len(profile) // (num_manual_bands + 1)) * (i + 1) + 5),
                    key=f"right_{i}"
                )

            analyzer.bands.append({'left': min(left, right), 'right': max(left, right)})

        if st.button("✅ Apply Manual Bands", key="apply_manual"):
            st.session_state.bands_detected = True
            st.rerun()

    st.write("---")

    # Display graph and stats
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
              '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#A8D8EA']

    col1, col2 = st.columns([3, 1])

    with col1:
        # Create Plotly figure
        fig = display_densitometry_plot(profile, analyzer.peaks, background,
                                       analyzer.bands, colors)
        st.plotly_chart(fig, use_container_width=True)

        # Display gel tube image below graph for correlation
        st.write("**Gel Tube Image (Corresponding to Graph Above)**")
        try:
            tube_info = processor.tubes[st.session_state.current_tube]
            tube_region = tube_info['region']

            # Convert to 8-bit image for display
            if np.max(tube_region) > 0:
                tube_display = np.clip((tube_region / np.max(tube_region)) * 255, 0, 255).astype(np.uint8)
            else:
                tube_display = tube_region.astype(np.uint8)

            # Create a figure with matplotlib
            fig_tube = plt.figure(figsize=(4, 6))
            ax_tube = fig_tube.add_subplot(111)
            ax_tube.imshow(tube_display, cmap='gray', aspect='auto')
            ax_tube.set_xlabel('Width (pixels)')
            ax_tube.set_ylabel('Depth (pixels) →')
            ax_tube.set_title(f'Tube {st.session_state.current_tube + 1}')

            st.pyplot(fig_tube, use_container_width=True)
            plt.close(fig_tube)
        except Exception as e:
            st.warning(f"Could not display tube image: {str(e)}")

    with col2:
        st.write("### 📊 Profile Statistics")
        st.metric("Background OD", f"{background:.4f}")
        st.metric("Peak OD", f"{np.max(profile):.4f}")
        st.metric("Profile Length", f"{len(profile)} px")
        st.metric("Detected Bands", len(analyzer.bands))

    # Band analysis
    if analyzer.bands:
        st.write("---")
        st.write("### 📋 Band Composition Analysis")

        band_aucs, percentages = analyzer.calculate_band_percentages()
        total_auc = sum(band_aucs)

        # Display as table
        band_data = []
        for i, (band, auc, pct) in enumerate(zip(analyzer.bands, band_aucs, percentages)):
            band_data.append({
                'Band': f'Band {i+1}',
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
        st.write("#### Band Distribution")
        chart_data = {
            'Band': [f"Band {i+1}" for i in range(len(percentages))],
            'Percentage': percentages
        }

        fig_bar = go.Figure(data=[
            go.Bar(
                x=[f"Band {i+1}" for i in range(len(percentages))],
                y=percentages,
                marker_color=colors[:len(percentages)],
                text=[f"{p:.1f}%" for p in percentages],
                textposition='auto',
                hovertemplate='%{x}<br>%{y:.2f}%<extra></extra>'
            )
        ])

        fig_bar.update_layout(
            title='Band Percentage Composition',
            xaxis_title='Band',
            yaxis_title='Percentage (%)',
            height=400,
            template='plotly_white',
            showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)

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
