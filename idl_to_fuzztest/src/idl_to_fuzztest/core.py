import json
import logging
from typing import Any, Dict, List, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_header(input_files: list[str]) -> str:
    """
    Generate C++ header with fuzztest mutators from IDL JSON files.
    Output parameters are completely ignored.
    """
    if not input_files:
        logger.error("No input files provided")
        return "// Error: No input files\n"

    content = []
    content.append("// Generated header with FuzzTest mutators for IDL types")
    content.append("// Output parameters are ignored")
    content.append("#pragma once\n")
    content.append("#include <fuzztest/fuzztest.h>")
    content.append("#include <fuzztest/domain.h>")
    content.append("")
    content.append("#include <cstdint>")
    content.append("#include <string>")
    content.append("#include <vector>")

    content.append("")
    content.append(f"template <typename T>")
    content.append(f"auto GetDefaultMutator();")
    content.append("")

    content.append("")
    content.append(f"template <typename T, size_t n>")
    content.append(f"auto GetDefaultArrayMutator(){{")
    content.append(
        "    return fuzztest::ContainerOf<std::vector<T>>(GetDefaultMutator<T>()).WithMaxSize(n);"
    )
    content.append("}")
    content.append("")

    content.append("")
    content.append(f"template <size_t n>")
    content.append(f"auto GetDefaultStringMutator() {{")
    content.append("    return fuzztest::String().WithMaxSize(n);")
    content.append("}")
    content.append("")

    content.append("")
    content.append(f"template <size_t n>")
    content.append(f"auto GetDefaultBytesMutator() {{")
    content.append(
        "    return fuzztest::ContainerOf<std::vector<uint8_t>>(fuzztest::Arbitrary<uint8_t>()).WithMaxSize(n);"
    )
    content.append("}")
    content.append("")

    # Обрабатываем каждый входной файл
    for file_path in input_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Извлекаем информацию о модуле
            module_name = extract_module_name(data)
            namespace = f"kosipc::stdcpp::{module_name}"

            content.append(f"// Generated from: {file_path}")

            # Генерируем forward declarations для структур

            # Генерируем мутаторы для каждого типа
            generate_mutators_for_types(data, content, namespace)

            logger.info(f"Successfully processed {file_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            content.append(f"// Error: Invalid JSON in {file_path}\n")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            content.append(f"// Error processing {file_path}: {e}\n")

    return "\n".join(content)


def extract_module_name(data: Dict[str, Any]) -> str:
    """Extract module name from JSON."""
    contents = data.get("contents", {})
    full_name = contents.get("name", "")
    # Extract last part after dot
    parts = full_name.split(".")
    return "".join(parts[:-1]) if parts else "unknown"


def extract_structs(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all struct definitions from JSON."""
    structs = []
    contents = data.get("contents", {})
    entries = contents.get("entries", [])

    for entry in entries:
        if entry.get("kind") == "struct":
            structs.append(
                {
                    "name": entry.get("name"),
                    "fields": entry.get("fields", []),
                    "static_size": entry.get("static_size", 0),
                }
            )

    return structs


def extract_typedefs(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all typedef definitions from JSON."""
    typedefs = []
    contents = data.get("contents", {})
    entries = contents.get("entries", [])

    for entry in entries:
        if entry.get("kind") == "typedef":
            typedefs.append({"name": entry.get("name"), "type": entry.get("type", {})})

    return typedefs


def extract_constants(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all constants from JSON."""
    constants = []
    contents = data.get("contents", {})
    entries = contents.get("entries", [])

    for entry in entries:
        if entry.get("kind") == "const":
            constants.append(
                {
                    "name": entry.get("name"),
                    "type": entry.get("type", {}),
                    "value": entry.get("value"),
                }
            )

    return constants


def generate_mutators_for_types(
    data: Dict[str, Any], content: List[str], namespace: str
):
    """Generate fuzztest mutators for all types."""

    # Генерируем мутаторы для структур
    structs = extract_structs(data)
    for struct_info in structs:
        generate_struct_mutator(struct_info, content, namespace)

    # Генерируем мутаторы для typedef
    typedefs = extract_typedefs(data)
    for typedef_info in typedefs:
        generate_typedef_mutator(typedef_info, content, namespace)

    # Генерируем мутаторы для констант
    constants = extract_constants(data)
    for const_info in constants:
        generate_constant_mutator(const_info, content, namespace)

    # Генерируем мутаторы для input параметров интерфейса
    generate_interface_mutators(data, content, namespace)


def get_cpp_type(idl_type: Dict[str, Any]) -> str:
    """Convert IDL type to C++ type."""
    kind = idl_type.get("kind")

    if kind == "basic_type":
        basic_type = idl_type.get("basic_type")
        type_map = {
            "SInt8": "int8_t",
            "SInt16": "int16_t",
            "SInt32": "int32_t",
            "SInt64": "int64_t",
            "UInt8": "uint8_t",
            "UInt16": "uint16_t",
            "UInt32": "uint32_t",
            "UInt64": "uint64_t",
            "UIntSize": "size_t",
            "UIntPtr": "uintptr_t",
        }
        return type_map.get(basic_type, "uint32_t")

    elif kind == "string":
        max_size = idl_type.get("size", 1024)
        return f"std::string"  # Используем std::string для UTF-8 строк

    elif kind == "bytes":
        max_size = idl_type.get("size", 1024)
        return f"std::vector<uint8_t>"

    elif kind == "array":
        element_type = get_cpp_type(idl_type.get("element_type", {}))
        size = idl_type.get("size", 0)
        return f"std::array<{element_type}, {size}>"

    elif kind == "typedef_type":
        return idl_type.get("name", "UnknownType")

    else:
        logger.warning(f"Unknown type kind: {kind}")
        return "uint32_t"


def generate_struct_mutator(
    struct_info: Dict[str, Any], content: List[str], namespace: str
):
    """Generate fuzztest mutator for a struct using StructOf."""
    struct_name = struct_info["name"]
    fields = struct_info["fields"]

    content.append(f"// Mutator for struct {struct_name} using StructOf")
    content.append(f"template<>")
    content.append(f"auto GetDefaultMutator<{namespace}::{struct_name}>() {{")
    content.append(f"    return fuzztest::StructOf<{namespace}::{struct_name}>(")

    # Генерируем генераторы для каждого поля
    for i, field in enumerate(fields):
        field_name = field.get("name")
        field_type = field.get("type", {})
        generator = get_field_generator(field_type, field_name)

        # Добавляем комментарий с именем поля для читаемости
        content.append(
            f"        {generator}{',' if i < len(fields) - 1 else ''} // {field_name}"
        )

    content.append(f"    );")
    content.append(f"}}\n")


def generate_union_mutator(
    union_info: Dict[str, Any], content: List[str], namespace: str
):
    """Generate fuzztest mutator for a union (std::variant) using VariantOf."""
    union_name = union_info["name"]
    variants = union_info.get("variants", [])

    content.append(f"// Mutator for union {union_name} using VariantOf")
    content.append(f"template<>")
    content.append(f"auto GetDefaultMutator<{namespace}::{union_name}>() {{")
    content.append(f"    return fuzztest::VariantOf<{namespace}::{union_name}>(")

    # Генерируем генераторы для каждого варианта
    for i, variant in enumerate(variants):
        variant_type = variant.get("type", {})
        variant_name = variant.get("name", f"variant_{i}")
        generator = get_field_generator(variant_type, variant_name)

        # Добавляем комментарий с именем варианта для читаемости
        content.append(
            f"        {generator}{',' if i < len(variants) - 1 else ''} // {variant_name}"
        )

    content.append(f"    );")
    content.append(f"}}\n")


def get_field_generator(field_type: Dict[str, Any], field_name: str) -> str:
    """Get fuzztest generator for a field type."""
    kind = field_type.get("kind")

    if kind == "basic_type":
        basic_type = field_type.get("basic_type")
        if "SInt" in basic_type or "UInt" in basic_type:
            # Определяем диапазон на основе типа
            return f"fuzztest::Arbitrary<{get_cpp_type(field_type)}>()"

    elif kind == "string":
        max_size = field_type.get("size", 1024)
        return f"GetDefaultStringMutator<{max_size}>()"

    elif kind == "bytes":
        max_size = field_type.get("size", 1024)
        return f"GetDefaultBytesMutator<{max_size}>()"

    elif kind == "array":
        element_type = field_type.get("element_type", {})
        size = field_type.get("size", 0)
        elem_gen = get_field_generator(element_type, "element")
        return f"fuzztest::ArrayOf({size}, {elem_gen})"

    elif kind == "type_definition":
        type_name = field_type.get("name", {})
        type_namespace = "::".join(field_type.get("package", {}).split(".")[:-1])
        return f"GetDefaultMutator<kosipc::stdcpp::{type_namespace}::{type_name}>()"

    # По умолчанию
    return "GetDefaultBytesMutator<>()"


def get_min_value(basic_type: str) -> str:
    """Get minimum value for basic type."""
    if "UInt" in basic_type:
        return "0"
    elif "SInt8" in basic_type:
        return "-128"
    elif "SInt16" in basic_type:
        return "-32768"
    elif "SInt32" in basic_type:
        return "-2147483648"
    elif "SInt64" in basic_type:
        return "-9223372036854775808LL"
    return "0"


def get_max_value(basic_type: str) -> str:
    """Get maximum value for basic type."""
    if "UInt8" in basic_type:
        return "255"
    elif "UInt16" in basic_type:
        return "65535"
    elif "UInt32" in basic_type:
        return "4294967295U"
    elif "UInt64" in basic_type:
        return "18446744073709551615ULL"
    elif "SInt8" in basic_type:
        return "127"
    elif "SInt16" in basic_type:
        return "32767"
    elif "SInt32" in basic_type:
        return "2147483647"
    elif "SInt64" in basic_type:
        return "9223372036854775807LL"
    elif "UIntSize" in basic_type or "UIntPtr" in basic_type:
        return "SIZE_MAX"
    return "1000"


def generate_typedef_mutator(
    typedef_info: Dict[str, Any], content: List[str], namespace: str
):
    """Generate fuzztest mutator for a typedef."""
    pass
    # typedef_name = typedef_info["name"]
    # original_type = typedef_info["type"]
    # cpp_type = get_cpp_type(original_type)

    # content.append(f"// Mutator for typedef {typedef_name}")
    # content.append(f"template <>")
    # content.append(f"auto fuzztest::Arbitrary<{namespace}::{typedef_name}>() {{")
    # content.append(f"        return fuzztest::Map(")
    # content.append(
    #     f"            []({cpp_type} value) {{ return static_cast<{typedef_name}>(value); }},"
    # )
    # content.append(f"            fuzztest::Arbitrary<{cpp_type}>()")
    # content.append(f"        );")
    # content.append(f"}};\n")


def generate_constant_mutator(
    const_info: Dict[str, Any], content: List[str], namespace: str
):
    """Generate fuzztest mutator for a constant."""
    const_name = const_info["name"]
    const_type = const_info["type"]
    const_value = const_info["value"]
    cpp_type = get_cpp_type(const_type)

    content.append(f"// Constant {const_name}")
    content.append(f"constexpr {cpp_type} {const_name} = {const_value};")
    content.append(f"// Mutator for constant {const_name}")
    content.append(f"auto {const_name}Generator() {{")
    content.append(f"    return fuzztest::Just({const_name});")
    content.append(f"}}\n")


def generate_interface_mutators(
    data: Dict[str, Any], content: List[str], namespace: str
):
    """Generate mutators for input parameters of interface methods only."""
    interface = data.get("contents", {}).get("interface")
    if not interface:
        return

    methods = interface.get("methods", [])

    for method in methods:
        method_name = method.get("name")
        parameters = method.get("parameters", [])

        # Фильтруем только input параметры
        input_params = [p for p in parameters if p.get("direction") == "input"]

        if input_params:
            content.append(
                f"// Mutator for {method_name} input parameters (output parameters ignored)"
            )

            # Генерируем структуру только для input параметров
            param_struct_name = f"{method_name}InputParams"
            content.append(f"struct {param_struct_name} {{")
            for param in input_params:
                param_name = param.get("name")
                param_type = param.get("type", {})
                cpp_type = get_cpp_type(param_type)
                content.append(f"    {cpp_type} {param_name};")
            content.append(f"}};\n")

            # Генерируем мутатор для структуры input параметров
            content.append(f"template <>")
            content.append(f"auto GetDefaultMutator<{param_struct_name}>() {{")

            param_generators = []
            for param in input_params:
                param_type = param.get("type", {})
                generator = get_field_generator(param_type, param.get("name"))
                param_generators.append(generator)

            if param_generators:
                content.append(f"    return fuzztest::StructOf<{param_struct_name}>(")
                param_types = [get_cpp_type(p.get("type", {})) for p in input_params]
                param_names = [p.get("name") for p in input_params]
                # content.append(
                #     f"            []({', '.join(param_types)} {', '.join(param_names)}) {{"
                # )
                # content.append(
                #     f"                return {param_struct_name}{{{', '.join(param_names)}}};"
                # )
                # content.append(f"            }},")
                for i, gen in enumerate(param_generators):
                    content.append(
                        f"        {gen}{',' if i + 1 < len(param_generators) else ''}"
                    )
                content.append(f"    );")
            else:
                content.append(
                    f"        return fuzztest::Just({param_struct_name}{{}});"
                )

            # content.append(f"    }}")
            content.append(f"}};")
            content.append("")

            # Добавляем отдельную функцию-генератор для простоты использования
            content.append(
                f"// Convenience generator for {method_name} input parameters"
            )
            content.append(f"auto {method_name}InputGenerator() {{")
            content.append(f"    return fuzztest::Arbitrary<{param_struct_name}>();")
            content.append(f"}}\n")

            logger.info(
                f"Generated mutator for {method_name} with {len(input_params)} input parameters"
            )
        else:
            content.append(
                f"// Method {method_name} has no input parameters (all outputs), skipping\n"
            )
            logger.info(f"Skipping {method_name} - no input parameters")
