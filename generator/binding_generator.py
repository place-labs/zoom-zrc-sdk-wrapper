#!/usr/bin/env python3
"""
Zoom Rooms SDK Binding Generator

Parses C++ SDK headers and generates pybind11 bindings automatically.
This allows easy updates when new SDK versions are released.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from jinja2 import Template

try:
    from clang.cindex import Index, CursorKind, TypeKind, AccessSpecifier
except ImportError:
    print("ERROR: libclang not found. Install with: pip install libclang")
    sys.exit(1)


@dataclass
class MethodInfo:
    """Represents a method/function to bind"""
    name: str
    return_type: str
    params: List[tuple]  # [(name, type), ...]
    is_static: bool = False
    is_const: bool = False
    is_virtual: bool = False
    is_pure_virtual: bool = False


@dataclass
class ClassInfo:
    """Represents a class/interface to bind"""
    name: str
    full_name: str
    is_interface: bool = False
    methods: List[MethodInfo] = field(default_factory=list)
    parent_classes: List[str] = field(default_factory=list)
    is_sink: bool = False  # Callback interface


@dataclass
class EnumInfo:
    """Represents an enum to bind"""
    name: str
    values: List[tuple]  # [(name, value), ...]


class SDKParser:
    """Parse SDK headers with libclang"""

    def __init__(self, sdk_include_path: str):
        self.sdk_include_path = Path(sdk_include_path)
        self.index = Index.create()
        self.classes: Dict[str, ClassInfo] = {}
        self.enums: Dict[str, EnumInfo] = {}

    def parse_header(self, header_path: Path, clang_args: List[str] = None):
        """Parse a single header file"""
        if clang_args is None:
            clang_args = [
                '-x', 'c++',
                '-std=c++11',
                f'-I{self.sdk_include_path}',
                f'-I{self.sdk_include_path}/include',
                f'-I{self.sdk_include_path}/include/ServiceComponents',
            ]

        print(f"Parsing {header_path.name}...")
        tu = self.index.parse(str(header_path), args=clang_args)

        # Check for parse errors
        for diag in tu.diagnostics:
            if diag.severity >= 3:  # Error or Fatal
                print(f"  Warning: {diag.spelling}")

        # Walk the AST
        self._walk_cursor(tu.cursor, header_path)

    def _walk_cursor(self, cursor, target_file: Path):
        """Recursively walk AST cursor"""
        # Only process declarations in the target file
        if cursor.location.file and Path(cursor.location.file.name) == target_file:
            if cursor.kind == CursorKind.CLASS_DECL or cursor.kind == CursorKind.STRUCT_DECL:
                self._process_class(cursor)
            elif cursor.kind == CursorKind.ENUM_DECL:
                self._process_enum(cursor)

        # Recurse to children
        for child in cursor.get_children():
            self._walk_cursor(child, target_file)

    def _process_class(self, cursor):
        """Process a class/struct declaration"""
        name = cursor.spelling
        if not name or name.startswith('_'):
            return  # Skip anonymous or internal classes

        is_interface = name.startswith('I') and name[1].isupper()
        is_sink = 'Sink' in name or 'Callback' in name

        class_info = ClassInfo(
            name=name,
            full_name=cursor.type.spelling,
            is_interface=is_interface,
            is_sink=is_sink
        )

        # Get parent classes
        for base in cursor.get_children():
            if base.kind == CursorKind.CXX_BASE_SPECIFIER:
                parent_name = base.type.spelling
                # Clean up the name (remove "class " prefix if present)
                parent_name = parent_name.replace('class ', '').replace('struct ', '')
                class_info.parent_classes.append(parent_name)

        # Get methods
        for child in cursor.get_children():
            if child.kind == CursorKind.CXX_METHOD:
                method = self._process_method(child)
                if method:
                    class_info.methods.append(method)

        self.classes[name] = class_info

    def _process_method(self, cursor) -> Optional[MethodInfo]:
        """Process a method declaration"""
        name = cursor.spelling
        if not name or name.startswith('_'):
            return None  # Skip private/internal methods

        # Skip operator overloads and destructors
        if name.startswith('operator') or name.startswith('~'):
            return None

        # Get return type
        return_type = cursor.result_type.spelling

        # Get parameters
        params = []
        for arg in cursor.get_arguments():
            param_name = arg.spelling or f'arg{len(params)}'
            param_type = arg.type.spelling
            params.append((param_name, param_type))

        return MethodInfo(
            name=name,
            return_type=return_type,
            params=params,
            is_static=cursor.is_static_method(),
            is_const=cursor.is_const_method(),
            is_virtual=cursor.is_virtual_method(),
            is_pure_virtual=cursor.is_pure_virtual_method()
        )

    def _process_enum(self, cursor):
        """Process an enum declaration"""
        name = cursor.spelling
        if not name or name.startswith('_'):
            return

        values = []
        for child in cursor.get_children():
            if child.kind == CursorKind.ENUM_CONSTANT_DECL:
                values.append((child.spelling, child.enum_value))

        self.enums[name] = EnumInfo(name=name, values=values)


class BindingGenerator:
    """Generate pybind11 C++ code from parsed SDK info"""

    BINDING_TEMPLATE = """
