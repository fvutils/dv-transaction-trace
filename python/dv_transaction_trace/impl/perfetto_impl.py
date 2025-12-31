"""Perfetto-based implementation of DV Transaction Trace API

This module provides a concrete implementation of the ITrace, IStream, and
ITransaction protocols using the Perfetto trace format and protobuf API.

The implementation emits Perfetto TracePacket messages that can be viewed
in the Perfetto UI (ui.perfetto.dev) or analyzed with the trace processor.
"""

from typing import Optional, List, Dict
import struct
from ..api import ITrace, IStream, ITransaction, Radix, LinkType

# Import Perfetto protobuf messages
from perfetto.protos.perfetto.trace import perfetto_trace_pb2 as pb


class PerfettoTransaction(ITransaction):
    """Perfetto-based transaction implementation"""
    
    def __init__(self, txn_id: int, stream: 'PerfettoStream', name: str, 
                 start_time: int, type_name: Optional[str] = None,
                 parent: Optional['PerfettoTransaction'] = None):
        self._id = txn_id
        self._stream = stream
        self._name = name
        self._type_name = type_name
        self._start_time = start_time
        self._end_time = 0
        self._is_open = True
        self._parent = parent
        self._attributes: List[pb.DebugAnnotation] = []
        self._flow_ids: List[int] = []
        
        # Allocate track based on parent relationship
        if parent:
            # Child transaction gets its own track
            self._track_uuid = self._stream._trace._allocate_track_uuid()
            # Emit track descriptor with parent relationship
            self._stream._trace._emit_child_track_descriptor(self)
        else:
            # Root transaction uses stream's track
            self._track_uuid = stream._track_uuid
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def type_name(self) -> Optional[str]:
        return self._type_name
    
    @property
    def start_time(self) -> int:
        return self._start_time
    
    @property
    def end_time(self) -> int:
        return self._end_time
    
    @property
    def attributes(self) -> List[pb.DebugAnnotation]:
        """List of attributes attached to this transaction"""
        return self._attributes
    
    def is_open(self) -> bool:
        return self._is_open
    
    def is_closed(self) -> bool:
        return not self._is_open and self._end_time > 0
    
    def close(self, end_time: int) -> None:
        """Close the transaction and emit Perfetto events"""
        if not self._is_open:
            return
        
        self._end_time = end_time
        self._is_open = False
        
        # Emit slice begin event
        self._stream._trace._emit_slice_begin(self)
        
        # Emit slice end event
        self._stream._trace._emit_slice_end(self)
    
    def add_int(self, name: str, value: int, radix: Radix = Radix.HEX) -> None:
        """Add signed integer attribute"""
        attr = pb.DebugAnnotation()
        attr.name = self._format_name(name, radix)
        attr.int_value = value
        self._attributes.append(attr)
    
    def add_uint(self, name: str, value: int, radix: Radix = Radix.HEX) -> None:
        """Add unsigned integer attribute"""
        attr = pb.DebugAnnotation()
        attr.name = self._format_name(name, radix)
        attr.uint_value = value
        self._attributes.append(attr)
    
    def add_float(self, name: str, value: float) -> None:
        """Add floating-point attribute"""
        attr = pb.DebugAnnotation()
        attr.name = name
        attr.double_value = value
        self._attributes.append(attr)
    
    def add_string(self, name: str, value: str) -> None:
        """Add string attribute"""
        attr = pb.DebugAnnotation()
        attr.name = name
        attr.string_value = value
        self._attributes.append(attr)
    
    def add_time(self, name: str, value: int) -> None:
        """Add time attribute"""
        self.add_uint(name, value, Radix.TIME)
    
    def add_bits(self, name: str, bits: bytes, num_bits: int, 
                 radix: Radix = Radix.HEX) -> None:
        """Add bit vector attribute"""
        attr = pb.DebugAnnotation()
        attr.name = self._format_name(name, radix)
        attr.string_value = self._bits_to_string(bits, num_bits, radix)
        self._attributes.append(attr)
    
    def add_blob(self, name: str, data: bytes) -> None:
        """Add binary blob attribute"""
        attr = pb.DebugAnnotation()
        attr.name = name
        # Convert to hex string for display
        attr.string_value = data.hex()
        self._attributes.append(attr)
    
    def add_link(self, target: ITransaction, link_type: LinkType = LinkType.RELATED,
                 relation_name: Optional[str] = None) -> None:
        """Create a link to another transaction"""
        if not isinstance(target, PerfettoTransaction):
            raise TypeError("Target must be a PerfettoTransaction")
        
        # Allocate a flow ID that both transactions will share
        flow_id = self._stream._trace._allocate_flow_id()
        self._flow_ids.append(flow_id)
        target._flow_ids.append(flow_id)
    
    @staticmethod
    def _format_name(name: str, radix: Radix) -> str:
        """Format attribute name with radix suffix"""
        radix_suffixes = {
            Radix.BIN: "[bin]",
            Radix.OCT: "[oct]",
            Radix.DEC: "[dec]",
            Radix.HEX: "[hex]",
            Radix.UNSIGNED: "[u]",
            Radix.TIME: "[time]",
        }
        suffix = radix_suffixes.get(radix, "")
        return name + suffix
    
    @staticmethod
    def _bits_to_string(bits: bytes, num_bits: int, radix: Radix) -> str:
        """Convert bit vector to string representation"""
        if radix == Radix.HEX:
            return "0x" + bits.hex()
        elif radix == Radix.BIN:
            result = "0b"
            for byte in reversed(bits):
                result += format(byte, '08b')
            return result[:2 + num_bits]
        elif radix == Radix.OCT:
            value = int.from_bytes(bits, 'little')
            return "0o" + oct(value)[2:]
        else:
            return "0x" + bits.hex()


