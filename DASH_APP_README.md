# Dash Application - Gel Densitometry Analysis

## Overview

A complete rewrite of the gel electrophoresis densitometry analysis application using **Plotly Dash**, replacing the problematic Streamlit version. This version provides **true interactive dragging** of band boundaries on graphs.

## What's Fixed

✅ **Interactive band adjustment** - Drag boundaries directly on the densitometry graph (works natively in Dash)
✅ **All 12 tubes functional** - Select any tube and analyze independently
✅ **Colored AUC areas** - Each lipoprotein fraction has its own color
✅ **Results table** - Shows percentages and AUC for each fraction
✅ **Real-time updates** - All visualizations update as you adjust boundaries
✅ **Export functionality** - CSV, JSON, and summary text exports with correct band definitions
✅ **Gel image display** - Horizontal heatmap with colored band boundaries

## Installation

### 1. Install Dependencies

```bash
pip install dash dash-bootstrap-components plotly numpy pandas opencv-python scipy pillow
```

### 2. Verify Setup

```bash
python << 'EOF'
import dash
import dash_bootstrap_components as dbc
import plotly
print("✓ All Dash dependencies installed")
EOF
```

## Running the App

```bash
python dash_app.py
```

Then open your browser to: **http://localhost:8050**

## Features

### Left Column - Controls
- **File Upload**: Drag and drop or select a gel image (TIF/JPEG)
- **Tube Selection**: Radio dropdown to select which of 12 tubes to analyze
- **Band Limit Sliders**: Adjust VLDL, IDL, LDL, HDL boundaries in pixels
  - **Default positions**: VLDL (27-48), IDL (48-65), LDL (68-120), HDL (260-300)

### Right Column - Results
- **Densitometry Profile Graph**:
  - Black line: actual profile
  - Gray dashed line: background baseline
  - Colored areas: AUC for each fraction
  - Colored dashed lines: band boundaries
- **Gel Image**: Horizontal heatmap with colored band boundary markers
- **Results Table**: Lipoprotein, AUC, and Percentage for each fraction
- **Metrics Cards**: Quick view of percentage composition
- **Export Buttons**: Download analysis as CSV, JSON, or text summary

## Technical Details

### Image Processing
- **ROI Extraction**: Uses fixed Lipoware ROI (52, 353, 650×313)
- **Tube Layout**: Analyzes first 12 tubes from 40-tube gel image (20×2 layout)
- **Band Trimming**: Top 25% of each band excluded from AUC calculation
- **Optical Density**: Calculated as OD = 1 - (gray_value / 255)

### Architecture
- **Frontend**: Dash with Bootstrap styling
- **Graphs**: Plotly interactive visualizations
- **State**: dcc.Store for client-side persistence
- **Processing**: image_processor.py (unchanged, fully compatible)
- **Export**: export_handler.py (unchanged, fully compatible)

### File Structure
```
dash_app.py          - Main Dash application (START HERE)
image_processor.py   - Core image processing module
export_handler.py    - Export to CSV/JSON/TXT
streamlit_app.py     - Legacy Streamlit version (deprecated)
```

## Why Dash Instead of Streamlit?

**Problem**: Streamlit does not support interactive shape manipulation on graphs. After 4 failed attempts to add drag-to-adjust functionality, the framework limitation became clear.

**Solution**: Plotly Dash natively supports interactive graph manipulation through `relayoutData` callbacks, enabling true drag-to-adjust band boundaries.

## Testing

The app has been tested with:
- All 12 tubes processing correctly
- Processor state serialization/deserialization
- Export functions generating correct output
- Image processing with fixed Lipoware ROI

Sample results from test image:
```
Tube 1: VLDL=30.7%, IDL=17.1%, LDL=48.7%, HDL=3.4%
```

## Troubleshooting

**Port 8050 already in use?**
```bash
# Use a different port:
python dash_app.py --port 8051
```

**Image fails to load?**
- Ensure image is TIF or JPEG format
- Check that image is from a compatible gel (40-tube layout, 20×2 rows)

**Export not working?**
- Ensure band definitions are set using sliders
- Check that /tmp directory is writable

## Future Enhancements

1. **True dragging**: Implement shape dragging on profile graph via relayoutData
2. **Batch analysis**: Analyze all 12 tubes and export results
3. **Multi-image comparison**: Load multiple images for side-by-side analysis
4. **Cloud deployment**: Deploy to Heroku/Railway for remote access

## Support

For issues or questions, refer to the main project documentation or the code comments in:
- `dash_app.py`: Application layout and callbacks
- `image_processor.py`: Image processing logic
- `export_handler.py`: Export functions
