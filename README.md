# Header Dependency Finder

A lightweight Python utility that recursively discovers C/C++ header dependencies starting from a single header file. It can export the dependency list and copy the discovered files into a separate directory while preserving their relative directory structure.

## Features

- **Recursive dependency discovery** — follows `#include` directives through nested header files.
- **Multiple include directories** — supports additional search paths using `-I`.
- **Duplicate prevention** — processes each header file only once.
- **Dependency export** — saves the list of discovered files to a text file.
- **Header copying** — copies discovered headers to a destination directory.
- **Directory structure preservation** — keeps relative paths to help maintain existing include directives.
- **Unresolved include reporting** — lists dependencies that could not be found.

## Requirements

- Python 3.10 or later
- No third-party Python packages required

## Installation

Clone the repository:

```bash
git clone https://github.com/dyostr/cpp-header-dependency-tool.git
cd cpp-header-dependency-tool
```

Alternatively, download `find_include.py` and run it directly with Python.

## Usage

### Find header dependencies

```bash
python find_include.py path/to/main.h
```

### Specify include directories

Use `-I` to specify directories where the script should search for included headers:

```bash
python find_include.py path/to/main.h \
    -I path/to/sdk/include \
    -I path/to/third_party/include
```

Multiple `-I` arguments are supported.

### Export the dependency list

Use `-o` to save the discovered file paths:

```bash
python find_include.py path/to/main.h \
    -I path/to/sdk/include \
    -o headers.txt
```

### Copy discovered headers

Use `--copy-to` to copy the discovered files to a destination directory:

```bash
python find_include.py path/to/main.h \
    -I path/to/sdk/include \
    --root path/to/sdk \
    --copy-to output/headers
```

The script preserves paths relative to the specified source root.

For example, a source file located at:

```text
sdk/include/core/types.h
```

will be copied to:

```text
output/headers/include/core/types.h
```

### Export dependencies and copy files

All options can be combined:

```bash
python find_include.py path/to/main.h \
    -I path/to/sdk/include \
    -I path/to/sdk/third_party/include \
    --root path/to/sdk \
    --copy-to output/headers \
    -o headers.txt
```

## Command-Line Options

| Option | Description |
| --- | --- |
| `header` | Path to the starting header file |
| `-I DIR` | Additional include search directory; can be specified multiple times |
| `-o FILE` | Save the discovered dependency list to a text file |
| `--copy-to DIR` | Copy discovered headers to the specified directory |
| `--root DIR` | Source root used to preserve relative directory structure |

## How It Works

The script parses `#include` directives and recursively searches for referenced header files.

For quoted includes:

```cpp
#include "local.h"
```

it first searches the directory containing the current header, then the configured include directories.

For angle-bracket includes:

```cpp
#include <sdk/types.h>
```

it searches the configured include directories.

A visited-file set prevents duplicate processing and infinite recursion caused by circular dependencies.

## Limitations

This utility performs text-based dependency analysis rather than running a C/C++ preprocessor.

As a result:

- Conditional compilation directives such as `#ifdef` and `#if` are not evaluated.
- Macro-based includes such as `#include HEADER_NAME` are not resolved.
- Platform-specific and configuration-specific dependencies may be reported differently from those used by an actual build.
- Generated headers must already exist to be discovered.
- System headers and external dependencies may require additional include directories.
- Files outside the specified source root are skipped during copying to avoid writing files outside the intended directory structure.

For exact compiler-specific dependencies, consider using compiler dependency tools such as MSVC's `/showIncludes` or integrating with the existing CMake build configuration.
