from dataclasses import dataclass
from typing import Any

from src.ast_nodes import (
    ProgramNode, MapNode, MarkerNode, LabelNode, RouteNode,
    CircleNode, RectNode, PolygonNode, LetNode, LayerNode,
    ForNode, IfNode, ExportNode,
)


@dataclass
class TACInstruction:
    op: str
    arg1: Any = None
    arg2: Any = None
    result: Any = None
    line: int = 0

    def __str__(self):
        parts = [self.op]
        if self.arg1 is not None:
            parts.append(str(self.arg1))
        if self.arg2 is not None:
            parts.append(str(self.arg2))
        if self.result is not None:
            parts.append("-> " + str(self.result))
        return " ".join(parts)


class ICGError(Exception):
    pass


class IntermediateCodeGenerator:
    def __init__(self):
        self.instructions: list[TACInstruction] = []
        self.temp_count = 0
        self.label_count = 0

    def generate(self, program: ProgramNode) -> list[TACInstruction]:
        self.instructions = []
        for stmt in program.statements:
            self._emit_node(stmt)
        return self.instructions

    def format(self, instructions: list[TACInstruction]) -> str:
        return "\n".join(f"{i:03}: {inst}" for i, inst in enumerate(instructions))

    def _temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def _emit(self, op, arg1=None, arg2=None, result=None, line=0):
        self.instructions.append(TACInstruction(op, arg1, arg2, result, line))

    def _emit_node(self, node):
        method = "_emit_" + type(node).__name__
        emitter = getattr(self, method, None)
        if not emitter:
            raise ICGError(f"No ICG rule for {type(node).__name__}")
        emitter(node)

    def _emit_MapNode(self, node: MapNode):
        self._emit("MAP", (node.lat, node.lon), node.zoom, node.theme, node.line)

    def _emit_MarkerNode(self, node: MarkerNode):
        self._emit("MARKER", node.label, (node.lat, node.lon), f"{node.color},{node.icon}", node.line)

    def _emit_LabelNode(self, node: LabelNode):
        self._emit("LABEL", node.text, (node.lat, node.lon), f"{node.size},{node.color}", node.line)

    def _emit_RouteNode(self, node: RouteNode):
        self._emit("ROUTE", (node.from_lat, node.from_lon), (node.to_lat, node.to_lon), node.name, node.line)
        self._emit("DISTANCE_KM", (node.from_lat, node.from_lon), (node.to_lat, node.to_lon), f"{node.name}_distance", node.line)
        self._emit("ROUTE_STYLE", node.color, node.style, node.width, node.line)

    def _emit_CircleNode(self, node: CircleNode):
        self._emit("CIRCLE", (node.lat, node.lon), node.radius, f"{node.color},{node.opacity}", node.line)

    def _emit_RectNode(self, node: RectNode):
        self._emit("RECT", (node.lat1, node.lon1), (node.lat2, node.lon2), f"{node.color},{node.opacity}", node.line)

    def _emit_PolygonNode(self, node: PolygonNode):
        self._emit("POLYGON", node.points, None, f"{node.color},{node.opacity}", node.line)

    def _emit_LetNode(self, node: LetNode):
        self._emit("ASSIGN", node.value, None, node.name, node.line)

    def _emit_LayerNode(self, node: LayerNode):
        self._emit("BEGIN_LAYER", node.name, None, None, node.line)
        for stmt in node.body:
            self._emit_node(stmt)
        self._emit("END_LAYER", node.name, None, None, node.line)

    def _emit_ForNode(self, node: ForNode):
        self._emit("FOR_BEGIN", node.iterable, None, node.var, node.line)
        for stmt in node.body:
            self._emit_node(stmt)
        self._emit("FOR_END", node.var, None, None, node.line)

    def _emit_IfNode(self, node: IfNode):
        cond_temp = self._temp()
        end_label = self._label()
        self._emit("CMP", node.left, f"{node.op} {node.right}", cond_temp, node.line)
        self._emit("JUMP_IF_FALSE", cond_temp, None, end_label, node.line)
        for stmt in node.then_body:
            self._emit_node(stmt)
        self._emit("LABEL_TARGET", end_label, None, None, node.line)

    def _emit_ExportNode(self, node: ExportNode):
        self._emit("EXPORT", node.filename, None, None, node.line)
