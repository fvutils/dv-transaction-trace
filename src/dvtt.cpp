#include "dvtt_impl.h"
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <sstream>
#include <iomanip>

namespace dvtt {

// Protobuf wire types
enum WireType {
    VARINT = 0,
    FIXED64 = 1,
    LENGTH_DELIMITED = 2,
    FIXED32 = 5
};

void write_varint(FILE* f, uint64_t value) {
    while (value >= 0x80) {
        uint8_t byte = (value & 0x7F) | 0x80;
        fwrite(&byte, 1, 1, f);
        value >>= 7;
    }
    uint8_t byte = value & 0x7F;
    fwrite(&byte, 1, 1, f);
}

void write_tag(FILE* f, uint32_t field_number, uint32_t wire_type) {
    write_varint(f, (field_number << 3) | wire_type);
}

void write_length_delimited(FILE* f, uint32_t field_number, const void* data, size_t size) {
    write_tag(f, field_number, LENGTH_DELIMITED);
    write_varint(f, size);
    fwrite(data, 1, size, f);
}

void write_string_field(FILE* f, uint32_t field_number, const std::string& str) {
    write_length_delimited(f, field_number, str.data(), str.size());
}

void write_uint64_field(FILE* f, uint32_t field_number, uint64_t value) {
    write_tag(f, field_number, VARINT);
    write_varint(f, value);
}

void write_int64_field(FILE* f, uint32_t field_number, int64_t value) {
    // ZigZag encoding for signed integers
    uint64_t encoded = (value << 1) ^ (value >> 63);
    write_uint64_field(f, field_number, encoded);
}

void write_double_field(FILE* f, uint32_t field_number, double value) {
    write_tag(f, field_number, FIXED64);
    fwrite(&value, sizeof(double), 1, f);
}

std::string format_radix_name(const std::string& name, dvtt_radix_t radix) {
    const char* suffix = "";
    switch (radix) {
        case DVTT_RADIX_BIN: suffix = "[bin]"; break;
        case DVTT_RADIX_OCT: suffix = "[oct]"; break;
        case DVTT_RADIX_DEC: suffix = "[dec]"; break;
        case DVTT_RADIX_HEX: suffix = "[hex]"; break;
        case DVTT_RADIX_UNSIGNED: suffix = "[u]"; break;
        case DVTT_RADIX_TIME: suffix = "[time]"; break;
        default: break;
    }
    return name + suffix;
}

std::string bits_to_string(const void* bits, size_t num_bits, dvtt_radix_t radix) {
    const uint8_t* bytes = static_cast<const uint8_t*>(bits);
    size_t num_bytes = (num_bits + 7) / 8;
    std::ostringstream oss;
    
    if (radix == DVTT_RADIX_HEX) {
        oss << "0x";
        for (int i = num_bytes - 1; i >= 0; i--) {
            oss << std::hex << std::setw(2) << std::setfill('0') << (int)bytes[i];
        }
    } else if (radix == DVTT_RADIX_BIN) {
        oss << "0b";
        for (int i = num_bytes - 1; i >= 0; i--) {
            for (int bit = 7; bit >= 0; bit--) {
                oss << ((bytes[i] >> bit) & 1);
            }
        }
    } else {
        // Default to hex
        oss << "0x";
        for (int i = num_bytes - 1; i >= 0; i--) {
            oss << std::hex << std::setw(2) << std::setfill('0') << (int)bytes[i];
        }
    }
    
    return oss.str();
}

void emit_clock_snapshot(TraceImpl* trace) {
    // Emit ClockSnapshot packet with time units
    std::vector<uint8_t> buffer;
    
    // Build ClockSnapshot message
    // Field 6: clocks (repeated Clock)
    // Clock has: field 1: clock_id, field 2: timestamp, field 6: unit_multiplier_ns
    
    // For simplicity, we'll emit a basic clock with BUILTIN_CLOCK_MONOTONIC
    // This is a simplified implementation - full protobuf generation would be more robust
    
    // Write a comment to the trace indicating time units
    // (Actual implementation would need proper protobuf encoding)
}

void emit_track_descriptor(TraceImpl* trace, StreamImpl* stream) {
    // Emit TrackDescriptor packet
    std::vector<uint8_t> track_desc_buf;
    
    // Build TrackDescriptor: uuid (field 1), name (field 2)
    // This is simplified - actual implementation needs proper nested message encoding
}

void emit_track_descriptor(TraceImpl* trace, TransactionImpl* txn) {
    // Emit TrackDescriptor packet for child transaction track
    // The track should have parent_uuid set to parent transaction's track_uuid
    // Build TrackDescriptor: uuid, name, parent_uuid
    // This is simplified - actual implementation needs proper nested message encoding
}

void emit_track_event_begin(TraceImpl* trace, TransactionImpl* txn) {
    // Emit TYPE_SLICE_BEGIN event with attributes
    // Use txn->track_uuid instead of stream->uuid
    // This is a simplified placeholder - actual implementation needs proper protobuf
}

void emit_track_event_end(TraceImpl* trace, TransactionImpl* txn) {
    // Emit TYPE_SLICE_END event
    // Use txn->track_uuid instead of stream->uuid
}

} // namespace dvtt

