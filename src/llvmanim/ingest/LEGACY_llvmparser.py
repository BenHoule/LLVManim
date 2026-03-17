import llvmlite.binding as llvm

from llvmanim.ingest import LEGACY_ir_helpers as irout
from llvmanim.ingest import LEGACY_ophandlers as oph

with open("double.ll") as f:
    llvm_ir = f.read()

prog = llvm.parse_assembly(llvm_ir)
prog.verify()  # Ensures module is well-formed


print(f"SOURCE FILE: {prog.source_file}")
print(f"MODULE NAME: {prog.name}")
print(f"DATA LAYOUT: {prog.data_layout}")

for func in prog.functions:
    irout.print_func_sig(func)
    for block in func.blocks:
        print(f"  Block: {block.name}")
        for instr in block.instructions:
            match instr.opcode:
                # Terminator Instructions
                case "ret":
                    oph.handle_ret(instr)
                case "br":
                    oph.handle_br(instr)
                case "switch":
                    oph.handle_switch(instr)
                case "indirectbr":
                    oph.handle_indirectbr(instr)
                case "invoke":
                    oph.handle_invoke(instr)
                case "callbr":
                    oph.handle_callbr(instr)
                case "resume":
                    oph.handle_resume(instr)
                case "catchswitch":
                    oph.handle_catchswitch(instr)
                case "catchret":
                    oph.handle_catchret(instr)
                case "cleanupret":
                    oph.handle_cleanupret(instr)
                case "unreachable":
                    oph.handle_unreachable(instr)
                # Unary Operations
                case "fneg":
                    oph.handle_fneg(instr)
                # Binary Operations
                case "add":
                    oph.handle_add(instr)
                case "fadd":
                    oph.handle_fadd(instr)
                case "sub":
                    oph.handle_sub(instr)
                case "fsub":
                    oph.handle_fsub(instr)
                case "mul":
                    oph.handle_mul(instr)
                case "fmul":
                    oph.handle_fmul(instr)
                case "udiv":
                    oph.handle_udiv(instr)
                case "sdiv":
                    oph.handle_sdiv(instr)
                case "fdiv":
                    oph.handle_fdiv(instr)
                case "urem":
                    oph.handle_urem(instr)
                case "srem":
                    oph.handle_srem(instr)
                case "frem":
                    oph.handle_frem(instr)
                # Logical Operations
                case "shl":
                    oph.handle_shl(instr)
                case "lshr":
                    oph.handle_lshr(instr)
                case "ashr":
                    oph.handle_ashr(instr)
                case "and":
                    oph.handle_and(instr)
                case "or":
                    oph.handle_or(instr)
                case "xor":
                    oph.handle_xor(instr)
                # Vector Operations
                case "extractelement":
                    oph.handle_extractelement(instr)
                case "insertelement":
                    oph.handle_insertelement(instr)
                case "shufflevector":
                    oph.handle_shufflevector(instr)
                # Aggregate Operations
                case "extractvalue":
                    oph.handle_extractvalue(instr)
                case "insertvalue":
                    oph.handle_insertvalue(instr)
                # Memory Operations
                case "alloca":
                    oph.handle_alloca(instr)
                case "load":
                    oph.handle_load(instr)
                case "store":
                    oph.handle_store(instr)
                case "fence":
                    oph.handle_fence(instr)
                case "cmpxchg":
                    oph.handle_cmpxchg(instr)
                case "atomicrmw":
                    oph.handle_atomicrmw(instr)
                case "getelementptr":
                    oph.handle_getelementptr(instr)
                # Casts and Conversions
                case "trunc":
                    oph.handle_trunc(instr)
                case "zext":
                    oph.handle_zext(instr)
                case "sext":
                    oph.handle_sext(instr)
                case "fptrunc":
                    oph.handle_fptrunc(instr)
                case "fpext":
                    oph.handle_fpext(instr)
                case "fptoui":
                    oph.handle_fptoui(instr)
                case "fptosi":
                    oph.handle_fptosi(instr)
                case "uitofp":
                    oph.handle_uitofp(instr)
                case "sitofp":
                    oph.handle_sitofp(instr)
                case "ptrtoint":
                    oph.handle_ptrtoint(instr)
                case "inttoptr":
                    oph.handle_inttoptr(instr)
                case "bitcast":
                    oph.handle_bitcast(instr)
                case "addrspacecast":
                    oph.handle_addrspacecast(instr)
                # Compare Instructions
                case "icmp":
                    oph.handle_icmp(instr)
                case "fcmp":
                    oph.handle_fcmp(instr)
                # Other Instructions
                case "phi":
                    oph.handle_phi(instr)
                case "select":
                    oph.handle_select(instr)
                case "freeze":
                    oph.handle_freeze(instr)
                case "call":
                    oph.handle_call(instr)
                case "va_arg":
                    oph.handle_va_arg(instr)
                case "landingpad":
                    oph.handle_landingpad(instr)
                case "catchpad":
                    oph.handle_catchpad(instr)
                case "cleanuppad":
                    oph.handle_cleanuppad(instr)
                case _:
                    print(f"Unknown instruction opcode: {instr.opcode}")
                    break
