import argparse
import json
import logging
import os
import sys
import tempfile

from idl_to_fuzztest.core import generate_fuzztest_from_json
from idl_to_fuzztest.nk_driver import (
    check_nk_driver_available,
    convert_idl_to_json,
    get_nk_driver_version,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate fuzztest fixtures from KasperskyOS IDL JSON files."
    )
    parser.add_argument(
        "files", nargs="+", help="List of paths to the input IDL files."
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the resulting C++ header file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, do not create the output file, but print where it would be written and the list of processed files.",
    )
    parser.add_argument(
        "--nk-driver",
        dest="nk_driver_path",
        help="Path to the nk-driver executable (optional, may not exist).",
    )
    parser.add_argument(
        "-I",
        "--include-dir",
        action="append",
        dest="include_dirs",
        help="Add directory to include search path. Can be used multiple times.",
        default=[],
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (debug level logging).",
    )

    args = parser.parse_args()

    # Настройка уровня логирования в зависимости от verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    # Validate input files exist
    for file_path in args.files:
        if not os.path.exists(file_path):
            logger.error(f"Input file not found: {file_path}")
            sys.exit(1)

    # Check nk-driver availability
    if not check_nk_driver_available(args.nk_driver_path):
        if args.nk_driver_path:
            logger.error(f"nk-driver not found at: {args.nk_driver_path}")
        else:
            logger.error(
                "nk-driver not found in PATH. Please install it or provide explicit path with --nk-driver."
            )
        sys.exit(1)

    # Get and display nk-driver version
    version = get_nk_driver_version(args.nk_driver_path)
    if version:
        logger.info(f"Using nk-driver: {version}")

    # Validate include directories
    for include_dir in args.include_dirs:
        if not os.path.isdir(include_dir):
            logger.warning(f"Include directory does not exist: {include_dir}")

    # Convert each IDL file to JSON using temporary files
    json_data_list = []
    temp_files = []

    try:
        for idl_file in args.files:
            try:
                logger.info(f"Converting {idl_file} to JSON...")

                # Create temporary file for JSON output
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8"
                ) as tmp_file:
                    temp_file_path = tmp_file.name
                    temp_files.append(temp_file_path)

                # Convert IDL to JSON
                convert_idl_to_json(
                    idl_file=idl_file,
                    output_file=temp_file_path,
                    include_dirs=args.include_dirs,
                    nk_driver_path=args.nk_driver_path,
                )

                # Read the generated JSON
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                    json_data_list.append(json_data)

                logger.debug(f"Successfully converted {idl_file}")

            except subprocess.CalledProcessError as e:
                logger.error(f"nk-driver failed for {idl_file}: {e}")
                if e.stderr:
                    logger.error(f"stderr: {e.stderr}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error converting {idl_file}: {e}")
                sys.exit(1)

        # Generate the header from JSON data
        try:
            logger.debug("Generating header from JSON data...")
            result = []
            for json_data in json_data_list:
                result.append(generate_fuzztest_from_json(json_data))

            logger.debug("Header generation completed")
        except Exception as e:
            logger.error(f"Error during header generation: {e}")
            sys.exit(1)

        if args.dry_run:
            logger.info(f"[Dry-run] Would write to: {args.output}")
            logger.info(f"[Dry-run] Processed files: {', '.join(args.files)}")
            if args.nk_driver_path:
                logger.info(f"[Dry-run] nk-driver path: {args.nk_driver_path}")
            if args.include_dirs:
                logger.info(
                    f"[Dry-run] Include directories: {', '.join(args.include_dirs)}"
                )
            return

        # Write the output file
        try:
            output_dir = os.path.dirname(os.path.abspath(args.output))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"Created output directory: {output_dir}")

            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n\n".join(result))

            logger.info(f"Successfully generated: {args.output}")
        except Exception as e:
            logger.error(f"Error writing to output file: {args.output}\n{e}")
            sys.exit(1)

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                logger.debug(f"Removed temporary file: {temp_file}")
            except OSError as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")


if __name__ == "__main__":
    main()