// Global error state
thread_local dvtt_error_t g_last_error = DVTT_OK;

// Error handling
dvtt_error_t dvtt_get_last_error(void) {
    return g_last_error;
}

const char* dvtt_error_string(dvtt_error_t error) {
    switch (error) {
        case DVTT_OK: return "Success";
        case DVTT_ERROR_NULL_HANDLE: return "NULL handle";
        case DVTT_ERROR_NULL_POINTER: return "NULL pointer";
        case DVTT_ERROR_INVALID_NAME: return "Invalid name";
        case DVTT_ERROR_MEMORY: return "Memory allocation failed";
        case DVTT_ERROR_NOT_INITIALIZED: return "Not initialized";
        case DVTT_ERROR_ALREADY_ENDED: return "Already ended";
        case DVTT_ERROR_NOT_ENDED: return "Not ended";
        default: return "Unknown error";
    }
}

// Initialization
dvtt_error_t dvtt_init(void) {
    g_last_error = DVTT_OK;
    return DVTT_OK;
}

void dvtt_shutdown(void) {
    // Cleanup any global state if needed
}

// Trace management
dvtt_trace_t dvtt_create_trace(const char* filename, const char* name, const char* time_units) {
    if (!filename || !name || !time_units) {
        g_last_error = DVTT_ERROR_NULL_POINTER;
        return nullptr;
    }
    
    dvtt_trace_t trace = new dvtt_trace_s;
    trace->impl = new dvtt::TraceImpl;
    
    trace->impl->filename = filename;
    trace->impl->name = name;
    trace->impl->time_units = time_units;
    trace->impl->sequence_id = 1;
    trace->impl->clock_id = 64; // BUILTIN_CLOCK_MONOTONIC
    trace->impl->next_stream_handle = 1;
    trace->impl->next_transaction_handle = 1;
    trace->impl->next_track_uuid = 1;
    trace->impl->next_transaction_id = 1;
    trace->impl->next_flow_id = 1;
    
    trace->impl->output_file = fopen(filename, "wb");
    if (!trace->impl->output_file) {
        delete trace->impl;
        delete trace;
        g_last_error = DVTT_ERROR_MEMORY;
        return nullptr;
    }
    
    dvtt::emit_clock_snapshot(trace->impl);
    
    g_last_error = DVTT_OK;
    return trace;
}

void dvtt_close_trace(dvtt_trace_t trace) {
    if (!trace || !trace->impl) return;
    
    // Close all streams
    for (auto* stream : trace->impl->streams) {
        if (stream->state == dvtt::STATE_OPEN) {
            dvtt_close_stream((dvtt_stream_t)&stream);
        }
    }
    
    if (trace->impl->output_file) {
        fclose(trace->impl->output_file);
    }
    
    // Cleanup
    for (auto* stream : trace->impl->streams) {
        for (auto* txn : stream->transactions) {
            delete txn;
        }
        delete stream;
    }
    
    delete trace->impl;
    delete trace;
}

