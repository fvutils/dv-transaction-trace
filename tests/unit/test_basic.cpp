#include <gtest/gtest.h>
#include "include/dvtt.h"
#include <cstdio>
#include <string>

class DVTTBasicTest : public ::testing::Test {
protected:
    void SetUp() override {
        dvtt_init();
    }
    
    void TearDown() override {
        dvtt_shutdown();
    }
};

TEST_F(DVTTBasicTest, InitShutdown) {
    EXPECT_EQ(dvtt_init(), DVTT_OK);
    dvtt_shutdown();
}

TEST_F(DVTTBasicTest, CreateTrace) {
    const char* filename = "test_trace.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test_trace", "1ns");
    
    ASSERT_NE(trace, nullptr);
    EXPECT_STREQ(dvtt_get_trace_name(trace), "test_trace");
    EXPECT_STREQ(dvtt_get_trace_filename(trace), filename);
    EXPECT_STREQ(dvtt_get_trace_time_units(trace), "1ns");
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, CreateNullFilename) {
    dvtt_trace_t trace = dvtt_create_trace(nullptr, "test", "1ns");
    EXPECT_EQ(trace, nullptr);
    EXPECT_EQ(dvtt_get_last_error(), DVTT_ERROR_NULL_POINTER);
}

TEST_F(DVTTBasicTest, OpenStream) {
    const char* filename = "test_stream.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", "scope1", "type1");
    ASSERT_NE(stream, nullptr);
    
    EXPECT_STREQ(dvtt_get_stream_name(stream), "stream1");
    EXPECT_STREQ(dvtt_get_stream_scope(stream), "scope1");
    EXPECT_STREQ(dvtt_get_stream_type_name(stream), "type1");
    EXPECT_TRUE(dvtt_is_stream_open(stream));
    EXPECT_FALSE(dvtt_is_stream_closed(stream));
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, CloseStream) {
    const char* filename = "test_close_stream.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    EXPECT_TRUE(dvtt_is_stream_open(stream));
    
    dvtt_close_stream(stream);
    EXPECT_FALSE(dvtt_is_stream_open(stream));
    EXPECT_TRUE(dvtt_is_stream_closed(stream));
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, OpenTransaction) {
    const char* filename = "test_transaction.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, "type1");
    ASSERT_NE(txn, nullptr);
    
    EXPECT_STREQ(dvtt_get_transaction_name(txn), "txn1");
    EXPECT_STREQ(dvtt_get_transaction_type_name(txn), "type1");
    EXPECT_EQ(dvtt_get_transaction_start_time(txn), 1000);
    EXPECT_TRUE(dvtt_is_transaction_open(txn));
    EXPECT_FALSE(dvtt_is_transaction_closed(txn));
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, CloseTransaction) {
    const char* filename = "test_close_txn.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    EXPECT_TRUE(dvtt_is_transaction_open(txn));
    
    dvtt_close_transaction(txn, 2000);
    EXPECT_FALSE(dvtt_is_transaction_open(txn));
    EXPECT_TRUE(dvtt_is_transaction_closed(txn));
    EXPECT_EQ(dvtt_get_transaction_end_time(txn), 2000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, AddAttributes) {
    const char* filename = "test_attributes.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    
    // Add various attributes
    dvtt_add_attr_uint64(txn, "addr", 0x1234ABCD, DVTT_RADIX_HEX);
    dvtt_add_attr_int32(txn, "count", 42, DVTT_RADIX_DEC);
    dvtt_add_attr_double(txn, "voltage", 3.3);
    dvtt_add_attr_string(txn, "status", "OK");
    dvtt_add_attr_time(txn, "timestamp", 1000);
    
    dvtt_close_transaction(txn, 2000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, AddBitVector) {
    const char* filename = "test_bitvector.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    
    uint8_t bits[] = {0xAB, 0xCD, 0xEF};
    dvtt_add_attr_bits(txn, "data", bits, 24, DVTT_RADIX_HEX);
    
    dvtt_close_transaction(txn, 2000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, AddBlob) {
    const char* filename = "test_blob.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    
    uint8_t data[] = {0x01, 0x02, 0x03, 0x04, 0x05};
    dvtt_add_attr_blob(txn, "payload", data, sizeof(data));
    
    dvtt_close_transaction(txn, 2000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, MultipleStreamsAndTransactions) {
    const char* filename = "test_multiple.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    // Create multiple streams
    dvtt_stream_t stream1 = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    dvtt_stream_t stream2 = dvtt_open_stream(trace, "stream2", nullptr, nullptr);
    ASSERT_NE(stream1, nullptr);
    ASSERT_NE(stream2, nullptr);
    
    // Create transactions on different streams
    dvtt_transaction_t txn1 = dvtt_open_transaction(stream1, "txn1", 1000, nullptr);
    dvtt_transaction_t txn2 = dvtt_open_transaction(stream2, "txn2", 1500, nullptr);
    dvtt_transaction_t txn3 = dvtt_open_transaction(stream1, "txn3", 2000, nullptr);
    
    ASSERT_NE(txn1, nullptr);
    ASSERT_NE(txn2, nullptr);
    ASSERT_NE(txn3, nullptr);
    
    // Close transactions
    dvtt_close_transaction(txn1, 2000);
    dvtt_close_transaction(txn2, 2500);
    dvtt_close_transaction(txn3, 3000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, StreamHandle) {
    const char* filename = "test_handle.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    int handle = dvtt_get_stream_handle(stream);
    EXPECT_GT(handle, 0);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, TransactionHandle) {
    const char* filename = "test_txn_handle.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    
    int handle = dvtt_get_transaction_handle(txn);
    EXPECT_GT(handle, 0);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

TEST_F(DVTTBasicTest, BatchAttributes) {
    const char* filename = "test_batch.perfetto";
    dvtt_trace_t trace = dvtt_create_trace(filename, "test", "1ns");
    ASSERT_NE(trace, nullptr);
    
    dvtt_stream_t stream = dvtt_open_stream(trace, "stream1", nullptr, nullptr);
    ASSERT_NE(stream, nullptr);
    
    dvtt_transaction_t txn = dvtt_open_transaction(stream, "txn1", 1000, nullptr);
    ASSERT_NE(txn, nullptr);
    
    dvtt_begin_attributes(txn);
    for (int i = 0; i < 10; i++) {
        dvtt_add_attr_int32(txn, "value", i, DVTT_RADIX_DEC);
    }
    dvtt_end_attributes(txn);
    
    dvtt_close_transaction(txn, 2000);
    
    dvtt_close_trace(trace);
    std::remove(filename);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
