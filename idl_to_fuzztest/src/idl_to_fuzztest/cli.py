import argparse
import json
import logging
import os
import subprocess
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


def find_idl_file(import_name, include_dirs):
    """
    Find IDL file by its import name in the given include directories.

    Args:
        import_name: e.g., "kl.core.Types"
        include_dirs: list of include directory paths

    Returns:
        Path to the IDL file if found, None otherwise
    """
    # Convert import name to file path
    # "kl.core.Types" -> "kl/core/Types.idl"
    relative_path = import_name.replace(".", os.sep) + ".idl"

    for include_dir in include_dirs:
        full_path = os.path.join(include_dir, relative_path)
        if os.path.exists(full_path):
            logger.debug(f"Found import {import_name} at {full_path}")
            return full_path

    logger.warning(
        f"Import {import_name} not found in include directories: {include_dirs}"
    )
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate fuzztest fixtures from KasperskyOS IDL JSON files."
    )
    parser.add_argument("idl", help="Path to the input IDL file.")
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the resulting C++ header file."
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
    if not os.path.exists(args.idl):
        logger.error(f"Input file not found: {args.idl}")
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

    # Convert all IDL files using BFS traversal
    json_data_list = []
    temp_files = []

    # BFS queue for IDL files to process
    queue = [args.idl]
    # Track processed files to avoid duplicates
    processed_files = set()
    # Track processed imports to avoid redundant searching
    processed_imports = {}

    while queue:
        idl_file = queue.pop(0)  # pop first element for BFS order

        # Skip if already processed
        if idl_file in processed_files:
            continue

        processed_files.add(idl_file)

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

            # Resolve imports from this JSON and add to queue
            imports = json_data.get("contents", {}).get("imports", [])
            for import_name in imports:
                if import_name not in processed_imports:
                    imported_file = find_idl_file(import_name, args.include_dirs)
                    if imported_file:
                        processed_imports[import_name] = imported_file
                        if imported_file not in processed_files:
                            queue.append(imported_file)
                            logger.debug(f"Added import to queue: {imported_file}")
                    else:
                        logger.error(f"Required import not found: {import_name}")
                        sys.exit(1)

        except subprocess.CalledProcessError as e:
            logger.error(f"nk-driver failed for {idl_file}: {e}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error converting {idl_file}: {e}")
            sys.exit(1)

    # Reverse the list so that dependencies come before dependents
    # This ensures that when generating mutators, base types are processed first
    json_data_list.reverse()
    logger.debug(f"Processing {len(json_data_list)} JSON files in dependency order")

    # Generate the header from all JSON data
    try:
        logger.debug("Generating fuzztest mutators from JSON data...")
        # Call the updated function with the list of all JSON data
        result = generate_fuzztest_from_json(json_data_list)
        logger.debug("Header generation completed")
    except Exception as e:
        logger.error(f"Error during header generation: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)

    # Write the output file
    try:
        output_dir = os.path.dirname(os.path.abspath(args.output))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)  # Write the generated string directly

        logger.info(f"Successfully generated: {args.output}")
    except Exception as e:
        logger.error(f"Error writing to output file: {args.output}\n{e}")
        sys.exit(1)

    # Clean up temporary files
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
            logger.debug(f"Removed temporary file: {temp_file}")
        except OSError as e:
            logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

if __name__ == "__main__":
    main()
