# Gel Densitometry - API Documentation

Complete API reference for the gel electrophoresis densitometry analysis system.

## Module Overview

### image_processor.py

Image processing and densitometry analysis core module.

#### GelImageProcessor

Main class for loading and processing gel images.

**Methods:**

##### `__init__(image_path)`
- **Parameters:** `image_path` (str) - Path to TIF image file
- **Returns:** GelImageProcessor instance
- **Raises:** ValueError if image cannot be loaded

```python
processor = GelImageProcessor('gel_image.tif')
```

##### `load_image()`
- **Returns:** None
- **Effects:** Loads image, converts to grayscale, inverts colors
- Called automatically by `__init__`

##### `extract_tubes(num_tubes=12, rows=2)`
- **Parameters:**
  - `num_tubes` (int): Total number of tubes to extract
  - `rows` (int): Number of rows in grid
- **Returns:** List of tube region dictionaries
- **Tube dictionary contains:**
  - `index`: Tube number (0-based)
  - `region`: 2D numpy array of inverted pixel values
  - `y_range`: (y_start, y_end) tuple
  - `x_range`: (x_start, x_end) tuple

```python
processor.extract_tubes(num_tubes=12, rows=2)
tubes = processor.tubes  # List of 12 tube regions
```

##### `get_densitometry_profile(tube_index)`
- **Parameters:** `tube_index` (int) - 0-based tube number
- **Returns:** 1D numpy array (float32) - Optical density profile
- **Range:** 0.0 to 1.0 (normalized)
- **Length:** Height of tube region

```python
profile = processor.get_densitometry_profile(0)
# Returns array of density values from top to bottom
```

##### `detect_background(profile, window_size=5)`
- **Parameters:**
  - `profile` (ndarray): 1D densitometry profile
  - `window_size` (int): Window size for analysis (unused, kept for compatibility)
- **Returns:** float - Background OD value
- **Algorithm:** Median of three estimates (percentile, edge, mode)

```python
background = processor.detect_background(profile)
# Returns background OD ~0.05 for typical images
```

##### `detect_peaks_and_bands(profile, background_value=None, prominence_threshold=None, distance=5)`
- **Parameters:**
  - `profile` (ndarray): 1D densitometry profile
  - `background_value` (float): Background OD (auto-detected if None)
  - `prominence_threshold` (float): Peak prominence threshold (auto-calculated if None)
  - `distance` (int): Minimum pixel distance between peaks
- **Returns:** Tuple of (peaks, prominences, background_value)
  - `peaks` (ndarray): Array of peak indices
  - `prominences` (ndarray): Peak prominence values
  - `background_value` (float): Background used

```python
peaks, prominences, background = processor.detect_peaks_and_bands(profile)
print(f"Found {len(peaks)} peaks at positions: {peaks}")
```

##### `calculate_band_auc(profile, peak_idx, left_cutoff, right_cutoff, background_value=0)`
- **Parameters:**
  - `profile` (ndarray): 1D densitometry profile
  - `peak_idx` (int): Peak index (for reference only)
  - `left_cutoff` (int): Left boundary index
  - `right_cutoff` (int): Right boundary index
  - `background_value` (float): Background to subtract
- **Returns:** float - Area under curve for band

```python
auc = processor.calculate_band_auc(profile, 10, 5, 15, 0.05)
# Returns area value ~2.5 for typical band
```

---

### DensitometryAnalyzer

High-level interface for analysis and band management.

**Methods:**

##### `__init__(profile, background_value=0)`
- **Parameters:**
  - `profile` (ndarray): 1D densitometry profile
  - `background_value` (float): Background OD value
- **Returns:** DensitometryAnalyzer instance

```python
analyzer = DensitometryAnalyzer(profile, background=0.05)
```

##### `detect_automatic_peaks(prominence_threshold=0.05, distance=5)`
- **Parameters:**
  - `prominence_threshold` (float): Peak prominence threshold
  - `distance` (int): Minimum distance between peaks
