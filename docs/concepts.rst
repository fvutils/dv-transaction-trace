Core Concepts
=============

Overview
--------

DV Transaction Trace (DVTT) is a library for recording and visualizing transactions in design verification. 
It provides a simple, flexible API for capturing the essential information about system activity during 
simulation, making debug and analysis significantly more effective.

Transaction recording transforms low-level signal activity into high-level transaction views, enabling 
engineers to quickly understand system behavior, identify bugs, and analyze performance.

Key Abstractions
----------------

The library is built around three fundamental concepts:

Trace
~~~~~

A **Trace** is the top-level container for all recorded data in a simulation. It represents a complete 
recording session and contains all streams and their transactions. Each simulation typically has one trace 
object that persists for the duration of the run.

A trace is created with three essential pieces of information:

- **Filename**: The output file path where trace data will be written
- **Name**: A descriptive name for identification and display
- **Time Units**: The time scale for all timestamps (e.g., "1ns", "1ps", "1us")

**Key Operations:**

- **Create**: Initialize a new trace with filename, name, and time units
- **Close**: Finalize and flush the trace at simulation end
- **Query**: Retrieve trace properties (name, filename, time units)

Stream
~~~~~~

A **Stream** is a logical collection of related transactions. Streams provide organization and visual structure 
for transaction data. In a waveform viewer, each stream typically appears as a horizontal row where transactions 
are displayed chronologically.

Streams can represent different aspects of the system:

- **Per-Bus Streams**: One stream per communication bus (AXI, PCIe, etc.)
- **Per-Component Streams**: Separate streams for monitors, drivers, or other verification components
- **Per-Type Streams**: Distinct streams for different transaction types (READ, WRITE)
- **Hierarchical Streams**: Streams organized by design hierarchy

**Key Operations:**

- **Open**: Create and activate a stream within a trace
- **Close**: Complete a stream when no more transactions will be recorded
- **Free**: Release resources when stream is no longer needed
- **Query**: Retrieve stream properties (name, scope, handle)

A stream has three states:

1. **Open**: Actively accepting new transactions
2. **Closed**: No longer accepting transactions but available for queries
3. **Freed**: Resources released, handle invalid

Transaction
~~~~~~~~~~~

A **Transaction** represents a discrete activity or communication event in the system. Transactions are the 
fundamental units of recorded information.

**Core Properties:**

- **Name**: Identifies the transaction type (e.g., "READ", "WRITE", "BLOCK_TRANSFER")
- **Start Time**: When the transaction began
- **End Time**: When the transaction completed
- **Stream**: The stream to which the transaction belongs

**Key Operations:**

- **Open**: Begin a new transaction at a specific time
- **Add Attributes**: Attach properties describing the transaction
- **Close**: Mark transaction complete at end time
- **Free**: Release transaction resources

Like streams, transactions have three states:

1. **Open**: Accepting attribute additions
2. **Closed**: Complete but available for relationships and queries
3. **Freed**: Resources released, handle invalid

**Transaction Timing:**

Transactions are inherently temporal. Start and end times can be:

- **Same Time**: Zero-duration transactions for instantaneous events
- **Past Times**: When recording after the fact
- **Current Time**: For real-time recording
- **Future Times**: When scheduling future events (less common)

The visual representation typically shows transactions as horizontal bars on their stream, 
with triangular markers indicating start and end times.

Attributes
----------

Attributes are name-value pairs that describe transaction properties. They capture the meaningful 
data associated with a transaction.

**Common Attributes:**

- **Primary Data**: Address, data payload, command type
- **Status Information**: Response codes, error flags
- **Derived Metrics**: Bandwidth, latency, utilization
- **Debug Information**: IDs, tags, sequence numbers

**Attribute Types:**

The API supports rich data types:

- **Integers**: Signed and unsigned (8, 16, 32, 64-bit)
- **Floating-Point**: Single and double precision
- **Strings**: Text descriptions and enumerated values
- **Bit Vectors**: Arbitrary-width bit fields
- **Binary Data**: Unstructured byte arrays
- **Time Values**: Timestamps with appropriate units

**Display Radix:**

Numeric attributes can specify their display format:

- Binary, Octal, Decimal, Hexadecimal
- Unsigned, Signed
- String representation for enumerations
- Time format with units

**Adding Attributes:**

Attributes should be added while a transaction is open or closed (but not freed). 
The typical pattern:

1. Open transaction
2. Add all relevant attributes
3. Close transaction (optionally free immediately)

For performance, the API supports bulk attribute additions using begin/end brackets.

Relationships and Links
-----------------------

Transactions often have relationships with other transactions. While relationships can be valuable, 
they come with complexity and cost.

**Relationship Types:**

- **Parent-Child**: A parent transaction spawns child transactions (e.g., BLOCK_READ → multiple WORD_READs)
- **Cause-Effect**: One transaction triggers another
- **Related**: General association between transactions
- **Custom**: User-defined relationships

**Implementation Considerations:**

Maintaining a relationship database during simulation can be:

- Memory intensive with millions of transactions
- Complex to implement correctly
- Difficult to manage across testbench and RTL boundaries

**Alternative Approaches:**

Experience suggests that simpler alternatives to explicit relationships are often more effective:

- **ID Fields**: Related transactions share common IDs or tags
- **Address Matching**: Transactions on same address are implicitly related
- **Stream Organization**: Place related transactions on the same stream
- **Search and Filter**: Use viewer tools to find related transactions

These approaches are more natural, require no database, work across abstraction boundaries, 
and often provide better visualization.

