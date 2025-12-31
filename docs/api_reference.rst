C API Reference
===============

This section documents the complete C API for DV Transaction Trace. Multiple implementations 
of this API may exist (SystemVerilog DPI, standalone C library, vendor-specific), but all 
implementations should conform to this interface specification.

Types and Enumerations
----------------------

Handle Types
~~~~~~~~~~~~

All handles are opaque pointers. Implementations may use different internal representations, 
but the API always uses these type-safe handles:

.. c:type:: dvtt_trace_t

   Opaque handle to a trace object.

.. c:type:: dvtt_stream_t

   Opaque handle to a stream object.

.. c:type:: dvtt_transaction_t

   Opaque handle to a transaction object.

Enumeration Types
~~~~~~~~~~~~~~~~~

.. c:enum:: dvtt_radix_t

   Display radix for numeric values.

   .. c:enumerator:: DVTT_RADIX_BIN

      Binary (base 2) representation.

   .. c:enumerator:: DVTT_RADIX_OCT

      Octal (base 8) representation.

   .. c:enumerator:: DVTT_RADIX_DEC

      Decimal (base 10) signed representation.

   .. c:enumerator:: DVTT_RADIX_HEX

      Hexadecimal (base 16) representation.

   .. c:enumerator:: DVTT_RADIX_UNSIGNED

      Unsigned decimal representation.

   .. c:enumerator:: DVTT_RADIX_STRING

      String representation (for enumerations).

   .. c:enumerator:: DVTT_RADIX_TIME

      Time value with units.

   .. c:enumerator:: DVTT_RADIX_REAL

      Real number representation.

.. c:enum:: dvtt_attr_type_t

   Attribute value types supported by the API.

   .. c:enumerator:: DVTT_ATTR_INT8

      8-bit signed integer.

   .. c:enumerator:: DVTT_ATTR_INT16

      16-bit signed integer.

   .. c:enumerator:: DVTT_ATTR_INT32

      32-bit signed integer.

   .. c:enumerator:: DVTT_ATTR_INT64

      64-bit signed integer.

   .. c:enumerator:: DVTT_ATTR_UINT8

      8-bit unsigned integer.

   .. c:enumerator:: DVTT_ATTR_UINT16

      16-bit unsigned integer.

   .. c:enumerator:: DVTT_ATTR_UINT32

      32-bit unsigned integer.

   .. c:enumerator:: DVTT_ATTR_UINT64

      64-bit unsigned integer.

   .. c:enumerator:: DVTT_ATTR_REAL

      Single-precision floating point.

   .. c:enumerator:: DVTT_ATTR_DOUBLE

      Double-precision floating point.

   .. c:enumerator:: DVTT_ATTR_STRING

      Null-terminated string.

   .. c:enumerator:: DVTT_ATTR_BITSTRING

      Arbitrary-width bit vector.

   .. c:enumerator:: DVTT_ATTR_BLOB

      Binary data blob.

.. c:enum:: dvtt_link_type_t

   Relationship types between transactions.

   .. c:enumerator:: DVTT_LINK_PARENT_CHILD

      Parent-child hierarchical relationship.

   .. c:enumerator:: DVTT_LINK_RELATED

      General association.

   .. c:enumerator:: DVTT_LINK_CAUSE_EFFECT

      Causal relationship (source causes target).

   .. c:enumerator:: DVTT_LINK_CUSTOM

      Custom relationship (use relation_name parameter).

.. c:enum:: dvtt_error_t

   Error codes returned by API functions.

   .. c:enumerator:: DVTT_OK

      Operation completed successfully.

   .. c:enumerator:: DVTT_ERROR_NULL_HANDLE

      A required handle parameter was NULL.

   .. c:enumerator:: DVTT_ERROR_NULL_POINTER

      A required pointer parameter was NULL.

   .. c:enumerator:: DVTT_ERROR_INVALID_NAME

      An invalid name string was provided.

   .. c:enumerator:: DVTT_ERROR_MEMORY

      Memory allocation failed.

   .. c:enumerator:: DVTT_ERROR_NOT_INITIALIZED

      API used before initialization.

   .. c:enumerator:: DVTT_ERROR_ALREADY_ENDED

      Operation on already-closed object.

   .. c:enumerator:: DVTT_ERROR_NOT_ENDED

      Operation requires closed object.

