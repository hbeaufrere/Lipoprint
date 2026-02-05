"""Image processing module for gel electrophoresis analysis."""
import numpy as np
import cv2
from PIL import Image
from scipy.signal import find_peaks
from scipy.ndimage import binary_dilation, label, gaussian_filter1d
import warnings


class GelImageProcessor:
    """Process gel electrophoresis images and extract densitometry profiles."""

    def __init__(self, image_path):
        """Initialize with image path."""
        self.image_path = image_path
        self.image = None
        self.gray_image = None
        self.inverted = None
        self.tubes = []
        self.load_image()

    def load_image(self):
        """Load image from file."""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError(f"Could not load image from {self.image_path}")

        # Convert to grayscale
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Invert: black bands become white (high values)
        self.inverted = 255 - self.gray_image

    def extract_tubes(self, num_tubes=12, rows=2):
        """
        Extract individual tube regions from the gel image.
        Assumes tubes are arranged in rows.
        """
        height, width = self.inverted.shape

        # Calculate approximate tube dimensions
        tubes_per_row = num_tubes // rows
        tube_width = width // tubes_per_row
        tube_height = height // rows

        self.tubes = []
        tube_idx = 0

        for row in range(rows):
            for col in range(tubes_per_row):
                if tube_idx >= num_tubes:
                    break

                y_start = row * tube_height
                y_end = (row + 1) * tube_height
                x_start = col * tube_width
                x_end = (col + 1) * tube_width

                tube_region = self.inverted[y_start:y_end, x_start:x_end]
                self.tubes.append({
                    'index': tube_idx,
                    'region': tube_region,
                    'y_range': (y_start, y_end),
                    'x_range': (x_start, x_end)
                })

                tube_idx += 1

        return self.tubes

    def get_densitometry_profile(self, tube_index):
        """
        Get the densitometry profile for a specific tube.
        Returns a 1D array of optical density values from top to bottom.
        """
        if not self.tubes or tube_index >= len(self.tubes):
            raise ValueError(f"Tube {tube_index} not found")

        tube_region = self.tubes[tube_index]['region']

        # Average across the width to get vertical profile
        profile = np.mean(tube_region, axis=1).astype(np.float32)

        # Normalize to 0-1 range (treating as optical density)
        profile_max = np.max(profile)
        if profile_max > 0:
            profile = profile / 255.0

        return profile

    def detect_background(self, profile, window_size=5):
        """
        Detect background level using multiple methods and take the most robust estimate.
        Returns the background baseline value.
        """
        if len(profile) == 0:
            return 0

        # Method 1: Use low percentile (handles most cases)
        percentile_bg = np.percentile(profile, 10)

        # Method 2: Use edges (where there's likely no band)
        edge_height = min(20, len(profile) // 5)
        edge_vals = np.concatenate([profile[:edge_height], profile[-edge_height:]])
        edge_bg = np.mean(edge_vals)

        # Method 3: Use mode-like approach with histogram
        hist, bin_edges = np.histogram(profile, bins=50)
        mode_idx = np.argmax(hist)
        mode_bg = (bin_edges[mode_idx] + bin_edges[mode_idx + 1]) / 2

        # Take the median of these estimates
        background = np.median([percentile_bg, edge_bg, mode_bg])

        return max(0, background)

    def detect_peaks_and_bands(self, profile, background_value=None,
                               prominence_threshold=None, distance=5):
        """
        Detect peaks (bands) in the densitometry profile.

        Returns:
            peaks: array of peak indices
            prominences: array of peak prominences
            background: background value used
        """
        if background_value is None:
            background_value = self.detect_background(profile)

        # Subtract background
        adjusted_profile = profile - background_value
        adjusted_profile = np.maximum(adjusted_profile, 0)

        # Auto-calculate prominence threshold if not provided
        if prominence_threshold is None:
            profile_range = np.max(adjusted_profile) - np.min(adjusted_profile)
            prominence_threshold = max(0.02, profile_range * 0.05)

        # Smooth the profile to reduce noise
        smoothed_profile = gaussian_filter1d(adjusted_profile, sigma=1.0)

        # Find peaks with prominence criterion
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            peaks, properties = find_peaks(
                smoothed_profile,
                prominence=prominence_threshold,
                distance=distance,
                height=prominence_threshold * 0.5
            )

        prominences = properties.get('prominences', np.zeros(len(peaks)))

        # Filter peaks by minimum height
        if len(peaks) > 0:
            heights = smoothed_profile[peaks]
            min_height = np.max(heights) * 0.15  # At least 15% of max peak
            valid = heights >= min_height
            peaks = peaks[valid]

        return peaks, prominences, background_value

    def calculate_band_auc(self, profile, peak_idx, left_cutoff, right_cutoff,
                          background_value=0):
        """
        Calculate the area under the curve (AUC) for a band between cutoff indices.
        Also calculates percentage of total AUC.
        """
        band_region = profile[left_cutoff:right_cutoff+1]
        adjusted_band = band_region - background_value
        adjusted_band = np.maximum(adjusted_band, 0)

        band_auc = np.sum(adjusted_band)

        return band_auc


class DensitometryAnalyzer:
    """Analyze densitometry data and manage band regions."""

    def __init__(self, profile, background_value=0):
        """Initialize with a densitometry profile."""
        self.profile = profile
        self.background_value = background_value
        self.peaks = []
        self.bands = []  # List of band definitions with cutoffs

    def detect_automatic_peaks(self, prominence_threshold=0.05, distance=5):
        """Automatically detect peaks."""
        processor = GelImageProcessor.__new__(GelImageProcessor)
        peaks, prominences, _ = processor.detect_peaks_and_bands(
            self.profile,
            self.background_value,
            prominence_threshold,
            distance
        )
        self.peaks = peaks
        return peaks

    def set_band_cutoffs(self, band_index, left_idx, right_idx):
        """Set manual cutoff points for a band."""
        if band_index >= len(self.bands):
            self.bands.append({'left': left_idx, 'right': right_idx})
        else:
            self.bands[band_index]['left'] = left_idx
            self.bands[band_index]['right'] = right_idx

    def calculate_band_percentages(self):
        """Calculate percentage of total AUC for each band."""
        processor = GelImageProcessor.__new__(GelImageProcessor)

        total_auc = 0
        band_aucs = []

        for band in self.bands:
            auc = processor.calculate_band_auc(
                self.profile,
                None,
                band['left'],
                band['right'],
                self.background_value
            )
            band_aucs.append(auc)
            total_auc += auc

        percentages = []
        if total_auc > 0:
            percentages = [(auc / total_auc) * 100 for auc in band_aucs]

        return band_aucs, percentages
