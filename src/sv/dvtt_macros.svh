
`ifndef INCLUDED_DVTT_MACROS_SVH
`define INCLUDED_DVTT_MACROS_SVH

`define DVTT_DEBUG_ENTER(msg) \
    if (_dvtt_debug_level > 0) begin \
        $writef("--> "); \
        $display msg ; \
    end

`define DVTT_DEBUG_LEAVE(msg) \
    if (_dvtt_debug_level > 0) begin \
        $writef("<-- "); \
        $display msg ; \
    end

`endif INCLUDED_DVTT_MACROS_SVH