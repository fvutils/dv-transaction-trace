/**
 * @file dvtt.h
 * @brief DV Transaction Trace - C API for transaction recording
 * 
 * This API provides transaction recording capabilities for design verification,
 * based on the "Transaction Recording Anywhere Anytime" specification.
 * 
 * Key concepts:
 * - Streams: Organize transactions into logical groups (e.g., per bus, monitor)
 * - Transactions: Have start/end times and belong to a stream
 * - Attributes: Name-value pairs that describe transaction properties
 * - Relations: Optional links between transactions
 */

#ifndef DVTT_H
#define DVTT_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque handle types - use pointers for type safety */
typedef struct dvtt_trace_s* dvtt_trace_t;
typedef struct dvtt_stream_s* dvtt_stream_t;
typedef struct dvtt_transaction_s* dvtt_transaction_t;

/**
 * Radix for displaying numeric values
 */
typedef enum {
    DVTT_RADIX_BIN,
    DVTT_RADIX_OCT,
    DVTT_RADIX_DEC,
    DVTT_RADIX_HEX,
    DVTT_RADIX_UNSIGNED,
    DVTT_RADIX_STRING,
    DVTT_RADIX_TIME,
    DVTT_RADIX_REAL
} dvtt_radix_t;

/**
 * Attribute value types supported by the API
 */
typedef enum {
    DVTT_ATTR_INT8,
    DVTT_ATTR_INT16,
    DVTT_ATTR_INT32,
    DVTT_ATTR_INT64,
    DVTT_ATTR_UINT8,
    DVTT_ATTR_UINT16,
    DVTT_ATTR_UINT32,
    DVTT_ATTR_UINT64,
    DVTT_ATTR_REAL,
    DVTT_ATTR_DOUBLE,
    DVTT_ATTR_STRING,
    DVTT_ATTR_BITSTRING,  /* For bit vectors of arbitrary width */
    DVTT_ATTR_BLOB        /* For arbitrary binary data */
} dvtt_attr_type_t;

/**
 * Attribute value container
 */
typedef struct {
    dvtt_attr_type_t type;
    union {
        int8_t i8;
        int16_t i16;
        int32_t i32;
        int64_t i64;
        uint8_t u8;
        uint16_t u16;
        uint32_t u32;
        uint64_t u64;
        float f;
        double d;
        const char* str;
        struct {
            const void* data;
            size_t size_bytes;
        } blob;
    } value;
} dvtt_attr_value_t;

/**
 * Time representation (in simulation time units)
 */
typedef uint64_t dvtt_time_t;

/* ========================================================================
 * Trace Management
 * ======================================================================== */

/**
 * Create a new trace object and open output file
 * 
 * @param filename Output trace filename (e.g., "trace.perfetto")
 * @param name Trace name for display/identification (e.g., "simulation_trace")
 * @param time_units Time unit string (e.g., "1ns", "1ps", "1us")
 * @return Trace handle, or NULL on failure
 * 
 * Note: A trace object is the top-level container for all streams.
 * The time_units parameter defines the resolution of all timestamps in the trace.
 * 
 * Example:
 *   trace = dvtt_create_trace("sim.perfetto", "my_simulation", "1ns");
 */
dvtt_trace_t dvtt_create_trace(const char* filename, 
                                const char* name,
                                const char* time_units);

/**
 * Close and free a trace object and all its streams
 * 
 * @param trace Trace handle to close
 * 
 * Note: This flushes all pending data and closes the output file
 */
void dvtt_close_trace(dvtt_trace_t trace);

/**
 * Get trace name
 * 
 * @param trace Trace handle
 * @return Trace name string (valid for lifetime of trace)
 */
const char* dvtt_get_trace_name(dvtt_trace_t trace);

/**
 * Get trace filename
 * 
 * @param trace Trace handle
 * @return Trace filename string (valid for lifetime of trace)
 */
const char* dvtt_get_trace_filename(dvtt_trace_t trace);

/**
 * Get trace time units
 * 
 * @param trace Trace handle
 * @return Time unit string (valid for lifetime of trace)
 */
const char* dvtt_get_trace_time_units(dvtt_trace_t trace);

/* ========================================================================
 * Stream Management
 * ======================================================================== */

/**
 * Create and open a transaction stream
 * 
 * @param trace Trace handle
 * @param name Stream name (e.g., "axi_master", "pcie_monitor")
 * @param scope Optional scope (hierarchical path, may be NULL)
 * @param type_name Optional type name (may be NULL)
 * @return Stream handle, or NULL on failure
 * 
 * Note: Stream is automatically opened upon creation
 */
