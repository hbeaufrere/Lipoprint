"""Handle exporting analysis results."""
import csv
import json
from datetime import datetime
import numpy as np


class AnalysisExporter:
    """Export densitometry analysis results in various formats."""

    def __init__(self, processor, analyzer, tube_index):
        """Initialize exporter with analysis data."""
        self.processor = processor
        self.analyzer = analyzer
        self.tube_index = tube_index
        self.timestamp = datetime.now().isoformat()

    def export_to_csv(self, filepath):
        """Export densitometry profile and band data to CSV."""
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(['Gel Electrophoresis Densitometry Analysis'])
                writer.writerow(['Generated:', self.timestamp])
                writer.writerow(['Tube Number:', self.tube_index + 1])
                writer.writerow([])

                # Profile data
                writer.writerow(['Position', 'Optical Density', 'Background', 'Adjusted OD'])
                profile = self.analyzer.profile
                background = self.analyzer.background_value

                for i, od in enumerate(profile):
                    adjusted = max(0, od - background)
                    writer.writerow([i, f'{od:.4f}', f'{background:.4f}', f'{adjusted:.4f}'])

                writer.writerow([])
                writer.writerow(['Band Analysis'])
                writer.writerow([])

                # Band details
                if self.analyzer.bands:
                    band_aucs, percentages = self.analyzer.calculate_band_percentages()

                    writer.writerow(['Band', 'Left', 'Right', 'AUC', 'Percentage'])
                    for i, (band, auc, pct) in enumerate(zip(self.analyzer.bands, band_aucs, percentages)):
                        writer.writerow([
                            i + 1,
                            band['left'],
                            band['right'],
                            f'{auc:.2f}',
                            f'{pct:.2f}%'
                        ])

            return filepath
        except Exception as e:
            raise ValueError(f"Failed to export to CSV: {str(e)}")

    def export_to_json(self, filepath):
        """Export analysis data to JSON format."""
        try:
            data = {
                'timestamp': self.timestamp,
                'tube_number': self.tube_index + 1,
                'background_od': float(self.analyzer.background_value),
                'profile': self.analyzer.profile.tolist(),
                'peaks': [int(p) for p in self.analyzer.peaks],
                'bands': []
            }

            if self.analyzer.bands:
                band_aucs, percentages = self.analyzer.calculate_band_percentages()

                for i, (band, auc, pct) in enumerate(zip(self.analyzer.bands, band_aucs, percentages)):
                    data['bands'].append({
                        'band_number': i + 1,
                        'left_boundary': int(band['left']),
                        'right_boundary': int(band['right']),
                        'area_under_curve': float(auc),
                        'percentage': float(pct)
                    })

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return filepath
        except Exception as e:
            raise ValueError(f"Failed to export to JSON: {str(e)}")

    def export_summary(self, filepath):
        """Export a summary report."""
        try:
            with open(filepath, 'w') as f:
                f.write('GEL ELECTROPHORESIS DENSITOMETRY ANALYSIS\n')
                f.write('=' * 50 + '\n\n')

                f.write(f'Analysis Date: {self.timestamp}\n')
                f.write(f'Tube Analyzed: {self.tube_index + 1}\n\n')

                f.write('PROFILE STATISTICS\n')
                f.write('-' * 50 + '\n')
                profile = self.analyzer.profile
                f.write(f'Profile Length: {len(profile)} pixels\n')
                f.write(f'Maximum OD: {np.max(profile):.4f}\n')
                f.write(f'Minimum OD: {np.min(profile):.4f}\n')
                f.write(f'Background OD: {self.analyzer.background_value:.4f}\n')
                f.write(f'Number of Detected Bands: {len(self.analyzer.bands)}\n\n')

                if self.analyzer.bands:
                    f.write('BAND COMPOSITION\n')
                    f.write('-' * 50 + '\n')
                    band_aucs, percentages = self.analyzer.calculate_band_percentages()
                    total_auc = sum(band_aucs)

                    f.write(f'{"Band":<6} {"Position":<20} {"AUC":<12} {"Percentage":<12}\n')
                    f.write('-' * 50 + '\n')

                    for i, (band, auc, pct) in enumerate(zip(self.analyzer.bands, band_aucs, percentages)):
                        position_range = f"{band['left']}-{band['right']}"
                        f.write(f'{i+1:<6} {position_range:<20} {auc:<12.2f} {pct:<12.2f}%\n')

            return filepath
        except Exception as e:
            raise ValueError(f"Failed to export summary: {str(e)}")
