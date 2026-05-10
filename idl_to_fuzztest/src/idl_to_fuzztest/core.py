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
                elif kind == "union":
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
            # Убираем имя интерфейса из пакета (последнюю часть)
            # Например "test.IEcho" -> "test"
            package_parts = package.split(".")
            # Если последняя часть пакета - это имя интерфейса, убираем её
            if len(package_parts) > 1:
                package_parts = package_parts[:-1]
            cpp_package = "::".join(package_parts)
            return f"kosipc::stdcpp::{cpp_package}::{name}"
        else:
            return f"kosipc::stdcpp::{name}"

    def _get_interface_type(self, package: str, interface_name: str) -> str:
        """Get fully qualified C++ interface type name."""
        if package:
            # Убираем имя интерфейса из пакета
            package_parts = package.split(".")
            if package_parts and package_parts[-1] == interface_name:
                package_parts = package_parts[:-1]
            cpp_package = "::".join(package_parts)
            return f"kosipc::stdcpp::{cpp_package}::{interface_name}"
        else:
            return f"kosipc::stdcpp::{interface_name}"

    def _get_type_name_for_cpp(self, type_info: Dict[str, Any]) -> str:
        """Get C++ type name for a given type info."""
        if not type_info or not isinstance(type_info, dict):
            return "unknown"

        kind = type_info.get("kind")

        if kind == "basic_type":
            basic_type = type_info.get("basic_type")
            cpp_types = {
                "UInt8": "uint8_t",
                "UInt16": "uint16_t",
                "UInt32": "uint32_t",
                "UInt64": "uint64_t",
                "SInt8": "int8_t",
                "SInt16": "int16_t",
                "SInt32": "int32_t",
                "SInt64": "int64_t",
                "Float": "float",
                "Double": "double",
                "Bool": "bool",
                "Byte": "uint8_t",
            }
            return cpp_types.get(basic_type, "unknown")

        elif kind == "type_definition":
            type_name = type_info.get("name", "unknown")
            package = type_info.get("package", None)
            return self._get_fully_qualified_name(type_name, package)

        elif kind == "string":
            return "std::string"

        elif kind == "bytes":
            return "std::vector<std::byte>"

        elif kind == "sequence":
            item_type = type_info.get("item_type")
            if item_type:
                item_cpp_type = self._get_type_name_for_cpp(item_type)
                return f"std::vector<{item_cpp_type}>"
            return "std::vector<unknown>"

        # elif kind == "array":
        #     # Array is a variable-size array with max size (like std::vector)
        #     item_type = type_info.get("item_type")
        #     if item_type:
        #         item_cpp_type = self._get_type_name_for_cpp(item_type)
        #         return f"std::vector<{item_cpp_type}>"
        #     return "std::vector<unknown>"

        elif kind == "array":
            # Fixed-size array -> std::array
            item_type = type_info.get("item_type")
            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            # Ensure size is numeric
            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            if item_type:
                item_cpp_type = self._get_type_name_for_cpp(item_type)
                return f"std::array<{item_cpp_type}, {size}>"
            return f"std::array<unknown, {size}>"
        
        elif kind == "handle":
            return "nk_handle_desc_t"

        else:
            return "unknown"

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
                return f"fuzztest::ContainerOf<std::string>(ascii_char).WithMaxSize({size})"
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

        elif kind == "sequence":
            # Sequence is like a fixed-size array in IDL
            item_type = type_info.get("item_type")
            if not item_type:
                raise ValueError(f"Missing 'item_type' in sequence: {type_info}")

            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            # Ensure size is numeric
            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            # Get mutator for the item type
            item_mutator = self._get_mutator_for_type(item_type)

            return f"fuzztest::VectorOf({item_mutator}).WithMaxSize({size})"

        elif kind == "array":
            # Fixed-size array -> std::array with exact size
            item_type = type_info.get("item_type")
            if not item_type:
                raise ValueError(f"Missing 'item_type' in array: {type_info}")

            size = type_info.get("size", 0)

            # Resolve size if it's a constant reference
            if isinstance(size, str):
                size = self._resolve_const_value(size)

            # Ensure size is numeric
            try:
                size = int(size) if size else 0
            except (ValueError, TypeError):
                size = 0

            # Get mutator for the item type
            item_mutator = self._get_mutator_for_type(item_type)

            if size > 0:
                return f"fuzztest::ArrayOf<{size}>({item_mutator})"
            else:
                return f"fuzztest::ArrayOf({item_mutator}).WithSize(0)"

        elif kind == "handle":
            return "GetDefaultMutator<nk_handle_desc_t>()"

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

        # Generate mutator (global, no namespace)
        return f"""// Mutator for struct {struct_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
{",\n".join(field_mutators)}
    );
}}"""

    def _generate_union_mutator(
        self, union_name: str, variants: List[Dict[str, Any]], package: str
    ) -> str:
        """Generate mutator for union type using VariantOf."""
        fully_qualified = self._get_fully_qualified_name(union_name, package)

        variant_mutators = []
        for idx, variant in enumerate(variants):
            variant_type = variant.get("type")
            if not variant_type:
                raise ValueError(f"Missing 'type' in union variant: {variant}")

            variant_name = variant.get("name", f"variant_{idx}")
            mutator = self._get_mutator_for_type(variant_type)
            variant_mutators.append(f"        {mutator} /* {variant_name} */")

        # Generate mutator for union
        return f"""// Mutator for union {union_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::VariantOf(
{",\n".join(variant_mutators)}
    );
}}"""

    def _generate_input_params_struct(
        self,
        package: str,
        interface_name: str,
        method_name: str,
        parameters: List[Dict[str, Any]],
    ) -> Tuple[str, str]:
        """Generate InputParams struct for a method."""
        # Build struct name
        struct_name = f"{interface_name}_{method_name}_InputParams"

        # Fully qualified name for mutator (just the struct name, since it's global)
        fully_qualified = struct_name

        # Generate fields (only input parameters)
        struct_fields = []
        for param in parameters:
            param_name = param.get("name")
            param_direction = param.get("direction")

            # Only include input parameters
            if param_direction == "input":
                param_type = param.get("type")
                if param_type:
                    cpp_type = self._get_type_name_for_cpp(param_type)
                    struct_fields.append(f"    {cpp_type} {param_name};")

        # Generate mutator for this struct
        field_mutators = []
        for param in parameters:
            param_name = param.get("name")
            param_direction = param.get("direction")

            if param_direction == "input":
                param_type = param.get("type")
                if param_type:
                    mutator = self._get_mutator_for_type(param_type)
                    field_mutators.append(f"        {mutator} /* {param_name} */")

        # Generate the struct definition (global)
        if struct_fields:
            struct_code = f"""// Input parameters structure for {interface_name}::{method_name}
struct {struct_name} {{
{chr(10).join(struct_fields)}
}};"""
        else:
            struct_code = f"""// Input parameters structure for {interface_name}::{method_name}
struct {struct_name} {{
    // No input parameters
}};"""

        # Generate mutator (global, no namespace)
        if field_mutators:
            mutator_code = f"""// Mutator for input params of {interface_name}::{method_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
{",\n".join(field_mutators)}
    );
}}"""
        else:
            mutator_code = f"""// Mutator for input params of {interface_name}::{method_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
        // No input parameters
    );
}}"""

        return struct_code, mutator_code

    def _generate_output_params_struct(
        self,
        package: str,
        interface_name: str,
        method_name: str,
        parameters: List[Dict[str, Any]],
    ) -> Tuple[str, str]:
        """Generate OutputParams struct for a method."""
        # Build struct name
        struct_name = f"{interface_name}_{method_name}_OutputParams"

        # Fully qualified name for mutator (just the struct name, since it's global)
        fully_qualified = struct_name

        # Generate fields (only output parameters)
        struct_fields = []
        for param in parameters:
            param_name = param.get("name")
            param_direction = param.get("direction")

            # Only include output parameters
            if param_direction == "output":
                param_type = param.get("type")
                if param_type:
                    cpp_type = self._get_type_name_for_cpp(param_type)
                    struct_fields.append(f"    {cpp_type} {param_name};")

        # Generate mutator for this struct
        field_mutators = []
        for param in parameters:
            param_name = param.get("name")
            param_direction = param.get("direction")

            if param_direction == "output":
                param_type = param.get("type")
                if param_type:
                    mutator = self._get_mutator_for_type(param_type)
                    field_mutators.append(f"        {mutator} /* {param_name} */")

        # Generate the struct definition (global)
        if struct_fields:
            struct_code = f"""// Output parameters structure for {interface_name}::{method_name}
struct {struct_name} {{
{chr(10).join(struct_fields)}
}};"""
        else:
            struct_code = f"""// Output parameters structure for {interface_name}::{method_name}
struct {struct_name} {{
    // No output parameters
}};"""

        # Generate mutator (global, no namespace)
        if field_mutators:
            mutator_code = f"""// Mutator for output params of {interface_name}::{method_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
{",\n".join(field_mutators)}
    );
}}"""
        else:
            mutator_code = f"""// Mutator for output params of {interface_name}::{method_name}
template<>
auto GetDefaultMutator<{fully_qualified}>() {{
    return fuzztest::StructOf<{fully_qualified}>(
        // No output parameters
    );
}}"""

        return struct_code, mutator_code

    def _generate_interface_variant(
        self, package: str, interface_name: str, method_names: List[str]
    ) -> str:
        """Generate using statement with std::variant for all InputParams types."""
        # Build variant types (just the struct names, since they are global)
        variant_types = []
        for method_name in method_names:
            struct_name = f"{interface_name}_{method_name}_InputParams"
            variant_types.append(struct_name)

        # Create variant type
        variant_type = f"std::variant<{', '.join(variant_types)}>"

        # Build variant name (global)
        variant_name = f"{interface_name}_AllInputParams"

        # For mutator, also use just the variant name (global)
        fully_qualified_variant = variant_name

        # Build mutator for variant with all types
        variant_mutator_parts = []
        for variant_type_name in variant_types:
            variant_mutator_parts.append(
                f"        GetDefaultMutator<{variant_type_name}>()"
            )

        variant_mutator = ",\n".join(variant_mutator_parts)

        variant_code = f"""// Variant containing all possible input parameter combinations for interface {interface_name}
    using {variant_name} = {variant_type};

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<{fully_qualified_variant}>() {{
        return fuzztest::VariantOf(
    {variant_mutator}
        );
    }}"""

        return variant_code

    def _generate_output_variant(
        self, package: str, interface_name: str, method_names: List[str]
    ) -> str:
        """Generate using statement with std::variant for all OutputParams types."""
        # Build variant types (just the struct names, since they are global)
        variant_types = []
        for method_name in method_names:
            struct_name = f"{interface_name}_{method_name}_OutputParams"
            variant_types.append(struct_name)

        # Create variant type
        variant_type = f"std::variant<{', '.join(variant_types)}>"

        # Build variant name (global)
        variant_name = f"{interface_name}_AllOutputParams"

        # For mutator, also use just the variant name (global)
        fully_qualified_variant = variant_name

        # Build mutator for variant with all types
        variant_mutator_parts = []
        for variant_type_name in variant_types:
            variant_mutator_parts.append(
                f"        GetDefaultMutator<{variant_type_name}>()"
            )

        variant_mutator = ",\n".join(variant_mutator_parts)

        variant_code = f"""// Variant containing all possible output parameter combinations for interface {interface_name}
    using {variant_name} = {variant_type};

    // Mutator for the variant
    template<>
    auto GetDefaultMutator<{fully_qualified_variant}>() {{
        return fuzztest::VariantOf(
    {variant_mutator}
        );
    }}"""

        return variant_code

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
        elif kind == "union":  # Add this
            variants = entry.get("variants", [])
            return self._generate_union_mutator(entry_name, variants, package)

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

    def _generate_interface_dispatcher(
        self, package: str, interface_name: str, methods: List[Dict[str, Any]]
    ) -> str:
        """Generate dispatcher function for an interface."""

        # Build interface C++ type name - убираем лишний интерфейс из неймспейса
        if package:
            # Убираем имя интерфейса из пакета (последнюю часть)
            package_parts = package.split(".")
            if package_parts and package_parts[-1] == interface_name:
                package_parts = package_parts[:-1]
            cpp_package = "::".join(package_parts)
            interface_type = f"kosipc::stdcpp::{cpp_package}::{interface_name}"
        else:
            interface_type = f"kosipc::stdcpp::{interface_name}"

        # Build variant names
        input_variant_name = f"{interface_name}_AllInputParams"
        output_variant_name = f"{interface_name}_AllOutputParams"

        # Generate switch cases
        switch_cases = []
        for idx, method in enumerate(methods):
            method_name = method.get("name")
            parameters = method.get("parameters", [])

            # Build parameter list for method call in the exact order from JSON
            call_params = []
            for param in parameters:
                param_name = param.get("name")
                param_direction = param.get("direction")

                if param_direction == "input":
                    call_params.append(f"inputParams.{param_name}")
                elif param_direction == "output":
                    call_params.append(f"outputParams.{param_name}")

            call_params_str = ", ".join(call_params) if call_params else ""

            # Get output handle parameters that need StoreHandle
            output_handle_params = self._get_output_handle_params(parameters)
            
            # Generate StoreHandle calls for each output handle parameter
            store_handle_calls = []
            for handle_param in output_handle_params:
                store_handle_calls.append(f"                StoreHandle(outputParams.{handle_param});")
            
            store_handles_str = "\n".join(store_handle_calls)

            # Generate case - без const
            if store_handles_str:
                case_code = f"""        case {idx}: {{
                    auto& inputParams = std::get<{idx}>(input_variant);
                    {interface_name}_{method_name}_OutputParams outputParams;
                    interface.{method_name}({call_params_str});
    {store_handles_str}
                    output_variant = outputParams;
                    break;
                }}"""
            else:
                case_code = f"""        case {idx}: {{
                    auto& inputParams = std::get<{idx}>(input_variant);
                    {interface_name}_{method_name}_OutputParams outputParams;
                    interface.{method_name}({call_params_str});
                    output_variant = outputParams;
                    break;
                }}"""
            switch_cases.append(case_code)

        # Generate the dispatcher function - без const в параметрах
        dispatcher_code = f"""// Dispatcher function for interface {interface_name}
    // Calls the appropriate method based on the variant index
    void Dispatch({interface_type}& interface,
                  {input_variant_name}& input_variant,
                  {output_variant_name}& output_variant) {{
        switch (input_variant.index()) {{
    {chr(10).join(switch_cases)}
            default:
                __builtin_unreachable();
        }}
    }}"""

        return dispatcher_code
    
    def _has_handle_type(self, type_info: Dict[str, Any]) -> bool:
        """Check if a type is a handle or contains handles."""
        if not isinstance(type_info, dict):
            return False
        
        kind = type_info.get("kind")
        
        if kind == "handle":
            return True
        elif kind == "type_definition":
            # Resolve typedef to check underlying type
            type_name = type_info.get("name")
            if type_name:
                resolved = self._resolve_typedef(type_name)
                if resolved:
                    return self._has_handle_type(resolved)
            return False
        elif kind in ("struct", "union"):
            # Check all fields/variants for handles
            fields = type_info.get("fields", []) or type_info.get("variants", [])
            for field in fields:
                field_type = field.get("type")
                if field_type and self._has_handle_type(field_type):
                    return True
            return False
        elif kind == "sequence":
            item_type = type_info.get("item_type")
            if item_type:
                return self._has_handle_type(item_type)
            return False
        elif kind == "array":
            item_type = type_info.get("item_type")
            if item_type:
                return self._has_handle_type(item_type)
            return False
        
        return False

    def _get_output_handle_params(self, parameters: List[Dict[str, Any]]) -> List[str]:
        """Get list of output parameter names that are handles."""
        handle_params = []
        for param in parameters:
            param_direction = param.get("direction")
            if param_direction == "output":
                param_type = param.get("type")
                param_name = param.get("name")
                if param_type and self._has_handle_type(param_type):
                    handle_params.append(param_name)
        return handle_params

    def generate_mutators(
        self,
    ) -> Tuple[
        List[str],
        List[str],
        List[str],
        List[str],
        List[str],
        List[str],
        List[str],
        List[str],
    ]:
        """
        Generate all mutators from all JSON files.

        Returns:
            Tuple of (mutators, debug_info, input_params_structs, output_params_structs,
                      input_variants, output_variants, interface_dispatchers, test_fixtures)
        """
        mutators = []
        debug_info = []
        input_params_structs = []
        output_params_structs = []
        input_variants = []
        output_variants = []
        interface_dispatchers = []
        test_fixtures = []
        generated_structs = set()
        generated_interfaces = set()

        # First, document typedef resolutions from all packages
        for typedef_name in self.typedef_registry:
            description = self._resolve_and_generate_mutator_description(typedef_name)
            if description and description not in debug_info:
                debug_info.append(description)

        # Then generate mutators for all struct types across all JSON files
        for json_data in self.json_data_list:
            contents = json_data.get("contents", {})
            if not contents:
                continue

            package = contents.get("name", "")
            entries = contents.get("entries", [])
            interface = contents.get("interface")

            # Generate mutators for structs
            for entry in entries:
                if entry.get("kind") in ("struct", "union"):
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

            # Generate InputParams and OutputParams structs for each method (only if interface exists)
            if interface and isinstance(interface, dict):
                methods = interface.get("methods", [])
                if methods:
                    # Extract interface name from package
                    interface_name = package.split(".")[-1] if package else "Unknown"
                    method_names = []
                    methods_list = []

                    for method in methods:
                        method_name = method.get("name")
                        parameters = method.get("parameters", [])

                        if method_name:
                            method_names.append(method_name)
                            methods_list.append(method)

                            # Generate InputParams
                            input_struct_code, input_mutator_code = (
                                self._generate_input_params_struct(
                                    package, interface_name, method_name, parameters
                                )
                            )
                            input_params_structs.append(input_struct_code)
                            input_params_structs.append(input_mutator_code)

                            # Generate OutputParams
                            output_struct_code, output_mutator_code = (
                                self._generate_output_params_struct(
                                    package, interface_name, method_name, parameters
                                )
                            )
                            output_params_structs.append(output_struct_code)
                            output_params_structs.append(output_mutator_code)

                    # Generate input variant for this interface
                    if method_names:
                        input_variant_code = self._generate_interface_variant(
                            package, interface_name, method_names
                        )
                        input_variants.append(input_variant_code)

                        # Generate output variant for this interface
                        output_variant_code = self._generate_output_variant(
                            package, interface_name, method_names
                        )
                        output_variants.append(output_variant_code)

                        # Generate dispatcher for this interface
                        dispatcher_code = self._generate_interface_dispatcher(
                            package, interface_name, methods_list
                        )
                        interface_dispatchers.append(dispatcher_code)

                        # Generate test fixture for this interface (only once per interface)
                        if interface_name not in generated_interfaces:
                            test_fixture_code = self._generate_test_fixture(
                                package, interface_name
                            )
                            test_fixtures.append(test_fixture_code)
                            generated_interfaces.add(interface_name)

        return (
            mutators,
            debug_info,
            input_params_structs,
            output_params_structs,
            input_variants,
            output_variants,
            interface_dispatchers,
            test_fixtures,
        )

    def _generate_test_fixture(self, package: str, interface_name: str) -> str:
        """Generate test fixture class for an interface."""

        # Build interface C++ type name
        if package:
            package_parts = package.split(".")
            if package_parts and package_parts[-1] == interface_name:
                package_parts = package_parts[:-1]
            cpp_package = "::".join(package_parts)
            interface_type = f"kosipc::stdcpp::{cpp_package}::{interface_name}"
        else:
            interface_type = f"kosipc::stdcpp::{interface_name}"

        # Build variant names
        input_variant_name = f"{interface_name}_AllInputParams"
        output_variant_name = f"{interface_name}_AllOutputParams"

        # Generate fixture class
        fixture_code = f"""// Fuzz test fixture for interface {interface_name}
    class {interface_name}IpcFixture
    {{
    public:
        {interface_name}IpcFixture()
            : m_app(kosipc::MakeApplicationPureClient())
            , m_proxy(m_app.MakeProxy<{interface_type}>(kosipc::ConnectDcmPublication()))
        {{}}

        void Fuzz({input_variant_name} input)
        {{
            {output_variant_name} output;

            try
            {{
                Dispatch(
                    *m_proxy,
                    input,
                    output);
            }}
            catch(const std::runtime_error& e)
            {{
                std::string msg = e.what();
                const std::string prefix = "Transport error";
                
                if (msg.size() >= prefix.size() && 
                    msg.compare(0, prefix.size(), prefix) == 0) {{
                    throw;
                }}
            }}
        }}

        kosipc::Application m_app;
        kosipc::unique_ptr<{interface_type}> m_proxy;
    }};

    FUZZ_TEST_F({interface_name}IpcFixture, Fuzz)
        .WithDomains(GetDefaultMutator<{input_variant_name}>());
    """

        return fixture_code


