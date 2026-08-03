#!/usr/bin/env python3
"""
prep_photo.py

Production-ready image processing script for GitHub Profile ASCII portrait pipeline.

Pipeline steps:
1. EXIF orientation auto-correction
2. Background removal using rembg
3. Subject compositing onto pure white canvas
4. Automatic face/subject detection and centering
5. Aspect-ratio preserving cropping & resizing
6. Grayscale conversion & Gamma correction
7. Histogram normalization (min-max full dynamic range)
8. CLAHE (Contrast Limited Adaptive Histogram Equalization)
9. Bilateral edge-preserving denoising & subtle sharpening
10. High-compression PNG export

Author: Senior Python Graphics Engineer
"""

import logging
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps
from rembg import remove

# ==============================================================================
# CONFIGURABLE CONSTANTS
# ==============================================================================

# Default file paths
DEFAULT_INPUT_PATH = Path("assets/source-photo.jpg")
DEFAULT_OUTPUT_PATH = Path("assets/source-prepped.png")

# Processing hyperparameters
MAX_DIMENSION = 800           # Maximum dimension (width or height) after resize
GAMMA = 1.15                  # Gamma value for midtone contrast tuning (>1 brightens midtones)
CLAHE_CLIP_LIMIT = 2.5        # CLAHE contrast limit
CLAHE_TILE_GRID = (8, 8)      # CLAHE grid tile size
DENOISE_STRENGTH = 5          # Bilateral filter diameter
SHARPEN_FACTOR = 0.5          # Sharpening filter intensity
FACE_PADDING_RATIO = 0.65     # Padding factor around detected face/subject bounding box
PNG_COMPRESSION_LEVEL = 9     # Maximum PNG compression level (0-9)

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ==============================================================================
# PIPELINE HELPER FUNCTIONS
# ==============================================================================

def correct_exif_orientation(image: Image.Image) -> Image.Image:
    """Correct image orientation using EXIF metadata if present."""
    try:
        corrected = ImageOps.exif_transpose(image)
        logger.info("EXIF orientation check completed.")
        return corrected
    except Exception as e:
        logger.warning(f"EXIF orientation correction skipped: {e}")
        return image


def center_and_crop_face(bgr_img: np.ndarray, padding_ratio: float = FACE_PADDING_RATIO) -> np.ndarray:
    """
    Detect human face or subject bounds and crop region centered on face/portrait
    with configurable padding, maintaining original aspect ratio.
    """
    try:
        h, w = bgr_img.shape[:2]
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # Attempt OpenCV Haar Cascade face detection if available
        faces = []
        if hasattr(cv2, "CascadeClassifier"):
            cascade_path = getattr(cv2.data, "haarcascades", "") + "haarcascade_frontalface_default.xml"
            if Path(cascade_path).exists():
                face_cascade = cv2.CascadeClassifier(cascade_path)
                detected = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
                )
                if len(detected) > 0:
                    faces = sorted(detected, key=lambda f: f[2] * f[3], reverse=True)

        if len(faces) > 0:
            fx, fy, fw, fh = faces[0]
            logger.info(f"Detected face bounding box via Haar cascade at x={fx}, y={fy}, w={fw}, h={fh}.")
            cx, cy = fx + fw / 2.0, fy + fh / 2.0
            box_size = max(fw, fh) * (1.0 + padding_ratio)
        else:
            # Fallback: Subject bounding box from non-white composited pixels
            mask = gray < 250
            coords = np.argwhere(mask)
            if len(coords) == 0:
                logger.info("Empty subject mask; keeping full image dimensions.")
                return bgr_img

            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            # Focus on upper 75% region of subject (head & torso)
            subj_w = x_max - x_min
            subj_h = y_max - y_min
            head_y_max = int(y_min + subj_h * 0.75)

            cx = (x_min + x_max) / 2.0
            cy = (y_min + head_y_max) / 2.0
            box_size = max(subj_w, subj_h * 0.75) * (1.0 + padding_ratio * 0.3)
            logger.info(f"Centering subject framing at cx={cx:.1f}, cy={cy:.1f}.")

        # Maintain original image aspect ratio (w/h)
        img_aspect = w / float(h)
        if img_aspect >= 1.0:
            crop_w = box_size * img_aspect
            crop_h = box_size
        else:
            crop_w = box_size
            crop_h = box_size / img_aspect

        x1 = max(0, int(cx - crop_w / 2.0))
        y1 = max(0, int(cy - crop_h / 2.0))
        x2 = min(w, int(cx + crop_w / 2.0))
        y2 = min(h, int(cy + crop_h / 2.0))

        cropped = bgr_img[y1:y2, x1:x2]
        logger.info(f"Cropped centered region: {x2 - x1}x{y2 - y1} px.")
        return cropped

    except Exception as e:
        logger.error(f"Error during face detection & centering: {e}. Reverting to uncropped image.")
        return bgr_img


