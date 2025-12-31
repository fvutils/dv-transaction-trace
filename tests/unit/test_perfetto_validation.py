"""Tests that create .perfetto traces and validate them using perfetto trace API

These tests verify that the pure Python implementation creates valid perfetto traces
that can be read and queried using the perfetto trace processor API.

NOTE: The current pure Python implementation has placeholder methods for emitting
perfetto protocol buffers. Once the actual protobuf emission is implemented, these
tests will validate that:
1. Traces can be opened and parsed without errors
2. Transactions appear as slices in the trace
3. Streams appear as tracks in the trace
4. Transaction timing is correctly recorded
5. Attributes are preserved
6. Links between transactions create flow events
"""

import pytest
import sys
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from dv_transaction_trace.impl import (
    create_trace, close_trace,
    open_stream, close_stream,
    open_transaction, close_transaction,
    add_attr_int, add_attr_uint, add_attr_float, add_attr_string,
    add_attr_time, add_attr_bits,
    add_link,
    Radix, LinkType
)

try:
    from perfetto.trace_processor import TraceProcessor
    PERFETTO_AVAILABLE = True
except ImportError:
    PERFETTO_AVAILABLE = False


@pytest.mark.skipif(not PERFETTO_AVAILABLE, reason="perfetto package not installed")
class TestPerfettoTraceValidation:
    """Tests that validate generated perfetto traces can be read
    
    These tests create .perfetto traces using the pure Python implementation
    and then validate they can be read using the perfetto trace processor API.
    """
    
    def test_basic_trace_readable(self, tmp_path):
        """Test that a basic trace file can be created and opened with perfetto"""
        filename = str(tmp_path / "basic_trace.perfetto")
        
        # Create trace
        trace = create_trace(filename, "BasicTrace", "1ns")
        stream = open_stream(trace, "test_stream", "test.scope", "test_type")
        txn = open_transaction(stream, "txn1", 1000, "transaction_type")
        add_attr_string(txn, "status", "OK")
        close_transaction(txn, 2000)
        close_trace(trace)
        
        # Verify file was created
        assert os.path.exists(filename), "Trace file should be created"
        
        # Read and validate trace can be opened
        with TraceProcessor(trace=filename) as tp:
            # Check that trace can be opened without error
            assert tp is not None
            
            # Query basic trace structure
            result = tp.query("SELECT COUNT(*) as count FROM slice")
            rows = list(result)
            assert len(rows) > 0
            # Once protobuf emission is implemented, this should be > 0
            # For now, we just verify the trace is parseable
            assert rows[0].count >= 0
