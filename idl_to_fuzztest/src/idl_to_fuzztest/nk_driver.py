import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional


def find_nk_driver(executable_path: Optional[str] = None) -> str:
    """
    Find the nk-driver executable.

    Args:
        executable_path: Optional explicit path to the executable

    Returns:
        Path to the nk-driver executable

    Raises:
        FileNotFoundError: If nk-driver cannot be found
    """
    if executable_path:
        # Use the explicitly provided path
        if os.path.isfile(executable_path) and os.access(executable_path, os.X_OK):
            return executable_path
        raise FileNotFoundError(f"nk-driver not found at: {executable_path}")

    # Try to find in PATH
    import shutil

    nk_driver_path = shutil.which("nk-driver")
    if nk_driver_path:
        return nk_driver_path

    raise FileNotFoundError(
        "nk-driver not found in PATH. Please install it or provide explicit path."
    )


def convert_idl_to_json(
    idl_file: str,
    output_file: str,
    include_dirs: Optional[List[str]] = None,
    nk_driver_path: Optional[str] = None,
) -> None:
    """
    Convert IDL file to JSON using nk-driver.

    Args:
        idl_file: Path to the main IDL file
        output_file: Path to output JSON file (required)
        include_dirs: List of search directories for includes (-I)
        nk_driver_path: Explicit path to nk-driver executable

    Raises:
        subprocess.CalledProcessError: If nk-driver fails
        FileNotFoundError: If nk-driver not found
    """
    # Find nk-driver executable
    nk_driver = find_nk_driver(nk_driver_path)

    # Build command
    cmd = [nk_driver]

    # Add include directories
    if include_dirs:
        for inc_dir in include_dirs:
            cmd.extend(["-I", inc_dir])

    # Add output file (required)
    cmd.extend(["-o", output_file])

    # Add main IDL file
    cmd.append(idl_file)

    # Run nk-driver
    subprocess.run(cmd, check=True)


def check_nk_driver_available(nk_driver_path: Optional[str] = None) -> bool:
    """
    Check if nk-driver is available.

    Args:
        nk_driver_path: Optional explicit path

    Returns:
        True if nk-driver is available, False otherwise
    """
    try:
        find_nk_driver(nk_driver_path)
        return True
    except FileNotFoundError:
        return False


def get_nk_driver_version(nk_driver_path: Optional[str] = None) -> Optional[str]:
    """
    Get nk-driver version information.

    Args:
        nk_driver_path: Optional explicit path

    Returns:
        Version string or None if not available
    """
    try:
        nk_driver = find_nk_driver(nk_driver_path)
        result = subprocess.run(
            [nk_driver, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