// Auto-generated pybind11 bindings for Zoom Rooms SDK
// Generated by binding_generator.py - DO NOT EDIT MANUALLY

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// SDK headers
#include "IZRCSDK.h"
#include "IZoomRoomsService.h"
#include "IMeetingService.h"
#include "IPreMeetingService.h"
#include "IProAVService.h"
#include "ISettingService.h"
#include "IPhoneCallService.h"
#include "ZRCSDKTypes.h"

// Helper headers
#include "ServiceComponents/IMeetingAudioHelper.h"
#include "ServiceComponents/IMeetingVideoHelper.h"
#include "ServiceComponents/IParticipantHelper.h"
#include "ServiceComponents/IMeetingControlHelper.h"
#include "ServiceComponents/IMeetingChatHelper.h"
#include "ServiceComponents/ICameraControlHelper.h"

namespace py = pybind11;
using namespace ZRCSDK;

// Trampoline classes for callbacks (allow Python to override C++ virtual methods)
{% for class in sink_classes %}
class Py{{ class.name }} : public {{ class.name }} {
public:
    using {{ class.name }}::{{ class.name }};

    {% for method in class.methods %}
    {{ method.return_type }} {{ method.name }}({{ method.param_decls }}) override {
        PYBIND11_OVERRIDE{% if method.is_pure_virtual %}_PURE{% endif %}(
            {{ method.return_type }},
            {{ class.name }},
            {{ method.name }}{% for param in method.param_names %},
            {{ param }}{% endfor %}
        );
    }
    {% endfor %}
};
{% endfor %}

PYBIND11_MODULE(zrc_sdk, m) {
    m.doc() = "Zoom Rooms Controller SDK Python Bindings";

    // ========== Enums ==========
    {% for enum in enums %}
    py::enum_<{{ enum.name }}>(m, "{{ enum.name }}")
        {% for value_name, value_val in enum.values %}
        .value("{{ value_name }}", {{ enum.name }}::{{ value_name }})
        {% endfor %}
        .export_values();
    {% endfor %}

    // ========== Core SDK Classes ==========
    {% for class in core_classes %}
    py::class_<{{ class.name }}{% if class.parent_classes %}, {{ class.parent_classes|join(', ') }}{% endif %}>(m, "{{ class.name }}")
        {% for method in class.methods %}
        .def("{{ method.name }}", &{{ class.name }}::{{ method.name }})
        {% endfor %};
    {% endfor %}

    // ========== Sink/Callback Classes (with trampolines) ==========
    {% for class in sink_classes %}
    py::class_<{{ class.name }}, Py{{ class.name }}>(m, "{{ class.name }}")
        {% for method in class.methods %}
        .def("{{ method.name }}", &{{ class.name }}::{{ method.name }})
        {% endfor %};
    {% endfor %}
}
"""

    def __init__(self, parser: SDKParser):
        self.parser = parser

    def generate(self, output_path: Path):
        """Generate pybind11 C++ binding code"""
        print(f"\nGenerating bindings to {output_path}...")

        # Separate core classes from sinks
        core_classes = [c for c in self.parser.classes.values() if not c.is_sink]
        sink_classes = [c for c in self.parser.classes.values() if c.is_sink]

        # Prepare template data
        template_data = {
            'enums': list(self.parser.enums.values()),
            'core_classes': core_classes,
            'sink_classes': sink_classes,
        }

        # Enhance method info for template
        for cls in sink_classes:
            for method in cls.methods:
                method.param_decls = ', '.join(f'{t} {n}' for n, t in method.params)
                method.param_names = [n for n, t in method.params]

        # Render template
        template = Template(self.BINDING_TEMPLATE)
        code = template.render(**template_data)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

        print(f"✓ Generated bindings for:")
        print(f"  - {len(self.parser.enums)} enums")
        print(f"  - {len(core_classes)} core classes")
        print(f"  - {len(sink_classes)} callback interfaces")


def main():
    """Main entry point"""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    sdk_include = project_root.parent / 'include'
    output_file = project_root / 'bindings' / 'zrc_bindings.cpp'

    print("=" * 60)
    print("Zoom Rooms SDK Binding Generator")
    print("=" * 60)
    print(f"SDK Include: {sdk_include}")
    print(f"Output: {output_file}")
    print()

    # Headers to parse (core services only for now)
    headers_to_parse = [
        'IZRCSDK.h',
        'IZoomRoomsService.h',
        'IMeetingService.h',
        'IPreMeetingService.h',
        'IProAVService.h',
        'ZRCSDKTypes.h',
    ]

    # Create parser
    parser = SDKParser(str(sdk_include))

    # Parse headers
    for header_name in headers_to_parse:
        header_path = sdk_include / 'include' / header_name
        if not header_path.exists():
            header_path = sdk_include / header_name

        if header_path.exists():
            parser.parse_header(header_path)
        else:
            print(f"WARNING: Header not found: {header_name}")

    # Generate bindings
    generator = BindingGenerator(parser)
    generator.generate(output_file)

    print("\n" + "=" * 60)
    print("✓ Binding generation complete!")
    print("  Run './build.sh' to compile the Python module")
    print("=" * 60)


if __name__ == '__main__':
    main()