Structure Types
~~~~~~~~~~~~~~~

.. c:type:: dvtt_time_t

   Type for representing simulation time (64-bit unsigned integer).

.. c:struct:: dvtt_attr_value_t

   Container for attribute values with type information.

   .. c:member:: dvtt_attr_type_t type

      The type of value stored.

   **Union Member: value**

   Anonymous union containing the actual value. Access the appropriate member based on ``type``:

   - ``value.i8`` - int8_t
   - ``value.i16`` - int16_t
   - ``value.i32`` - int32_t
   - ``value.i64`` - int64_t
   - ``value.u8`` - uint8_t
   - ``value.u16`` - uint16_t
   - ``value.u32`` - uint32_t
   - ``value.u64`` - uint64_t
   - ``value.f`` - float
   - ``value.d`` - double
   - ``value.str`` - const char*
   - ``value.blob.data`` - const void* (binary data pointer)
   - ``value.blob.size_bytes`` - size_t (binary data size)

Initialization and Cleanup
---------------------------

.. c:function:: dvtt_error_t dvtt_init(void)

   Initialize the transaction recording system.

   This function must be called before creating any trace objects. It initializes 
   internal data structures and prepares the system for recording.

   :return: DVTT_OK on success, error code on failure
   :note: Some implementations may auto-initialize on first use

.. c:function:: void dvtt_shutdown(void)

   Shutdown the transaction recording system.

   Closes all open traces and frees all resources. After calling this function, 
   the API cannot be used until ``dvtt_init()`` is called again.

   :note: All trace, stream, and transaction handles become invalid

Trace Management
----------------

.. c:function:: dvtt_trace_t dvtt_create_trace(const char* name)

   Create a new trace object.

   The trace is the top-level container for all streams and transactions. Typically, 
   one trace is created per simulation run.

   :param name: Name for the trace (e.g., "simulation_trace")
   :return: Trace handle on success, NULL on failure
   :note: Trace must be closed with ``dvtt_close_trace()`` when simulation completes

.. c:function:: void dvtt_close_trace(dvtt_trace_t trace)

   Close and free a trace object.

   This closes all open streams within the trace and releases all associated resources. 
   All stream and transaction handles belonging to this trace become invalid.

   :param trace: Trace handle to close

.. c:function:: const char* dvtt_get_trace_name(dvtt_trace_t trace)

   Get the name of a trace.

   :param trace: Trace handle
   :return: Trace name string (valid for lifetime of trace) or NULL if trace is invalid

.. c:function:: void dvtt_set_time_unit(dvtt_trace_t trace, const char* units)

   Set the time scale and precision for a trace.

   This defines how time values should be interpreted and displayed. Common values 
   are "1ns", "1ps", "1us", "1ms".

   :param trace: Trace handle
   :param units: Time unit string (e.g., "1ns", "1ps")
   :note: Should be set early, before recording many transactions

Stream Management
-----------------

.. c:function:: dvtt_stream_t dvtt_open_stream(dvtt_trace_t trace, const char* name, const char* scope, const char* type_name)

   Create and open a transaction stream.

   Streams organize transactions into logical groups. Each stream appears as a horizontal 
   row in waveform viewers.

   :param trace: Parent trace handle
   :param name: Stream name (e.g., "axi_master", "pcie_monitor")
   :param scope: Optional hierarchical scope (e.g., "top.dut.axi", may be NULL)
   :param type_name: Optional type identifier (may be NULL)
   :return: Stream handle on success, NULL on failure
   :note: Stream is created in the open state

.. c:function:: void dvtt_close_stream(dvtt_stream_t stream)

   Close a transaction stream.

   A closed stream no longer accepts new transactions but remains valid for queries 
   and relationship operations. All open transactions in the stream are automatically closed.

   :param stream: Stream handle to close
   :note: Stream handle remains valid until ``dvtt_free_stream()`` is called

.. c:function:: void dvtt_free_stream(dvtt_stream_t stream)

   Free a transaction stream and all its resources.

   If the stream is still open, it is closed first. After freeing, the stream handle 
   becomes invalid.

   :param stream: Stream handle to free

.. c:function:: int dvtt_is_stream_open(dvtt_stream_t stream)

   Check if a stream is open.

   :param stream: Stream handle
   :return: 1 if stream is open and accepting transactions, 0 otherwise

