# dv-transaction-trace
Provides APIs to support writing transactional data to [Perfetto]()
traces, with a focus on design and verification (DV) environments.

Integrations are provided for:
- SystemVerilog environments (low-level API)
- UVM environments (via the recorder)
- Python environments (low-level API)
- Zuspec Python environments

Python environments have access to both a pure-Python and C++-implemented
API. SystemVerilog environments require a native implementation. The Python
module must be able to auto-detect the presence of a native implementation
and use it. 

# Packaging / Release
The library, with both pure-Python and binary-wheel implementation, is released
as a Python wheel on pypi.org

# Other integrations

## DFM

# Low-level Transaction API
Transactions are recorded using a low-level C API. This same implementation is
used for Python/Native, Plain-C, and SystemVerilog clients.

## Python specifics

## C++ specifics

## SystemVerilog specifics


