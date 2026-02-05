"""Main GUI application for gel electrophoresis densitometry analysis."""
import sys
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFileDialog, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

from image_processor import GelImageProcessor, DensitometryAnalyzer
from export_handler import AnalysisExporter


class DensitometryGraphCanvas(FigureCanvas):
    """Canvas for displaying densitometry graphs."""

    def __init__(self, parent=None, width=8, height=6):
        """Initialize the canvas."""
        self.fig = Figure(figsize=(width, height), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.profile = None
        self.peaks = []
        self.bands = []
        self.background_value = 0
        self.colors = self._generate_colors()
        self.cutoff_lines = {}
        self.selected_band = None
        self.line_artists = {}

        # Enable mouse events
        self.mpl_connect('button_press_event', self.on_click)
        self.mpl_connect('button_release_event', self.on_release)
        self.mpl_connect('motion_notify_event', self.on_motion)

    def _generate_colors(self):
        """Generate a list of distinct colors for bands."""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
                  '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#A8D8EA']
        return colors

    def plot_profile(self, profile, peaks, background_value, bands=None, analyzer=None):
        """Plot the densitometry profile with peaks and bands."""
        self.ax.clear()
        self.line_artists = {}
        self.profile = profile
        self.peaks = peaks
        self.background_value = background_value
        self.bands = bands or []
        self.analyzer = analyzer

        x = np.arange(len(profile))

        # Plot profile
        self.ax.plot(x, profile, 'k-', linewidth=2.5, label='Densitometry Profile', zorder=3)

        # Plot background line
        self.ax.axhline(y=background_value, color='gray', linestyle='--',
                       linewidth=1.5, label=f'Background: {background_value:.3f}', zorder=1)

        # Plot peaks
        if len(peaks) > 0:
            self.ax.plot(peaks, profile[peaks], 'o', color='red', markersize=8,
                        label='Detected Peaks', zorder=4)

        # Plot bands with color coding
        if bands:
            for i, band in enumerate(bands):
                left = band['left']
                right = band['right']
                color = self.colors[i % len(self.colors)]

                # Fill under the curve for this band
                band_x = x[left:right+1]
                band_y = profile[left:right+1]
                self.ax.fill_between(band_x, background_value, band_y,
                                    alpha=0.3, color=color, zorder=2)

                # Draw vertical cutoff lines with labels
                line_left = self.ax.axvline(x=left, color=color, linestyle='--',
                                           linewidth=2.5, zorder=3)
                line_right = self.ax.axvline(x=right, color=color, linestyle='--',
                                            linewidth=2.5, zorder=3)

                self.line_artists[f'band_{i}_left'] = line_left
                self.line_artists[f'band_{i}_right'] = line_right

                # Store line references for interactive editing
                self.cutoff_lines[f'band_{i}_left'] = left
                self.cutoff_lines[f'band_{i}_right'] = right

        self.ax.set_xlabel('Position (pixels)', fontsize=12)
        self.ax.set_ylabel('Optical Density', fontsize=12)
        self.ax.set_title('Gel Densitometry Profile (Click lines to adjust)',
                         fontsize=14, fontweight='bold')
        self.ax.legend(loc='upper right', fontsize=9)
        self.ax.grid(True, alpha=0.3, zorder=0)
        self.fig.tight_layout()
        self.draw()

    def on_click(self, event):
        """Handle mouse click on the canvas."""
        if not event.inaxes or not self.bands:
            return

        x_click = event.xdata
        if x_click is None:
            return

        # Find the nearest cutoff line
        min_distance = float('inf')
        nearest_line = None

        for line_key, x_pos in self.cutoff_lines.items():
            distance = abs(x_click - x_pos)
            if distance < min_distance and distance < 10:
                min_distance = distance
                nearest_line = line_key

        if nearest_line:
            self.selected_band = nearest_line

    def on_motion(self, event):
        """Handle mouse motion for interactive cutoff adjustment."""
        if not event.inaxes or self.selected_band is None or not self.profile:
            return

        x_pos = event.xdata
        if x_pos is None:
            return

        # Constrain to profile bounds
        x_pos = max(0, min(len(self.profile) - 1, int(x_pos)))

        # Update cutoff position
        self.cutoff_lines[self.selected_band] = x_pos

        # Update band definitions
        for i, band in enumerate(self.bands):
            if f'band_{i}_left' == self.selected_band:
                band['left'] = x_pos
            elif f'band_{i}_right' == self.selected_band:
                band['right'] = x_pos

        # Redraw with updated cutoffs
        if self.analyzer:
            self.plot_profile(self.profile, self.peaks, self.background_value,
                            self.bands, self.analyzer)

    def on_release(self, event):
        """Handle mouse release to finalize cutoff adjustment."""
        self.selected_band = None


