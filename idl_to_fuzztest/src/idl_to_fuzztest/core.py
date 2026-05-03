import json
import re
from typing import Any, Dict, List, Optional, Tuple

# Mapping basic types to their mutators
BASIC_TYPE_MUTATORS = {
    "UInt8": "fuzztest::Arbitrary<uint8_t>()",
    "UInt16": "fuzztest::Arbitrary<uint16_t>()",
    "UInt32": "fuzztest::Arbitrary<uint32_t>()",
    "UInt64": "fuzztest::Arbitrary<uint64_t>()",
    "SInt8": "fuzztest::Arbitrary<int8_t>()",
    "SInt16": "fuzztest::Arbitrary<int16_t>()",
    "SInt32": "fuzztest::Arbitrary<int32_t>()",
    "SInt64": "fuzztest::Arbitrary<int64_t>()",
    "Float": "fuzztest::Arbitrary<float>()",
    "Double": "fuzztest::Arbitrary<double>()",
    "Bool": "fuzztest::Arbitrary<bool>()",
    "Byte": "fuzztest::Arbitrary<uint8_t>()",
}


class IDLParser:
    """Parses IDL JSON and generates mutators with typedef and const resolution."""

    def __init__(self, json_data_list: List[Dict[str, Any]]):
        """
        Initialize parser with a list of JSON data.
        Later JSON files can reference types from earlier ones.

        Args:
            json_data_list: List of parsed JSON dictionaries containing IDL descriptions
        """
        self.json_data_list = json_data_list

        # Combined registries from all JSON files
        self.type_registry: Dict[str, Dict[str, Any]] = {}  # struct definitions
        self.typedef_registry: Dict[str, Dict[str, Any]] = {}  # typedef definitions
        self.const_registry: Dict[str, Any] = {}  # const definitions

        # Track which package each type belongs to
        self.type_package: Dict[str, str] = {}  # type_name -> package

        # Cache for generated mutators
        self.mutator_cache: Dict[str, str] = {}

        # Build registries from all JSON files in order
        self._build_global_registry()

    def _build_global_registry(self):
        """Build registries from all JSON files, preserving order."""
        for json_data in self.json_data_list:
            contents = json_data["contents"]
            package = contents["name"]
            entries = contents.get("entries", [])

            for entry in entries:
                kind = entry["kind"]
                name = entry["name"]

                if kind == "struct":
                    self.type_registry[name] = entry
                    self.type_package[name] = package
                elif kind == "typedef":
                    self.typedef_registry[name] = entry
                    self.type_package[name] = package
                elif kind == "const":
                    # Store const value
                    const_value = entry.get("value")
                    # Try to parse numeric value if it's a string
                    if isinstance(const_value, str):
                        try:
                            # Try to convert to int if it looks like a number
                            if const_value.isdigit():
                                const_value = int(const_value)
                            else:
                                # Try to parse as hex
                                if const_value.startswith("0x"):
                                    const_value = int(const_value, 16)
                        except (ValueError, AttributeError):
                            pass
                    self.const_registry[name] = const_value
                    self.type_package[name] = package

    def _resolve_const_value(self, const_name: str) -> Any:
        """
        Resolve a constant value by name.
        Returns the value if found, otherwise returns the name itself.
        """
        if const_name in self.const_registry:
            return self.const_registry[const_name]

        # Try to parse as numeric value
        try:
            return int(const_name)
        except ValueError:
            pass

        # Try to parse as hex
        try:
            if isinstance(const_name, str) and const_name.startswith("0x"):
                return int(const_name, 16)
        except (ValueError, AttributeError):
            pass

        # Return as is if can't resolve
        return const_name

    def _resolve_typedef(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        Recursively resolve typedef to its underlying type.
        Handles nested typedefs and constant references.
        """
        if type_name not in self.typedef_registry:
            return None

        typedef_entry = self.typedef_registry[type_name]
        underlying_type = typedef_entry["type"]

        # If it's a type_definition (reference to another typedef), resolve recursively
        if underlying_type["kind"] == "type_definition":
            referenced_name = underlying_type["name"]
            return self._resolve_typedef(referenced_name)

        # For string types, try to resolve size from constants
        if underlying_type["kind"] == "string":
            size = underlying_type.get("size", 0)

            # If size is a string (reference to constant), try to resolve it
            if isinstance(size, str):
                resolved_size = self._resolve_const_value(size)
                underlying_type = underlying_type.copy()
                underlying_type["size"] = resolved_size

            return underlying_type

        # For bytes types, try to resolve size from constants
        if underlying_type["kind"] == "bytes":
            size = underlying_type.get("size", 0)

            # If size is a string (reference to constant), try to resolve it
            if isinstance(size, str):
                resolved_size = self._resolve_const_value(size)
                underlying_type = underlying_type.copy()
                underlying_type["size"] = resolved_size

            return underlying_type

        # For other types, return as is
        return underlying_type

    def _get_package_for_type(self, type_name: str) -> str:
        """Get the package where a type is defined."""
        if type_name in self.type_package:
            return self.type_package[type_name]
        return ""

    def _get_fully_qualified_name(
        self, name: str, package: Optional[str] = None
    ) -> str:
        """Get fully qualified C++ type name."""
        if not package:
            package = self._get_package_for_type(name)

        if package:
            cpp_package = package.replace(".", "::")
            return f"kosipc::stdcpp::{cpp_package}::{name}"
        else:
            # Fallback: try to find in any package (should not happen)
            return f"kosipc::stdcpp::{name}"

    def _get_mutator_for_type(self, type_info: Dict[str, Any]) -> str:
        """Recursively generate mutator for a given type, resolving typedefs."""
        # Ensure type_info is a dictionary
        if not isinstance(type_info, dict):
            raise ValueError(
                f"Expected dict for type_info, got {type(type_info)}: {type_info}"
            )

        kind = type_info.get("kind")
        if not kind:
            raise ValueError(f"Missing 'kind' in type_info: {type_info}")

        if kind == "basic_type":
            basic_type = type_info.get("basic_type")
            if not basic_type:
                raise ValueError(f"Missing 'basic_type' in type_info: {type_info}")
            if basic_type in BASIC_TYPE_MUTATORS:
                return BASIC_TYPE_MUTATORS[basic_type]
            else:
                raise ValueError(f"Unknown basic type: {basic_type}")

        elif kind == "type_definition":
            type_name = type_info.get("name")
            if not type_name:
                raise ValueError(f"Missing 'name' in type_definition: {type_info}")
            package = type_info.get("package", None)

            # Check if this is a typedef reference
            resolved_type = self._resolve_typedef(type_name)
            if resolved_type:
                # Generate mutator based on resolved underlying type
                return self._get_mutator_for_type(resolved_type)
            else:
                # It's a struct type - look up its package
                if not package:
                    package = self._get_package_for_type(type_name)
                return f"GetDefaultMutator<{self._get_fully_qualified_name(type_name, package)}>()"

        elif kind == "string":
            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            # Ensure size is numeric
            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            if size and size > 0:
                return f"fuzztest::Arbitrary<std::string>().WithMaxSize({size})"
            else:
                return "fuzztest::Arbitrary<std::string>()"

        elif kind == "bytes":
            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            # Ensure size is numeric
            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            if size and size > 0:
                # std::vector<std::byte> with size limit
                return (
                    f"fuzztest::Arbitrary<std::vector<std::byte>>().WithMaxSize({size})"
                )
            else:
                return "fuzztest::Arbitrary<std::vector<std::byte>>()"

        elif kind == "array":
            element_type = type_info.get("element_type")
            if not element_type:
                raise ValueError(f"Missing 'element_type' in array: {type_info}")
            element_mutator = self._get_mutator_for_type(element_type)
            size = type_info.get("size", 0)

            if isinstance(size, str):
                size = self._resolve_const_value(size)

            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            if size and size > 0:
                return f"fuzztest::ArrayOf({element_mutator}).WithSize({size})"
            else:
                return f"fuzztest::ContainerOf<std::vector>({element_mutator})"

        elif kind == "vector":
            element_type = type_info.get("element_type")
            if not element_type:
                raise ValueError(f"Missing 'element_type' in vector: {type_info}")
            element_mutator = self._get_mutator_for_type(element_type)
            max_size = type_info.get("max_size", 0)

            if isinstance(max_size, str):
                max_size = self._resolve_const_value(max_size)

            try:
                max_size = int(max_size) if max_size else 0
            except (ValueError, TypeError):
                max_size = 0

            if max_size and max_size > 0:
                return f"fuzztest::VectorOf({element_mutator}).WithMaxSize({max_size})"
            else:
                return f"fuzztest::VectorOf({element_mutator})"

        elif kind == "optional":
            inner_type = type_info.get("inner_type")
            if not inner_type:
                raise ValueError(f"Missing 'inner_type' in optional: {type_info}")
            inner_mutator = self._get_mutator_for_type(inner_type)
            return f"fuzztest::OptionalOf({inner_mutator})"

        else:
            raise ValueError(f"Unknown type kind: {kind}")

    def _generate_struct_mutator(
        self, struct_name: str, fields: List[Dict[str, Any]], package: str
    ) -> str:
        """Generate mutator for struct type using StructOf."""
        fully_qualified = self._get_fully_qualified_name(struct_name, package)

        field_mutators = []
        for field in fields:
            # Safely get field type
            field_type = field.get("type")
            if not field_type:
                raise ValueError(f"Missing 'type' in field: {field}")

            mutator = self._get_mutator_for_type(field_type)
            field_name = field.get("name", "unknown")
            # Add comment showing the resolved type
            field_mutators.append(f"        {mutator} /* {field_name} */")

        # Add package comment
        package_comment = f"// from package: {package}" if package else ""

        return f"""// Mutator for struct {struct_name} {package_comment}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
{",\n".join(field_mutators)}
    );
}}"""

    def _generate_mutator_for_entry(
        self, entry: Dict[str, Any], package: str
    ) -> Optional[str]:
        """Generate mutator function for a type entry."""
        entry_name = entry.get("name")
        if not entry_name:
            return None

        kind = entry.get("kind")

        if kind == "struct":
            fields = entry.get("fields", [])
            return self._generate_struct_mutator(entry_name, fields, package)

        # Typedefs and constants don't need separate mutators
        # They are resolved inline when used
        return None

    def _resolve_and_generate_mutator_description(self, type_name: str) -> str:
        """
        Generate a human-readable description of how a type is resolved.
        Useful for debugging.
        """
        if type_name in self.typedef_registry:
            underlying = self._resolve_typedef(type_name)

            if underlying and isinstance(underlying, dict):
                if underlying.get("kind") == "string":
                    size = underlying.get("size", "unknown")
                    return f"// {type_name} -> string<{size}>"
                elif underlying.get("kind") == "bytes":
                    size = underlying.get("size", "unknown")
                    return f"// {type_name} -> bytes<{size}>"
                elif underlying.get("kind") == "basic_type":
                    return (
                        f"// {type_name} -> {underlying.get('basic_type', 'unknown')}"
                    )
                else:
                    return f"// {type_name} -> {underlying.get('kind', 'unknown')}"

        return f"// {type_name}"

    def generate_mutators(self) -> Tuple[List[str], List[str]]:
        """
        Generate all mutators from all JSON files.

        Returns:
            Tuple of (mutators, debug_info)
            - mutators: List of generated C++ mutator functions
            - debug_info: List of comments showing type resolution
        """
        mutators = []
        debug_info = []
        generated_structs = set()

        # First, document typedef resolutions from all packages
        for typedef_name in self.typedef_registry:
            description = self._resolve_and_generate_mutator_description(typedef_name)
            if description and description not in debug_info:
                debug_info.append(description)

        # Then generate mutators for all struct types across all JSON files
        for json_data in self.json_data_list:
            contents = json_data["contents"]
            package = contents["name"]
            entries = contents.get("entries", [])

            for entry in entries:
                if entry.get("kind") == "struct":
                    entry_name = entry.get("name")
                    if not entry_name:
                        continue

                    # Skip if already generated (in case of duplicate definitions)
                    if entry_name in generated_structs:
                        continue

                    mutator = self._generate_mutator_for_entry(entry, package)
                    if mutator:
                        self.mutator_cache[entry_name] = mutator
                        mutators.append(mutator)
                        generated_structs.add(entry_name)

        return mutators, debug_info


def generate_fuzztest_from_json(json_data_list: List[Dict[str, Any]]) -> str:
    """
    Main function to generate fuzztest mutators from a list of IDL JSON data.

    Later JSON files can reference types from earlier ones. The order matters
    because types from previous files are available for resolution.

    Args:
        json_data_list: List of parsed JSON dictionaries containing IDL descriptions.
                        First files should contain base types that may be imported by later files.

    Returns:
        String containing generated C++ mutator code
    """
    if not json_data_list:
        return "// No JSON data provided"

    parser = IDLParser(json_data_list)
    mutators, debug_info = parser.generate_mutators()

    result_parts = []

    # Add header
    result_parts.append("// Auto-generated mutators for IDL interfaces")
    result_parts.append("// Generated from multiple IDL files")

    # Add package info
    packages = [data["contents"]["name"] for data in json_data_list]
    result_parts.append(f"// Packages: {', '.join(packages)}")
    result_parts.append("")

    # Add typedef resolution info
    if debug_info:
        result_parts.append("// Type definitions resolution:")
        result_parts.extend(debug_info)
        result_parts.append("")

    # Add mutators
    if mutators:
        result_parts.extend(mutators)
    else:
        result_parts.append("// No mutators generated")

    return "\n".join(result_parts)