- **Returns:** ndarray - Peak indices
- **Effects:** Updates internal `peaks` list

```python
peaks = analyzer.detect_automatic_peaks(prominence_threshold=0.05)
```

##### `set_band_cutoffs(band_index, left_idx, right_idx)`
- **Parameters:**
  - `band_index` (int): Band number
  - `left_idx` (int): Left boundary pixel
  - `right_idx` (int): Right boundary pixel
- **Returns:** None
- **Effects:** Creates or updates band in `bands` list

```python
analyzer.set_band_cutoffs(0, 10, 20)  # Band 0: pixels 10-20
```

##### `calculate_band_percentages()`
- **Parameters:** None
- **Returns:** Tuple of (band_aucs, percentages)
  - `band_aucs` (list): AUC for each band
  - `percentages` (list): Percentage for each band (sum to 100)

```python
aucs, percentages = analyzer.calculate_band_percentages()
for i, pct in enumerate(percentages):
    print(f"Band {i}: {pct:.1f}%")
```

**Properties:**

- `profile` (ndarray): Densitometry profile
- `background_value` (float): Background OD
- `peaks` (ndarray): Detected peak positions
- `bands` (list): List of band dictionaries
  - Each band: `{'left': int, 'right': int, 'peak': int (optional)}`

---

### export_handler.py

Export analysis results in various formats.

#### AnalysisExporter

**Methods:**

##### `__init__(processor, analyzer, tube_index)`
- **Parameters:**
  - `processor` (GelImageProcessor): Image processor instance
  - `analyzer` (DensitometryAnalyzer): Analysis data
  - `tube_index` (int): Tube number being exported
- **Returns:** AnalysisExporter instance

```python
exporter = AnalysisExporter(processor, analyzer, tube_index=0)
```

##### `export_to_csv(filepath)`
- **Parameters:** `filepath` (str) - Output CSV file path
- **Returns:** str - File path
- **Format:** CSV with headers, profile data, band summary
- **Raises:** ValueError if export fails

```python
exporter.export_to_csv('analysis.csv')
```

##### `export_to_json(filepath)`
- **Parameters:** `filepath` (str) - Output JSON file path
- **Returns:** str - File path
- **Format:** JSON with timestamp, profile, peaks, bands
- **Raises:** ValueError if export fails

```python
exporter.export_to_json('analysis.json')
```

##### `export_summary(filepath)`
- **Parameters:** `filepath` (str) - Output text file path
- **Returns:** str - File path
- **Format:** Human-readable text report
- **Raises:** ValueError if export fails

```python
exporter.export_summary('report.txt')
```

---

## Usage Examples

### Basic Workflow

```python
from image_processor import GelImageProcessor, DensitometryAnalyzer

# Load image
processor = GelImageProcessor('gel_image.tif')
processor.extract_tubes(num_tubes=12, rows=2)

# Analyze tube 0
profile = processor.get_densitometry_profile(0)
analyzer = DensitometryAnalyzer(profile)

# Auto-detect bands
peaks = analyzer.detect_automatic_peaks()

# Create bands around peaks
for peak in peaks:
    left = max(0, peak - 5)
    right = min(len(profile) - 1, peak + 5)
    analyzer.set_band_cutoffs(len(analyzer.bands), left, right)

# Get results
aucs, percentages = analyzer.calculate_band_percentages()
print(f"Bands found: {len(analyzer.bands)}")
for i, pct in enumerate(percentages):
    print(f"  Band {i+1}: {pct:.1f}%")
```

### Batch Processing

