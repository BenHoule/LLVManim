import llvmlite.binding as llvm
import re

with open("double.ll", "r") as f:
    llvm_ir = f.read()

prog = llvm.parse_assembly(llvm_ir)
prog.verify()  # Ensures module is well-formed


def value_label(value):
    if value.name:
        return f"%{value.name}"

    text = str(value).strip()
    # For unnamed values, try to extract a label from the instruction text
    match = re.match(r'^(%[-a-zA-Z$._0-9]+)\s*=.*$', text)
    if match:
        return match.group(1)
    return text


print(f"SOURCE FILE: {prog.source_file}")
print(f"MODULE NAME: {prog.name}")
print(f"DATA LAYOUT: {prog.data_layout}")

for func in prog.functions:
    # Functions are weirdly represented as global values in llvmlite,
    # so we need to get their type to access the return/argument types.
    func_type = func.global_value_type
    print(f"Function: {func.name}, "
          f"Return Type: {func_type.get_function_return()}, "
          f"Args: {[str(arg) for arg in func_type.get_function_parameters()]}")
    for block in func.blocks:
        print(f"  Block: {block.name}")
        for instr in block.instructions:
            operands = [f"{value_label(op)}" for op in instr.operands]
            instr_target = value_label(instr)
            has_target = bool(instr.name) or instr_target.startswith('%')
            print(f"\t{instr_target + ' = ' if has_target else ''}"
                  f"{instr.opcode} {', '.join(operands)} ({instr.type})")