const char* dvtt_get_trace_name(dvtt_trace_t trace) {
    if (!trace || !trace->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return trace->impl->name.c_str();
}

const char* dvtt_get_trace_filename(dvtt_trace_t trace) {
    if (!trace || !trace->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return trace->impl->filename.c_str();
}

const char* dvtt_get_trace_time_units(dvtt_trace_t trace) {
    if (!trace || !trace->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return trace->impl->time_units.c_str();
}

// Stream management
dvtt_stream_t dvtt_open_stream(dvtt_trace_t trace, const char* name, 
                               const char* scope, const char* type_name) {
    if (!trace || !trace->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    if (!name) {
        g_last_error = DVTT_ERROR_NULL_POINTER;
        return nullptr;
    }
    
    dvtt_stream_t stream = new dvtt_stream_s;
    stream->impl = new dvtt::StreamImpl;
    
    stream->impl->uuid = trace->impl->next_track_uuid++;
    stream->impl->name = name;
    stream->impl->scope = scope ? scope : "";
    stream->impl->type_name = type_name ? type_name : "";
    stream->impl->state = dvtt::STATE_OPEN;
    stream->impl->trace = trace;
    stream->impl->handle = trace->impl->next_stream_handle++;
    
    trace->impl->streams.push_back(stream->impl);
    trace->impl->stream_handles[stream->impl->handle] = stream->impl;
    
    dvtt::emit_track_descriptor(trace->impl, stream->impl);
    
    g_last_error = DVTT_OK;
    return stream;
}

void dvtt_close_stream(dvtt_stream_t stream) {
    if (!stream || !stream->impl) return;
    
    // Close all open transactions
    for (auto* txn : stream->impl->transactions) {
        if (txn->state == dvtt::STATE_OPEN) {
            dvtt_close_transaction((dvtt_transaction_t)&txn, txn->start_time);
        }
    }
    
    stream->impl->state = dvtt::STATE_CLOSED;
}

void dvtt_free_stream(dvtt_stream_t stream) {
    if (!stream || !stream->impl) return;
    
    if (stream->impl->state == dvtt::STATE_OPEN) {
        dvtt_close_stream(stream);
    }
    
    stream->impl->state = dvtt::STATE_FREED;
    // Note: Actual cleanup happens when trace is closed
}

int dvtt_is_stream_open(dvtt_stream_t stream) {
    if (!stream || !stream->impl) return 0;
    return stream->impl->state == dvtt::STATE_OPEN ? 1 : 0;
}

int dvtt_is_stream_closed(dvtt_stream_t stream) {
    if (!stream || !stream->impl) return 0;
    return stream->impl->state == dvtt::STATE_CLOSED ? 1 : 0;
}

const char* dvtt_get_stream_name(dvtt_stream_t stream) {
    if (!stream || !stream->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return stream->impl->name.c_str();
}

const char* dvtt_get_stream_scope(dvtt_stream_t stream) {
    if (!stream || !stream->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return stream->impl->scope.empty() ? nullptr : stream->impl->scope.c_str();
}

const char* dvtt_get_stream_type_name(dvtt_stream_t stream) {
    if (!stream || !stream->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return stream->impl->type_name.empty() ? nullptr : stream->impl->type_name.c_str();
}

int dvtt_get_stream_handle(dvtt_stream_t stream) {
    if (!stream || !stream->impl || stream->impl->state == dvtt::STATE_FREED) {
        return 0;
    }
    return stream->impl->handle;
}

dvtt_stream_t dvtt_get_stream_from_handle(int handle) {
    // This requires a global registry or trace context
    // For now, return nullptr
    return nullptr;
}

// Transaction management
dvtt_transaction_t dvtt_open_transaction(dvtt_stream_t stream, const char* name,
                                         dvtt_time_t start_time, const char* type_name,
                                         dvtt_transaction_t parent) {
    if (!stream || !stream->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    if (stream->impl->state != dvtt::STATE_OPEN) {
        g_last_error = DVTT_ERROR_NOT_INITIALIZED;
        return nullptr;
    }
    if (!name) {
        g_last_error = DVTT_ERROR_NULL_POINTER;
        return nullptr;
    }
    
    dvtt_transaction_t txn = new dvtt_transaction_s;
    txn->impl = new dvtt::TransactionImpl;
    
    dvtt::TraceImpl* trace = stream->impl->trace->impl;
    
    txn->impl->id = trace->next_transaction_id++;
    txn->impl->name = name;
    txn->impl->type_name = type_name ? type_name : "";
    txn->impl->start_time = start_time;
    txn->impl->end_time = 0;
    txn->impl->state = dvtt::STATE_OPEN;
    txn->impl->stream = stream;
    txn->impl->handle = trace->next_transaction_handle++;
    txn->impl->attributes_batch_mode = false;
    txn->impl->parent = parent;
    
    // Allocate track based on parent relationship
    if (parent && parent->impl) {
        // Child transaction gets its own track with parent relationship
        txn->impl->track_uuid = trace->next_track_uuid++;
    } else {
        // Root transaction uses stream's track
        txn->impl->track_uuid = stream->impl->uuid;
    }
    
    stream->impl->transactions.push_back(txn->impl);
    trace->transaction_handles[txn->impl->handle] = txn->impl;
    
    // Emit track descriptor for child transactions
    if (parent && parent->impl) {
        dvtt::emit_track_descriptor(trace, txn->impl);
    }
    
    g_last_error = DVTT_OK;
    return txn;
}

void dvtt_close_transaction(dvtt_transaction_t transaction, dvtt_time_t end_time) {
    if (!transaction || !transaction->impl) return;
    
    if (transaction->impl->state != dvtt::STATE_OPEN) return;
    
    transaction->impl->end_time = end_time;
    transaction->impl->state = dvtt::STATE_CLOSED;
    
    // Emit protobuf packets
    dvtt::TraceImpl* trace = transaction->impl->stream->impl->trace->impl;
    dvtt::emit_track_event_begin(trace, transaction->impl);
    dvtt::emit_track_event_end(trace, transaction->impl);
}

void dvtt_free_transaction(dvtt_transaction_t transaction, dvtt_time_t close_time) {
    if (!transaction || !transaction->impl) return;
    
    if (transaction->impl->state == dvtt::STATE_OPEN) {
        dvtt_close_transaction(transaction, close_time);
    }
    
    transaction->impl->state = dvtt::STATE_FREED;
}

int dvtt_is_transaction_open(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) return 0;
    return transaction->impl->state == dvtt::STATE_OPEN ? 1 : 0;
}

int dvtt_is_transaction_closed(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) return 0;
    return transaction->impl->state == dvtt::STATE_CLOSED ? 1 : 0;
}

const char* dvtt_get_transaction_name(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return transaction->impl->name.c_str();
}

const char* dvtt_get_transaction_type_name(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return transaction->impl->type_name.empty() ? nullptr : transaction->impl->type_name.c_str();
}

dvtt_time_t dvtt_get_transaction_start_time(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return 0;
    }
    return transaction->impl->start_time;
}

dvtt_time_t dvtt_get_transaction_end_time(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return 0;
    }
    return transaction->impl->end_time;
}

dvtt_stream_t dvtt_get_transaction_stream(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) {
        g_last_error = DVTT_ERROR_NULL_HANDLE;
        return nullptr;
    }
    return transaction->impl->stream;
}

int dvtt_get_transaction_handle(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl || transaction->impl->state == dvtt::STATE_FREED) {
        return 0;
    }
    return transaction->impl->handle;
}

dvtt_transaction_t dvtt_get_transaction_from_handle(int handle) {
    // Requires global registry
    return nullptr;
}

// Attribute addition
void dvtt_add_attr_int64(dvtt_transaction_t transaction, const char* name, int64_t value, dvtt_radix_t radix) {
    if (!transaction || !transaction->impl || !name) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = dvtt::format_radix_name(name, radix);
    attr.type = DVTT_ATTR_INT64;
    attr.radix = radix;
    attr.numeric_value.i64 = value;
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attr_int32(dvtt_transaction_t transaction, const char* name, int32_t value, dvtt_radix_t radix) {
    dvtt_add_attr_int64(transaction, name, value, radix);
}

void dvtt_add_attr_int16(dvtt_transaction_t transaction, const char* name, int16_t value, dvtt_radix_t radix) {
    dvtt_add_attr_int64(transaction, name, value, radix);
}

void dvtt_add_attr_int8(dvtt_transaction_t transaction, const char* name, int8_t value, dvtt_radix_t radix) {
    dvtt_add_attr_int64(transaction, name, value, radix);
}

void dvtt_add_attr_uint64(dvtt_transaction_t transaction, const char* name, uint64_t value, dvtt_radix_t radix) {
    if (!transaction || !transaction->impl || !name) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = dvtt::format_radix_name(name, radix);
    attr.type = DVTT_ATTR_UINT64;
    attr.radix = radix;
    attr.numeric_value.u64 = value;
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attr_uint32(dvtt_transaction_t transaction, const char* name, uint32_t value, dvtt_radix_t radix) {
    dvtt_add_attr_uint64(transaction, name, value, radix);
}

void dvtt_add_attr_uint16(dvtt_transaction_t transaction, const char* name, uint16_t value, dvtt_radix_t radix) {
    dvtt_add_attr_uint64(transaction, name, value, radix);
}

void dvtt_add_attr_uint8(dvtt_transaction_t transaction, const char* name, uint8_t value, dvtt_radix_t radix) {
    dvtt_add_attr_uint64(transaction, name, value, radix);
}

void dvtt_add_attr_float(dvtt_transaction_t transaction, const char* name, float value) {
    dvtt_add_attr_double(transaction, name, value);
}

void dvtt_add_attr_double(dvtt_transaction_t transaction, const char* name, double value) {
    if (!transaction || !transaction->impl || !name) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = name;
    attr.type = DVTT_ATTR_DOUBLE;
    attr.radix = DVTT_RADIX_REAL;
    attr.numeric_value.d = value;
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attr_string(dvtt_transaction_t transaction, const char* name, const char* value) {
    if (!transaction || !transaction->impl || !name || !value) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = name;
    attr.type = DVTT_ATTR_STRING;
    attr.radix = DVTT_RADIX_STRING;
    attr.string_value = value;
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attr_time(dvtt_transaction_t transaction, const char* name, dvtt_time_t value) {
    dvtt_add_attr_uint64(transaction, name, value, DVTT_RADIX_TIME);
}

void dvtt_add_attr_bits(dvtt_transaction_t transaction, const char* name, 
                        const void* bits, size_t num_bits, dvtt_radix_t radix) {
    if (!transaction || !transaction->impl || !name || !bits) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = dvtt::format_radix_name(name, radix);
    attr.type = DVTT_ATTR_BITSTRING;
    attr.radix = radix;
    attr.string_value = dvtt::bits_to_string(bits, num_bits, radix);
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attr_blob(dvtt_transaction_t transaction, const char* name,
                        const void* data, size_t size) {
    if (!transaction || !transaction->impl || !name || !data) return;
    
    dvtt::DebugAnnotation attr;
    attr.name = name;
    attr.type = DVTT_ATTR_BLOB;
    attr.radix = DVTT_RADIX_HEX;
    attr.blob_value.assign(static_cast<const uint8_t*>(data),
                           static_cast<const uint8_t*>(data) + size);
    
    transaction->impl->attributes.push_back(attr);
}

void dvtt_add_attribute(dvtt_transaction_t transaction, const char* name,
                        const dvtt_attr_value_t* value) {
    if (!transaction || !name || !value) return;
    
    switch (value->type) {
        case DVTT_ATTR_INT64:
            dvtt_add_attr_int64(transaction, name, value->value.i64, DVTT_RADIX_HEX);
            break;
        case DVTT_ATTR_UINT64:
            dvtt_add_attr_uint64(transaction, name, value->value.u64, DVTT_RADIX_HEX);
            break;
        case DVTT_ATTR_DOUBLE:
            dvtt_add_attr_double(transaction, name, value->value.d);
            break;
        case DVTT_ATTR_STRING:
            dvtt_add_attr_string(transaction, name, value->value.str);
            break;
        case DVTT_ATTR_BLOB:
            dvtt_add_attr_blob(transaction, name, value->value.blob.data, value->value.blob.size_bytes);
            break;
        default:
            break;
    }
}

// Links and relations
void dvtt_add_link(dvtt_transaction_t source, dvtt_transaction_t target,
                   dvtt_link_type_t link_type, const char* relation_name) {
    if (!source || !source->impl || !target || !target->impl) return;
    
    dvtt::TraceImpl* trace = source->impl->stream->impl->trace->impl;
    uint64_t flow_id = trace->next_flow_id++;
    
    source->impl->flow_ids.push_back(flow_id);
    target->impl->flow_ids.push_back(flow_id);
}

void dvtt_add_stream_link(dvtt_stream_t stream, dvtt_transaction_t transaction,
                          dvtt_link_type_t link_type, const char* relation_name) {
    // Stream links are less common, simplified implementation
}

// Bulk operations
void dvtt_begin_attributes(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) return;
    transaction->impl->attributes_batch_mode = true;
}

void dvtt_end_attributes(dvtt_transaction_t transaction) {
    if (!transaction || !transaction->impl) return;
    transaction->impl->attributes_batch_mode = false;
}