.. c:function:: int dvtt_is_stream_closed(dvtt_stream_t stream)

   Check if a stream is closed but not freed.

   :param stream: Stream handle
   :return: 1 if stream is closed but still valid, 0 otherwise

.. c:function:: const char* dvtt_get_stream_name(dvtt_stream_t stream)

   Get the name of a stream.

   :param stream: Stream handle
   :return: Stream name string (valid for lifetime of stream) or NULL if invalid

.. c:function:: const char* dvtt_get_stream_scope(dvtt_stream_t stream)

   Get the hierarchical scope of a stream.

   :param stream: Stream handle
   :return: Stream scope string (valid for lifetime of stream) or NULL if not set

.. c:function:: const char* dvtt_get_stream_type_name(dvtt_stream_t stream)

   Get the type name of a stream.

   :param stream: Stream handle
   :return: Stream type name string (valid for lifetime of stream) or NULL if not set

.. c:function:: int dvtt_get_stream_handle(dvtt_stream_t stream)

   Get a unique integer handle for a stream.

   This can be used for storing stream references in integer fields or for 
   SystemVerilog DPI integration.

   :param stream: Stream handle
   :return: Unique non-zero integer handle, or 0 if stream is invalid

.. c:function:: dvtt_stream_t dvtt_get_stream_from_handle(int handle)

   Retrieve a stream from an integer handle.

   :param handle: Integer handle from ``dvtt_get_stream_handle()``
   :return: Stream handle or NULL if not found or freed

Transaction Lifecycle
---------------------

.. c:function:: dvtt_transaction_t dvtt_open_transaction(dvtt_stream_t stream, const char* name, dvtt_time_t start_time, const char* type_name)

   Open a new transaction on a stream.

   Creates a transaction with the specified start time. The transaction remains open 
   for adding attributes until ``dvtt_close_transaction()`` is called.

   :param stream: Stream to which transaction belongs
   :param name: Transaction name (e.g., "READ", "WRITE", "trans_1234")
   :param start_time: Transaction start time in trace time units
   :param type_name: Optional type identifier (may be NULL)
   :return: Transaction handle on success, NULL on failure
   :note: Transactions can only be opened on open streams

.. c:function:: void dvtt_close_transaction(dvtt_transaction_t transaction, dvtt_time_t end_time)

   Close a transaction.

   Sets the end time and marks the transaction as complete. The transaction remains 
   valid for adding relationships and querying until freed.

   :param transaction: Transaction handle
   :param end_time: Transaction end time in trace time units
   :note: Attributes can still be added to closed transactions in some implementations

.. c:function:: void dvtt_free_transaction(dvtt_transaction_t transaction, dvtt_time_t close_time)

   Free a transaction and its resources.

   If the transaction is not closed, it is closed first using ``close_time``. 
   After freeing, the transaction handle becomes invalid.

   :param transaction: Transaction handle
   :param close_time: Time to use if transaction not yet closed (ignored if already closed)
   :note: For zero-duration transactions, close_time can equal start_time

.. c:function:: int dvtt_is_transaction_open(dvtt_transaction_t transaction)

   Check if a transaction is open.

   :param transaction: Transaction handle
   :return: 1 if transaction is open, 0 otherwise

.. c:function:: int dvtt_is_transaction_closed(dvtt_transaction_t transaction)

   Check if a transaction is closed but not freed.

   :param transaction: Transaction handle
   :return: 1 if transaction is closed but still valid, 0 otherwise

.. c:function:: const char* dvtt_get_transaction_name(dvtt_transaction_t transaction)

   Get the name of a transaction.

   :param transaction: Transaction handle
   :return: Transaction name string (valid until freed) or NULL if invalid

.. c:function:: const char* dvtt_get_transaction_type_name(dvtt_transaction_t transaction)

   Get the type name of a transaction.

   :param transaction: Transaction handle
   :return: Transaction type name string (valid until freed) or NULL if not set

.. c:function:: dvtt_time_t dvtt_get_transaction_start_time(dvtt_transaction_t transaction)

   Get the start time of a transaction.

   :param transaction: Transaction handle
   :return: Start time in trace time units, or 0 if invalid

.. c:function:: dvtt_time_t dvtt_get_transaction_end_time(dvtt_transaction_t transaction)

   Get the end time of a transaction.

   :param transaction: Transaction handle
   :return: End time in trace time units, or 0 if not yet closed or invalid

