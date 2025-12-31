"""DV Transaction Trace - Python Protocol API

This module defines Protocol classes that represent the abstract interface
for transaction tracing, based on the dvtt.h C API. These protocols define
the contract that implementations must fulfill.

The API follows a hierarchical structure:
- Trace: Top-level container representing a trace file
- Stream: Logical grouping of transactions (e.g., per bus, monitor)
- Transaction: A time-bounded event with attributes and relationships

This design allows for multiple backend implementations (Perfetto, VCD, custom)
while maintaining a consistent, Pythonic interface.
"""

from typing import Protocol, Optional, Union, runtime_checkable
from enum import IntEnum


class Radix(IntEnum):
    """Display radix for numeric values"""
    BIN = 0
    OCT = 1
    DEC = 2
    HEX = 3
    UNSIGNED = 4
    STRING = 5
    TIME = 6
    REAL = 7


class LinkType(IntEnum):
    """Link types for establishing relationships between transactions"""
    PARENT_CHILD = 0
    RELATED = 1
    CAUSE_EFFECT = 2
    CUSTOM = 3


@runtime_checkable
class ITransaction(Protocol):
    """Protocol for transaction objects
    
    Transactions represent time-bounded events in the trace with a start
    and end time. They can have attributes (name-value pairs) and
    relationships to other transactions.
    """
    
    @property
    def name(self) -> str:
        """Transaction name"""
        ...
    
    @property
    def type_name(self) -> Optional[str]:
        """Optional type name for the transaction"""
        ...
    
    @property
    def start_time(self) -> int:
        """Transaction start time in trace time units"""
        ...
    
    @property
    def end_time(self) -> int:
        """Transaction end time in trace time units (0 if not closed)"""
        ...
    
    def is_open(self) -> bool:
        """Check if transaction is currently open"""
        ...
    
    def is_closed(self) -> bool:
        """Check if transaction is closed (but not freed)"""
        ...
    
    def close(self, end_time: int) -> None:
        """Close the transaction at specified end time"""
        ...
    
    def add_int(self, name: str, value: int, radix: Radix = Radix.HEX) -> None:
        """Add signed integer attribute"""
        ...
    
    def add_uint(self, name: str, value: int, radix: Radix = Radix.HEX) -> None:
        """Add unsigned integer attribute"""
        ...
    
    def add_float(self, name: str, value: float) -> None:
        """Add floating-point attribute"""
        ...
    
    def add_string(self, name: str, value: str) -> None:
        """Add string attribute"""
        ...
    
    def add_time(self, name: str, value: int) -> None:
        """Add time attribute"""
        ...
    
    def add_bits(self, name: str, bits: bytes, num_bits: int, 
                 radix: Radix = Radix.HEX) -> None:
        """Add bit vector attribute"""
        ...
    
    def add_blob(self, name: str, data: bytes) -> None:
        """Add binary blob attribute"""
        ...
    
    def add_link(self, target: 'ITransaction', link_type: LinkType = LinkType.RELATED,
                 relation_name: Optional[str] = None) -> None:
        """Create a link to another transaction"""
        ...


@runtime_checkable
class IStream(Protocol):
    """Protocol for stream objects
    
    Streams organize transactions into logical groups, typically representing
    a monitor, bus, or component. Each stream appears as a separate track
    in the trace viewer.
    """
    
    @property
    def name(self) -> str:
        """Stream name"""
        ...
    
    @property
    def scope(self) -> Optional[str]:
        """Optional hierarchical scope path"""
        ...
    
    @property
    def type_name(self) -> Optional[str]:
        """Optional type name for the stream"""
        ...
    
    def is_open(self) -> bool:
        """Check if stream is currently open"""
        ...
    
    def is_closed(self) -> bool:
        """Check if stream is closed (but not freed)"""
        ...
    
    def close(self) -> None:
        """Close the stream (closes all open transactions)"""
        ...
    
    def begin_transaction(self, name: str, start_time: int,
                         type_name: Optional[str] = None,
                         parent: Optional[ITransaction] = None) -> ITransaction:
        """Open a new transaction on this stream
        
        Args:
            name: Transaction name
            start_time: Transaction start time
            type_name: Optional type name
            parent: Optional parent transaction for hierarchical nesting.
                   If specified, this transaction will be rendered as a child
                   in the trace viewer with its own sub-track.
        
        Returns:
            New transaction handle
        """
        ...


@runtime_checkable
class ITrace(Protocol):
    """Protocol for trace objects
    
    The trace is the top-level container that manages the output file and
    coordinates all streams and transactions. It defines the time units
    and overall trace metadata.
    """
    
    @property
    def name(self) -> str:
        """Trace name for display/identification"""
        ...
    
    @property
    def filename(self) -> str:
        """Output trace filename"""
        ...
    
    @property
    def time_units(self) -> str:
        """Time unit string (e.g., '1ns', '1ps', '1us')"""
        ...
    
    def create_stream(self, name: str, scope: Optional[str] = None,
                     type_name: Optional[str] = None) -> IStream:
        """Create and open a new transaction stream"""
        ...
    
    def close(self) -> None:
        """Close the trace and flush to file"""
        ...
    
    def __enter__(self) -> 'ITrace':
        """Context manager entry"""
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        ...


def create_trace(filename: str, name: str, time_units: str) -> ITrace:
    """Factory function to create a new trace
    
    Args:
        filename: Output trace filename (e.g., 'trace.perfetto')
        name: Trace name for display/identification
        time_units: Time unit string (e.g., '1ns', '1ps', '1us')
    
    Returns:
        A new trace object implementing ITrace protocol
    
    Example:
        with create_trace('sim.perfetto', 'simulation', '1ns') as trace:
            stream = trace.create_stream('axi_master')
            txn = stream.begin_transaction('READ', 1000)
            txn.add_uint('addr', 0x1000, Radix.HEX)
            txn.close(2000)
    """
    from .impl.perfetto_impl import PerfettoTrace
    return PerfettoTrace(filename, name, time_units)