def apply_gamma_correction(gray_img: np.ndarray, gamma: float = GAMMA) -> np.ndarray:
    """Apply non-linear gamma correction to adjust midtone contrast."""
    if abs(gamma - 1.0) < 1e-3:
        return gray_img

    inv_gamma = 1.0 / gamma
    lookup_table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(gray_img, lookup_table)


def normalize_histogram(gray_img: np.ndarray) -> np.ndarray:
    """Stretch histogram intensity spectrum across full [0, 255] dynamic range."""
    return cv2.normalize(gray_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)


# ==============================================================================
# MAIN PROCESSING FUNCTION
# ==============================================================================

def prep_photo(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    max_dimension: int = MAX_DIMENSION
) -> Path:
    """
    Executes the complete photo preprocessing pipeline.
    
    Returns:
        Path: Path to saved output image.
    """
    logger.info(f"Starting photo preparation pipeline for: {input_path}")

    # Robust file validation
    if not input_path.exists():
        logger.error(f"Input image file does not exist: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        # Step 1: Open image & apply EXIF orientation correction
        logger.info("[1/9] Opening source image and correcting EXIF orientation...")
        src_pil = Image.open(input_path)
        exif_corrected = correct_exif_orientation(src_pil)

        # Step 2: Remove background using rembg
        logger.info("[2/9] Executing background removal via rembg...")
        rgba_img = remove(exif_corrected)

        # Step 3: Composite onto pure white background
        logger.info("[3/9] Compositing subject onto pure white background...")
        white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
        composited_pil = Image.alpha_composite(white_bg, rgba_img).convert("RGB")
        bgr_img = cv2.cvtColor(np.array(composited_pil), cv2.COLOR_RGB2BGR)

        # Step 4: Automatic face centering and cropping
        logger.info("[4/9] Performing automatic face/subject detection & centering...")
        cropped_bgr = center_and_crop_face(bgr_img)

        # Step 5: Grayscale conversion & Gamma correction
        logger.info("[5/9] Converting to grayscale & applying gamma correction...")
        gray = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2GRAY)
        gray_gamma = apply_gamma_correction(gray, gamma=GAMMA)

        # Step 6: Histogram Normalization
        logger.info("[6/9] Normalizing histogram to full dynamic range...")
        gray_norm = normalize_histogram(gray_gamma)

        # Step 7: CLAHE Contrast Enhancement
        logger.info("[7/9] Applying CLAHE adaptive contrast enhancement...")
        clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
        gray_clahe = clahe.apply(gray_norm)

        # Step 8: Bilateral Denoising & Sharpening
        logger.info("[8/9] Applying bilateral denoising and subtle sharpening...")
        denoised = cv2.bilateralFilter(
            gray_clahe,
            d=DENOISE_STRENGTH,
            sigmaColor=35,
            sigmaSpace=35
        )

        sharpen_kernel = np.array([
            [0, -SHARPEN_FACTOR, 0],
            [-SHARPEN_FACTOR, 1.0 + 4 * SHARPEN_FACTOR, -SHARPEN_FACTOR],
            [0, -SHARPEN_FACTOR, 0]
        ], dtype=np.float32)
        sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)

        # Step 9: Intelligent resizing preserving facial proportions
        logger.info("[9/9] Resizing image while preserving aspect ratio...")
        h, w = sharpened.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            prepped = cv2.resize(sharpened, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h}.")
        else:
            prepped = sharpened

        # Export high-compression PNG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        success = cv2.imwrite(
            str(output_path),
            prepped,
            [cv2.IMWRITE_PNG_COMPRESSION, PNG_COMPRESSION_LEVEL]
        )

        if not success:
            raise IOError(f"Failed to write image output to: {output_path}")

        logger.info(f"Pipeline successfully completed! Prepped image saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Critical failure in photo preparation pipeline: {e}", exc_info=True)
        raise


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    input_path = project_root / "assets" / "source-photo.jpg"
    output_path = project_root / "assets" / "source-prepped.png"

    try:
        prep_photo(input_path, output_path)
    except Exception as err:
        sys.exit(f"Error: {err}")


if __name__ == "__main__":
    main()