class PerfettoStream(IStream):
    """Perfetto-based stream implementation"""
    
    def __init__(self, trace: 'PerfettoTrace', track_uuid: int, name: str,
                 scope: Optional[str] = None, type_name: Optional[str] = None):
        self._trace = trace
        self._track_uuid = track_uuid
        self._name = name
        self._scope = scope
        self._type_name = type_name
        self._is_open = True
        self._transactions: List[PerfettoTransaction] = []
        
        # Emit track descriptor when stream is created
        self._trace._emit_track_descriptor(self)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def scope(self) -> Optional[str]:
        return self._scope
    
    @property
    def type_name(self) -> Optional[str]:
        return self._type_name
    
    @property
    def transactions(self) -> List['PerfettoTransaction']:
        """List of transactions in this stream"""
        return self._transactions
    
    def is_open(self) -> bool:
        return self._is_open
    
    def is_closed(self) -> bool:
        return not self._is_open
    
    def close(self) -> None:
        """Close the stream and all open transactions"""
        if not self._is_open:
            return
        
        # Close all open transactions
        for txn in self._transactions:
            if txn.is_open():
                txn.close(txn.start_time)
        
        self._is_open = False
    
    def begin_transaction(self, name: str, start_time: int,
                         type_name: Optional[str] = None,
                         parent: Optional[ITransaction] = None) -> ITransaction:
        """Open a new transaction on this stream"""
        if not self._is_open:
            raise RuntimeError("Cannot create transaction on closed stream")
        
        txn_id = self._trace._allocate_transaction_id()
        
        # Ensure parent is PerfettoTransaction if provided
        parent_txn = None
        if parent:
            if not isinstance(parent, PerfettoTransaction):
                raise TypeError("Parent must be a PerfettoTransaction")
            parent_txn = parent
        
        txn = PerfettoTransaction(txn_id, self, name, start_time, type_name, parent_txn)
        self._transactions.append(txn)
        return txn