dvtt_stream_t dvtt_open_stream(dvtt_trace_t trace, const char* name, 
                                const char* scope, const char* type_name);

/**
 * Close a transaction stream
 * 
 * @param stream Stream handle to close
 * 
 * Note: Closing a stream closes all open transactions in the stream.
 * The stream remains valid for querying until freed.
 */
void dvtt_close_stream(dvtt_stream_t stream);

/**
 * Free a transaction stream
 * 
 * @param stream Stream handle to free
 * 
 * Note: Frees all resources associated with the stream.
 * If stream is still open, it will be closed first.
 */
void dvtt_free_stream(dvtt_stream_t stream);

/**
 * Check if stream is open
 * 
 * @param stream Stream handle
 * @return 1 if open, 0 otherwise
 */
int dvtt_is_stream_open(dvtt_stream_t stream);

/**
 * Check if stream is closed (but not freed)
 * 
 * @param stream Stream handle
 * @return 1 if closed but not freed, 0 otherwise
 */
int dvtt_is_stream_closed(dvtt_stream_t stream);

/**
 * Get stream name
 * 
 * @param stream Stream handle
 * @return Stream name string (valid for lifetime of stream)
 */
const char* dvtt_get_stream_name(dvtt_stream_t stream);

/**
 * Get stream scope
 * 
 * @param stream Stream handle
 * @return Stream scope string (valid for lifetime of stream), or NULL
 */
const char* dvtt_get_stream_scope(dvtt_stream_t stream);

/**
 * Get stream type name
 * 
 * @param stream Stream handle
 * @return Stream type name string (valid for lifetime of stream), or NULL
 */
const char* dvtt_get_stream_type_name(dvtt_stream_t stream);

/**
 * Get unique handle for stream
 * 
 * @param stream Stream handle
 * @return Unique integer handle, or 0 if stream is invalid/freed
 */
int dvtt_get_stream_handle(dvtt_stream_t stream);

/**
 * Get stream from integer handle
 * 
 * @param handle Integer handle returned from dvtt_get_stream_handle
 * @return Stream handle, or NULL if not found or freed
 */
dvtt_stream_t dvtt_get_stream_from_handle(int handle);

/* ========================================================================
 * Transaction Lifecycle
 * ======================================================================== */

/**
 * Open a new transaction on a stream
 * 
 * @param stream Stream handle
 * @param name Transaction name (e.g., "READ", "WRITE", "trans_1234")
 * @param start_time Transaction start time
 * @param type_name Optional type name (may be NULL)
 * @param parent Optional parent transaction for hierarchical nesting (may be NULL)
 * @return Transaction handle, or NULL on failure
 * 
 * Note: Transactions can only be opened on open streams.
 * If parent is specified, the transaction will be rendered as a child in the trace viewer,
 * using a sub-track allocated under the parent's track. This makes track allocation
 * explicit and simplifies parent-child relationship tracking.
 */
dvtt_transaction_t dvtt_open_transaction(dvtt_stream_t stream, 
                                          const char* name,
                                          dvtt_time_t start_time,
                                          const char* type_name,
                                          dvtt_transaction_t parent);

/**
 * Close a transaction
 * 
 * @param transaction Transaction handle
 * @param end_time Transaction end time
 * 
 * Note: Transaction remains valid for adding relations and querying until freed.
 */
void dvtt_close_transaction(dvtt_transaction_t transaction, dvtt_time_t end_time);

/**
 * Free a transaction
 * 
 * @param transaction Transaction handle
 * @param close_time Optional close time (used if transaction not yet closed)
 * 
 * Note: If transaction is not closed, it will be closed first with close_time.
 * Frees all resources associated with the transaction.
 */
void dvtt_free_transaction(dvtt_transaction_t transaction, dvtt_time_t close_time);

/**
 * Check if transaction is open
 * 
 * @param transaction Transaction handle
 * @return 1 if open, 0 otherwise
 */
int dvtt_is_transaction_open(dvtt_transaction_t transaction);

/**
 * Check if transaction is closed (but not freed)
 * 
 * @param transaction Transaction handle
 * @return 1 if closed but not freed, 0 otherwise
 */
int dvtt_is_transaction_closed(dvtt_transaction_t transaction);

