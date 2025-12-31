"""Unit tests for Python implementation of DVTT"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from dv_transaction_trace.impl import (
    create_trace, close_trace,
    open_stream, close_stream,
    open_transaction, close_transaction,
    add_attr_int, add_attr_uint, add_attr_float, add_attr_string,
    add_attr_time, add_attr_bits, add_attr_blob,
    add_link,
    get_stream_name, get_stream_handle, is_stream_open, is_stream_closed,
    get_transaction_name, get_transaction_start_time, get_transaction_end_time,
    is_transaction_open, is_transaction_closed,
    Radix, LinkType
)


class TestBasic:
    """Basic functionality tests"""
    
    def test_create_trace(self, tmp_path):
        """Test creating a trace"""
        filename = str(tmp_path / "test_trace.perfetto")
        trace = create_trace(filename, "test_trace", "1ns")
        
        assert trace is not None
        assert trace.name == "test_trace"
        assert trace.filename == filename
        assert trace.time_units == "1ns"
        
        close_trace(trace)
        assert os.path.exists(filename)
    
    def test_open_stream(self, tmp_path):
        """Test opening a stream"""
        filename = str(tmp_path / "test_stream.perfetto")
        trace = create_trace(filename, "test", "1ns")
        
        stream = open_stream(trace, "stream1", "scope1", "type1")
        
        assert stream is not None
        assert get_stream_name(stream) == "stream1"
        assert stream.scope == "scope1"
        assert stream.type_name == "type1"
        assert is_stream_open(stream)
        assert not is_stream_closed(stream)
        
        close_trace(trace)
    
    def test_close_stream(self, tmp_path):
        """Test closing a stream"""
        filename = str(tmp_path / "test_close_stream.perfetto")
        trace = create_trace(filename, "test", "1ns")
        
        stream = open_stream(trace, "stream1")
        assert is_stream_open(stream)
        
        close_stream(stream)
        assert not is_stream_open(stream)
        assert is_stream_closed(stream)
        
        close_trace(trace)
    
    def test_open_transaction(self, tmp_path):
        """Test opening a transaction"""
        filename = str(tmp_path / "test_transaction.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        
        txn = open_transaction(stream, "txn1", 1000, "type1")
        
        assert txn is not None
        assert get_transaction_name(txn) == "txn1"
        assert txn.type_name == "type1"
        assert get_transaction_start_time(txn) == 1000
        assert is_transaction_open(txn)
        assert not is_transaction_closed(txn)
        
        close_trace(trace)
    
    def test_close_transaction(self, tmp_path):
        """Test closing a transaction"""
        filename = str(tmp_path / "test_close_txn.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        
        txn = open_transaction(stream, "txn1", 1000)
        assert is_transaction_open(txn)
        
        close_transaction(txn, 2000)
        assert not is_transaction_open(txn)
        assert is_transaction_closed(txn)
        assert get_transaction_end_time(txn) == 2000
        
        close_trace(trace)


class TestAttributes:
    """Attribute addition tests"""
    
    def test_add_int_attributes(self, tmp_path):
        """Test adding integer attributes"""
        filename = str(tmp_path / "test_int_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_int(txn, "value1", 42, Radix.DEC)
        add_attr_int(txn, "value2", -100, Radix.DEC)
        
        assert len(txn.attributes) == 2
        assert txn.attributes[0].name == "value1[dec]"
        assert txn.attributes[0].value == 42
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_uint_attributes(self, tmp_path):
        """Test adding unsigned integer attributes"""
        filename = str(tmp_path / "test_uint_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_uint(txn, "addr", 0x1234ABCD, Radix.HEX)
        
        assert len(txn.attributes) == 1
        assert txn.attributes[0].name == "addr[hex]"
        assert txn.attributes[0].value == 0x1234ABCD
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_float_attributes(self, tmp_path):
        """Test adding float attributes"""
        filename = str(tmp_path / "test_float_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_float(txn, "voltage", 3.3)
        
        assert len(txn.attributes) == 1
        assert txn.attributes[0].name == "voltage"
        assert abs(txn.attributes[0].value - 3.3) < 0.01
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_string_attributes(self, tmp_path):
        """Test adding string attributes"""
        filename = str(tmp_path / "test_string_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_string(txn, "status", "OK")
        add_attr_string(txn, "message", "Test message")
        
        assert len(txn.attributes) == 2
        assert txn.attributes[0].value == "OK"
        assert txn.attributes[1].value == "Test message"
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_time_attributes(self, tmp_path):
        """Test adding time attributes"""
        filename = str(tmp_path / "test_time_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_time(txn, "timestamp", 5000)
        
        assert len(txn.attributes) == 1
        assert txn.attributes[0].name == "timestamp[time]"
        assert txn.attributes[0].value == 5000
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_bitvector_attributes(self, tmp_path):
        """Test adding bit vector attributes"""
        filename = str(tmp_path / "test_bitvector_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        bits = bytes([0xAB, 0xCD, 0xEF])
        add_attr_bits(txn, "data", bits, 24, Radix.HEX)
        
        assert len(txn.attributes) == 1
        assert txn.attributes[0].name == "data[hex]"
        assert "0x" in txn.attributes[0].value
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_add_blob_attributes(self, tmp_path):
        """Test adding blob attributes"""
        filename = str(tmp_path / "test_blob_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        data = bytes([0x01, 0x02, 0x03, 0x04, 0x05])
        add_attr_blob(txn, "payload", data)
        
        assert len(txn.attributes) == 1
        assert txn.attributes[0].name == "payload"
        assert txn.attributes[0].value == data
        
        close_transaction(txn, 2000)
        close_trace(trace)
    
    def test_multiple_attributes(self, tmp_path):
        """Test adding multiple attributes"""
        filename = str(tmp_path / "test_multiple_attrs.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        txn = open_transaction(stream, "txn1", 1000)
        
        add_attr_uint(txn, "addr", 0x1234, Radix.HEX)
        add_attr_int(txn, "count", 42, Radix.DEC)
        add_attr_float(txn, "voltage", 3.3)
        add_attr_string(txn, "status", "OK")
        add_attr_time(txn, "timestamp", 1000)
        
        assert len(txn.attributes) == 5
        
        close_transaction(txn, 2000)
        close_trace(trace)


class TestMultiple:
    """Tests with multiple streams and transactions"""
    
    def test_multiple_streams(self, tmp_path):
        """Test creating multiple streams"""
        filename = str(tmp_path / "test_multiple_streams.perfetto")
        trace = create_trace(filename, "test", "1ns")
        
        stream1 = open_stream(trace, "stream1")
        stream2 = open_stream(trace, "stream2")
        stream3 = open_stream(trace, "stream3")
        
        assert stream1 is not None
        assert stream2 is not None
        assert stream3 is not None
        
        assert get_stream_name(stream1) == "stream1"
        assert get_stream_name(stream2) == "stream2"
        assert get_stream_name(stream3) == "stream3"
        
        close_trace(trace)
    
    def test_multiple_transactions(self, tmp_path):
        """Test creating multiple transactions"""
        filename = str(tmp_path / "test_multiple_txns.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        
        txn1 = open_transaction(stream, "txn1", 1000)
        txn2 = open_transaction(stream, "txn2", 1500)
        txn3 = open_transaction(stream, "txn3", 2000)
        
        assert txn1 is not None
        assert txn2 is not None
        assert txn3 is not None
        
        close_transaction(txn1, 2000)
        close_transaction(txn2, 2500)
        close_transaction(txn3, 3000)
        
        close_trace(trace)
    
    def test_transactions_on_multiple_streams(self, tmp_path):
        """Test creating transactions on multiple streams"""
        filename = str(tmp_path / "test_txns_multiple_streams.perfetto")
        trace = create_trace(filename, "test", "1ns")
        
        stream1 = open_stream(trace, "stream1")
        stream2 = open_stream(trace, "stream2")
        
        txn1 = open_transaction(stream1, "txn1", 1000)
        txn2 = open_transaction(stream2, "txn2", 1500)
        txn3 = open_transaction(stream1, "txn3", 2000)
        
        assert txn1.stream == stream1
        assert txn2.stream == stream2
        assert txn3.stream == stream1
        
        close_transaction(txn1, 2000)
        close_transaction(txn2, 2500)
        close_transaction(txn3, 3000)
        
        close_trace(trace)


class TestLinks:
    """Link and relationship tests"""
    
    def test_add_link(self, tmp_path):
        """Test adding links between transactions"""
        filename = str(tmp_path / "test_links.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        
        txn1 = open_transaction(stream, "txn1", 1000)
        txn2 = open_transaction(stream, "txn2", 2000)
        
        add_link(txn1, txn2, LinkType.CAUSE_EFFECT)
        
        assert len(txn1.flow_ids) == 1
        assert len(txn2.flow_ids) == 1
        assert txn1.flow_ids[0] == txn2.flow_ids[0]
        
        close_transaction(txn1, 2000)
        close_transaction(txn2, 3000)
        close_trace(trace)


class TestHandles:
    """Handle management tests"""
    
    def test_stream_handles(self, tmp_path):
        """Test stream handle management"""
        filename = str(tmp_path / "test_stream_handles.perfetto")
        trace = create_trace(filename, "test", "1ns")
        
        stream1 = open_stream(trace, "stream1")
        stream2 = open_stream(trace, "stream2")
        
        handle1 = get_stream_handle(stream1)
        handle2 = get_stream_handle(stream2)
        
        assert handle1 > 0
        assert handle2 > 0
        assert handle1 != handle2
        
        close_trace(trace)
    
    def test_transaction_handles(self, tmp_path):
        """Test transaction handle management"""
        filename = str(tmp_path / "test_txn_handles.perfetto")
        trace = create_trace(filename, "test", "1ns")
        stream = open_stream(trace, "stream1")
        
        txn1 = open_transaction(stream, "txn1", 1000)
        txn2 = open_transaction(stream, "txn2", 1500)
        
        assert txn1.handle > 0
        assert txn2.handle > 0
        assert txn1.handle != txn2.handle
        
        close_trace(trace)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
