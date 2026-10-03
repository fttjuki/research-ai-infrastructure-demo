"""Create the checked-in fictional raw study file with its documented seed."""

import argparse

from research_demo.experiment import write_synthetic_raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace the checked-in synthetic fixture")
    args = parser.parse_args()
    from research_demo.experiment import RAW_CSV
    if RAW_CSV.exists() and not args.force:
        parser.error("raw fixture already exists; pass --force only if you intend to replace it")
    print(f"Created synthetic raw data; SHA-256: {write_synthetic_raw()}")