.. c:function:: dvtt_stream_t dvtt_get_transaction_stream(dvtt_transaction_t transaction)

   Get the stream that owns a transaction.

   :param transaction: Transaction handle
   :return: Stream handle or NULL if invalid

.. c:function:: int dvtt_get_transaction_handle(dvtt_transaction_t transaction)

   Get a unique integer handle for a transaction.

   :param transaction: Transaction handle
   :return: Unique non-zero integer handle, or 0 if invalid

.. c:function:: dvtt_transaction_t dvtt_get_transaction_from_handle(int handle)

   Retrieve a transaction from an integer handle.

   :param handle: Integer handle from ``dvtt_get_transaction_handle()``
   :return: Transaction handle or NULL if not found or freed

Transaction Attributes
----------------------

Integer Attributes
~~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_int8(dvtt_transaction_t transaction, const char* name, int8_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_int16(dvtt_transaction_t transaction, const char* name, int16_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_int32(dvtt_transaction_t transaction, const char* name, int32_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_int64(dvtt_transaction_t transaction, const char* name, int64_t value, dvtt_radix_t radix)

   Add a signed integer attribute to a transaction.

   :param transaction: Transaction handle
   :param name: Attribute name (e.g., "addr", "data", "latency")
   :param value: Integer value
   :param radix: Display format for the value
   :note: The radix affects how viewers display the value, not the stored value

.. c:function:: void dvtt_add_attr_uint8(dvtt_transaction_t transaction, const char* name, uint8_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_uint16(dvtt_transaction_t transaction, const char* name, uint16_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_uint32(dvtt_transaction_t transaction, const char* name, uint32_t value, dvtt_radix_t radix)
.. c:function:: void dvtt_add_attr_uint64(dvtt_transaction_t transaction, const char* name, uint64_t value, dvtt_radix_t radix)

   Add an unsigned integer attribute to a transaction.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param value: Unsigned integer value
   :param radix: Display format for the value

Floating-Point Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_float(dvtt_transaction_t transaction, const char* name, float value)

   Add a single-precision floating-point attribute.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param value: Float value

.. c:function:: void dvtt_add_attr_double(dvtt_transaction_t transaction, const char* name, double value)

   Add a double-precision floating-point attribute.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param value: Double value

String Attributes
~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_string(dvtt_transaction_t transaction, const char* name, const char* value)

   Add a string attribute to a transaction.

   The string is copied; the caller retains ownership of the original string.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param value: Null-terminated string value
   :note: Useful for enumeration names, status messages, and text descriptions

Time Attributes
~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_time(dvtt_transaction_t transaction, const char* name, dvtt_time_t value)

   Add a time-valued attribute.

   :param transaction: Transaction handle
   :param name: Attribute name (e.g., "latency", "duration")
   :param value: Time value in trace time units

Bit Vector Attributes
~~~~~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_bits(dvtt_transaction_t transaction, const char* name, const void* bits, size_t num_bits, dvtt_radix_t radix)

   Add an arbitrary-width bit vector attribute.

   The bit vector data is copied; the caller retains ownership of the original data.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param bits: Pointer to bit data (packed bytes, LSB first)
   :param num_bits: Number of bits in the vector
   :param radix: Display format
   :note: Use for wide addresses, data buses, or bit fields

Binary Data Attributes
~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attr_blob(dvtt_transaction_t transaction, const char* name, const void* data, size_t size)

   Add a binary blob attribute.

   The data is copied; the caller retains ownership of the original data.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param data: Pointer to binary data
   :param size: Size in bytes
   :note: Use for unstructured binary payloads

Generic Attributes
~~~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_attribute(dvtt_transaction_t transaction, const char* name, const dvtt_attr_value_t* value)

   Add an attribute with explicit type information.

   This is a generic function that can add any attribute type. Type-specific functions 
   are typically more convenient.

   :param transaction: Transaction handle
   :param name: Attribute name
   :param value: Pointer to attribute value structure with type and data

Color Attributes
~~~~~~~~~~~~~~~~

.. c:function:: void dvtt_add_color(dvtt_transaction_t transaction, const char* color)

   Add a color attribute for visualization.

   Color helps with visual debugging in waveform viewers. Use distinctive colors for 
   important events or error conditions.

   :param transaction: Transaction handle
   :param color: Color name ("red", "blue", "green", etc.) or RGB hex string ("#FF0000")
   :note: Supported color names depend on the viewer implementation

Links and Relations
-------------------

.. c:function:: void dvtt_add_link(dvtt_transaction_t source, dvtt_transaction_t target, dvtt_link_type_t link_type, const char* relation_name)

   Add a relationship link between two transactions.

   Links express dependencies, hierarchies, or associations between transactions. 
   Note that maintaining relationships can be expensive; consider simpler alternatives 
   like ID attributes.

   :param source: Source transaction handle
   :param target: Target transaction handle
   :param link_type: Type of relationship
   :param relation_name: Custom name (required for DVTT_LINK_CUSTOM, optional otherwise)
   :note: Both transactions should be closed (not freed) when adding links

.. c:function:: void dvtt_add_stream_link(dvtt_stream_t stream, dvtt_transaction_t transaction, dvtt_link_type_t link_type, const char* relation_name)

   Add a relationship link between a stream and a transaction.

   This can express that a transaction belongs to or is associated with a particular 
   stream in a special way.

   :param stream: Stream handle
   :param transaction: Transaction handle
   :param link_type: Type of relationship
   :param relation_name: Custom name (required for DVTT_LINK_CUSTOM, optional otherwise)

Bulk Operations
---------------

.. c:function:: void dvtt_begin_attributes(dvtt_transaction_t transaction)

   Begin a batch of attribute additions.

   This can improve performance when adding many attributes to a transaction by 
   allowing the implementation to optimize internal operations.

   :param transaction: Transaction handle
   :note: Must be paired with ``dvtt_end_attributes()``

.. c:function:: void dvtt_end_attributes(dvtt_transaction_t transaction)

   Complete a batch of attribute additions.

   :param transaction: Transaction handle
   :note: Must be preceded by ``dvtt_begin_attributes()``

Example usage:

.. code-block:: c

   dvtt_begin_attributes(txn);
   dvtt_add_attr_uint32(txn, "addr", 0x1000, DVTT_RADIX_HEX);
   dvtt_add_attr_uint32(txn, "data", 0xDEADBEEF, DVTT_RADIX_HEX);
   dvtt_add_attr_string(txn, "cmd", "READ");
   dvtt_end_attributes(txn);

Error Handling
--------------

.. c:function:: dvtt_error_t dvtt_get_last_error(void)

   Get the error code from the most recent operation.

   Not all functions return error codes directly. This function retrieves the last 
   error that occurred in the current thread.

   :return: Error code from last operation
   :note: Thread-local in thread-safe implementations

.. c:function:: const char* dvtt_error_string(dvtt_error_t error)

   Get a human-readable error message.

   :param error: Error code
   :return: Error description string
   :note: The returned string is constant and does not need to be freed

Helper Macros
-------------

.. c:macro:: dvtt_add_attr_int(txn, name, val)

   Generic integer attribute macro that selects the appropriate sized function based 
   on the value type. Uses hexadecimal radix by default.

   Expands to the correct ``dvtt_add_attr_intX`` or ``dvtt_add_attr_uintX`` function 
   based on the C type of ``val``.

.. c:macro:: dvtt_begin_transaction(stream, name, time)

   Convenience macro equivalent to ``dvtt_open_transaction(stream, name, time, NULL)``.

.. c:macro:: dvtt_end_transaction(txn, time)

   Convenience macro equivalent to ``dvtt_close_transaction(txn, time)``.

Implementation Notes
--------------------

Multiple implementations of this API may exist:

**SystemVerilog DPI Implementation**
   Uses SystemVerilog DPI-C to provide transaction recording from SystemVerilog 
   testbenches. Handles are typically integers mapped to internal objects.

**Standalone C Library**
   Pure C implementation that can be linked with any simulator or application. 
   Outputs to standard trace formats (FST, VCD, custom formats).

**Vendor-Specific Implementation**
   Simulator vendors may provide optimized implementations that integrate directly 
   with their waveform databases and debugging tools.

**Python/Other Language Bindings**
   Wrappers around the C API for use in Python testbenches or analysis scripts.

All implementations must maintain:

- Thread safety for handles created in the same thread
- Proper resource cleanup on trace closure
- Consistent behavior for state transitions (open → closed → freed)

Implementation-specific features (like output format selection) are typically 
provided through additional APIs or environment variables outside this core specification.
