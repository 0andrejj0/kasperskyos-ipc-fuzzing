import json
import re
from typing import Any, Dict, List, Optional, Tuple

# Mapping basic types to their mutators
BASIC_TYPE_MUTATORS = {
    "UInt8": "fuzztest::Arbitrary<uint8_t>()",
    "UInt16": "fuzztest::Arbitrary<uint16_t>()",
    "UInt32": "fuzztest::Arbitrary<uint32_t>()",
    "UInt64": "fuzztest::Arbitrary<uint64_t>()",
    "Int8": "fuzztest::Arbitrary<int8_t>()",
    "Int16": "fuzztest::Arbitrary<int16_t>()",
    "Int32": "fuzztest::Arbitrary<int32_t>()",
    "Int64": "fuzztest::Arbitrary<int64_t>()",
    "Float": "fuzztest::Arbitrary<float>()",
    "Double": "fuzztest::Arbitrary<double>()",
    "Bool": "fuzztest::Arbitrary<bool>()",
    "Byte": "fuzztest::Arbitrary<uint8_t>()",
}


class IDLParser:
    """Parses IDL JSON and generates mutators with typedef and const resolution."""

    def __init__(self, json_data: Dict[str, Any]):
        self.contents = json_data["contents"]
        self.package = self.contents["name"]
        self.entries = self.contents.get("entries", [])
        self.interface = self.contents.get("interface", {})

        # Cache for generated mutators
        self.mutator_cache: Dict[str, str] = {}

        # Type resolution registries
        self.type_registry: Dict[str, Any] = {}  # struct definitions
        self.typedef_registry: Dict[str, Dict[str, Any]] = {}  # typedef definitions
        self.const_registry: Dict[str, Any] = {}  # const definitions

        self._build_type_registry()

    def _build_type_registry(self):
        """Build registries of all defined types, typedefs, and constants."""
        for entry in self.entries:
            kind = entry["kind"]
            name = entry["name"]

            if kind == "struct":
                self.type_registry[name] = entry
            elif kind == "typedef":
                self.typedef_registry[name] = entry
            elif kind == "const":
                self.const_registry[name] = entry

    def _resolve_const_value(self, const_name: str) -> Any:
        """
        Resolve a constant value by name.
        Returns the value if found, otherwise returns the name itself.
        """
        if const_name in self.const_registry:
            return self.const_registry[const_name]["value"]

        # Try to parse as numeric value
        try:
            return int(const_name)
        except ValueError:
            pass

        # Return as is if can't resolve
        return const_name

    def _resolve_typedef(self, type_name: str) -> Dict[str, Any]:
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

        # For other types, return as is
        return underlying_type

    def _get_fully_qualified_name(
        self, name: str, package: Optional[str] = None
    ) -> str:
        """Get fully qualified C++ type name."""
        if package:
            cpp_package = package.replace(".", "::")
            return f"kosipc::stdcpp::{cpp_package}::{name}"
        else:
            cpp_package = self.package.replace(".", "::")
            return f"kosipc::stdcpp::{cpp_package}::{name}"

    def _get_mutator_for_type(self, type_info: Dict[str, Any]) -> str:
        """Recursively generate mutator for a given type, resolving typedefs."""
        kind = type_info["kind"]

        if kind == "basic_type":
            basic_type = type_info["basic_type"]
            if basic_type in BASIC_TYPE_MUTATORS:
                return BASIC_TYPE_MUTATORS[basic_type]
            else:
                raise ValueError(f"Unknown basic type: {basic_type}")

        elif kind == "type_definition":
            type_name = type_info["name"]
            package = type_info.get("package", self.package)

            # Check if this is a typedef reference
            resolved_type = self._resolve_typedef(type_name)
            if resolved_type:
                # Generate mutator based on resolved underlying type
                return self._get_mutator_for_type(resolved_type)
            else:
                # It's a struct type
                return f"GetDefaultMutator<{self._get_fully_qualified_name(type_name, package)}>()"

        elif kind == "string":
            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            if size and size > 0:
                return f"fuzztest::Arbitrary<std::string>().WithMaxSize({size})"
            else:
                return "fuzztest::Arbitrary<std::string>()"

        elif kind == "array":
            element_mutator = self._get_mutator_for_type(type_info["element_type"])
            size = type_info.get("size", 0)

            if isinstance(size, str):
                size = self._resolve_const_value(size)

            if size and size > 0:
                return f"fuzztest::ArrayOf({element_mutator}).WithSize({size})"
            else:
                return f"fuzztest::ContainerOf<std::vector>({element_mutator})"

        elif kind == "vector":
            element_mutator = self._get_mutator_for_type(type_info["element_type"])
            max_size = type_info.get("max_size", 0)

            if isinstance(max_size, str):
                max_size = self._resolve_const_value(max_size)

            if max_size and max_size > 0:
                return f"fuzztest::VectorOf({element_mutator}).WithMaxSize({max_size})"
            else:
                return f"fuzztest::VectorOf({element_mutator})"

        elif kind == "optional":
            inner_mutator = self._get_mutator_for_type(type_info["inner_type"])
            return f"fuzztest::OptionalOf({inner_mutator})"

        else:
            raise ValueError(f"Unknown type kind: {kind}")

    def _generate_struct_mutator(
        self, struct_name: str, fields: List[Dict[str, Any]]
    ) -> str:
        """Generate mutator for struct type using StructOf."""
        fully_qualified = self._get_fully_qualified_name(struct_name)

        field_mutators = []
        for field in fields:
            mutator = self._get_mutator_for_type(field["type"])
            # Add comment showing the resolved type
            field_mutators.append(f"        {mutator} /* {field['name']} */")

        return f"""// Mutator for struct {struct_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
{",\n".join(field_mutators)}
    );
}}"""

    def _generate_mutator_for_entry(self, entry: Dict[str, Any]) -> Optional[str]:
        """Generate mutator function for a type entry."""
        entry_name = entry["name"]
        kind = entry["kind"]

        if kind == "struct":
            fields = entry.get("fields", [])
            return self._generate_struct_mutator(entry_name, fields)

        # Typedefs and constants don't need separate mutators
        # They are resolved inline when used
        return None

    def _resolve_and_generate_mutator_description(self, type_name: str) -> str:
        """
        Generate a human-readable description of how a type is resolved.
        Useful for debugging.
        """
        if type_name in self.typedef_registry:
            typedef = self.typedef_registry[type_name]
            underlying = self._resolve_typedef(type_name)

            if underlying["kind"] == "string":
                size = underlying.get("size", "unknown")
                return f"// {type_name} -> string<{size}>"
            elif underlying["kind"] == "basic_type":
                return f"// {type_name} -> {underlying['basic_type']}"
            else:
                return f"// {type_name} -> {underlying['kind']}"

        return f"// {type_name}"

    def generate_mutators(self) -> Tuple[List[str], List[str]]:
        """
        Generate all mutators.

        Returns:
            Tuple of (mutators, debug_info)
            - mutators: List of generated C++ mutator functions
            - debug_info: List of comments showing type resolution
        """
        mutators = []
        debug_info = []

        # First, document typedef resolutions
        for typedef_name in self.typedef_registry:
            description = self._resolve_and_generate_mutator_description(typedef_name)
            if description:
                debug_info.append(description)

        # Then generate mutators for all struct types
        for entry in self.entries:
            if entry["kind"] == "struct":
                entry_name = entry["name"]
                if entry_name not in self.mutator_cache:
                    mutator = self._generate_mutator_for_entry(entry)
                    if mutator:
                        self.mutator_cache[entry_name] = mutator
                        mutators.append(mutator)

        return mutators, debug_info


def generate_fuzztest_from_json(json_data: Dict[str, Any]) -> str:
    """
    Main function to generate fuzztest mutators from IDL JSON data.

    Args:
        json_data: Parsed JSON dictionary containing IDL description

    Returns:
        String containing generated C++ mutator code
    """
    parser = IDLParser(json_data)
    mutators, debug_info = parser.generate_mutators()

    result_parts = []

    # Add package info
    package = json_data["contents"]["name"]
    result_parts.append(f"// Auto-generated mutators for {package}")

    # Add typedef resolution info
    if debug_info:
        result_parts.append("// Type definitions resolution:")
        result_parts.extend(debug_info)
        result_parts.append("")

    # Add mutators
    result_parts.extend(mutators)

    return "\n".join(result_parts)
