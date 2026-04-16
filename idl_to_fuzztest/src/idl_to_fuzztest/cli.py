import argparse
import os
import sys

from idl_to_fuzztest.core import generate_header


def main():
    parser = argparse.ArgumentParser(
        description="Generate fuzztest fixtures from KasperskyOS IDL JSON files."
    )
    parser.add_argument("files", nargs="+", help="List of paths to the input files.")
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the resulting C++ header file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, do not create the output file, but print where it would be written and the list of processed files.",
    )

    args = parser.parse_args()

    # Validate input files exist
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: Input file not found: {file_path}", file=sys.stderr)
            sys.exit(1)

    # Generate the content
    try:
        content = generate_header(args.files)
    except Exception as e:
        print(f"Error during header generation: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[Dry-run] Would write to: {args.output}")
        print(f"[Dry-run] Processed files: {', '.join(args.files)}")
        return

    # Write the output file
    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated: {args.output}")
    except Exception as e:
        print(f"Error writing to output file: {args.output}\n{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
