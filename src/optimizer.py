from src.icg import TACInstruction


class Optimizer:
    def __init__(self):
        self.changes: list[str] = []
        self.constants: dict = {}

    def optimize(self, instructions: list[TACInstruction]) -> list[TACInstruction]:
        self.changes = []
        self.constants = {}
        current = list(instructions)
        current = self._constant_folding(current)
        current = self._copy_propagation(current)
        current = self._dead_code_elimination(current)
        return current

    def format_report(self) -> str:
        if not self.changes:
            return "No optimization changes were needed."
        return "\n".join(f"- {change}" for change in self.changes)

    def _constant_folding(self, instructions):
        optimized = []
        for inst in instructions:
            if inst.op == "MAP":
                self.constants["zoom"] = inst.arg2
            if inst.op == "CMP":
                right_text = str(inst.arg2)
                parts = right_text.split(" ", 1)
                if len(parts) == 2:
                    op, right = parts
                    left_value = self._known_value(inst.arg1)
                    right_value = self._known_value(right)
                    if left_value is not None and right_value is not None:
                        result = self._compare(left_value, op, right_value)
                        optimized.append(TACInstruction("ASSIGN", result, None, inst.result, inst.line))
                        self.changes.append(f"Constant folding: {inst.arg1} {op} {right} became {result}")
                        continue
            optimized.append(inst)
        return optimized

    def _copy_propagation(self, instructions):
        aliases = {}
        optimized = []
        for inst in instructions:
            if inst.op == "ASSIGN" and isinstance(inst.arg1, str) and inst.arg1 in aliases:
                aliases[inst.result] = aliases[inst.arg1]
                optimized.append(TACInstruction(inst.op, aliases[inst.arg1], inst.arg2, inst.result, inst.line))
                self.changes.append(f"Copy propagation: {inst.arg1} replaced with {aliases[inst.arg1]}")
                continue
            if inst.op == "ASSIGN" and isinstance(inst.arg1, str):
                aliases[inst.result] = inst.arg1
            optimized.append(TACInstruction(
                inst.op,
                self._replace_alias(inst.arg1, aliases),
                self._replace_alias(inst.arg2, aliases),
                inst.result,
                inst.line,
            ))
        return optimized

    def _dead_code_elimination(self, instructions):
        optimized = []
        skip_until = None
        removed = 0
        values = {}

        for inst in instructions:
            if inst.op == "ASSIGN":
                values[inst.result] = inst.arg1

            if skip_until:
                if inst.op == "LABEL_TARGET" and inst.arg1 == skip_until:
                    skip_until = None
                    continue
                removed += 1
                continue

            if inst.op == "JUMP_IF_FALSE" and values.get(inst.arg1) is False:
                skip_until = inst.result
                removed += 1
                continue
            if inst.op == "JUMP_IF_FALSE" and values.get(inst.arg1) is True:
                removed += 1
                continue
            if inst.op == "LABEL_TARGET":
                continue
            optimized.append(inst)

        if removed:
            self.changes.append(f"Dead code elimination: removed {removed} unreachable/control instructions")
        return optimized

    def _replace_alias(self, value, aliases):
        if isinstance(value, str) and value in aliases:
            self.changes.append(f"Copy propagation: {value} replaced with {aliases[value]}")
            return aliases[value]
        if isinstance(value, tuple):
            replaced = tuple(aliases.get(item, item) for item in value)
            if replaced != value:
                self.changes.append(f"Copy propagation: {value} replaced with {replaced}")
            return replaced
        return value

    def _known_value(self, value):
        if value in self.constants:
            return self.constants[value]
        if isinstance(value, bool):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _compare(self, left, op, right):
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        return False
