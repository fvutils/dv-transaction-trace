"""Test parent-child transaction relationships with explicit parent parameter"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from dv_transaction_trace import create_trace, Radix


def test_parent_child_basic(tmp_path):
    """Test basic parent-child transaction creation"""
    filename = str(tmp_path / "parent_child.perfetto")
    
    with create_trace(filename, "ParentChildTest", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Create parent transaction
        parent = stream.begin_transaction("parent", 1000)
        parent.add_uint("parent_id", 1, Radix.DEC)
        
        # Create child transactions with explicit parent parameter
        child1 = stream.begin_transaction("child1", 1100, parent=parent)
        child1.add_uint("child_id", 1, Radix.DEC)
        child1.close(1300)
        
        child2 = stream.begin_transaction("child2", 1400, parent=parent)
        child2.add_uint("child_id", 2, Radix.DEC)
        child2.close(1600)
        
        parent.close(2000)
        
        # Verify structure
        assert len(stream.transactions) == 3
        assert parent.name == "parent"
        assert child1.name == "child1"
        assert child2.name == "child2"
    
    assert os.path.exists(filename)


def test_nested_hierarchy(tmp_path):
    """Test multi-level parent-child hierarchy"""
    filename = str(tmp_path / "nested_hierarchy.perfetto")
    
    with create_trace(filename, "NestedHierarchy", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Level 1: Root transaction
        root = stream.begin_transaction("root", 1000)
        
        # Level 2: Children of root
        child1 = stream.begin_transaction("child1", 1100, parent=root)
        
        # Level 3: Grandchildren (children of child1)
        grandchild1 = stream.begin_transaction("grandchild1", 1200, parent=child1)
        grandchild1.close(1300)
        
        grandchild2 = stream.begin_transaction("grandchild2", 1350, parent=child1)
        grandchild2.close(1450)
        
        child1.close(1500)
        
        # Level 2: Another child of root
        child2 = stream.begin_transaction("child2", 1600, parent=root)
        child2.close(1800)
        
        root.close(2000)
        
        # Verify all transactions created
        assert len(stream.transactions) == 5
    
    assert os.path.exists(filename)


def test_parent_child_with_independent_transactions(tmp_path):
    """Test mix of parent-child and independent transactions on same stream"""
    filename = str(tmp_path / "mixed.perfetto")
    
    with create_trace(filename, "MixedTransactions", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Independent transaction 1
        txn1 = stream.begin_transaction("independent1", 1000)
        txn1.close(1200)
        
        # Parent-child group
        parent = stream.begin_transaction("parent", 1500)
        child = stream.begin_transaction("child", 1600, parent=parent)
        child.close(1800)
        parent.close(2000)
        
        # Independent transaction 2
        txn2 = stream.begin_transaction("independent2", 2500)
        txn2.close(2700)
        
        # Verify all transactions (parent + child count as 2)
        assert len(stream.transactions) == 4  # txn1, parent, child, txn2
    
    assert os.path.exists(filename)


def test_multiple_children_same_parent(tmp_path):
    """Test multiple children can share the same parent"""
    filename = str(tmp_path / "multiple_children.perfetto")
    
    with create_trace(filename, "MultipleChildren", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        parent = stream.begin_transaction("parent", 1000)
        
        # Create many children
        children = []
        for i in range(5):
            start_time = 1100 + i * 100
            end_time = start_time + 50
            child = stream.begin_transaction(f"child{i}", start_time, parent=parent)
            child.add_uint("child_id", i, Radix.DEC)
            child.close(end_time)
            children.append(child)
        
        parent.close(2000)
        
        assert len(stream.transactions) == 6
        assert len(children) == 5
    
    assert os.path.exists(filename)


def test_parent_child_with_attributes(tmp_path):
    """Test parent and child transactions both have attributes"""
    filename = str(tmp_path / "attrs.perfetto")
    
    with create_trace(filename, "WithAttributes", "1ns") as trace:
        stream = trace.create_stream("axi_stream")
        
        # Parent transaction with attributes
        write_txn = stream.begin_transaction("AXI_WRITE", 1000, "axi_write")
        write_txn.add_uint("addr", 0x1000, Radix.HEX)
        write_txn.add_uint("size", 64, Radix.DEC)
        write_txn.add_string("burst_type", "INCR")
        
        # Child: Address phase
        addr_phase = stream.begin_transaction("AWVALID", 1000, "addr_phase", parent=write_txn)
        addr_phase.add_uint("awaddr", 0x1000, Radix.HEX)
        addr_phase.add_uint("awlen", 4, Radix.DEC)
        addr_phase.close(1050)
        
        # Child: Data phase
        data_phase = stream.begin_transaction("WDATA", 1050, "data_phase", parent=write_txn)
        data_phase.add_bits("wdata", bytes([0xDE, 0xAD, 0xBE, 0xEF]), 32, Radix.HEX)
        data_phase.close(1400)
        
        # Child: Response phase
        resp_phase = stream.begin_transaction("BRESP", 1400, "resp_phase", parent=write_txn)
        resp_phase.add_uint("bresp", 0, Radix.DEC)
        resp_phase.close(1450)
        
        write_txn.close(1500)
        
        assert len(stream.transactions) == 4
        assert len(write_txn.attributes) == 3
        assert len(addr_phase.attributes) == 2
    
    assert os.path.exists(filename)


def test_parent_child_different_streams(tmp_path):
    """Test that parent-child only works within the same stream"""
    filename = str(tmp_path / "different_streams.perfetto")
    
    with create_trace(filename, "DifferentStreams", "1ns") as trace:
        stream1 = trace.create_stream("stream1")
        stream2 = trace.create_stream("stream2")
        
        # Parent on stream1
        parent = stream1.begin_transaction("parent", 1000)
        
        # Child on stream1 - should work
        child1 = stream1.begin_transaction("child1", 1100, parent=parent)
        child1.close(1200)
        
        # Transaction on stream2 - independent
        txn2 = stream2.begin_transaction("txn2", 1500)
        txn2.close(1700)
        
        parent.close(2000)
        
        assert len(stream1.transactions) == 2
        assert len(stream2.transactions) == 1
    
    assert os.path.exists(filename)


def test_parent_none_explicit(tmp_path):
    """Test that explicitly passing parent=None creates root transaction"""
    filename = str(tmp_path / "explicit_none.perfetto")
    
    with create_trace(filename, "ExplicitNone", "1ns") as trace:
        stream = trace.create_stream("test_stream")
        
        # Explicitly specify parent=None
        txn1 = stream.begin_transaction("txn1", 1000, parent=None)
        txn1.close(1200)
        
        # Default (no parent specified)
        txn2 = stream.begin_transaction("txn2", 1500)
        txn2.close(1700)
        
        # Both should be root transactions
        assert len(stream.transactions) == 2
    
    assert os.path.exists(filename)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
