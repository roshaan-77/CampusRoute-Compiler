from src.icg import TACInstruction


class TargetCodeGenerator:
    def generate(self, instructions: list[TACInstruction]) -> list[str]:
        code: list[str] = []
        for inst in instructions:
            code.extend(self._emit(inst))
        return code

    def format(self, code: list[str]) -> str:
        return "\n".join(f"{i:03}: {line}" for i, line in enumerate(code))

    def _emit(self, inst: TACInstruction) -> list[str]:
        op = inst.op
        if op == "MAP":
            return [f"PUSH_CENTER {inst.arg1}", f"PUSH_ZOOM {inst.arg2}", f"CREATE_MAP {inst.result}"]
        if op == "ASSIGN":
            return [f"LOAD_CONST {inst.arg1}", f"STORE {inst.result}"]
        if op == "MARKER":
            return [f"PUSH_POINT {inst.arg2}", f"PUSH_TEXT {inst.arg1}", f"ADD_MARKER {inst.result}"]
        if op == "LABEL":
            return [f"PUSH_POINT {inst.arg2}", f"PUSH_TEXT {inst.arg1}", f"ADD_LABEL {inst.result}"]
        if op == "ROUTE":
            return [f"PUSH_POINT {inst.arg1}", f"PUSH_POINT {inst.arg2}", f"ADD_ROUTE {inst.result}"]
        if op == "DISTANCE_KM":
            return [f"PUSH_POINT {inst.arg1}", f"PUSH_POINT {inst.arg2}", f"CALC_DISTANCE_KM", f"STORE {inst.result}"]
        if op == "ROUTE_STYLE":
            return [f"SET_ROUTE_STYLE color={inst.arg1} style={inst.arg2} width={inst.result}"]
        if op == "CIRCLE":
            return [f"PUSH_POINT {inst.arg1}", f"PUSH_RADIUS {inst.arg2}", f"ADD_CIRCLE {inst.result}"]
        if op == "RECT":
            return [f"PUSH_POINT {inst.arg1}", f"PUSH_POINT {inst.arg2}", f"ADD_RECT {inst.result}"]
        if op == "POLYGON":
            return [f"PUSH_POINTS {inst.arg1}", f"ADD_POLYGON {inst.result}"]
        if op == "BEGIN_LAYER":
            return [f"BEGIN_LAYER {inst.arg1}"]
        if op == "END_LAYER":
            return [f"END_LAYER {inst.arg1}"]
        if op == "FOR_BEGIN":
            return [f"FOR_EACH {inst.result} IN {inst.arg1}"]
        if op == "FOR_END":
            return [f"END_FOR {inst.arg1}"]
        if op == "CMP":
            return [f"LOAD {inst.arg1}", f"COMPARE {inst.arg2}", f"STORE {inst.result}"]
        if op == "JUMP_IF_FALSE":
            return [f"JUMP_IF_FALSE {inst.arg1} {inst.result}"]
        if op == "LABEL_TARGET":
            return [f"LABEL {inst.arg1}"]
        if op == "EXPORT":
            return [f"EXPORT_HTML {inst.arg1}", "HALT"]
        return [f"NOOP ; unsupported TAC {inst}"]
