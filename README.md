# Gel Electrophoresis Densitometry Analysis Tool

A specialized image analysis application for quantitative analysis of gel electrophoresis images. This tool automatically detects bands, calculates band densities, and provides detailed quantitative metrics.

## Features

- **Image Upload**: Load TIF format gel electrophoresis images
- **Multi-tube Analysis**: Analyze up to 12 tubes from the top row
- **Automatic Peak Detection**: Automatically identify bands using prominence-based peak detection
- **Background Correction**: Automatic background level detection and subtraction
- **Interactive Cutoff Lines**: Manually adjust band boundaries for precise analysis
- **Quantitative Analysis**: Calculate area under curve (AUC) and percentage composition for each band
- **Color-Coded Visualization**: Different colors for each band in the graph

## Installation & Usage

### Option 1: Web App (Streamlit) - Recommended ⭐

The web app works in any browser and is easier to deploy.

```bash
# Install dependencies
pip install -r requirements.txt

# Run web app
streamlit run streamlit_app.py
```

Access at: http://localhost:8501

**Deploy to cloud**: See STREAMLIT_QUICKSTART.md for 1-click deployment to Streamlit Cloud (FREE!)

### Option 2: Desktop App (PyQt6) - Local Only

The desktop app provides enhanced interactivity with drag-and-drop cutoff adjustment.

```bash
# Install dependencies (desktop version with PyQt6)
pip install -r requirements-desktop.txt

# Run desktop app
python main.py
```

2. Click "Load TIF Image" to select your gel electrophoresis image
   - Images should have: black background, white gels, black bands
   - Supports standard TIF/TIFF format

3. Select a tube (1-12) from the dropdown menu

4. Click "Auto-Detect Peaks" to identify bands automatically

5. Review the densitometry profile:
   - X-axis: Position along the tube (pixels)
   - Y-axis: Optical density
   - Shaded areas represent individual bands
   - Vertical lines mark band boundaries

6. View band statistics in the "Band Analysis" panel:
   - Number of detected bands
   - Percentage of total AUC for each band
   - AUC values

## Image Requirements

- **Format**: TIF or TIFF files
- **Layout**: Tubes arranged in 2 rows, 6 tubes per row (top row used for analysis)
- **Colors**:
  - Black background
  - White gel matrix
  - Black bands
- **Resolution**: At least 300 x 400 pixels recommended

## How It Works

1. **Image Loading**: Converts TIF image to grayscale and inverts colors so bands become peaks
2. **Tube Extraction**: Divides image into 12 regions (6x2 grid)
3. **Densitometry**: For each tube, generates a vertical intensity profile
4. **Background Detection**: Identifies baseline noise using quantile analysis
5. **Peak Detection**: Uses scipy signal processing to find peaks with prominence filtering
6. **Band Analysis**: Calculates area under curve and percentage composition

## Technical Details

### Dependencies

**Web App (requirements.txt):**
- **Streamlit**: Web framework
- **Plotly**: Interactive graphs
- **NumPy/SciPy**: Numerical analysis and signal processing
- **OpenCV**: Image processing
- **Pillow**: Image I/O
- **Matplotlib**: Graph visualization
- **scikit-image**: Additional image processing utilities

**Desktop App (requirements-desktop.txt):**
- **PyQt6**: GUI framework
- Plus all dependencies above except Streamlit/Plotly

### Algorithm Parameters
- Peak prominence threshold: 0.05 (optical density units)
- Peak distance: 5 pixels minimum
- Background percentile: 10th percentile

## Future Enhancements

- Batch processing of multiple images
- Export analysis results to CSV/Excel
- Adjustable detection parameters via GUI
- Manual peak editing interface
- Reference lane normalization
- Statistical comparison between tubes
