# DV Transaction Trace Documentation

This directory contains the conceptual and reference documentation for the DV Transaction Trace (DVTT) library.

## Documentation Structure

The documentation is organized into three main sections:

### 1. Core Concepts (`concepts.rst`)
Explains the fundamental ideas behind transaction recording:
- **Key Abstractions**: Trace, Stream, and Transaction objects
- **Attributes**: Adding data to transactions
- **Relationships**: Optional links between transactions
- **Recording Patterns**: Common usage patterns
- **Best Practices**: Guidelines for effective transaction recording

This section focuses on **what** transaction recording is and **why** you would use it, not specific API details.

### 2. C API Reference (`api_reference.rst`)
Complete reference documentation for all API functions:
- Type definitions and enumerations
- Function signatures and parameters
- Return values and error handling
- Implementation notes

This section documents the **interface specification** that all implementations should follow. Multiple implementations may exist (SystemVerilog DPI, standalone C, vendor-specific), but all conform to this API.

### 3. Usage Examples (`examples.rst`)
Practical examples demonstrating real-world usage:
- Basic transaction recording
- Advanced patterns (bulk operations, multiple streams)
- SystemVerilog integration via DPI-C
- State machine tracking
- Error highlighting with colors
- Performance optimization techniques

This section shows **how** to use the API in practice.

## Building the Documentation

The documentation uses Sphinx with reStructuredText format.

### Prerequisites
```bash
pip install sphinx
```

### Build HTML Documentation
```bash
make html
```

The generated HTML will be in `_build/html/`. Open `_build/html/index.html` in a browser.

### Other Formats
```bash
make latexpdf  # PDF via LaTeX
make epub      # EPUB format
make clean     # Remove build artifacts
```

## Documentation Philosophy

This documentation follows these principles:

1. **Concepts First**: Users should understand the mental model before diving into APIs
2. **Multiple Implementations**: The API is a specification; implementations may vary
3. **Practical Examples**: Show real-world usage, not just toy examples
4. **Complete Reference**: Document every function, parameter, and return value
5. **Cross-Reference**: Link concepts to API functions to examples

## Source Material

The documentation is based on:
- The C API header file (`src/include/dvtt.h`)
- Common verification patterns and best practices
- Industry experience with transaction-level debugging

## Contributing

When updating documentation:
- Keep concepts separate from API details
- Add examples for new features
- Update all three sections consistently
- Run `make html` to verify no errors
- Check that cross-references work correctly
