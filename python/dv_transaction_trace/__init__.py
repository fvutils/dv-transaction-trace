"""DV Transaction Trace - Python API

A clean, Pythonic API for transaction-level tracing in design verification.

This package provides Protocol-based abstract interfaces and concrete
implementations for recording transaction traces that can be viewed in
tools like Perfetto UI.

Basic usage:
    from dv_transaction_trace import create_trace, Radix
    
    with create_trace('trace.perfetto', 'simulation', '1ns') as trace:
        stream = trace.create_stream('axi_master')
        
        txn = stream.begin_transaction('READ', start_time=1000)
        txn.add_uint('addr', 0x1000, Radix.HEX)
        txn.add_uint('data', 0xDEADBEEF, Radix.HEX)
        txn.add_string('status', 'OK')
        txn.close(end_time=2000)
"""

from .api import (
    ITrace,
    IStream,
    ITransaction,
    Radix,
    LinkType,
    create_trace,
)

__all__ = [
    'ITrace',
    'IStream', 
    'ITransaction',
    'Radix',
    'LinkType',
    'create_trace',
]

__version__ = '0.1.0'
