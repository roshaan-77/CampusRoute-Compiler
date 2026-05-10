from src.ast_nodes import (
    ProgramNode, MapNode, MarkerNode, LabelNode, RouteNode,
    CircleNode, RectNode, PolygonNode, LetNode, LayerNode,
    ForNode, IfNode, ExportNode,
)


NAMED_COLORS = {
    "red", "blue", "green", "orange", "purple", "yellow",
    "black", "white", "gray", "grey", "pink", "brown",
    "cyan", "magenta", "lime", "navy", "teal", "maroon",
    "steelblue", "darkgreen", "darkred",
}

VALID_THEMES = {"light", "dark", "satellite"}
VALID_SIZES = {"small", "medium", "large"}
VALID_STYLES = {"solid", "dashed", "dotted"}
VALID_ICONS = {"pin", "dot", "star", "plane", "hospital", "school"}


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table: dict = {}
        self.type_table: dict = {}
        self.scope_table: dict = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self._layer_names: set = set()
        self._zoom: int = 10

    def analyse(self, program: ProgramNode):
        self._check_map_and_export_present(program)
        for stmt in program.statements:
            self._visit(stmt)
        if self.errors:
            raise SemanticError("\n".join(self.errors))

    def _check_map_and_export_present(self, program: ProgramNode):
        types = [type(s).__name__ for s in program.statements]
        if "MapNode" not in types:
            self.errors.append("[Semantic Error] No 'map' declaration found - every CampusRoute program must start with a map statement.")
        elif types[0] != "MapNode":
            self.errors.append("[Semantic Error] 'map' declaration must be the first statement in the program.")
        if "ExportNode" not in types:
            self.errors.append("[Semantic Error] No 'export' declaration found - program must end with an export statement.")

    def _visit(self, node):
        method = "_visit_" + type(node).__name__
        visitor = getattr(self, method, self._generic_visit)
        visitor(node)

    def _generic_visit(self, node):
        pass

    def _visit_MapNode(self, node: MapNode):
        self._zoom = node.zoom
        self._check_coord(node.lat, node.lon, node.line)
        if not (1 <= node.zoom <= 18):
            self.errors.append(f"[Semantic Error] Line {node.line}: zoom={node.zoom} is invalid - zoom must be between 1 and 18.")
        if node.theme not in VALID_THEMES:
            self.warnings.append(f"[Semantic Warning] Line {node.line}: theme='{node.theme}' not recognised - defaulting to 'light'.")

    def _visit_MarkerNode(self, node: MarkerNode):
        lat, lon = self._resolve_coord(node.lat, node.lon, node.line)
        self._check_coord(lat, lon, node.line)
        self._check_color(node.color, node.line)
        if node.icon not in VALID_ICONS:
            self.warnings.append(f"[Semantic Warning] Line {node.line}: icon='{node.icon}' not recognised - defaulting to 'pin'.")

    def _visit_LabelNode(self, node: LabelNode):
        lat, lon = self._resolve_coord(node.lat, node.lon, node.line)
        self._check_coord(lat, lon, node.line)
        self._check_color(node.color, node.line)
        if node.size not in VALID_SIZES:
            self.warnings.append(f"[Semantic Warning] Line {node.line}: size='{node.size}' not recognised - defaulting to 'medium'.")

    def _visit_RouteNode(self, node: RouteNode):
        flat, flon = self._resolve_coord(node.from_lat, node.from_lon, node.line)
        tlat, tlon = self._resolve_coord(node.to_lat, node.to_lon, node.line)
        self._check_coord(flat, flon, node.line)
        self._check_coord(tlat, tlon, node.line)
        self._check_color(node.color, node.line)
        if node.style not in VALID_STYLES:
            self.warnings.append(f"[Semantic Warning] Line {node.line}: style='{node.style}' not recognised - defaulting to 'solid'.")
        if node.width < 1:
            self.errors.append(f"[Semantic Error] Line {node.line}: route width must be >= 1, got {node.width}.")

    def _visit_CircleNode(self, node: CircleNode):
        lat, lon = self._resolve_coord(node.lat, node.lon, node.line)
        self._check_coord(lat, lon, node.line)
        self._check_color(node.color, node.line)
        self._check_opacity(node.opacity, node.line)
        if node.radius <= 0:
            self.errors.append(f"[Semantic Error] Line {node.line}: circle radius must be > 0, got {node.radius}.")

    def _visit_RectNode(self, node: RectNode):
        lat1, lon1 = self._resolve_coord(node.lat1, node.lon1, node.line)
        lat2, lon2 = self._resolve_coord(node.lat2, node.lon2, node.line)
        self._check_coord(lat1, lon1, node.line)
        self._check_coord(lat2, lon2, node.line)
        self._check_color(node.color, node.line)
        self._check_opacity(node.opacity, node.line)

    def _visit_PolygonNode(self, node: PolygonNode):
        if len(node.points) < 3:
            self.errors.append(f"[Semantic Error] Line {node.line}: polygon requires at least 3 points, got {len(node.points)}.")
        for lat, lon in node.points:
            self._check_coord(lat, lon, node.line)
        self._check_color(node.color, node.line)
        self._check_opacity(node.opacity, node.line)

    def _visit_LetNode(self, node: LetNode):
        if node.name in self.symbol_table:
            self.warnings.append(f"[Semantic Warning] Line {node.line}: variable '{node.name}' is already declared - it will be overwritten.")
        if isinstance(node.value, tuple):
            self._check_coord(node.value[0], node.value[1], node.line)
        if isinstance(node.value, list):
            for item in node.value:
                if isinstance(item, tuple):
                    self._check_coord(item[0], item[1], node.line)
        if isinstance(node.value, str) and node.value in self.symbol_table:
            resolved = self._resolve_value(node.value)
            self.type_table[node.name] = self._infer_type(resolved)
        else:
            self.type_table[node.name] = self._infer_type(node.value)
        self.symbol_table[node.name] = node.value
        self.scope_table[node.name] = "global"

    def _visit_LayerNode(self, node: LayerNode):
        if node.name in self._layer_names:
            self.errors.append(f"[Semantic Error] Line {node.line}: duplicate layer name '{node.name}'.")
        self._layer_names.add(node.name)
        for stmt in node.body:
            self._visit(stmt)

    def _visit_ForNode(self, node: ForNode):
        if node.iterable not in self.symbol_table:
            self.errors.append(f"[Semantic Error] Line {node.line}: undefined variable '{node.iterable}' used in for loop.")
            return
        iterable_val = self._resolve_value(node.iterable)
        if not isinstance(iterable_val, list):
            self.errors.append(f"[Semantic Error] Line {node.line}: variable '{node.iterable}' is not a list - cannot iterate over it.")
            return
        if iterable_val:
            self.symbol_table[node.var] = iterable_val[0]
            self.type_table[node.var] = self._infer_type(iterable_val[0])
            self.scope_table[node.var] = f"for:{node.iterable}"
        for stmt in node.body:
            self._visit(stmt)
        self.symbol_table.pop(node.var, None)
        self.type_table.pop(node.var, None)
        self.scope_table.pop(node.var, None)

    def _visit_IfNode(self, node: IfNode):
        left = node.left
        if isinstance(left, str) and left != "zoom" and left not in self.symbol_table:
            self.errors.append(f"[Semantic Error] Line {node.line}: undefined variable '{left}' used in if condition.")
            return
        for stmt in node.then_body:
            self._visit(stmt)

    def _visit_ExportNode(self, node: ExportNode):
        if not node.filename.endswith((".html", ".png")):
            self.warnings.append(f"[Semantic Warning] Line {node.line}: export filename '{node.filename}' does not end in .html or .png.")

    def _resolve_value(self, name):
        value = self.symbol_table.get(name)
        seen = set()
        while isinstance(value, str) and value in self.symbol_table and value not in seen:
            seen.add(value)
            value = self.symbol_table[value]
        return value

    def _resolve_coord(self, lat, lon, line: int):
        if isinstance(lat, str):
            if lat not in self.symbol_table:
                self.errors.append(f"[Semantic Error] Line {line}: undefined variable '{lat}'.")
                return (0.0, 0.0)
            val = self._resolve_value(lat)
            if not isinstance(val, tuple):
                self.errors.append(f"[Semantic Error] Line {line}: variable '{lat}' is not a coordinate.")
                return (0.0, 0.0)
            return val
        return (lat, lon)

    def _check_coord(self, lat, lon, line: int):
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return
        if not (-90 <= lat <= 90):
            self.errors.append(f"[Semantic Error] Line {line}: latitude {lat} is out of range - must be between -90 and 90.")
        if not (-180 <= lon <= 180):
            self.errors.append(f"[Semantic Error] Line {line}: longitude {lon} is out of range - must be between -180 and 180.")

    def _check_color(self, color: str, line: int):
        if color.startswith("#"):
            if not (len(color) in (4, 7) and all(c in "0123456789abcdefABCDEF" for c in color[1:])):
                self.warnings.append(f"[Semantic Warning] Line {line}: '{color}' does not look like a valid hex color - defaulting to blue.")
        elif color not in NAMED_COLORS:
            self.warnings.append(f"[Semantic Warning] Line {line}: color '{color}' not recognised - defaulting to blue.")

    def _check_opacity(self, opacity: float, line: int):
        if not (0.0 <= opacity <= 1.0):
            self.errors.append(f"[Semantic Error] Line {line}: opacity {opacity} is out of range - must be between 0.0 and 1.0.")

    def _infer_type(self, value):
        if isinstance(value, tuple):
            return "coordinate"
        if isinstance(value, list):
            return "list"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        return "unknown"