def generate_fuzztest_from_json(json_data_list: List[Dict[str, Any]]) -> str:
    """
    Main function to generate fuzztest mutators from a list of IDL JSON data.
    """
    if not json_data_list:
        return "// No JSON data provided"

    parser = IDLParser(json_data_list)
    (
        mutators,
        debug_info,
        input_params_structs,
        output_params_structs,
        input_variants,
        output_variants,
        interface_dispatchers,
        test_fixtures,
    ) = parser.generate_mutators()

    result_parts = []

    # Add header
    result_parts.append("// Auto-generated mutators for IDL interfaces")
    result_parts.append("")

    include_list = [
        "fuzztest/fuzztest.h",
        "fuzztest/googletest_adaptor.h",
        "fuzztest/googletest_fixture_adapter.h",
        "gtest/gtest.h",
        "",
        "testing/common.h",
        "testing/handle_storage.h",
        "",
        "kl/CoverageMapper.cdl.cpp.h",
        "component/coverage_mapper/coverage_mapper_reciever.h",
        "",
        "kosipc/application.h",
        "kosipc/connect_dcm_publication.h",
        "kosipc/api.h",
        "",
        "kos/trace.h",
    ]

    for include in include_list:
        if include == "":
            result_parts.append("")
        else:
            result_parts.append(f"#include<{include}>")
    result_parts.append("")

    packages = [data["contents"]["name"] for data in json_data_list]

    for package in packages:
        result_parts.append(f"#include<{package.replace('.', '/')}.idl.cpp.h>")
    result_parts.append("")

    result_parts.append(f"// Packages: {', '.join(packages)}")
    result_parts.append("")

    # Char mutator for using in strings
    result_parts.append("auto ascii_char = fuzztest::InRange<char>(0, 127);")

    # Add typedef resolution info
    if debug_info:
        result_parts.append("// Type definitions resolution:")
        result_parts.extend(debug_info)
        result_parts.append("")

    # Add mutators for struct types
    if mutators:
        result_parts.extend(mutators)
        result_parts.append("")
    else:
        result_parts.append("// No mutators generated")
        result_parts.append("")

    # Add input parameter structures
    if input_params_structs:
        result_parts.append("// Input parameter structures for interface methods")
        result_parts.extend(input_params_structs)
        result_parts.append("")

    # Add output parameter structures
    if output_params_structs:
        result_parts.append("// Output parameter structures for interface methods")
        result_parts.extend(output_params_structs)
        result_parts.append("")

    # Add input variants
    if input_variants:
        result_parts.append(
            "// Input variants (all possible input parameter combinations)"
        )
        result_parts.extend(input_variants)
        result_parts.append("")

    # Add output variants
    if output_variants:
        result_parts.append(
            "// Output variants (all possible output parameter combinations)"
        )
        result_parts.extend(output_variants)
        result_parts.append("")

    # Add interface dispatchers
    if interface_dispatchers:
        result_parts.append("// Interface dispatcher functions")
        result_parts.extend(interface_dispatchers)
        result_parts.append("")

    if test_fixtures:
        result_parts.append("// Fuzz test fixtures")
        result_parts.extend(test_fixtures)
        result_parts.append("")

    return "\n".join(result_parts)
