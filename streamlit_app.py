"""Streamlit web app for gel electrophoresis densitometry analysis.

Clean rewrite based on Lipoware software workflow.
Left: Controls | Right: Results
Simple, functional, and maintainable.
"""
import streamlit as st
import numpy as np
import pandas as pd
import tempfile
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from image_processor import GelImageProcessor, DensitometryAnalyzer
from export_handler import AnalysisExporter

# Page configuration
st.set_page_config(
    page_title="Gel Densitometry Analysis",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 Gel Electrophoresis Densitometry Analysis")

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'current_tube' not in st.session_state:
    st.session_state.current_tube = 0


def load_image(uploaded_file):
    """Load gel image and extract 12 tubes using Lipoware ROI."""
    file_ext = '.tif' if uploaded_file.name.lower().endswith(('.tif', '.tiff')) else '.jpg'

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        processor = GelImageProcessor(tmp_path)
        # Use fixed ROI from Lipoware: top-left (52, 353), width=650, height=313
        # This ROI contains all 12 tubes in the first row
        lipoware_roi = (52, 353, 650, 313)
        processor.extract_tubes(num_tubes=12, tubes_per_row=20, roi=lipoware_roi)
        return processor
    except Exception as e:
        st.error(f"Failed to load image: {str(e)}")
        return None


def trim_top_25(start, end):
    """Trim top 25% of band region."""
    band_height = end - start
    trim = int(band_height * 0.25)
    return start + trim


# MAIN LAYOUT: LEFT (controls) + RIGHT (results)
left_col, right_col = st.columns([1, 2], gap="medium")

# ============================================================================
# LEFT COLUMN: CONTROLS
# ============================================================================
with left_col:
    st.header("Controls")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Gel Image",
        type=['tif', 'tiff', 'jpg', 'jpeg']
    )

    if uploaded_file is not None:
        processor = load_image(uploaded_file)
        if processor is not None:
            st.session_state.processor = processor
            st.success("✅ Image loaded!")

    st.divider()

    if st.session_state.processor is None:
        st.info("📤 Upload a gel image to start")
    else:
        processor = st.session_state.processor

        # Tube selection
        st.subheader("Tube Selection")
        tube_idx = st.radio(
            "Select tube:",
            range(12),
            format_func=lambda x: f"Tube {x+1}",
            key="tube_radio"
        )
        st.session_state.current_tube = tube_idx

        st.divider()

        # Band definition sliders
        st.subheader("Band Limits")
        st.caption("Define boundaries for each lipoprotein fraction")

        profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
        profile_len = len(profile)

        # Simple independent sliders for each fraction
        vldl_start = st.slider("VLDL start", 0, profile_len-1, 0, key="vldl_s")
        vldl_end = st.slider("VLDL end", vldl_start+1, profile_len-1, profile_len//4, key="vldl_e")

        idl_start = st.slider("IDL start", vldl_end, profile_len-1, profile_len//4, key="idl_s")
        idl_end = st.slider("IDL end", idl_start+1, profile_len-1, profile_len//2, key="idl_e")

        ldl_start = st.slider("LDL start", idl_end, profile_len-1, profile_len//2, key="ldl_s")
        ldl_end = st.slider("LDL end", ldl_start+1, profile_len-1, int(profile_len*0.75), key="ldl_e")

        hdl_start = st.slider("HDL start", ldl_end, profile_len-1, int(profile_len*0.75), key="hdl_s")
        hdl_end = st.slider("HDL end", hdl_start+1, profile_len, profile_len, key="hdl_e")
        hdl_end = min(hdl_end, profile_len-1)

# ============================================================================
# RIGHT COLUMN: RESULTS
# ============================================================================
with right_col:
    if st.session_state.processor is None:
        st.info("👈 Load a gel image on the left to see results")
    else:
        processor = st.session_state.processor
        tube_idx = st.session_state.current_tube

        # Get profile and background
        profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
        background = processor.detect_background(profile)

        # Create analyzer
        analyzer = DensitometryAnalyzer(profile, background)

        # Build bands from sliders
        bands = [
            {'left': vldl_start, 'right': vldl_end, 'category': 'VLDL'},
            {'left': idl_start, 'right': idl_end, 'category': 'IDL'},
            {'left': ldl_start, 'right': ldl_end, 'category': 'LDL'},
            {'left': hdl_start, 'right': hdl_end, 'category': 'HDL'},
        ]
        analyzer.bands = bands

        # ---- DENSITOMETRY GRAPH ----
        st.subheader(f"Tube {tube_idx+1} Profile")

        x = np.arange(len(profile))
        category_colors = {
            'VLDL': '#FF6B6B',
            'IDL': '#FFA07A',
            'LDL': '#FFD700',
            'HDL': '#4ECDC4'
        }

        fig = go.Figure()

        # Profile line
        fig.add_trace(go.Scatter(
            x=x, y=profile,
            mode='lines',
            name='Profile',
            line=dict(color='black', width=2.5)
        ))

        # Background line
        fig.add_hline(y=background, line_dash="dash", line_color="gray", name="Background")

        # Colored AUC areas
        for band in bands:
            left = band['left']
            right = band['right']
            category = band['category']
            color = category_colors[category]

            # Trim top 25%
            left_trim = trim_top_25(left, right)

            # AUC area (trimmed)
            band_x = x[left_trim:right+1]
            band_y = profile[left_trim:right+1]

            fig.add_trace(go.Scatter(
                x=band_x, y=band_y,
                fill='tozeroy',
                fillcolor=color,
                opacity=0.35,
                line=dict(color=color, width=2),
                name=category,
                hovertemplate=f'<b>{category}</b><br>%{{x}}<br>%{{y:.3f}}<extra></extra>'
            ))

            # Boundary lines (on trimmed boundaries)
            fig.add_vline(x=left_trim, line_dash="dash", line_color=color, line_width=2, opacity=0.7)
            fig.add_vline(x=right, line_dash="dash", line_color=color, line_width=2, opacity=0.7)

        fig.update_layout(
            title='Densitometry Profile',
            xaxis_title='Position (pixels)',
            yaxis_title='Optical Density',
            height=500,
            hovermode='x unified',
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---- GEL IMAGE ----
        st.subheader("Gel Tube Image")

        try:
            tube_info = processor.tubes[tube_idx]
            tube_region = tube_info['region']

            # Enhance contrast
            tube_norm = tube_region.astype(float)
            vmin = np.percentile(tube_norm, 5)
            vmax = np.percentile(tube_norm, 95)
            tube_display = np.clip((tube_norm - vmin) / (vmax - vmin + 1e-6) * 255, 0, 255).astype(np.uint8)

            # Dimensions: (depth, width)
            depth, width = tube_display.shape

            # Trim top 25% of depth
            trim_offset = int(depth * 0.25)
            tube_trimmed = tube_display[trim_offset:, :]

            # Transpose to show horizontally: (width, depth) so width is x-axis
            tube_horizontal = np.transpose(tube_trimmed)

            # Plot
            fig_gel = plt.figure(figsize=(12, 2.5))
            ax = fig_gel.add_subplot(111)

            im = ax.imshow(tube_horizontal, cmap='gray', aspect='auto', origin='upper')
            plt.colorbar(im, ax=ax, label='Intensity')

            # Draw band boundaries
            for band in bands:
                left = band['left']
                right = band['right']
                category = band['category']
                color = category_colors[category]

                left_trim = trim_top_25(left, right)

                # Adjust for 25% crop
                left_adj = left_trim - trim_offset
                right_adj = right - trim_offset

                if 0 <= left_adj < tube_horizontal.shape[1]:
                    ax.axhline(y=left_adj, color=color, linestyle='--', linewidth=2, alpha=0.8)
                if 0 <= right_adj < tube_horizontal.shape[1]:
                    ax.axhline(y=right_adj, color=color, linestyle='--', linewidth=2, alpha=0.8)

            ax.set_xlabel('Width')
            ax.set_ylabel('Depth (trimmed 25%)')
            ax.set_title(f'Tube {tube_idx+1} - Horizontal View')

            st.pyplot(fig_gel, use_container_width=True)
            plt.close(fig_gel)

        except Exception as e:
            st.warning(f"Could not display gel image: {str(e)}")

        # ---- RESULTS TABLE ----
        st.divider()
        st.subheader("Results")

        band_aucs, percentages = analyzer.calculate_band_percentages()

        # Build results dataframe
        results_data = []
        for band, auc, pct in zip(bands, band_aucs, percentages):
            results_data.append({
                'Lipoprotein': band['category'],
                'AUC': f"{auc:.2f}",
                'Percentage': f"{pct:.1f}%"
            })

        df_results = pd.DataFrame(results_data)

        # Main results table
        st.markdown("**Lipoprotein profile (%)**")
        st.dataframe(df_results, use_container_width=False, hide_index=True)

        # Metrics row
        metric_cols = st.columns(4)
        for idx, (band, pct) in enumerate(zip(bands, percentages)):
            with metric_cols[idx]:
                st.metric(band['category'], f"{pct:.1f}%")

        # ---- EXPORT ----
        st.divider()
        st.subheader("Export")

        col_exp1, col_exp2, col_exp3 = st.columns(3)

        with col_exp1:
            if st.button("📥 CSV", key="exp_csv"):
                try:
                    exporter = AnalysisExporter(processor, analyzer, tube_idx)
                    csv_path = "/tmp/analysis.csv"
                    exporter.export_to_csv(csv_path)
                    with open(csv_path, 'r') as f:
                        st.download_button(
                            "Download CSV",
                            f.read(),
                            f"tube_{tube_idx+1}.csv",
                            "text/csv"
                        )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

        with col_exp2:
            if st.button("📥 JSON", key="exp_json"):
                try:
                    exporter = AnalysisExporter(processor, analyzer, tube_idx)
                    json_path = "/tmp/analysis.json"
                    exporter.export_to_json(json_path)
                    with open(json_path, 'r') as f:
                        st.download_button(
                            "Download JSON",
                            f.read(),
                            f"tube_{tube_idx+1}.json",
                            "application/json"
                        )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

        with col_exp3:
            if st.button("📥 Summary", key="exp_sum"):
                try:
                    exporter = AnalysisExporter(processor, analyzer, tube_idx)
                    sum_path = "/tmp/summary.txt"
                    exporter.export_summary(sum_path)
                    with open(sum_path, 'r') as f:
                        st.download_button(
                            "Download Summary",
                            f.read(),
                            f"tube_{tube_idx+1}_summary.txt",
                            "text/plain"
                        )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
