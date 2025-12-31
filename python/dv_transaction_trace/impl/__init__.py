"""Pure Python implementation of DV Transaction Trace API

This module provides implementations of the dvtt API that generate 
Perfetto-compatible trace files.

Backwards compatibility note: This module previously contained a standalone
implementation. For the new Protocol-based API, use:
    from dv_transaction_trace import create_trace, Radix, LinkType

For the legacy implementation, use the functions exported here.
"""

import struct
import io
from typing import Optional, Dict, List, Any, Union
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


class AttrType(IntEnum):
    """Attribute value types"""
    INT8 = 0
    INT16 = 1
    INT32 = 2
    INT64 = 3
    UINT8 = 4
    UINT16 = 5
    UINT32 = 6
    UINT64 = 7
    REAL = 8
    DOUBLE = 9
    STRING = 10
    BITSTRING = 11
    BLOB = 12


class LinkType(IntEnum):
    """Link types for establishing relationships"""
    PARENT_CHILD = 0
    RELATED = 1
    CAUSE_EFFECT = 2
    CUSTOM = 3


class ObjectState(IntEnum):
    """State of trace objects"""
    OPEN = 0
    CLOSED = 1
    FREED = 2


class DebugAnnotation:
    """Container for transaction attributes"""
    def __init__(self, name: str, attr_type: AttrType, value: Any, radix: Radix = Radix.HEX):
        self.name = name
        self.type = attr_type
        self.value = value
        self.radix = radix


class Transaction:
    """Transaction implementation"""
    def __init__(self, txn_id: int, stream: 'Stream', name: str, start_time: int, 
                 type_name: Optional[str] = None):
        self.id = txn_id
        self.stream = stream
        self.name = name
        self.type_name = type_name or ""
        self.start_time = start_time
        self.end_time = 0
        self.state = ObjectState.OPEN
        self.handle = 0
        self.attributes: List[DebugAnnotation] = []
        self.flow_ids: List[int] = []
        self.attributes_batch_mode = False
    
    def is_open(self) -> bool:
        return self.state == ObjectState.OPEN
    
    def is_closed(self) -> bool:
        return self.state == ObjectState.CLOSED


class Stream:
    """Stream implementation"""
    def __init__(self, trace: 'Trace', uuid: int, name: str, 
                 scope: Optional[str] = None, type_name: Optional[str] = None):
        self.trace = trace
        self.uuid = uuid
        self.name = name
        self.scope = scope or ""
        self.type_name = type_name or ""
        self.state = ObjectState.OPEN
        self.handle = 0
        self.transactions: List[Transaction] = []
    
    def is_open(self) -> bool:
        return self.state == ObjectState.OPEN
    
    def is_closed(self) -> bool:
        return self.state == ObjectState.CLOSED


class ProtobufWriter:
    """Helper for writing Perfetto protobuf format"""
    
    VARINT = 0
    FIXED64 = 1
    LENGTH_DELIMITED = 2
    FIXED32 = 5
    
    def __init__(self, output: io.BufferedWriter):
        self.output = output
    
    def write_varint(self, value: int):
        """Write a varint-encoded integer"""
        while value >= 0x80:
            self.output.write(bytes([(value & 0x7F) | 0x80]))
            value >>= 7
        self.output.write(bytes([value & 0x7F]))
    
    def write_tag(self, field_number: int, wire_type: int):
        """Write a protobuf field tag"""
        self.write_varint((field_number << 3) | wire_type)
    
    def write_length_delimited(self, field_number: int, data: bytes):
        """Write a length-delimited field"""
        self.write_tag(field_number, self.LENGTH_DELIMITED)
        self.write_varint(len(data))
        self.output.write(data)
    
    def write_string_field(self, field_number: int, value: str):
        """Write a string field"""
        data = value.encode('utf-8')
        self.write_length_delimited(field_number, data)
    
    def write_uint64_field(self, field_number: int, value: int):
        """Write a uint64 field"""
        self.write_tag(field_number, self.VARINT)
        self.write_varint(value)
    
    def write_int64_field(self, field_number: int, value: int):
        """Write a signed int64 field with zigzag encoding"""
        encoded = (value << 1) ^ (value >> 63)
        self.write_uint64_field(field_number, encoded)
    
    def write_double_field(self, field_number: int, value: float):
        """Write a double field"""
        self.write_tag(field_number, self.FIXED64)
        self.output.write(struct.pack('<d', value))
    
    def write_message(self, field_number: int, message_bytes: bytes):
        """Write a nested message"""
        self.write_length_delimited(field_number, message_bytes)


