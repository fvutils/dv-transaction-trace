# DV Transaction Trace - Implementation Package

This package contains concrete implementations of the DV Transaction Trace API.

## Structure

```
impl/
├── __init__.py           - Legacy functional API (backwards compatibility)
└── perfetto_impl.py      - Protocol-based Perfetto implementation
```

## Perfetto Implementation

The `perfetto_impl.py` module provides classes that implement the Protocol interfaces
defined in `dv_transaction_trace.api`:

- **`PerfettoTrace`** - Implements `ITrace` protocol
- **`PerfettoStream`** - Implements `IStream` protocol  
- **`PerfettoTransaction`** - Implements `ITransaction` protocol

These classes emit proper Perfetto protobuf messages to create `.perfetto` trace files
viewable in Perfetto UI.

### Usage (Recommended - Protocol API)

```python
from dv_transaction_trace import create_trace, Radix

with create_trace('trace.perfetto', 'simulation', '1ns') as trace:
    stream = trace.create_stream('axi_master')
    txn = stream.begin_transaction('READ', 1000)
    txn.add_uint('addr', 0x1000, Radix.HEX)
    txn.close(2000)
```

## Legacy Functional API

The `__init__.py` module provides the original functional-style API for backwards
compatibility. This API is preserved for existing code but new code should use
the Protocol-based API.

### Usage (Legacy - Backwards Compatibility)

```python
from dv_transaction_trace.impl import (
    create_trace, close_trace,
    open_stream, close_stream,
    open_transaction, close_transaction,
    add_attr_uint, Radix
)

trace = create_trace('trace.perfetto', 'simulation', '1ns')
stream = open_stream(trace, 'axi_master')
txn = open_transaction(stream, 'READ', 1000)
add_attr_uint(txn, 'addr', 0x1000, Radix.HEX)
close_transaction(txn, 2000)
close_trace(trace)
```

## Adding New Implementations

To add a new trace format implementation:

1. Create a new module in this package (e.g., `vcd_impl.py`)
2. Implement the Protocol interfaces from `dv_transaction_trace.api`
3. Update `create_trace()` factory in `api.py` to support the new format

Example:

```python
# vcd_impl.py
from ..api import ITrace, IStream, ITransaction, Radix, LinkType

class VcdTrace(ITrace):
    """VCD format implementation"""
    # Implement all ITrace methods...

class VcdStream(IStream):
    """VCD stream implementation"""
    # Implement all IStream methods...

class VcdTransaction(ITransaction):
    """VCD transaction implementation"""
    # Implement all ITransaction methods...
```

Then update the factory:

```python
# api.py
def create_trace(filename: str, name: str, time_units: str, 
                 format: str = 'perfetto') -> ITrace:
    if format == 'perfetto':
        from .impl.perfetto_impl import PerfettoTrace
        return PerfettoTrace(filename, name, time_units)
    elif format == 'vcd':
        from .impl.vcd_impl import VcdTrace
        return VcdTrace(filename, name, time_units)
    # ...
```

## Implementation Details

### Perfetto Format

The Perfetto implementation writes binary protobuf messages:

- **ClockSnapshot** - Establishes time reference
- **TrackDescriptor** - Defines streams as tracks
- **TrackEvent (TYPE_SLICE_BEGIN)** - Transaction start
- **TrackEvent (TYPE_SLICE_END)** - Transaction end
- **DebugAnnotation** - Transaction attributes
- **Flow IDs** - Transaction links

Messages are written as length-delimited protobufs (varint length + data).

### Legacy Format

The legacy API in `__init__.py` uses the same underlying data structures but
with simplified protobuf emission (placeholder implementation).

## Testing

The Protocol API is tested in `tests/unit/test_protocol_api.py`:

```bash
pytest tests/unit/test_protocol_api.py -v
```

The legacy API is tested in other existing test files that use `dv_transaction_trace.impl`.

## See Also

- [Protocol API Documentation](../README_PROTOCOL_API.md) - Complete API reference
- [Quick Reference](../../../PROTOCOL_API_QUICK_REF.md) - Quick start guide
- [dvtt.h](../../../src/include/dvtt.h) - C API specification
