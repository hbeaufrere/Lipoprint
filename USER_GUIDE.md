# Gel Electrophoresis Densitometry Analysis - User Guide

## Overview

This application performs quantitative densitometric analysis of gel electrophoresis images. It automatically identifies protein/DNA bands, calculates their optical density, and provides detailed composition analysis.

## Getting Started

### Installation

1. **Install Python** (3.8 or later)
   ```bash
   python --version
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
python main.py
```

The GUI window will open, ready for analysis.

## Step-by-Step Usage

### 1. Load Image

1. Click **"Load TIF Image"** button
2. Select your gel electrophoresis TIF file
3. The application will:
   - Load the image
   - Detect 12 tubes (6×2 grid from top row)
   - Display the first tube's profile

**Image Requirements:**
- Format: TIF/TIFF
- Layout: 2 rows of tubes, with top row containing 6 tubes (first 12 tubes used)
- Colors: Black background, white gel, black bands
- Recommended resolution: At least 960×600 pixels

### 2. Select Tube

1. Use the **"Select Tube"** dropdown (1-12)
2. The densitometry profile for that tube appears in the graph
3. Background level is automatically detected (gray dashed line)

### 3. Auto-Detect Bands

1. Click **"Auto-Detect Peaks"** button
2. The algorithm identifies bands in the tube
3. Red circles mark detected peaks
4. Each band is shown as a colored shaded region with boundary lines
5. Band statistics appear in the right panel

### 4. Manual Adjustment (Optional)

If the automatic detection needs refinement:

1. **Move Band Boundaries:**
   - Click and drag the vertical dashed lines (band boundaries)
   - Release to finalize the position

2. **View Band Details:**
   - Right panel shows band composition percentages
   - Each band displays: percentage of total AUC and pixel range

### 5. Review Results

In the **"Band Analysis"** panel, you'll see:

- **Tube Number**: Which tube is being analyzed
- **Profile Statistics**: Background OD, peak OD, number of bands
- **Band Composition**:
  - Colored squares matching graph colors
  - Percentage of total density for each band
  - AUC value for each band
  - Pixel range for each band boundary

### 6. Export Results

Choose export format:

- **Export CSV**: Detailed pixel-by-pixel data
- **Export JSON**: Structured data for programmatic use
- **Export Summary**: Human-readable report

## Understanding the Graph

### Elements

- **Black Line**: Densitometry profile (vertical optical density across the tube)
- **Gray Dashed Line**: Background baseline (automatically detected)
- **Red Circles**: Detected peak positions
- **Colored Shaded Areas**: Individual bands
- **Colored Dashed Lines**: Band boundaries (movable)
- **X-Axis**: Position (pixels) from top to bottom of tube
- **Y-Axis**: Optical Density (0-1 normalized)

### Interpreting Results

**Optical Density (OD):**
- Represents darkness level at each position
- 0 = completely bright (no band)
- 1 = completely dark (maximum band intensity)
- Background ≈ baseline noise level

**Band AUC (Area Under Curve):**
- Total integrated density across band region
- Proportional to total protein/DNA in band
- Calculated after background subtraction

**Percentage:**
- What percentage of total band material is in this band
- All percentages sum to 100%
- Useful for comparing band intensities

## Advanced Features

### Background Detection

The application uses three complementary methods:
1. Low percentile of signal
2. Edge region analysis
3. Histogram mode analysis

The median of these three estimates is used as the background level.

### Peak Detection Algorithm

1. Smooths profile using Gaussian filter (σ=1.0)
2. Calculates dynamic prominence threshold
3. Identifies peaks with minimum height criterion
4. Filters spurious peaks based on prominence

### Band Definition

Default band width: ±5 pixels from peak center
- Adjustable by dragging boundaries
- Constrained within tube image boundaries

## Troubleshooting

### Issue: No bands detected

**Solutions:**
- Increase image contrast
- Check that bands are clearly visible (black on white)
- Ensure gel region is white (255) and bands are dark (<100)
- Try "Refresh Display" after loading

### Issue: Too many spurious peaks

**Solutions:**
- Manually adjust band boundaries to combine nearby peaks
- Verify image quality and contrast

### Issue: Incorrect background level

**Solutions:**
- Check image edges for noise or artifacts
- Verify background is truly black

### Issue: Export fails

**Solutions:**
- Ensure you have write permissions to the save location
- Check that disk space is available
- Try a different filename

## Testing with Sample Images

Generate a test image:
```bash
python test_image_generator.py
```

This creates `test_gel_sample.tif` with synthetic gel data for testing.

## Technical Details

### Supported Formats
- Input: TIF, TIFF (grayscale or RGB)
- Export: CSV, JSON, TXT

### Performance
- Image loading: <2 seconds (1000×800 px)
- Peak detection: <1 second per tube
- Export: <1 second

### Memory Requirements
- Typical gel image: ~2-5 MB
- RAM usage: ~100-200 MB during analysis

## Data Interpretation

### Example Analysis

Tube 5 with 3 bands:
```
Band 1: 35.2% - Most abundant protein
Band 2: 41.8% - Largest protein quantity
Band 3: 23.0% - Minor component
```

This could represent:
- Relative protein abundance
- Different glycosylation states
- Different protein isoforms
- Subunit composition

## Keyboard Shortcuts

Currently, keyboard shortcuts are not implemented. Planned for future versions:
- Ctrl+O: Open image
- Ctrl+E: Export
- Ctrl+D: Auto-detect
- Ctrl+Q: Quit

## Tips & Best Practices

1. **Image Preparation:**
   - Use high-contrast images
   - Ensure even lighting
   - Minimize shadows and artifacts

2. **Analysis:**
   - Review auto-detected bands carefully
   - Adjust boundaries only if necessary
   - Check background level makes sense

3. **Export:**
   - Use CSV for spreadsheet analysis
   - Use JSON for programmatic processing
   - Use Summary for reports

4. **Batch Analysis:**
   - Currently process one image at a time
   - Save results for each tube
   - Combine results in spreadsheet for comparison

## Limitations

1. **Tube Layout:** Fixed 6×2 grid layout (12 tubes from top row)
2. **Color Scheme:** Assumes black bands on white background
3. **No Calibration:** Results are in relative units (OD), not absolute quantities
4. **Single Tube:** Analyze one tube at a time (batch planned for future)

## Future Enhancements

- Batch processing of multiple images
- Customizable tube layouts
- Reference lane normalization
- Statistical comparison tools
- Live image calibration
- Custom color schemes
- Keyboard shortcuts

## Contact & Support

For issues or questions:
- Check this guide
- Review the README.md for technical details
- Contact your system administrator

## Version

Current Version: 1.0
Last Updated: 2024