/**
 * Get transaction name
 * 
 * @param transaction Transaction handle
 * @return Transaction name string (valid until transaction is freed)
 */
const char* dvtt_get_transaction_name(dvtt_transaction_t transaction);

/**
 * Get transaction type name
 * 
 * @param transaction Transaction handle
 * @return Transaction type name string (valid until transaction is freed), or NULL
 */
const char* dvtt_get_transaction_type_name(dvtt_transaction_t transaction);

/**
 * Get transaction start time
 * 
 * @param transaction Transaction handle
 * @return Start time
 */
dvtt_time_t dvtt_get_transaction_start_time(dvtt_transaction_t transaction);

/**
 * Get transaction end time
 * 
 * @param transaction Transaction handle
 * @return End time (0 if not yet closed)
 */
dvtt_time_t dvtt_get_transaction_end_time(dvtt_transaction_t transaction);

/**
 * Get transaction stream
 * 
 * @param transaction Transaction handle
 * @return Stream handle that owns this transaction
 */
dvtt_stream_t dvtt_get_transaction_stream(dvtt_transaction_t transaction);

/**
 * Get unique handle for transaction
 * 
 * @param transaction Transaction handle
 * @return Unique integer handle, or 0 if transaction is invalid/freed
 */
int dvtt_get_transaction_handle(dvtt_transaction_t transaction);

/**
 * Get transaction from integer handle
 * 
 * @param handle Integer handle returned from dvtt_get_transaction_handle
 * @return Transaction handle, or NULL if not found or freed
 */
dvtt_transaction_t dvtt_get_transaction_from_handle(int handle);

/* ========================================================================
 * Transaction Attributes
 * ======================================================================== */

/**
 * Add an integer attribute to a transaction with optional radix
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param value Integer value
 * @param radix Display radix (use DVTT_RADIX_HEX if not specified)
 */
void dvtt_add_attr_int64(dvtt_transaction_t transaction, const char* name, int64_t value, dvtt_radix_t radix);
void dvtt_add_attr_int32(dvtt_transaction_t transaction, const char* name, int32_t value, dvtt_radix_t radix);
void dvtt_add_attr_int16(dvtt_transaction_t transaction, const char* name, int16_t value, dvtt_radix_t radix);
void dvtt_add_attr_int8(dvtt_transaction_t transaction, const char* name, int8_t value, dvtt_radix_t radix);

/**
 * Add an unsigned integer attribute to a transaction with optional radix
 */
void dvtt_add_attr_uint64(dvtt_transaction_t transaction, const char* name, uint64_t value, dvtt_radix_t radix);
void dvtt_add_attr_uint32(dvtt_transaction_t transaction, const char* name, uint32_t value, dvtt_radix_t radix);
void dvtt_add_attr_uint16(dvtt_transaction_t transaction, const char* name, uint16_t value, dvtt_radix_t radix);
void dvtt_add_attr_uint8(dvtt_transaction_t transaction, const char* name, uint8_t value, dvtt_radix_t radix);

/**
 * Add a floating-point attribute to a transaction
 */
void dvtt_add_attr_float(dvtt_transaction_t transaction, const char* name, float value);
void dvtt_add_attr_double(dvtt_transaction_t transaction, const char* name, double value);

/**
 * Add a string attribute to a transaction
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param value String value (will be copied)
 */
void dvtt_add_attr_string(dvtt_transaction_t transaction, const char* name, const char* value);

/**
 * Add a time attribute to a transaction
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param value Time value
 */
void dvtt_add_attr_time(dvtt_transaction_t transaction, const char* name, dvtt_time_t value);

/**
 * Add a bit vector attribute to a transaction
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param bits Pointer to bit data (packed bytes, LSB first)
 * @param num_bits Number of bits in the vector
 * @param radix Display radix
 * 
 * Note: Data is copied, caller retains ownership
 */
void dvtt_add_attr_bits(dvtt_transaction_t transaction, const char* name, 
                         const void* bits, size_t num_bits, dvtt_radix_t radix);

/**
 * Add a binary blob attribute to a transaction
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param data Pointer to binary data
 * @param size Size in bytes
 * 
 * Note: Data is copied, caller retains ownership
 */
void dvtt_add_attr_blob(dvtt_transaction_t transaction, const char* name,
                         const void* data, size_t size);

/**
 * Add a generic attribute with explicit type
 * 
 * @param transaction Transaction handle
 * @param name Attribute name
 * @param value Attribute value with type information
 */
