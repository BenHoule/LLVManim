"""Legacy IR text-formatting helpers preserved for reference.

Not used by the current pipeline.  These utilities pre-date the llvmlite-based
ingestion layer (llvm_events.py) and are kept in-tree for context.
"""

import re


def value_label(value):
    if value.name:
        return f"%{value.name}"

    text = str(value).strip()
    # For unnamed values, try to extract a label from the instruction text
    match = re.match(r'^(%[-a-zA-Z$._0-9]+)\s*=.*$', text)
    if match:
        return match.group(1)
    return text


def print_instruction(instr):
    operands = [f"{value_label(op)}" for op in instr.operands]
    instr_target = value_label(instr)
    has_target = bool(instr.name) or instr_target.startswith('%')
    print(f"\t{instr_target + ' = ' if has_target else ''}"
          f"{instr.opcode} {', '.join(operands)} ({instr.type})")


def print_func_sig(func):
    # Functions are weirdly represented as global values in llvmlite,
    # so we need to get their type to access the return/argument types.
    func_type = func.global_value_type  # This shit just isn't in their docs?
    print(f"Function: {func.name}, "
          f"Return Type: {func_type.get_function_return()}, "
          f"Args: {[str(arg) for arg in func_type.get_function_parameters()]}")
