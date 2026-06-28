"""
Build the Leather Mold Generator add-on.
"""

from pathlib import Path
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).parent
ADDON_FOLDER = PROJECT_ROOT / "leather_mold_generator"
DIST_FOLDER = PROJECT_ROOT / "dist"
ZIP_FILE = DIST_FOLDER / "LeatherMoldGenerator.zip"


def main():

    DIST_FOLDER.mkdir(exist_ok=True)

    if ZIP_FILE.exists():
        ZIP_FILE.unlink()

    with ZipFile(ZIP_FILE, "w") as archive:

        for file in ADDON_FOLDER.rglob("*"):

            if file.is_file():

                archive.write(
                    file,
                    file.relative_to(PROJECT_ROOT)
                )

    print(f"Build successful:\n{ZIP_FILE}")


if __name__ == "__main__":
    main()