void dvtt_add_attribute(dvtt_transaction_t transaction, const char* name,
                         const dvtt_attr_value_t* value);

/* ========================================================================
 * Links and Relations
 * ======================================================================== */

/**
 * Link types for establishing relationships
 */
typedef enum {
    DVTT_LINK_PARENT_CHILD,  /* Parent-child relationship */
    DVTT_LINK_RELATED,       /* General related relationship */
    DVTT_LINK_CAUSE_EFFECT,  /* Cause-effect relationship */
    DVTT_LINK_CUSTOM         /* Custom relationship (use relation_name) */
} dvtt_link_type_t;

/**
 * Add a link between two transactions
 * 
 * @param source Source transaction handle
 * @param target Target transaction handle
 * @param link_type Type of link
 * @param relation_name Optional relationship name (for DVTT_LINK_CUSTOM)
 * 
 * Note: Relations are useful for showing dependencies but can be expensive
 * to maintain. Consider using ID attributes instead for simpler tracking.
 */
void dvtt_add_link(dvtt_transaction_t source, 
                    dvtt_transaction_t target,
                    dvtt_link_type_t link_type,
                    const char* relation_name);

/**
 * Add a link between a stream and a transaction
 * 
 * @param stream Stream handle
 * @param transaction Transaction handle
 * @param link_type Type of link
 * @param relation_name Optional relationship name (for DVTT_LINK_CUSTOM)
 */
void dvtt_add_stream_link(dvtt_stream_t stream,
                           dvtt_transaction_t transaction,
                           dvtt_link_type_t link_type,
                           const char* relation_name);

/* ========================================================================
 * Error Handling
 * ======================================================================== */

/**
 * Error codes
 */
typedef enum {
    DVTT_OK = 0,
    DVTT_ERROR_NULL_HANDLE,
    DVTT_ERROR_NULL_POINTER,
    DVTT_ERROR_INVALID_NAME,
    DVTT_ERROR_MEMORY,
    DVTT_ERROR_NOT_INITIALIZED,
    DVTT_ERROR_ALREADY_ENDED,
    DVTT_ERROR_NOT_ENDED
} dvtt_error_t;

/**
 * Get last error code
 * 
 * @return Error code from last operation
 */
dvtt_error_t dvtt_get_last_error(void);

/**
 * Get error message for error code
 * 
 * @param error Error code
 * @return Human-readable error message
 */
const char* dvtt_error_string(dvtt_error_t error);

/* ========================================================================
 * Initialization and Cleanup
 * ======================================================================== */

/**
 * Initialize the transaction recording system
 * 
 * @return DVTT_OK on success, error code on failure
 * 
 * Note: Should be called before creating any trace objects
 */
dvtt_error_t dvtt_init(void);

/**
 * Shutdown the transaction recording system
 * 
 * Closes all open traces and frees all resources
 */
void dvtt_shutdown(void);

/* ========================================================================
 * Optional: Bulk Operations
 * ======================================================================== */

/**
 * Begin multiple attribute additions
 * 
 * @param transaction Transaction handle
 * 
 * Note: Can improve performance when adding many attributes.
 * Must be paired with dvtt_end_attributes()
 */
void dvtt_begin_attributes(dvtt_transaction_t transaction);

/**
 * Complete attribute additions
 * 
 * @param transaction Transaction handle
 */
void dvtt_end_attributes(dvtt_transaction_t transaction);

/* ========================================================================
 * Helper Macros
 * ======================================================================== */

/* Convenience macros for common integer types with default radix */
#define dvtt_add_attr_int(txn, name, val) \
    _Generic((val), \
        int8_t: dvtt_add_attr_int8, \
        int16_t: dvtt_add_attr_int16, \
        int32_t: dvtt_add_attr_int32, \
        int64_t: dvtt_add_attr_int64, \
        uint8_t: dvtt_add_attr_uint8, \
        uint16_t: dvtt_add_attr_uint16, \
        uint32_t: dvtt_add_attr_uint32, \
        uint64_t: dvtt_add_attr_uint64, \
        default: dvtt_add_attr_int32 \
    )(txn, name, val, DVTT_RADIX_HEX)

/* Simplified names for backward compatibility */
#define dvtt_begin_transaction(stream, name, time) \
    dvtt_open_transaction(stream, name, time, NULL, NULL)
    
#define dvtt_end_transaction(txn, time) \
    dvtt_close_transaction(txn, time)

#ifdef __cplusplus
}
#endif

#endif /* DVTT_H */