class Trace:
    """Trace implementation"""
    
    def __init__(self, filename: str, name: str, time_units: str):
        self.filename = filename
        self.name = name
        self.time_units = time_units
        self.output_file = open(filename, 'wb')
        self.writer = ProtobufWriter(self.output_file)
        self.sequence_id = 1
        self.clock_id = 64  # BUILTIN_CLOCK_MONOTONIC
        
        self.streams: List[Stream] = []
        self.stream_handles: Dict[int, Stream] = {}
        self.transaction_handles: Dict[int, Transaction] = {}
        
        self.next_stream_handle = 1
        self.next_transaction_handle = 1
        self.next_track_uuid = 1
        self.next_transaction_id = 1
        self.next_flow_id = 1
        
        self._emit_clock_snapshot()
    
    def _emit_clock_snapshot(self):
        """Emit initial clock snapshot packet"""
        # Simplified - actual implementation would emit proper ClockSnapshot
        pass
    
    def _emit_track_descriptor(self, stream: Stream):
        """Emit TrackDescriptor packet for a stream"""
        # Simplified - actual implementation would emit proper TrackDescriptor
        pass
    
    def _emit_track_event_begin(self, txn: Transaction):
        """Emit TYPE_SLICE_BEGIN track event"""
        # Simplified - actual implementation would emit proper TrackEvent
        pass
    
    def _emit_track_event_end(self, txn: Transaction):
        """Emit TYPE_SLICE_END track event"""
        # Simplified - actual implementation would emit proper TrackEvent
        pass
    
    def close(self):
        """Close the trace and output file"""
        if self.output_file:
            self.output_file.close()
            self.output_file = None


def format_radix_name(name: str, radix: Radix) -> str:
    """Format attribute name with radix suffix"""
    suffixes = {
        Radix.BIN: "[bin]",
        Radix.OCT: "[oct]",
        Radix.DEC: "[dec]",
        Radix.HEX: "[hex]",
        Radix.UNSIGNED: "[u]",
        Radix.TIME: "[time]",
    }
    suffix = suffixes.get(radix, "")
    return name + suffix


def bits_to_string(bits: bytes, num_bits: int, radix: Radix) -> str:
    """Convert bit vector to string representation"""
    if radix == Radix.HEX:
        return "0x" + bits.hex()
    elif radix == Radix.BIN:
        result = "0b"
        for byte in reversed(bits):
            result += format(byte, '08b')
        return result[:2 + num_bits]
    else:
        return "0x" + bits.hex()


# API functions (legacy implementation)
def create_trace(filename: str, name: str, time_units: str) -> Trace:
    """Create a new trace object and open output file"""
    return Trace(filename, name, time_units)


def close_trace(trace: Trace):
    """Close and free a trace object"""
    if trace:
        # Close all open streams
        for stream in trace.streams:
            if stream.is_open():
                close_stream(stream)
        trace.close()


def open_stream(trace: Trace, name: str, scope: Optional[str] = None, 
                type_name: Optional[str] = None) -> Stream:
    """Create and open a transaction stream"""
    stream = Stream(trace, trace.next_track_uuid, name, scope, type_name)
    trace.next_track_uuid += 1
    stream.handle = trace.next_stream_handle
    trace.next_stream_handle += 1
    
    trace.streams.append(stream)
    trace.stream_handles[stream.handle] = stream
    
    trace._emit_track_descriptor(stream)
    
    return stream


def close_stream(stream: Stream):
    """Close a transaction stream"""
    if stream:
        # Close all open transactions
        for txn in stream.transactions:
            if txn.is_open():
                close_transaction(txn, txn.start_time)
        stream.state = ObjectState.CLOSED