class GelDensitometryApp(QMainWindow):
    """Main application window for gel densitometry analysis."""

    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.setWindowTitle('Gel Electrophoresis Densitometry Analysis')
        self.setGeometry(100, 100, 1400, 800)

        self.processor = None
        self.analyzer = None
        self.current_tube_index = 0

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Top control panel
        control_panel = self.create_control_panel()
        main_layout.addLayout(control_panel)

        # Splitter for graph and info
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Graph canvas
        self.canvas = DensitometryGraphCanvas(width=10, height=6)
        splitter.addWidget(self.canvas)

        # Info panel
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

    def create_control_panel(self):
        """Create the control panel with file upload and tube selection."""
        layout = QHBoxLayout()

        # File upload button
        upload_btn = QPushButton('Load TIF Image')
        upload_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        upload_btn.clicked.connect(self.load_image)
        layout.addWidget(upload_btn)

        # Tube selection dropdown
        layout.addWidget(QLabel('Select Tube:'))
        self.tube_combo = QComboBox()
        self.tube_combo.currentIndexChanged.connect(self.on_tube_changed)
        layout.addWidget(self.tube_combo)

        # Auto-detect peaks button
        auto_peaks_btn = QPushButton('Auto-Detect Peaks')
        auto_peaks_btn.setStyleSheet("background-color: #2196F3; color: white;")
        auto_peaks_btn.clicked.connect(self.auto_detect_peaks)
        layout.addWidget(auto_peaks_btn)

        # Refresh display button
        refresh_btn = QPushButton('Refresh Display')
        refresh_btn.clicked.connect(self.refresh_display)
        layout.addWidget(refresh_btn)

        # Export buttons
        export_csv_btn = QPushButton('Export CSV')
        export_csv_btn.clicked.connect(self.export_csv)
        layout.addWidget(export_csv_btn)

        export_json_btn = QPushButton('Export JSON')
        export_json_btn.clicked.connect(self.export_json)
        layout.addWidget(export_json_btn)

        export_summary_btn = QPushButton('Export Summary')
        export_summary_btn.clicked.connect(self.export_summary)
        layout.addWidget(export_summary_btn)

        layout.addStretch()
        return layout

    def create_info_panel(self):
        """Create the information panel showing band details."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel('Band Analysis')
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(title)

        self.info_text = QLabel('No image loaded.')
        self.info_text.setWordWrap(True)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.info_text)

        layout.addStretch()
        return widget

    def load_image(self):
        """Load a TIF image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Gel Image',
            '',
            'TIF Images (*.tif *.tiff);;All Files (*)'
        )

        if not file_path:
            return

        try:
            self.processor = GelImageProcessor(file_path)
            self.processor.extract_tubes(num_tubes=12, rows=2)

            # Populate tube combo box
            self.tube_combo.blockSignals(True)
            self.tube_combo.clear()
            for i in range(1, 13):
                self.tube_combo.addItem(f'Tube {i}', i-1)
            self.tube_combo.blockSignals(False)

            self.current_tube_index = 0
            self.display_tube(0)

            QMessageBox.information(self, 'Success',
                                   f'Image loaded successfully!\nFound {len(self.processor.tubes)} tubes.')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load image: {str(e)}')

    def on_tube_changed(self, index):
        """Handle tube selection change."""
        if index >= 0 and self.processor:
            self.current_tube_index = index
            self.display_tube(index)

    def display_tube(self, tube_index):
        """Display the densitometry profile for a tube."""
        if not self.processor:
            return

        try:
            # Get profile
            profile = self.processor.get_densitometry_profile(tube_index)

            # Detect background
            background = self.processor.detect_background(profile)

            # Create analyzer
            self.analyzer = DensitometryAnalyzer(profile, background)

            # For initial display, just show the profile
            self.canvas.plot_profile(profile, np.array([]), background, analyzer=self.analyzer)

            self.update_info_panel()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to analyze tube: {str(e)}')

    def auto_detect_peaks(self):
        """Automatically detect peaks and set up bands."""
        if not self.analyzer:
            QMessageBox.warning(self, 'Warning', 'Please load an image and select a tube first.')
            return

        try:
            peaks = self.analyzer.detect_automatic_peaks(prominence_threshold=0.05)

            # Create bands from peaks
            self.analyzer.bands = []
            peak_width = 5

            for peak in peaks:
                left = max(0, peak - peak_width)
                right = min(len(self.analyzer.profile) - 1, peak + peak_width)
                self.analyzer.bands.append({'left': left, 'right': right, 'peak': peak})

            # Plot with bands
            self.canvas.plot_profile(
                self.analyzer.profile,
                peaks,
                self.analyzer.background_value,
                self.analyzer.bands,
                analyzer=self.analyzer
            )

            self.update_info_panel()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to detect peaks: {str(e)}')

    def refresh_display(self):
        """Refresh the current tube display."""
        if self.analyzer and self.processor:
            self.canvas.plot_profile(
                self.analyzer.profile,
                self.analyzer.peaks,
                self.analyzer.background_value,
                self.analyzer.bands,
                analyzer=self.analyzer
            )
            self.update_info_panel()

    def export_csv(self):
        """Export current analysis to CSV format."""
        if not self.analyzer or not self.processor:
            QMessageBox.warning(self, 'Warning', 'No analysis data to export.')
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            'Save Analysis as CSV',
            f'tube_{self.current_tube_index + 1}_analysis.csv',
            'CSV Files (*.csv);;All Files (*)'
        )

        if not filepath:
            return

        try:
            exporter = AnalysisExporter(self.processor, self.analyzer, self.current_tube_index)
            exporter.export_to_csv(filepath)
            QMessageBox.information(self, 'Success', f'Analysis exported to:\n{filepath}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to export: {str(e)}')

    def export_json(self):
        """Export current analysis to JSON format."""
        if not self.analyzer or not self.processor:
            QMessageBox.warning(self, 'Warning', 'No analysis data to export.')
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            'Save Analysis as JSON',
            f'tube_{self.current_tube_index + 1}_analysis.json',
            'JSON Files (*.json);;All Files (*)'
        )

        if not filepath:
            return

        try:
            exporter = AnalysisExporter(self.processor, self.analyzer, self.current_tube_index)
            exporter.export_to_json(filepath)
            QMessageBox.information(self, 'Success', f'Analysis exported to:\n{filepath}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to export: {str(e)}')

    def export_summary(self):
        """Export current analysis as a summary report."""
        if not self.analyzer or not self.processor:
            QMessageBox.warning(self, 'Warning', 'No analysis data to export.')
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            'Save Summary Report',
            f'tube_{self.current_tube_index + 1}_summary.txt',
            'Text Files (*.txt);;All Files (*)'
        )

        if not filepath:
            return

        try:
            exporter = AnalysisExporter(self.processor, self.analyzer, self.current_tube_index)
            exporter.export_summary(filepath)
            QMessageBox.information(self, 'Success', f'Summary exported to:\n{filepath}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to export: {str(e)}')

    def update_info_panel(self):
        """Update the information panel with band details."""
        if not self.analyzer:
            return

        try:
            band_aucs, percentages = self.analyzer.calculate_band_percentages()

            colors = self.canvas.colors

            info = f'<b style="font-size:14px">Tube {self.current_tube_index + 1}</b><br>'
            info += f'<br><b>Profile Statistics:</b><br>'
            info += f'Background OD: {self.analyzer.background_value:.4f}<br>'
            info += f'Peak OD: {np.max(self.analyzer.profile):.4f}<br>'
            info += f'Number of Bands: {len(self.analyzer.bands)}<br><br>'

            if len(self.analyzer.bands) > 0:
                info += '<b>Band Composition:</b><br>'
                total_auc = sum(band_aucs)
                for i, (band, auc, pct) in enumerate(zip(self.analyzer.bands, band_aucs, percentages)):
                    color = colors[i % len(colors)]
                    info += f'<span style="color:{color}">■</span> '
                    info += f'Band {i+1}: <b>{pct:.1f}%</b> (AUC: {auc:.2f})<br>'
                    info += f'&nbsp;&nbsp;Range: {band["left"]} - {band["right"]} px<br>'

            self.info_text.setText(info)

        except Exception as e:
            self.info_text.setText(f'Error updating info: {str(e)}')


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    window = GelDensitometryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
