# Unit Tests

This directory contains unit tests for both the C++ and Python implementations of the DV Transaction Trace library.

## C++ Tests

The C++ tests use Google Test framework and test the C API implementation.

### Prerequisites
- Google Test (`libgtest-dev`)
- Protocol Buffers (`libprotobuf-dev`)

### Building and Running

```bash
# Configure CMake
cmake -B build -DBUILD_TESTS=ON

# Build tests
cmake --build build

# Run tests
cd build
ctest --output-on-failure

# Or run directly
./build/tests/unit/test_dvtt_basic
```

## Python Tests

The Python tests use pytest and test the pure Python implementation.

### Prerequisites
- Python 3.7+
- pytest

Install pytest:
```bash
pip install pytest
```

### Running Tests

From the repository root:

```bash
# Run all Python tests
pytest tests/unit/test_python_impl.py -v

# Or use pytest.ini configuration
pytest -v

# Run specific test class
pytest tests/unit/test_python_impl.py::TestBasic -v

# Run specific test
pytest tests/unit/test_python_impl.py::TestBasic::test_create_trace -v
```

## Test Coverage

### Basic Functionality Tests
- Trace creation and management
- Stream opening, closing, and lifecycle
- Transaction opening, closing, and lifecycle
- Handle management
- State queries

### Attribute Tests
- Integer attributes (signed/unsigned, various sizes)
- Floating-point attributes
- String attributes
- Time attributes
- Bit vector attributes
- Binary blob attributes
- Multiple attributes per transaction

### Advanced Features Tests
- Multiple streams
- Multiple transactions per stream
- Transactions across multiple streams
- Links between transactions
- Batch attribute operations

## Adding New Tests

### C++ Tests
Add new test cases to `test_basic.cpp` or create a new test file following the pattern:

```cpp
#include <gtest/gtest.h>
#include "include/dvtt.h"

TEST_F(DVTTBasicTest, YourNewTest) {
    // Test code here
}
```

### Python Tests
Add new test methods to existing test classes or create new test classes:

```python
class TestYourFeature:
    def test_your_test(self, tmp_path):
        # Test code here
        pass
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run C++ Tests
  run: |
    cmake -B build -DBUILD_TESTS=ON
    cmake --build build
    cd build && ctest --output-on-failure

- name: Run Python Tests
  run: |
    pip install pytest
    pytest -v
```