def open_transaction(stream: Stream, name: str, start_time: int,
                    type_name: Optional[str] = None,
                    parent: Optional[Transaction] = None) -> Transaction:
    """Open a new transaction on a stream
    
    Args:
        stream: Stream to create transaction on
        name: Transaction name
        start_time: Start time
        type_name: Optional type name
        parent: Optional parent transaction for hierarchical nesting
    
    Returns:
        New transaction object
    
    Note: This legacy implementation doesn't fully support the parent parameter.
          For full parent/child track hierarchy support, use the Protocol-based API.
    """
    if stream.state != ObjectState.OPEN:
        raise ValueError("Stream is not open")
    
    trace = stream.trace
    txn = Transaction(trace.next_transaction_id, stream, name, start_time, type_name)
    trace.next_transaction_id += 1
    txn.handle = trace.next_transaction_handle
    trace.next_transaction_handle += 1
    
    stream.transactions.append(txn)
    trace.transaction_handles[txn.handle] = txn
    
    return txn


def close_transaction(txn: Transaction, end_time: int):
    """Close a transaction"""
    if txn and txn.state == ObjectState.OPEN:
        txn.end_time = end_time
        txn.state = ObjectState.CLOSED
        
        # Emit protobuf packets
        trace = txn.stream.trace
        trace._emit_track_event_begin(txn)
        trace._emit_track_event_end(txn)


def add_attr_int(txn: Transaction, name: str, value: int, radix: Radix = Radix.HEX):
    """Add an integer attribute to a transaction"""
    if txn:
        attr = DebugAnnotation(format_radix_name(name, radix), AttrType.INT64, value, radix)
        txn.attributes.append(attr)


def add_attr_uint(txn: Transaction, name: str, value: int, radix: Radix = Radix.HEX):
    """Add an unsigned integer attribute to a transaction"""
    if txn:
        attr = DebugAnnotation(format_radix_name(name, radix), AttrType.UINT64, value, radix)
        txn.attributes.append(attr)


def add_attr_float(txn: Transaction, name: str, value: float):
    """Add a floating-point attribute to a transaction"""
    if txn:
        attr = DebugAnnotation(name, AttrType.DOUBLE, value, Radix.REAL)
        txn.attributes.append(attr)


def add_attr_string(txn: Transaction, name: str, value: str):
    """Add a string attribute to a transaction"""
    if txn:
        attr = DebugAnnotation(name, AttrType.STRING, value, Radix.STRING)
        txn.attributes.append(attr)


def add_attr_time(txn: Transaction, name: str, value: int):
    """Add a time attribute to a transaction"""
    add_attr_uint(txn, name, value, Radix.TIME)


def add_attr_bits(txn: Transaction, name: str, bits: bytes, num_bits: int, radix: Radix = Radix.HEX):
    """Add a bit vector attribute to a transaction"""
    if txn:
        value_str = bits_to_string(bits, num_bits, radix)
        attr = DebugAnnotation(format_radix_name(name, radix), AttrType.BITSTRING, value_str, radix)
        txn.attributes.append(attr)


def add_attr_blob(txn: Transaction, name: str, data: bytes):
    """Add a binary blob attribute to a transaction"""
    if txn:
        attr = DebugAnnotation(name, AttrType.BLOB, data, Radix.HEX)
        txn.attributes.append(attr)


def add_link(source: Transaction, target: Transaction, link_type: LinkType, 
             relation_name: Optional[str] = None):
    """Add a link between two transactions"""
    if source and target:
        trace = source.stream.trace
        flow_id = trace.next_flow_id
        trace.next_flow_id += 1
        
        source.flow_ids.append(flow_id)
        target.flow_ids.append(flow_id)


# Query functions
def get_stream_name(stream: Stream) -> str:
    """Get stream name"""
    return stream.name if stream else ""


def get_stream_handle(stream: Stream) -> int:
    """Get stream handle"""
    return stream.handle if stream and stream.state != ObjectState.FREED else 0


def is_stream_open(stream: Stream) -> bool:
    """Check if stream is open"""
    return stream.is_open() if stream else False


def is_stream_closed(stream: Stream) -> bool:
    """Check if stream is closed"""
    return stream.is_closed() if stream else False


def get_transaction_name(txn: Transaction) -> str:
    """Get transaction name"""
    return txn.name if txn else ""


def get_transaction_start_time(txn: Transaction) -> int:
    """Get transaction start time"""
    return txn.start_time if txn else 0


def get_transaction_end_time(txn: Transaction) -> int:
    """Get transaction end time"""
    return txn.end_time if txn else 0


def is_transaction_open(txn: Transaction) -> bool:
    """Check if transaction is open"""
    return txn.is_open() if txn else False


def is_transaction_closed(txn: Transaction) -> bool:
    """Check if transaction is closed"""
    return txn.is_closed() if txn else False
