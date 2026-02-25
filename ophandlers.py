import ir_helpers as irh


# Included handlers for all instructions, we will only need to implement a
# subset of these, but it's easier to have them all
# defined now and fill in the ones we need later.

# Terminator Instructions
def handle_ret(instr):
    irh.print_instruction(instr)


def handle_br(instr):
    irh.print_instruction(instr)


def handle_switch(instr):
    irh.print_instruction(instr)


def handle_indirectbr(instr):
    irh.print_instruction(instr)


def handle_invoke(instr):
    irh.print_instruction(instr)


def handle_callbr(instr):
    irh.print_instruction(instr)


def handle_resume(instr):
    irh.print_instruction(instr)


def handle_catchswitch(instr):
    irh.print_instruction(instr)


def handle_catchret(instr):
    irh.print_instruction(instr)


def handle_cleanupret(instr):
    irh.print_instruction(instr)


def handle_unreachable(instr):
    irh.print_instruction(instr)


# Unary Operations
def handle_fneg(instr):
    irh.print_instruction(instr)


# Binary Operations
def handle_add(instr):
    irh.print_instruction(instr)


def handle_fadd(instr):
    irh.print_instruction(instr)


def handle_sub(instr):
    irh.print_instruction(instr)


def handle_fsub(instr):
    irh.print_instruction(instr)


def handle_mul(instr):
    irh.print_instruction(instr)


def handle_fmul(instr):
    irh.print_instruction(instr)


def handle_udiv(instr):
    irh.print_instruction(instr)


def handle_sdiv(instr):
    irh.print_instruction(instr)


def handle_fdiv(instr):
    irh.print_instruction(instr)


def handle_urem(instr):
    irh.print_instruction(instr)


def handle_srem(instr):
    irh.print_instruction(instr)


def handle_frem(instr):
    irh.print_instruction(instr)


# Logical Operations
def handle_shl(instr):
    irh.print_instruction(instr)


def handle_lshr(instr):
    irh.print_instruction(instr)


def handle_ashr(instr):
    irh.print_instruction(instr)


def handle_and(instr):
    irh.print_instruction(instr)


def handle_or(instr):
    irh.print_instruction(instr)


def handle_xor(instr):
    irh.print_instruction(instr)


# Vector Operations
def handle_extractelement(instr):
    irh.print_instruction(instr)


def handle_insertelement(instr):
    irh.print_instruction(instr)


def handle_shufflevector(instr):
    irh.print_instruction(instr)


# Aggregate Operations
def handle_extractvalue(instr):
    irh.print_instruction(instr)


def handle_insertvalue(instr):
    irh.print_instruction(instr)


# Memory Operations
def handle_alloca(instr):
    irh.print_instruction(instr)


def handle_load(instr):
    irh.print_instruction(instr)


def handle_store(instr):
    irh.print_instruction(instr)


def handle_fence(instr):
    irh.print_instruction(instr)


def handle_cmpxchg(instr):
    irh.print_instruction(instr)


def handle_atomicrmw(instr):
    irh.print_instruction(instr)


def handle_getelementptr(instr):
    irh.print_instruction(instr)


# Casts and Conversions
def handle_trunc(instr):
    irh.print_instruction(instr)


def handle_zext(instr):
    irh.print_instruction(instr)


def handle_sext(instr):
    irh.print_instruction(instr)


def handle_fptrunc(instr):
    irh.print_instruction(instr)


def handle_fpext(instr):
    irh.print_instruction(instr)


def handle_fptoui(instr):
    irh.print_instruction(instr)


def handle_fptosi(instr):
    irh.print_instruction(instr)


def handle_uitofp(instr):
    irh.print_instruction(instr)


def handle_sitofp(instr):
    irh.print_instruction(instr)


def handle_ptrtoint(instr):
    irh.print_instruction(instr)


def handle_inttoptr(instr):
    irh.print_instruction(instr)


def handle_bitcast(instr):
    irh.print_instruction(instr)


def handle_addrspacecast(instr):
    irh.print_instruction(instr)


# Compare Instructions
def handle_icmp(instr):
    irh.print_instruction(instr)


def handle_fcmp(instr):
    irh.print_instruction(instr)


# Other Instructions
def handle_phi(instr):
    irh.print_instruction(instr)


def handle_select(instr):
    irh.print_instruction(instr)


def handle_freeze(instr):
    irh.print_instruction(instr)


def handle_call(instr):
    irh.print_instruction(instr)


def handle_va_arg(instr):
    irh.print_instruction(instr)


def handle_landingpad(instr):
    irh.print_instruction(instr)


def handle_catchpad(instr):
    irh.print_instruction(instr)


def handle_cleanuppad(instr):
    irh.print_instruction(instr)