class PerfettoTrace(ITrace):
    """Perfetto-based trace implementation
    
    This implementation writes Perfetto protobuf messages to a .perfetto file
    that can be opened in ui.perfetto.dev or analyzed with trace_processor.
    """
    
    def __init__(self, filename: str, name: str, time_units: str):
        self._filename = filename
        self._name = name
        self._time_units = time_units
        self._file = open(filename, 'wb')
        self._streams: List[PerfettoStream] = []
        
        # ID generation
        self._next_track_uuid = 1
        self._next_transaction_id = 1
        self._next_flow_id = 1
        self._sequence_id = 1
        
        # Perfetto configuration
        self._clock_id = 64  # BUILTIN_CLOCK_MONOTONIC
        
        # Emit initial clock snapshot
        self._emit_clock_snapshot()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def filename(self) -> str:
        return self._filename
    
    @property
    def time_units(self) -> str:
        return self._time_units
    
    @property
    def streams(self) -> List[PerfettoStream]:
        """List of streams in this trace"""
        return self._streams
    
    def create_stream(self, name: str, scope: Optional[str] = None,
                     type_name: Optional[str] = None) -> IStream:
        """Create and open a new transaction stream"""
        track_uuid = self._allocate_track_uuid()
        stream = PerfettoStream(self, track_uuid, name, scope, type_name)
        self._streams.append(stream)
        return stream
    
    def close(self) -> None:
        """Close the trace and flush to file"""
        # Close all open streams
        for stream in self._streams:
            if stream.is_open():
                stream.close()
        
        if self._file:
            self._file.flush()  # Ensure data is written
            self._file.close()
            self._file = None
    
    def __enter__(self) -> 'PerfettoTrace':
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()
    
    # Internal helper methods
    
    def _allocate_track_uuid(self) -> int:
        """Allocate a unique track UUID"""
        uuid = self._next_track_uuid
        self._next_track_uuid += 1
        return uuid
    
    def _allocate_transaction_id(self) -> int:
        """Allocate a unique transaction ID"""
        txn_id = self._next_transaction_id
        self._next_transaction_id += 1
        return txn_id
    
    def _allocate_flow_id(self) -> int:
        """Allocate a unique flow ID for linking transactions"""
        flow_id = self._next_flow_id
        self._next_flow_id += 1
        return flow_id
    
    def _write_packet(self, packet: pb.TracePacket) -> None:
        """Write a TracePacket to the output file"""
        # Serialize the packet
        data = packet.SerializeToString()
        
        # Write length-delimited packet (varint length + data)
        self._write_varint(len(data))
        self._file.write(data)
        self._file.flush()  # Ensure data is written immediately
    
    def _write_varint(self, value: int) -> None:
        """Write a varint-encoded integer"""
        while value >= 0x80:
            self._file.write(bytes([(value & 0x7F) | 0x80]))
            value >>= 7
        self._file.write(bytes([value & 0x7F]))
    
    def _emit_clock_snapshot(self) -> None:
        """Emit initial clock snapshot packet"""
        packet = pb.TracePacket()
        packet.timestamp = 0
        
        # Add clock snapshot
        clock_snapshot = packet.clock_snapshot
        clock = clock_snapshot.clocks.add()
        clock.clock_id = self._clock_id
        clock.timestamp = 0
        
        self._write_packet(packet)
    
    def _emit_track_descriptor(self, stream: PerfettoStream) -> None:
        """Emit TrackDescriptor packet for a stream"""
        packet = pb.TracePacket()
        packet.timestamp = 0
        
        # Create track descriptor
        descriptor = packet.track_descriptor
        descriptor.uuid = stream._track_uuid
        descriptor.name = stream.name
        
        self._write_packet(packet)
    
    def _emit_child_track_descriptor(self, txn: PerfettoTransaction) -> None:
        """Emit TrackDescriptor packet for a child transaction"""
        packet = pb.TracePacket()
        packet.timestamp = 0
        
        # Create track descriptor
        descriptor = packet.track_descriptor
        descriptor.uuid = txn._track_uuid
        descriptor.name = txn.name
        
        # Set parent UUID to the parent transaction's track
        if txn._parent:
            descriptor.parent_uuid = txn._parent._track_uuid
        
        self._write_packet(packet)
    
    def _emit_slice_begin(self, txn: PerfettoTransaction) -> None:
        """Emit TYPE_SLICE_BEGIN track event for transaction start"""
        packet = pb.TracePacket()
        packet.timestamp = txn.start_time
        
        # Create track event
        event = packet.track_event
        event.type = pb.TrackEvent.TYPE_SLICE_BEGIN
        event.track_uuid = txn._track_uuid  # Use transaction's track
        event.name = txn.name
        
        # Add category if type_name is provided
        if txn.type_name:
            event.categories.append(txn.type_name)
        
        # Add debug annotations (attributes)
        for attr in txn._attributes:
            annotation = event.debug_annotations.add()
            annotation.CopyFrom(attr)
        
        # Add flow events for outgoing links
        for flow_id in txn._flow_ids:
            event.flow_ids.append(flow_id)
        
        self._write_packet(packet)
    
    def _emit_slice_end(self, txn: PerfettoTransaction) -> None:
        """Emit TYPE_SLICE_END track event for transaction end"""
        packet = pb.TracePacket()
        packet.timestamp = txn.end_time
        
        # Create track event
        event = packet.track_event
        event.type = pb.TrackEvent.TYPE_SLICE_END
        event.track_uuid = txn._track_uuid  # Use transaction's track
        
        # Flow IDs for incoming links
        for flow_id in txn._flow_ids:
            event.flow_ids.append(flow_id)
        
        self._write_packet(packet)