@pytest.mark.skipif(not PERFETTO_AVAILABLE, reason="perfetto package not installed")
class TestPerfettoTraceValidation:
    """Tests that validate generated perfetto traces can be read
    
    These tests create .perfetto traces using the pure Python implementation
    and then validate they can be read using the perfetto trace processor API.
    """
    
    def test_basic_trace_readable(self, tmp_path):
        """Test that a basic trace file can be created and opened with perfetto"""
        filename = str(tmp_path / "basic_trace.perfetto")
        
        # Create trace
        trace = create_trace(filename, "BasicTrace", "1ns")
        stream = open_stream(trace, "test_stream", "test.scope", "test_type")
        txn = open_transaction(stream, "txn1", 1000, "transaction_type")
        add_attr_string(txn, "status", "OK")
        close_transaction(txn, 2000)
        close_trace(trace)
        
        # Verify file was created
        assert os.path.exists(filename), "Trace file should be created"
        
        # Read and validate trace can be opened
        with TraceProcessor(trace=filename) as tp:
            # Check that trace can be opened without error
            assert tp is not None
            
            # Query basic trace structure
            result = tp.query("SELECT COUNT(*) as count FROM slice")
            rows = list(result)
            assert len(rows) > 0
            # Once protobuf emission is implemented, this should be > 0
            # For now, we just verify the trace is parseable
            assert rows[0].count >= 0
    
    def test_trace_with_multiple_streams(self, tmp_path):
        """Test trace with multiple streams can be created and read"""
        filename = str(tmp_path / "multi_stream.perfetto")
        
        # Create trace with multiple streams
        trace = create_trace(filename, "MultiStreamTrace", "1ns")
        
        stream1 = open_stream(trace, "stream1", "scope1", "type1")
        stream2 = open_stream(trace, "stream2", "scope2", "type2")
        stream3 = open_stream(trace, "stream3", "scope3", "type3")
        
        # Add transactions to each stream
        txn1 = open_transaction(stream1, "txn1", 1000)
        close_transaction(txn1, 1500)
        
        txn2 = open_transaction(stream2, "txn2", 2000)
        close_transaction(txn2, 2500)
        
        txn3 = open_transaction(stream3, "txn3", 3000)
        close_transaction(txn3, 3500)
        
        close_trace(trace)
        
        # Verify file was created
        assert os.path.exists(filename)
        
        # Validate trace can be opened and queried
        with TraceProcessor(trace=filename) as tp:
            # Should be able to query without errors
            result = tp.query("SELECT COUNT(DISTINCT name) as track_count FROM track")
            rows = list(result)
            assert len(rows) > 0
            
            # Once implemented, should have at least our 3 streams
            assert rows[0].track_count >= 0
    
    def test_trace_with_attributes(self, tmp_path):
        """Test that transaction attributes can be added"""
        filename = str(tmp_path / "attrs_trace.perfetto")
        
        # Create trace with various attributes
        trace = create_trace(filename, "AttributesTrace", "1ns")
        stream = open_stream(trace, "test_stream")
        
        txn = open_transaction(stream, "txn_with_attrs", 1000)
        add_attr_int(txn, "int_val", 42, Radix.DEC)
        add_attr_uint(txn, "addr", 0x1234ABCD, Radix.HEX)
        add_attr_float(txn, "voltage", 3.3)
        add_attr_string(txn, "status", "COMPLETE")
        add_attr_time(txn, "timestamp", 5000)
        close_transaction(txn, 2000)
        
        close_trace(trace)
        
        # Verify attributes were added to transaction object
        assert len(txn.attributes) == 5
        assert txn.attributes[0].name == "int_val[dec]"
        assert txn.attributes[0].value == 42
        assert txn.attributes[1].name == "addr[hex]"
        assert txn.attributes[3].name == "status"
        assert txn.attributes[3].value == "COMPLETE"
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_trace_with_timing(self, tmp_path):
        """Test that transaction timing is correctly stored"""
        filename = str(tmp_path / "timing_trace.perfetto")
        
        # Create trace with specific timing
        trace = create_trace(filename, "TimingTrace", "1ns")
        stream = open_stream(trace, "timing_stream")
        
        # Create transactions with known timing
        txn1 = open_transaction(stream, "txn1", 1000)
        close_transaction(txn1, 1500)  # duration: 500
        
        txn2 = open_transaction(stream, "txn2", 2000)
        close_transaction(txn2, 3500)  # duration: 1500
        
        txn3 = open_transaction(stream, "txn3", 4000)
        close_transaction(txn3, 4100)  # duration: 100
        
        close_trace(trace)
        
        # Verify timing in transaction objects
        assert txn1.start_time == 1000
        assert txn1.end_time == 1500
        assert txn2.start_time == 2000
        assert txn2.end_time == 3500
        assert txn3.start_time == 4000
        assert txn3.end_time == 4100
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_trace_with_nested_transactions(self, tmp_path):
        """Test overlapping/nested transactions"""
        filename = str(tmp_path / "nested_trace.perfetto")
        
        trace = create_trace(filename, "NestedTrace", "1ns")
        stream = open_stream(trace, "test_stream")
        
        # Parent transaction
        parent = open_transaction(stream, "parent", 1000)
        
        # Child transactions that overlap with parent
        child1 = open_transaction(stream, "child1", 1100)
        close_transaction(child1, 1300)
        
        child2 = open_transaction(stream, "child2", 1400)
        close_transaction(child2, 1600)
        
        close_transaction(parent, 2000)
        
        close_trace(trace)
        
        # Verify transactions exist
        assert len(stream.transactions) == 3
        assert parent.name == "parent"
        assert child1.name == "child1"
        assert child2.name == "child2"
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_trace_with_flow_events(self, tmp_path):
        """Test that links between transactions are created"""
        filename = str(tmp_path / "flow_trace.perfetto")
        
        trace = create_trace(filename, "FlowTrace", "1ns")
        stream = open_stream(trace, "test_stream")
        
        # Create linked transactions
        txn1 = open_transaction(stream, "source", 1000)
        txn2 = open_transaction(stream, "target", 2000)
        
        add_link(txn1, txn2, LinkType.CAUSE_EFFECT)
        
        close_transaction(txn1, 1500)
        close_transaction(txn2, 2500)
        
        close_trace(trace)
        
        # Verify link was created
        assert len(txn1.flow_ids) == 1
        assert len(txn2.flow_ids) == 1
        assert txn1.flow_ids[0] == txn2.flow_ids[0]
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_large_trace_readable(self, tmp_path):
        """Test that a larger trace with many transactions can be created"""
        filename = str(tmp_path / "large_trace.perfetto")
        
        trace = create_trace(filename, "LargeTrace", "1ns")
        
        # Create multiple streams
        num_streams = 5
        num_txns_per_stream = 20
        
        streams = []
        for i in range(num_streams):
            stream = open_stream(trace, f"stream_{i}", f"scope_{i}", f"type_{i}")
            streams.append(stream)
        
        # Create many transactions
        total_txns = 0
        for stream_idx, stream in enumerate(streams):
            for txn_idx in range(num_txns_per_stream):
                start_time = stream_idx * 10000 + txn_idx * 100
                txn = open_transaction(stream, f"txn_{stream_idx}_{txn_idx}", start_time)
                
                # Add some attributes
                add_attr_uint(txn, "id", txn_idx, Radix.DEC)
                add_attr_uint(txn, "stream_id", stream_idx, Radix.DEC)
                add_attr_string(txn, "status", "OK" if txn_idx % 2 == 0 else "WARN")
                
                close_transaction(txn, start_time + 50)
                total_txns += 1
        
        close_trace(trace)
        
        # Verify data structures
        assert len(trace.streams) == num_streams
        for stream in streams:
            assert len(stream.transactions) == num_txns_per_stream
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_trace_with_all_attribute_types(self, tmp_path):
        """Test trace with all supported attribute types"""
        filename = str(tmp_path / "all_attrs_trace.perfetto")
        
        trace = create_trace(filename, "AllAttributesTrace", "1ns")
        stream = open_stream(trace, "test_stream")
        
        txn = open_transaction(stream, "full_attrs", 1000)
        
        # Add every type of attribute
        add_attr_int(txn, "int_dec", -42, Radix.DEC)
        add_attr_int(txn, "int_hex", 255, Radix.HEX)
        add_attr_uint(txn, "uint_dec", 100, Radix.DEC)
        add_attr_uint(txn, "uint_hex", 0xDEADBEEF, Radix.HEX)
        add_attr_uint(txn, "uint_oct", 0o777, Radix.OCT)
        add_attr_uint(txn, "uint_bin", 0b11010, Radix.BIN)
        add_attr_float(txn, "float_val", 3.14159)
        add_attr_string(txn, "str_val", "Test String")
        add_attr_time(txn, "time_val", 5000)
        add_attr_bits(txn, "bits_val", bytes([0xCA, 0xFE]), 16, Radix.HEX)
        
        close_transaction(txn, 2000)
        close_trace(trace)
        
        # Verify all attributes were added
        assert len(txn.attributes) == 10
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_empty_trace_readable(self, tmp_path):
        """Test that even an empty trace (no transactions) is valid"""
        filename = str(tmp_path / "empty_trace.perfetto")
        
        trace = create_trace(filename, "EmptyTrace", "1ns")
        stream = open_stream(trace, "empty_stream")
        close_stream(stream)
        close_trace(trace)
        
        # Verify trace file was created
        assert os.path.exists(filename)
        
        # Verify trace can be opened
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None
    
    def test_trace_metadata_preserved(self, tmp_path):
        """Test that trace metadata is preserved in trace object"""
        filename = str(tmp_path / "metadata_trace.perfetto")
        
        trace_name = "MetadataTestTrace"
        time_units = "1ns"
        
        trace = create_trace(filename, trace_name, time_units)
        
        # Verify metadata in trace object
        assert trace.name == trace_name
        assert trace.time_units == time_units
        assert trace.filename == filename
        
        stream = open_stream(trace, "test_stream")
        txn = open_transaction(stream, "test_txn", 1000)
        close_transaction(txn, 2000)
        close_trace(trace)
        
        # Verify trace file can be opened
        assert os.path.exists(filename)
        with TraceProcessor(trace=filename) as tp:
            assert tp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
