Usage Examples
==============

This section provides practical examples of using the DV Transaction Trace API in 
various verification scenarios.

Basic Transaction Recording
---------------------------

Simple Monitor Example
~~~~~~~~~~~~~~~~~~~~~~

This example shows basic transaction recording from a simple monitor watching 
a memory interface:

.. code-block:: c

   #include "dvtt.h"
   
   // Initialize at simulation start
   void init_recording() {
       dvtt_init();
       trace = dvtt_create_trace("memory_sim");
       dvtt_set_time_unit(trace, "1ns");
       
       // Create stream for memory transactions
       mem_stream = dvtt_open_stream(trace, "memory_bus", "top.dut.mem", NULL);
   }
   
   // Monitor function called when transaction detected
   void record_memory_transaction(uint64_t start_ns, uint64_t end_ns,
                                   int is_write, uint32_t addr, uint32_t data) {
       dvtt_transaction_t txn;
       const char* name = is_write ? "WRITE" : "READ";
       
       // Open transaction
       txn = dvtt_open_transaction(mem_stream, name, start_ns, NULL);
       
       // Add attributes
       dvtt_add_attr_uint32(txn, "addr", addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(txn, "data", data, DVTT_RADIX_HEX);
       dvtt_add_attr_string(txn, "type", name);
       
       // Add color for easy visualization
       dvtt_add_color(txn, is_write ? "blue" : "green");
       
       // Close and free transaction
       dvtt_close_transaction(txn, end_ns);
       dvtt_free_transaction(txn, 0);
   }
   
   // Cleanup at simulation end
   void close_recording() {
       dvtt_close_stream(mem_stream);
       dvtt_close_trace(trace);
       dvtt_shutdown();
   }

Zero-Duration Transactions
~~~~~~~~~~~~~~~~~~~~~~~~~~

For instantaneous events like interrupts or strobes:

.. code-block:: c

   void record_interrupt(uint64_t time, int irq_num) {
       dvtt_transaction_t txn;
       
       txn = dvtt_open_transaction(irq_stream, "IRQ", time, NULL);
       dvtt_add_attr_int32(txn, "irq_number", irq_num, DVTT_RADIX_DEC);
       dvtt_add_color(txn, "red");
       
       // Same time for start and end = zero duration
       dvtt_close_transaction(txn, time);
       dvtt_free_transaction(txn, 0);
   }

Advanced Patterns
-----------------

Bulk Attribute Recording
~~~~~~~~~~~~~~~~~~~~~~~~

When adding many attributes, use bulk operations for efficiency:

.. code-block:: c

   void record_axi_transaction(axi_txn_t* axi) {
       dvtt_transaction_t txn;
       
       txn = dvtt_open_transaction(axi_stream, "AXI", axi->start_time, "AXI4");
       
       // Begin bulk attribute addition
       dvtt_begin_attributes(txn);
       
       dvtt_add_attr_uint64(txn, "addr", axi->addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(txn, "id", axi->id, DVTT_RADIX_HEX);
       dvtt_add_attr_uint8(txn, "len", axi->len, DVTT_RADIX_DEC);
       dvtt_add_attr_uint8(txn, "size", axi->size, DVTT_RADIX_DEC);
       dvtt_add_attr_uint8(txn, "burst", axi->burst, DVTT_RADIX_DEC);
       dvtt_add_attr_string(txn, "type", axi_type_name(axi->type));
       
       // Add data payload (could be wide)
       dvtt_add_attr_bits(txn, "data", axi->data, axi->data_width, DVTT_RADIX_HEX);
       
       // Add derived metrics
       uint64_t latency = axi->end_time - axi->start_time;
       dvtt_add_attr_time(txn, "latency", latency);
       
       // End bulk addition
       dvtt_end_attributes(txn);
       
       dvtt_close_transaction(txn, axi->end_time);
       dvtt_free_transaction(txn, 0);
   }

Multiple Streams Organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organize transactions across multiple streams for clarity:

.. code-block:: c

   // Create separate streams for different aspects
   void setup_pcie_recording() {
       pcie_trace = dvtt_create_trace("pcie_verification");
       dvtt_set_time_unit(pcie_trace, "1ns");
       
       // Separate streams by transaction layer
       tlp_req_stream = dvtt_open_stream(pcie_trace, "TLP_Requests", 
                                          "pcie.tlp", "PCIe_TLP");
       tlp_cpl_stream = dvtt_open_stream(pcie_trace, "TLP_Completions", 
                                          "pcie.tlp", "PCIe_TLP");
       
       // Separate streams by direction
       tx_stream = dvtt_open_stream(pcie_trace, "TX_Path", 
                                     "pcie.link.tx", "PCIe_Link");
       rx_stream = dvtt_open_stream(pcie_trace, "RX_Path", 
                                     "pcie.link.rx", "PCIe_Link");
       
       // Stream for link-level events
       link_events_stream = dvtt_open_stream(pcie_trace, "Link_Events", 
                                              "pcie.link", NULL);
   }
   
   void record_tlp_request(tlp_request_t* tlp) {
       dvtt_transaction_t txn = dvtt_open_transaction(
           tlp_req_stream, 
           tlp_type_string(tlp->type),
           tlp->start_time,
           "TLP"
       );
       
       // Record TLP fields...
       dvtt_add_attr_uint32(txn, "requester_id", tlp->req_id, DVTT_RADIX_HEX);
       dvtt_add_attr_uint64(txn, "address", tlp->address, DVTT_RADIX_HEX);
       
       dvtt_close_transaction(txn, tlp->end_time);
       dvtt_free_transaction(txn, 0);
   }
   
   void record_tlp_completion(tlp_completion_t* cpl) {
       dvtt_transaction_t txn = dvtt_open_transaction(
           tlp_cpl_stream,
           "COMPLETION",
           cpl->start_time,
           "TLP"
       );
       
       // Record completion fields...
       dvtt_add_attr_uint32(txn, "completer_id", cpl->cpl_id, DVTT_RADIX_HEX);
       dvtt_add_attr_uint16(txn, "byte_count", cpl->byte_count, DVTT_RADIX_DEC);
       
       dvtt_close_transaction(txn, cpl->end_time);
       dvtt_free_transaction(txn, 0);
   }

Error Highlighting with Color
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use color to make errors and important events stand out:

.. code-block:: c

   void record_bus_transaction(bus_txn_t* txn_data) {
       dvtt_transaction_t txn;
       const char* color = "gray";  // Default
       
       txn = dvtt_open_transaction(bus_stream, txn_data->name, 
                                    txn_data->start_time, NULL);
       
       // Add transaction data
       dvtt_add_attr_uint32(txn, "addr", txn_data->addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(txn, "data", txn_data->data, DVTT_RADIX_HEX);
       
       // Color code based on status
       if (txn_data->error) {
           color = "red";
           dvtt_add_attr_string(txn, "error", txn_data->error_msg);
       } else if (txn_data->retry) {
           color = "orange";
           dvtt_add_attr_int32(txn, "retry_count", txn_data->retry_count, 
                              DVTT_RADIX_DEC);
       } else if (txn_data->priority_high) {
           color = "yellow";
       } else {
           color = "green";  // Normal successful transaction
       }
       
       dvtt_add_color(txn, color);
       
       dvtt_close_transaction(txn, txn_data->end_time);
       dvtt_free_transaction(txn, 0);
   }

Derived Metrics
~~~~~~~~~~~~~~~

Add computed attributes for analysis:

.. code-block:: c

   void record_network_packet(packet_t* pkt) {
       dvtt_transaction_t txn;
       double bandwidth_gbps;
       uint64_t duration_ns;
       
       txn = dvtt_open_transaction(net_stream, "PACKET", pkt->start_time, NULL);
       
       // Primary attributes
       dvtt_add_attr_uint64(txn, "src_addr", pkt->src_addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint64(txn, "dst_addr", pkt->dst_addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(txn, "size_bytes", pkt->size, DVTT_RADIX_DEC);
       
       // Derived metrics
       duration_ns = pkt->end_time - pkt->start_time;
       if (duration_ns > 0) {
           bandwidth_gbps = (pkt->size * 8.0) / duration_ns;  // Gbps
           dvtt_add_attr_double(txn, "bandwidth_gbps", bandwidth_gbps);
       }
       
       dvtt_add_attr_time(txn, "duration", duration_ns);
       dvtt_add_attr_double(txn, "efficiency_percent", pkt->efficiency * 100.0);
       
       dvtt_close_transaction(txn, pkt->end_time);
       dvtt_free_transaction(txn, 0);
   }

SystemVerilog Integration
--------------------------

Using DPI-C from SystemVerilog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SystemVerilog can call the C API through DPI-C:

.. code-block:: systemverilog

   // Import C functions
   import "DPI-C" function int dvtt_create_trace(string name);
   import "DPI-C" function int dvtt_open_stream(int trace, string name, 
                                                  string scope, string type_name);
   import "DPI-C" function int dvtt_open_transaction(int stream, string name,
                                                       longint start_time, 
                                                       string type_name);
   import "DPI-C" function void dvtt_add_attr_uint32(int txn, string name, 
                                                       int value, int radix);
   import "DPI-C" function void dvtt_add_attr_string(int txn, string name, 
                                                       string value);
   import "DPI-C" function void dvtt_add_color(int txn, string color);
   import "DPI-C" function void dvtt_close_transaction(int txn, longint end_time);
   import "DPI-C" function void dvtt_free_transaction(int txn, longint close_time);
   
   // Monitor module
   module axi_monitor(
       input logic clk,
       input logic arvalid,
       input logic arready,
       input logic [31:0] araddr,
       input logic [7:0] arid
   );
   
       int trace_h;
       int stream_h;
       
       initial begin
           trace_h = dvtt_create_trace("axi_sim");
           stream_h = dvtt_open_stream(trace_h, "AXI_AR", "top.axi", "AXI4");
       end
       
       // Record address read transactions
       always @(posedge clk) begin
           int txn;
           if (arvalid && arready) begin
               txn = dvtt_open_transaction(stream_h, "AR", $time, "AXI_AR");
               dvtt_add_attr_uint32(txn, "addr", araddr, 16); // 16 = hex radix
               dvtt_add_attr_uint32(txn, "id", arid, 16);
               dvtt_add_color(txn, "cyan");
               
               // Zero-duration transaction
               dvtt_close_transaction(txn, $time);
               dvtt_free_transaction(txn, 0);
           end
       end
   endmodule

Bind-Based Monitoring
~~~~~~~~~~~~~~~~~~~~~

Use SystemVerilog bind for non-intrusive monitoring:

.. code-block:: systemverilog

   // Transaction monitor module
   module mem_txn_monitor(
       input logic clk,
       input logic req,
       input logic ack,
       input logic wr,
       input logic [31:0] addr,
       input logic [31:0] wdata,
       input logic [31:0] rdata
   );
   
       int stream_h;
       int current_txn;
       bit txn_active = 0;
       
       import "DPI-C" function int dvtt_open_stream(int trace, string name,
                                                      string scope, string type_name);
       import "DPI-C" function int dvtt_open_transaction(int stream, string name,
                                                           longint start_time,
                                                           string type_name);
       import "DPI-C" function void dvtt_add_attr_uint32(int txn, string name,
                                                           int value, int radix);
       import "DPI-C" function void dvtt_add_attr_string(int txn, string name,
                                                           string value);
       import "DPI-C" function void dvtt_close_transaction(int txn, longint end_time);
       import "DPI-C" function void dvtt_free_transaction(int txn, longint close_time);
       
       initial begin
           // Get trace from parent, or create
           stream_h = dvtt_open_stream(0, "memory", $sformatf("%m"), "memory_bus");
       end
       
       always @(posedge clk) begin
           if (req && !txn_active) begin
               // Transaction starts
               current_txn = dvtt_open_transaction(stream_h, 
                                                    wr ? "WRITE" : "READ",
                                                    $time, "");
               dvtt_add_attr_uint32(current_txn, "addr", addr, 16);
               if (wr)
                   dvtt_add_attr_uint32(current_txn, "wdata", wdata, 16);
               txn_active = 1;
           end
           
           if (ack && txn_active) begin
               // Transaction completes
               if (!wr)
                   dvtt_add_attr_uint32(current_txn, "rdata", rdata, 16);
               dvtt_close_transaction(current_txn, $time);
               dvtt_free_transaction(current_txn, 0);
               txn_active = 0;
           end
       end
   endmodule
   
   // Bind to DUT in testbench top
   module top;
       // ... DUT instantiation ...
       
       bind memory_controller mem_txn_monitor mon(
           .clk(clk),
           .req(mem_req),
           .ack(mem_ack),
           .wr(mem_wr),
           .addr(mem_addr),
           .wdata(mem_wdata),
           .rdata(mem_rdata)
       );
   endmodule

State Machine Tracking
----------------------

Recording State Transitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track state machine behavior with transactions:

.. code-block:: c

   typedef enum {
       STATE_IDLE,
       STATE_ARMED,
       STATE_ACTIVE,
       STATE_COOLDOWN,
       STATE_ERROR
   } fsm_state_t;
   
   void record_state_transition(uint64_t time, fsm_state_t from, 
                                 fsm_state_t to, const char* trigger) {
       dvtt_transaction_t txn;
       char name[64];
       const char* color;
       
       snprintf(name, sizeof(name), "%s->%s", 
                state_name(from), state_name(to));
       
       txn = dvtt_open_transaction(fsm_stream, name, time, "FSM_Transition");
       
       dvtt_add_attr_string(txn, "from_state", state_name(from));
       dvtt_add_attr_string(txn, "to_state", state_name(to));
       dvtt_add_attr_string(txn, "trigger", trigger);
       
       // Color code by destination state
       switch (to) {
           case STATE_ERROR:  color = "red"; break;
           case STATE_IDLE:   color = "gray"; break;
           case STATE_ACTIVE: color = "green"; break;
           default:           color = "blue"; break;
       }
       dvtt_add_color(txn, color);
       
       // Transitions are instantaneous
       dvtt_close_transaction(txn, time);
       dvtt_free_transaction(txn, 0);
   }
   
   void record_state_duration(uint64_t enter_time, uint64_t exit_time,
                               fsm_state_t state) {
       dvtt_transaction_t txn;
       uint64_t duration;
       
       txn = dvtt_open_transaction(fsm_state_stream, state_name(state),
                                    enter_time, "FSM_State");
       
       duration = exit_time - enter_time;
       dvtt_add_attr_time(txn, "duration", duration);
       dvtt_add_attr_string(txn, "state", state_name(state));
       
       dvtt_close_transaction(txn, exit_time);
       dvtt_free_transaction(txn, 0);
   }

Transaction Relationships (Optional)
-------------------------------------

Parent-Child Relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~

If tracking hierarchical transactions:

.. code-block:: c

   void record_block_transfer(block_transfer_t* blk) {
       dvtt_transaction_t parent_txn;
       
       // Parent transaction for the entire block transfer
       parent_txn = dvtt_open_transaction(block_stream, "BLOCK_XFER",
                                          blk->start_time, "BlockTransfer");
       dvtt_add_attr_uint64(parent_txn, "base_addr", blk->addr, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(parent_txn, "block_size", blk->size, DVTT_RADIX_DEC);
       
       // Record individual word transfers as children
       for (int i = 0; i < blk->num_words; i++) {
           dvtt_transaction_t word_txn;
           
           word_txn = dvtt_open_transaction(word_stream, "WORD_XFER",
                                            blk->words[i].start_time, "WordTransfer");
           dvtt_add_attr_uint64(word_txn, "addr", 
                               blk->addr + i * 4, DVTT_RADIX_HEX);
           dvtt_add_attr_uint32(word_txn, "data", 
                               blk->words[i].data, DVTT_RADIX_HEX);
           
           dvtt_close_transaction(word_txn, blk->words[i].end_time);
           
           // Link child to parent
           dvtt_add_link(parent_txn, word_txn, DVTT_LINK_PARENT_CHILD, NULL);
           
           dvtt_free_transaction(word_txn, 0);
       }
       
       dvtt_close_transaction(parent_txn, blk->end_time);
       dvtt_free_transaction(parent_txn, 0);
   }

Alternative: ID-Based Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simpler approach using IDs instead of explicit links:

.. code-block:: c

   void record_block_transfer_simple(block_transfer_t* blk) {
       uint32_t block_id = get_unique_id();
       
       // Parent record
       dvtt_transaction_t parent = dvtt_open_transaction(
           block_stream, "BLOCK", blk->start_time, NULL);
       dvtt_add_attr_uint32(parent, "block_id", block_id, DVTT_RADIX_HEX);
       dvtt_add_attr_uint32(parent, "num_words", blk->num_words, DVTT_RADIX_DEC);
       dvtt_close_transaction(parent, blk->end_time);
       dvtt_free_transaction(parent, 0);
       
       // Child records - linked by shared block_id
       for (int i = 0; i < blk->num_words; i++) {
           dvtt_transaction_t word = dvtt_open_transaction(
               word_stream, "WORD", blk->words[i].start_time, NULL);
           dvtt_add_attr_uint32(word, "block_id", block_id, DVTT_RADIX_HEX);
           dvtt_add_attr_uint32(word, "word_index", i, DVTT_RADIX_DEC);
           dvtt_add_attr_uint32(word, "data", blk->words[i].data, DVTT_RADIX_HEX);
           dvtt_close_transaction(word, blk->words[i].end_time);
           dvtt_free_transaction(word, 0);
       }
   }

This ID-based approach is simpler, uses less memory, and allows correlation across 
abstraction boundaries without maintaining a relationship database.
