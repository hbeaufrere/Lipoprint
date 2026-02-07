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
        """Load image from file and crop to top half only."""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError(f"Could not load image from {self.image_path}")

        # Crop to top half only (remove bottom row of tubes we don't need)
        height = self.image.shape[0]
        self.image = self.image[:height//2, :]

        # Convert to grayscale
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Use grayscale directly - invert during profile calculation instead
        # In gel: white gel = 255 (high), black bands = 0 (low)
        # We want OD: white (no band) = 0, black (band) = 1
        # So: OD = 1 - (normalized_pixel) = 1 - (gray/255)
        self.inverted = self.gray_image

    def extract_tubes(self, num_tubes=12, tubes_per_row=20, roi=None):
        """
        Extract white tube rectangles from gel image.

        Can use fixed ROI (Region of Interest) for consistency with Lipoware,
        or AUTO-DETECT tubes if ROI not provided.

        Args:
            num_tubes: Number of tubes to extract (default: 12)
            tubes_per_row: Expected tubes per row (default: 20)
            roi: Optional tuple (left, top, width, height) to define fixed ROI.
                 If provided, tubes are extracted within this region.
                 If None, uses auto-detection.
        """
        height, width = self.gray_image.shape  # Already cropped to top half

        # If ROI provided, crop to it first
        if roi is not None:
            roi_left, roi_top, roi_width, roi_height = roi
            roi_region = self.gray_image[roi_top:roi_top+roi_height, roi_left:roi_left+roi_width]
            working_image = roi_region
            roi_offset_x = roi_left
            roi_offset_y = roi_top
        else:
            working_image = self.gray_image
            roi_offset_x = 0
            roi_offset_y = 0

        region_height, region_width = working_image.shape

        # Find white columns by averaging pixel intensity vertically
        # White tubes have HIGH gray values (close to 255)
        column_brightness = np.mean(working_image, axis=0)

        # Threshold to find white regions (tubes are bright, background is dark)
        # White tubes should have average > 150
        is_white = column_brightness > 150

        # Find boundaries of white regions (tube starts and ends)
        transitions = np.diff(is_white.astype(int))
        starts = np.where(transitions == 1)[0] + 1  # Where white begins
        ends = np.where(transitions == -1)[0]        # Where white ends

        # Match starts and ends to get tube boundaries
        if len(starts) > 0 and len(ends) > 0:
            if starts[0] > ends[0]:
                ends = ends[1:]
            if len(ends) > len(starts):
                ends = ends[:len(starts)]

        tube_boundaries = list(zip(starts[:len(ends)], ends[:len(starts)]))

        self.tubes = []

        # Extract first 12 detected tubes
        for tube_idx in range(min(num_tubes, len(tube_boundaries))):
            x_start, x_end = tube_boundaries[tube_idx]
            y_start = 0
            y_end = region_height  # Use full height of working region

            # Extract tube region - crop horizontally to remove black edges
            tube_region_full = working_image[y_start:y_end, x_start:x_end]

            # Find white rows (remove black top/bottom edges)
            row_brightness = np.mean(tube_region_full, axis=1)
            white_rows = row_brightness > 150

            if np.any(white_rows):
                # Find first and last white rows
                white_indices = np.where(white_rows)[0]
                y_start_white = white_indices[0]
                y_end_white = white_indices[-1] + 1
                tube_region = tube_region_full[y_start_white:y_end_white, :]
            else:
                tube_region = tube_region_full

            # Store with absolute coordinates (relative to full image, not ROI)
            self.tubes.append({
                'index': tube_idx,
                'region': tube_region,
                'y_range': (y_start + roi_offset_y, y_end + roi_offset_y),
                'x_range': (x_start + roi_offset_x, x_end + roi_offset_x),
                'original_coords': (y_start + roi_offset_y, y_end + roi_offset_y,
                                    x_start + roi_offset_x, x_end + roi_offset_x)
            })

        return self.tubes

    def get_densitometry_profile(self, tube_index, auto_crop=True):
        """
        Get the densitometry profile for a specific tube.
        Returns a 1D array of optical density values from top to bottom.
        OD scale: 0 = pure white (no band), higher = darker (band present)
        """
        if not self.tubes or tube_index >= len(self.tubes):
            raise ValueError(f"Tube {tube_index} not found")

        tube_region = self.tubes[tube_index]['region']

        # Average across the FULL width to get vertical profile
        profile = np.mean(tube_region, axis=1).astype(np.float32)

        # Convert to optical density: white (no band) = 0, black (band) = 1
        # OD = 1 - (normalized_gray) = 1 - (gray_value / 255)
        profile = 1.0 - (profile / 255.0)

        # Auto-crop to relevant region (from white to darkest band)
        if auto_crop:
            profile, crop_indices = self._auto_crop_profile(profile)
            # Store crop info for later use
            self.last_crop_indices = crop_indices
        else:
            self.last_crop_indices = (0, len(profile))

        return profile

    def _auto_crop_profile(self, profile):
        """
        Auto-crop profile to start at first significant band and end after last.
        Returns cropped profile and crop indices.
        """
        # Find regions with actual signal (not pure white/background)
        # Threshold: anything darker than pure white
        threshold = 0.95  # Only consider pixels darker than this as background (pure white is 1.0)

        # Find where signal (darker pixels) starts
        signal_mask = profile < threshold

        if not np.any(signal_mask):
            # No bands detected, return as is
            return profile, (0, len(profile))

        # Find first and last signal regions
        signal_indices = np.where(signal_mask)[0]

        if len(signal_indices) == 0:
            return profile, (0, len(profile))

        # Add margin to include context but remove pure white edges
        margin = max(3, len(profile) // 50)  # Small margin

        start_idx = max(0, signal_indices[0] - margin)
        end_idx = min(len(profile), signal_indices[-1] + margin)

        cropped = profile[start_idx:end_idx]

        return cropped, (start_idx, end_idx)

    def detect_background(self, profile, window_size=5):
        """
        Detect background level using multiple methods and take the most robust estimate.
        Returns the background baseline value (should be close to 0 for white gel areas).
        """
        if len(profile) == 0:
            return 0

        # Filter out pure white pixels (>0.95) which are not part of the gel matrix
        # Only consider pixels that are actually part of the gel/bands
        gel_pixels = profile[profile < 0.95]

        if len(gel_pixels) == 0:
            # All pixels are white, no actual gel data
            return 0

        # Method 1: Use low percentile of gel pixels only
        percentile_bg = np.percentile(gel_pixels, 5)

        # Method 2: Use minimum value in gel region
        min_bg = np.min(gel_pixels)

        # Take the minimum to get the darkest "white" (lowest OD gel background)
        background = min(percentile_bg, min_bg)

        # Ensure it's not negative and not too high
        return np.clip(background, 0, 0.3)  # Background should be very low for white gel

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
            # Use adaptive threshold based on profile characteristics
            profile_max = np.max(adjusted_profile)
            profile_std = np.std(adjusted_profile)

            # Prominence should be at least std, but not more than 5% of max
            prominence_threshold = max(profile_std * 0.5, profile_max * 0.02)
            prominence_threshold = min(prominence_threshold, profile_max * 0.10)

        # Smooth the profile to reduce noise
        smoothed_profile = gaussian_filter1d(adjusted_profile, sigma=0.8)

        # Find peaks with adaptive parameters
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            peaks, properties = find_peaks(
                smoothed_profile,
                prominence=prominence_threshold,
                distance=max(2, distance // 2),  # More sensitive distance for cropped profiles
                height=prominence_threshold * 0.3  # Lower height threshold
            )

        prominences = properties.get('prominences', np.zeros(len(peaks)))

        # Filter peaks by minimum height
        if len(peaks) > 0:
            heights = smoothed_profile[peaks]
            max_height = np.max(heights)
            if max_height > 0:
                min_height = max_height * 0.10  # At least 10% of max peak (more sensitive)
                valid = heights >= min_height
                peaks = peaks[valid]
                prominences = prominences[valid] if len(prominences) > 0 else prominences

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

    def calculate_band_percentages(self, trim_ratio=0.25):
        """Calculate percentage of total AUC for each band.

        Args:
            trim_ratio: Fraction of band height to trim from the top (default: 0.25 = 25%)
        """
        processor = GelImageProcessor.__new__(GelImageProcessor)

        total_auc = 0
        band_aucs = []

        for band in self.bands:
            left = band['left']
            right = band['right']

            # Apply trim to remove top fraction of band
            if trim_ratio > 0:
                trim_amount = int((right - left) * trim_ratio)
                left = left + trim_amount

            auc = processor.calculate_band_auc(
                self.profile,
                None,
                left,
                right,
                self.background_value
            )
            band_aucs.append(auc)
            total_auc += auc

        percentages = []
        if total_auc > 0:
            percentages = [(auc / total_auc) * 100 for auc in band_aucs]

        return band_aucs, percentages
