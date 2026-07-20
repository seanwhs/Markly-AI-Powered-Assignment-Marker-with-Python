#!/usr/bin/env python3
"""
install_fonts.py  —  Downloads Caveat & Patrick Hand handwriting fonts into ./fonts/
Run once before starting Markly:  python install_fonts.py
"""
import os
import logging
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Define the local directory where font files will be stored
FONTS_DIR = "fonts"

# Map of filenames to their raw source URLs from Google Fonts
FONTS = {
    "Caveat-Regular.ttf":
        "https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Regular.ttf",
    "Caveat-Bold.ttf":
        "https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Bold.ttf",
    "PatrickHand-Regular.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf",
}

# Ensure the fonts directory exists before downloading
os.makedirs(FONTS_DIR, exist_ok=True)

all_ok = True
# Iterate through each font to download it if it's not already present
for filename, url in FONTS.items():
    dest = os.path.join(FONTS_DIR, filename)
    # Check if the file already exists locally to avoid redundant downloads
    if os.path.exists(dest):
        logger.info(f"  ✓  {filename} already present — skipping")
        continue

    logger.info(f"  Downloading {filename}…")
    try:
        # Create a request with a User-Agent to ensure access to raw GitHub files
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()

        # Basic validation to ensure the response contains actual binary font data
        if len(data) < 1000:
            raise ValueError(f"Response too small ({len(data)} bytes) — likely not a font file")

        # Write the binary data to the destination file
        with open(dest, "wb") as f:
            f.write(data)
        logger.info(f"  done  ({len(data)//1024} KB)")
    except Exception as e:
        # Capture and report any connection or write errors
        logger.error(f"  FAILED: {e}")
        all_ok = False

# Provide final instructions based on whether the download was successful
print()
if all_ok:
    logger.info("✅  All fonts installed. Run:  panel serve app.py")
else:
    logger.warning("⚠️  Some fonts failed — Markly will use system fallback fonts (italic serif).")
    logger.warning("    Annotations will still work, just won't look as handwritten.")
    logger.info("    Run:  panel serve app.py")