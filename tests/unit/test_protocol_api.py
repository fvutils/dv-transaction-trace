"""Test the Protocol-based Python API

This test verifies that the clean Pythonic API works correctly
with the Perfetto implementation.
"""

import pytest
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from dv_transaction_trace import (
    create_trace,
    ITrace,
    IStream,
    ITransaction,
    Radix,
    LinkType,
)


def test_api_imports():
    """Test that all API elements can be imported"""
    assert ITrace is not None
    assert IStream is not None
    assert ITransaction is not None
    assert Radix is not None
    assert LinkType is not None
    assert create_trace is not None


def test_basic_trace_creation(tmp_path):
    """Test basic trace creation using Protocol API"""
    filename = str(tmp_path / "test_trace.perfetto")
    
    with create_trace(filename, "TestTrace", "1ns") as trace:
        # Verify trace properties
        assert trace.name == "TestTrace"
        assert trace.filename == filename
        assert trace.time_units == "1ns"
        
        # Create a stream
        stream = trace.create_stream("test_stream", "test.scope", "test_type")
        assert stream.name == "test_stream"
        assert stream.scope == "test.scope"
        assert stream.type_name == "test_type"
        assert stream.is_open()
        
        # Create a transaction
        txn = stream.begin_transaction("txn1", 1000, "txn_type")
        assert txn.name == "txn1"
        assert txn.type_name == "txn_type"
        assert txn.start_time == 1000
        assert txn.is_open()
        
        # Add attributes
        txn.add_uint("addr", 0x1234, Radix.HEX)
        txn.add_int("count", -42, Radix.DEC)
        txn.add_float("voltage", 3.3)
        txn.add_string("status", "OK")
        txn.add_time("timestamp", 5000)
        
        # Close transaction
        txn.close(2000)
        assert txn.end_time == 2000
        assert txn.is_closed()
        assert not txn.is_open()
    
    # Verify file was created
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 0


def test_multiple_streams(tmp_path):
    """Test creating multiple streams"""
    filename = str(tmp_path / "multi_stream.perfetto")
    
    with create_trace(filename, "MultiStream", "1ns") as trace:
        stream1 = trace.create_stream("stream1")
        stream2 = trace.create_stream("stream2")
        stream3 = trace.create_stream("stream3")
        
        # Add transactions to each stream
        txn1 = stream1.begin_transaction("txn1", 1000)
        txn1.close(1500)
        
        txn2 = stream2.begin_transaction("txn2", 2000)
        txn2.close(2500)
        
        txn3 = stream3.begin_transaction("txn3", 3000)
        txn3.close(3500)
    
    assert os.path.exists(filename)


def test_transaction_links(tmp_path):
    """Test linking transactions together"""
    filename = str(tmp_path / "linked.perfetto")
    
    with create_trace(filename, "LinkedTrace", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Create two transactions
        txn1 = stream.begin_transaction("source", 1000)
        txn2 = stream.begin_transaction("target", 2000)
        
        # Link them
        txn1.add_link(txn2, LinkType.CAUSE_EFFECT)
        
        txn1.close(1500)
        txn2.close(2500)
    
    assert os.path.exists(filename)


def test_nested_transactions(tmp_path):
    """Test overlapping/nested transactions"""
    filename = str(tmp_path / "nested.perfetto")
    
    with create_trace(filename, "NestedTrace", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Parent transaction
        parent = stream.begin_transaction("parent", 1000)
        
        # Child transactions overlapping with parent
        child1 = stream.begin_transaction("child1", 1100)
        child1.close(1300)
        
        child2 = stream.begin_transaction("child2", 1400)
        child2.close(1600)
        
        parent.close(2000)
    
    assert os.path.exists(filename)


def test_all_attribute_types(tmp_path):
    """Test all attribute types"""
    filename = str(tmp_path / "all_attrs.perfetto")
    
    with create_trace(filename, "AllAttrs", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        txn = stream.begin_transaction("full_txn", 1000)
        
        # All integer radixes
        txn.add_uint("hex_val", 0xFF, Radix.HEX)
        txn.add_uint("dec_val", 255, Radix.DEC)
        txn.add_uint("oct_val", 0o377, Radix.OCT)
        txn.add_uint("bin_val", 0b11111111, Radix.BIN)
        
        # Signed integers
        txn.add_int("signed", -42, Radix.DEC)
        
        # Floating point
        txn.add_float("float_val", 3.14159)
        
        # String
        txn.add_string("message", "Test message")
        
        # Time
        txn.add_time("timestamp", 5000)
        
        # Bit vector
        txn.add_bits("bitvec", bytes([0xCA, 0xFE]), 16, Radix.HEX)
        
        # Blob
        txn.add_blob("binary_data", b'\x00\x01\x02\x03')
        
        txn.close(2000)
    
    assert os.path.exists(filename)


def test_stream_close(tmp_path):
    """Test closing streams"""
    filename = str(tmp_path / "stream_close.perfetto")
    
    with create_trace(filename, "StreamClose", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Create open transaction
        txn = stream.begin_transaction("txn1", 1000)
        
        # Close stream (should close open transactions)
        stream.close()
        
        assert stream.is_closed()
        assert not stream.is_open()
    
    assert os.path.exists(filename)


def test_context_manager_cleanup(tmp_path):
    """Test that context manager properly closes trace"""
    filename = str(tmp_path / "context.perfetto")
    
    # Create and exit context
    with create_trace(filename, "Context", "1ns") as trace:
        stream = trace.create_stream("test")
        txn = stream.begin_transaction("txn", 1000)
        txn.close(2000)
    
    # File should exist and be closed
    assert os.path.exists(filename)
    
    # Should be able to open file (not locked)
    with open(filename, 'rb') as f:
        data = f.read()
        assert len(data) > 0


def test_large_trace(tmp_path):
    """Test creating a large trace with many transactions"""
    filename = str(tmp_path / "large.perfetto")
    
    with create_trace(filename, "LargeTrace", "1ns") as trace:
        # Create multiple streams
        for stream_idx in range(5):
            stream = trace.create_stream(f"stream_{stream_idx}")
            
            # Add many transactions
            for txn_idx in range(20):
                start = stream_idx * 10000 + txn_idx * 100
                txn = stream.begin_transaction(f"txn_{txn_idx}", start)
                txn.add_uint("id", txn_idx, Radix.DEC)
                txn.add_string("status", "OK")
                txn.close(start + 50)
    
    assert os.path.exists(filename)
    # Verify file has reasonable size
    assert os.path.getsize(filename) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
