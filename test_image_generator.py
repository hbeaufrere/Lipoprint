"""Generate synthetic gel electrophoresis test images for testing."""
import numpy as np
from PIL import Image
import random


def generate_gel_image(width=800, height=800, num_tubes=12, num_bands_per_tube=3,
                       output_path='test_gel.tif'):
    """
    Generate a synthetic gel electrophoresis image.

    Parameters:
    - width, height: Image dimensions
    - num_tubes: Number of tubes (should be 12)
    - num_bands_per_tube: Number of bands per tube
    - output_path: Path to save the TIF image
    """
    # Create black background
    image = np.zeros((height, width, 3), dtype=np.uint8)

    # Calculate tube dimensions
    tubes_per_row = 6
    rows = 2
    tube_width = width // tubes_per_row
    tube_height = height // rows

    # Generate tubes
    tube_idx = 0
    for row in range(rows):
        for col in range(tubes_per_row):
            if tube_idx >= num_tubes:
                break

            # Tube position
            x_start = col * tube_width
            y_start = row * tube_height
            x_end = x_start + tube_width
            y_end = y_start + tube_height

            # Create white gel region for this tube (with margins)
            margin_x = int(tube_width * 0.1)
            margin_y = int(tube_height * 0.05)

            gel_x_start = x_start + margin_x
            gel_x_end = x_end - margin_x
            gel_y_start = y_start + margin_y
            gel_y_end = y_end - margin_y

            # Fill gel region with white
            image[gel_y_start:gel_y_end, gel_x_start:gel_x_end] = 255

            # Add bands to this tube
            num_bands = num_bands_per_tube + random.randint(-1, 1)
            band_positions = np.linspace(gel_y_start + 10, gel_y_end - 10, num_bands)

            for band_y in band_positions:
                band_y = int(band_y)
                band_width = int((gel_x_end - gel_x_start) * 0.6)
                band_x_center = (gel_x_start + gel_x_end) // 2

                # Create band with some variability
                band_x_start = band_x_center - band_width // 2
                band_x_end = band_x_center + band_width // 2
                band_height = random.randint(8, 20)
                band_intensity = random.randint(30, 100)

                for by in range(max(gel_y_start, band_y - band_height // 2),
                               min(gel_y_end, band_y + band_height // 2)):
                    # Create a Gaussian-like band profile
                    distance = abs(by - band_y)
                    intensity = band_intensity * np.exp(-(distance ** 2) / (2 * (band_height / 4) ** 2))
                    image[by, band_x_start:band_x_end] = np.maximum(
                        image[by, band_x_start:band_x_end].astype(float) - intensity, 0
                    ).astype(np.uint8)

            tube_idx += 1

    # Add some background noise
    noise = np.random.normal(0, 3, image.shape)
    image = np.clip(image.astype(float) + noise, 0, 255).astype(np.uint8)

    # Convert to grayscale and save
    gray_image = np.mean(image, axis=2).astype(np.uint8)

    # Save as TIF
    pil_image = Image.fromarray(gray_image, mode='L')
    pil_image.save(output_path, format='TIFF')
    print(f"Generated test image: {output_path} ({width}x{height})")

    return output_path


if __name__ == '__main__':
    # Generate a test image
    generate_gel_image(width=960, height=800, num_tubes=12, num_bands_per_tube=3,
                      output_path='test_gel_sample.tif')
    print("Test image created successfully!")