```python
from pathlib import Path
from export_handler import AnalysisExporter

def analyze_all_tubes(image_path, output_dir):
    processor = GelImageProcessor(image_path)
    processor.extract_tubes(num_tubes=12, rows=2)

    results = {}
    for tube_idx in range(12):
        profile = processor.get_densitometry_profile(tube_idx)
        analyzer = DensitometryAnalyzer(profile)
        peaks = analyzer.detect_automatic_peaks()

        # Create bands (simplified)
        for peak in peaks:
            analyzer.set_band_cutoffs(len(analyzer.bands),
                                     max(0, peak - 5),
                                     min(len(profile) - 1, peak + 5))

        # Export
        exporter = AnalysisExporter(processor, analyzer, tube_idx)
        csv_path = Path(output_dir) / f'tube_{tube_idx + 1}.csv'
        exporter.export_to_csv(str(csv_path))

        results[tube_idx] = analyzer.calculate_band_percentages()

    return results

# Run
results = analyze_all_tubes('gel.tif', './output')
```

### Custom Peak Detection

```python
# Adjust detection sensitivity
profile = processor.get_densitometry_profile(0)
peaks, prominences, bg = processor.detect_peaks_and_bands(
    profile,
    prominence_threshold=0.10  # Stricter detection
)

# Or auto-calculate with different distance
peaks2, _, _ = processor.detect_peaks_and_bands(
    profile,
    distance=10  # Require more distance between peaks
)
```

### Manual Band Definition

```python
analyzer = DensitometryAnalyzer(profile, background=0.05)

# Define bands manually without auto-detection
analyzer.set_band_cutoffs(0, 10, 25)  # Band 1: pixels 10-25
analyzer.set_band_cutoffs(1, 50, 75)  # Band 2: pixels 50-75
analyzer.set_band_cutoffs(2, 100, 120)  # Band 3: pixels 100-120

aucs, percentages = analyzer.calculate_band_percentages()
```

---

## Data Structures

### Tube Dictionary
```python
{
    'index': 0,                      # Tube number (0-based)
    'region': ndarray,               # 2D pixel array (height×width)
    'y_range': (0, 400),            # Vertical extent
    'x_range': (0, 160)             # Horizontal extent
}
```

### Band Dictionary
```python
{
    'left': 10,                     # Left boundary (pixels)
    'right': 25,                    # Right boundary (pixels)
    'peak': 18                      # Peak position (optional)
}
```

### Export Data (JSON)
```json
{
    "timestamp": "2024-02-05T12:34:56.789123",
    "tube_number": 1,
    "background_od": 0.0456,
    "profile": [0.045, 0.047, ..., 0.043],
    "peaks": [18, 52, 105],
    "bands": [
        {
            "band_number": 1,
            "left_boundary": 10,
            "right_boundary": 25,
            "area_under_curve": 2.34,
            "percentage": 35.2
        },
        ...
    ]
}
```

---

## Constants and Defaults

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| num_tubes | 12 | 1-24 | Usually 12 (6×2 grid) |
| rows | 2 | 1-4 | Grid rows |
| prominence_threshold | auto | 0.01-0.2 | Auto-calculated from signal |
| distance | 5 | 1-50 | Minimum pixels between peaks |
| background_method | median | - | Uses 3-method consensus |
| gaussian_sigma | 1.0 | 0.5-2.0 | Smoothing for peak detection |

---

## Error Handling

```python
try:
    processor = GelImageProcessor('invalid_path.tif')
except ValueError as e:
    print(f"Failed to load: {e}")

try:
    exporter.export_to_csv('/read_only/file.csv')
except ValueError as e:
    print(f"Export failed: {e}")
```

---

## Performance Considerations

| Operation | Time | RAM |
|-----------|------|-----|
| Load image (1000×800) | <1s | 3MB |
| Extract tubes | <100ms | 2MB |
| Get profile | <50ms | 1MB |
| Detect peaks | <500ms | 1MB |
| Calculate AUC | <10ms | <1MB |
| Export CSV | <100ms | <1MB |

---

## Integration Notes

For programmatic integration:

1. Import required modules
2. Create GelImageProcessor with image path
3. Extract tubes
4. For each tube: create profile → create analyzer → detect/set bands
5. Export or query results

All operations are synchronous (blocking). For GUI integration, consider threading.

---

## Version

API Version: 1.0
Last Updated: 2024