Recording Patterns
------------------

Complete Example
~~~~~~~~~~~~~~~~

Here's a complete example showing trace creation and transaction recording:

.. code-block:: c

   // Create trace with filename, name, and time units
   dvtt_trace_t trace = dvtt_create_trace(
       "simulation.perfetto",    // Output filename
       "AXI_Simulation",          // Trace name
       "1ns"                      // Time units
   );
   
   // Create a stream for AXI transactions
   dvtt_stream_t axi_stream = dvtt_open_stream(
       trace,
       "axi_master",              // Stream name
       "top.dut.axi",             // Hierarchical scope
       "AXI4"                     // Protocol type
   );
   
   // Record a transaction
   dvtt_transaction_t txn = dvtt_open_transaction(
       axi_stream,
       "READ",                    // Transaction name
       1000,                      // Start time (in nanoseconds)
       "AXI_READ"                 // Transaction type
   );
   
   // Add attributes
   dvtt_add_attr_uint32(txn, "addr", 0x1000, DVTT_RADIX_HEX);
   dvtt_add_attr_uint32(txn, "size", 64, DVTT_RADIX_DEC);
   dvtt_add_attr_string(txn, "id", "master_0");
   
   // Close transaction at end time
   dvtt_close_transaction(txn, 1500);  // End at 1500ns
   dvtt_free_transaction(txn, 0);
   
   // Close stream and trace when done
   dvtt_close_stream(axi_stream);
   dvtt_close_trace(trace);

Monitor-Based Recording
~~~~~~~~~~~~~~~~~~~~~~~

Monitors observe signals and create transactions when protocol events occur:

.. code-block:: c

   // Pseudo-code pattern
   while (simulation_running) {
       wait_for_transaction_start();
       txn = dvtt_open_transaction(stream, "READ", current_time, NULL);
       dvtt_add_attr_uint32(txn, "addr", observed_address, DVTT_RADIX_HEX);
       
       wait_for_transaction_end();
       dvtt_add_attr_uint32(txn, "data", observed_data, DVTT_RADIX_HEX);
       dvtt_close_transaction(txn, current_time);
       dvtt_free_transaction(txn, 0);
   }

This pattern works for:

- RTL monitors using SystemVerilog bind
- Testbench monitors in UVM or other frameworks
- Interface-level protocol checkers

Sequence-Based Recording
~~~~~~~~~~~~~~~~~~~~~~~~

In UVM testbenches, sequences naturally create transactions:

1. Sequence starts → open transaction
2. Items execute → add attributes
3. Sequence completes → close transaction

This captures the intended stimulus, complementing observed monitor transactions.

Driver-Based Recording
~~~~~~~~~~~~~~~~~~~~~~

Drivers can record what they're sending:

1. Driver receives item → open transaction
2. Drive signals → record attributes
3. Handshake completes → close transaction

Real-Time vs. Post-Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Real-Time Recording**: Create transactions as events occur during simulation.

- Immediate feedback
- Memory-efficient (can free old transactions)
- Natural integration with testbench

**Post-Processing**: Collect event data, analyze after simulation.

- Can identify relationships after complete dataset available
- Allows complex analysis not possible during simulation
- Requires storing raw event data

Time Management
---------------

Time in transaction recording uses simulation time units. The time unit is specified when 
creating the trace and defines the resolution for all timestamps throughout the trace.

**Time Unit Examples:**

- "1ns" → nanoseconds
- "1ps" → picoseconds  
- "1us" → microseconds
- "1fs" → femtoseconds

All transaction start and end times are expressed as 64-bit unsigned integers in the 
configured time units. The time unit cannot be changed after trace creation.

Best Practices
--------------

**Stream Organization:**

- Create streams that match your mental model of the system
- Use hierarchical names for clarity (e.g., "top.axi_master.cmd_stream")
- Balance granularity: too many streams clutter the view, too few lose organization

**Attribute Selection:**

- Include primary transaction data (addresses, data, commands)
- Add derived metrics valuable for analysis (bandwidth, latency)
- Use meaningful names that match protocol specifications
- Consider adding IDs for correlation across abstraction levels

**Resource Management:**

- Free transactions after they're no longer needed for relationships
- Close streams when recording is complete
- Use begin/end attribute brackets for bulk additions

**Relationship Recording:**

- Consider simpler alternatives (IDs, addresses) before implementing relationship databases
- Only maintain relationships if tools specifically require them
- Free transactions promptly to manage memory

Performance Considerations
--------------------------

Transaction recording is designed to be lightweight, but large simulations require attention 
to performance:

**Memory Management:**

- Free transactions as soon as possible
- Close streams that are no longer active
- Use streaming output formats when available

**Attribute Efficiency:**

- Add attributes during transaction lifetime, not after closing
- Use appropriate data types (don't store 8-bit values as 64-bit)
- Batch attribute additions with begin/end brackets

**Minimizing Overhead:**

- Record transactions at appropriate abstraction levels (not every clock cycle)
- Sample high-frequency activity rather than recording everything
- Consider conditional recording for debug-only scenarios

Summary
-------

DV Transaction Trace provides a simple, powerful abstraction for design verification debug:

- **Traces** contain all recorded data for a simulation
- **Streams** organize transactions into logical groups
- **Transactions** represent discrete activities with start/end times
- **Attributes** describe transaction properties with rich data types
- **Relationships** can link transactions, but simpler alternatives often suffice

The API is designed for ease of use, flexibility, and performance, enabling effective 
debug "anywhere, anytime" in the verification process.
