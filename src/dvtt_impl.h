#ifndef DVTT_IMPL_H
#define DVTT_IMPL_H

#include "include/dvtt.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdio>

namespace dvtt {

enum ObjectState {
    STATE_OPEN,
    STATE_CLOSED,
    STATE_FREED
};

struct DebugAnnotation {
    std::string name;
    dvtt_attr_type_t type;
    dvtt_radix_t radix;
    union {
        int64_t i64;
        uint64_t u64;
        double d;
    } numeric_value;
    std::string string_value;
    std::vector<uint8_t> blob_value;
};

struct TransactionImpl {
    uint64_t id;
    std::string name;
    std::string type_name;
    dvtt_time_t start_time;
    dvtt_time_t end_time;
    ObjectState state;
    dvtt_stream_s* stream;
    int handle;
    
    dvtt_transaction_s* parent;  // Parent transaction (NULL if root)
    uint64_t track_uuid;         // Track UUID (may be shared with parent or unique)
    
    std::vector<DebugAnnotation> attributes;
    std::vector<uint64_t> flow_ids;
    bool attributes_batch_mode;
};

struct StreamImpl {
    uint64_t uuid;
    std::string name;
    std::string scope;
    std::string type_name;
    ObjectState state;
    dvtt_trace_s* trace;
    int handle;
    
    std::vector<TransactionImpl*> transactions;
};

struct TraceImpl {
    std::string filename;
    std::string name;
    std::string time_units;
    FILE* output_file;
    uint64_t sequence_id;
    uint32_t clock_id;
    
    std::vector<StreamImpl*> streams;
    std::map<int, StreamImpl*> stream_handles;
    std::map<int, TransactionImpl*> transaction_handles;
    
    int next_stream_handle;
    int next_transaction_handle;
    uint64_t next_track_uuid;
    uint64_t next_transaction_id;
    uint64_t next_flow_id;
};

// Protobuf writer functions
void write_varint(FILE* f, uint64_t value);
void write_tag(FILE* f, uint32_t field_number, uint32_t wire_type);
void write_length_delimited(FILE* f, uint32_t field_number, const void* data, size_t size);
void write_string_field(FILE* f, uint32_t field_number, const std::string& str);
void write_uint64_field(FILE* f, uint32_t field_number, uint64_t value);
void write_int64_field(FILE* f, uint32_t field_number, int64_t value);
void write_double_field(FILE* f, uint32_t field_number, double value);

// Helper functions
std::string format_radix_name(const std::string& name, dvtt_radix_t radix);
std::string bits_to_string(const void* bits, size_t num_bits, dvtt_radix_t radix);
void emit_clock_snapshot(TraceImpl* trace);
void emit_track_descriptor(TraceImpl* trace, StreamImpl* stream);
void emit_track_descriptor(TraceImpl* trace, TransactionImpl* txn);
void emit_track_event_begin(TraceImpl* trace, TransactionImpl* txn);
void emit_track_event_end(TraceImpl* trace, TransactionImpl* txn);

} // namespace dvtt

// C API structures
struct dvtt_trace_s {
    dvtt::TraceImpl* impl;
};

struct dvtt_stream_s {
    dvtt::StreamImpl* impl;
};

struct dvtt_transaction_s {
    dvtt::TransactionImpl* impl;
};

// Global state
extern thread_local dvtt_error_t g_last_error;

#endif // DVTT_IMPL_H
