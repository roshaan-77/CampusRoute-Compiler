# Walks the validated AST and directly executes folium API calls,
# result saved in html file
# Each AST node maps to one or more folium operations

import os
import math
import folium
from branca.element import Element
from src.ast_nodes import (
    ProgramNode, MapNode, MarkerNode, LabelNode, RouteNode,
    CircleNode, RectNode, PolygonNode, LetNode, LayerNode,
    ForNode, IfNode, ExportNode,
)

#  Icon mapping  (language icon → folium icon)
ICON_MAP = {
    "pin":      ("map-marker", "fa"),
    "dot":      ("circle",     "fa"),
    "star":     ("star",       "fa"),
    "plane":    ("plane",      "fa"),
    "hospital": ("plus-square","fa"),
    "school":   ("graduation-cap", "fa"),
}

# Label font sizes
LABEL_SIZE = {
    "small":  "11px",
    "medium": "14px",
    "large":  "18px",
}

# Folium named tile providers — these correctly configure subdomains, attribution,
TILE_THEMES = {
    "light":     "CartoDB positron",
    "dark":      "CartoDB dark_matter",
    "satellite": "CartoDB positron",
}

class CodeGenError(Exception):
    pass

class CodeGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self._map: folium.Map | None = None
        self._symbol_table: dict     = {}
        self._export_filename: str   = "output.html"
        self._zoom: int              = 10
        self._campus_labels: list[str] = []
        self._route_summaries: list[dict] = []
    
    #  Public entry
    def generate(self, program: ProgramNode) -> str:
        #Walk AST, build map, Returns output.
        for stmt in program.statements:
            self._visit(stmt)

        if self._map is None:
            raise CodeGenError("No map was initialised — cannot generate output.")

        self._add_interface()
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, self._export_filename)
        self._map.save(out_path)
        return out_path


    #  Visitor dispatch
    def _visit(self, node, extra_context: dict | None = None):
        method = "_emit_" + type(node).__name__
        emitter = getattr(self, method, None)
        if emitter:
            emitter(node, extra_context or {})


    #  Emitters
    def _emit_MapNode(self, node: MapNode, ctx: dict):
        tiles = TILE_THEMES.get(node.theme, TILE_THEMES["light"])
        self._zoom = node.zoom
        self._map = folium.Map(
            location=[node.lat, node.lon],
            zoom_start=node.zoom,
            tiles=tiles,
        )

    def _emit_MarkerNode(self, node: MarkerNode, ctx: dict):
        lat, lon = self._resolve(node.lat, node.lon, ctx)
        icon_name, prefix = ICON_MAP.get(node.icon, ("map-marker", "fa"))
        if "FAST NUCES" in node.label and node.label not in self._campus_labels:
            self._campus_labels.append(node.label)
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(node.label, max_width=200),
            tooltip=node.label,
            icon=folium.Icon(color=self._folium_color(node.color),
                             icon=icon_name, prefix=prefix),
        ).add_to(self._target(ctx))

    def _emit_LabelNode(self, node: LabelNode, ctx: dict):
        lat, lon = self._resolve(node.lat, node.lon, ctx)
        size = LABEL_SIZE.get(node.size, "14px")
        html = (
            f'<div style="font-size:{size};color:{node.color};'
            f'font-weight:bold;white-space:nowrap;">{node.text}</div>'
        )
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=html, icon_size=(150, 36), icon_anchor=(0, 0)),
        ).add_to(self._target(ctx))

    def _emit_RouteNode(self, node: RouteNode, ctx: dict):
        flat, flon = self._resolve(node.from_lat, node.from_lon, ctx)
        tlat, tlon = self._resolve(node.to_lat,   node.to_lon,   ctx)
        dash = "10 10" if node.style == "dashed" else ("5 5" if node.style == "dotted" else None)
        distance_km = self._distance_km(flat, flon, tlat, tlon)
        self._route_summaries.append({"name": node.name, "distance": distance_km})
        line = folium.PolyLine(
            locations=[[flat, flon], [tlat, tlon]],
            color=node.color,
            weight=node.width,
            opacity=0.8,
            tooltip=f"{node.name} - {distance_km:.2f} km",
            dash_array=dash,
        )
        line.add_to(self._target(ctx))

    def _emit_CircleNode(self, node: CircleNode, ctx: dict):
        lat, lon = self._resolve(node.lat, node.lon, ctx)
        folium.Circle(
            location=[lat, lon],
            radius=node.radius,
            color=node.color,
            fill=True,
            fill_color=node.color,
            fill_opacity=node.opacity,
        ).add_to(self._target(ctx))

    def _emit_RectNode(self, node: RectNode, ctx: dict):
        lat1, lon1 = self._resolve(node.lat1, node.lon1, ctx)
        lat2, lon2 = self._resolve(node.lat2, node.lon2, ctx)
        folium.Rectangle(
            bounds=[[lat1, lon1], [lat2, lon2]],
            color=node.color,
            fill=True,
            fill_color=node.color,
            fill_opacity=node.opacity,
        ).add_to(self._target(ctx))

    def _emit_PolygonNode(self, node: PolygonNode, ctx: dict):
        folium.Polygon(
            locations=[[lat, lon] for lat, lon in node.points],
            color=node.color,
            fill=True,
            fill_color=node.color,
            fill_opacity=node.opacity,
        ).add_to(self._target(ctx))

    def _emit_LetNode(self, node: LetNode, ctx: dict):
        value = node.value
        if isinstance(value, str) and value in self._symbol_table:
            value = self._symbol_table[value]
        self._symbol_table[node.name] = value

    def _emit_LayerNode(self, node: LayerNode, ctx: dict):
        feature_group = folium.FeatureGroup(name=node.name, show=True)
        layer_ctx = {"layer": feature_group}
        for stmt in node.body:
            self._visit(stmt, layer_ctx)
        feature_group.add_to(self._map)

    def _emit_ForNode(self, node: ForNode, ctx: dict):
        iterable = self._symbol_table.get(node.iterable, [])
        if not isinstance(iterable, list):
            return
        for item in iterable:
            self._symbol_table[node.var] = item
            for stmt in node.body:
                self._visit(stmt, ctx)
        self._symbol_table.pop(node.var, None)

    def _emit_IfNode(self, node: IfNode, ctx: dict):
        left  = self._eval_value(node.left,  ctx)
        right = self._eval_value(node.right, ctx)
        if self._compare(left, node.op, right):
            for stmt in node.then_body:
                self._visit(stmt, ctx)

    def _emit_ExportNode(self, node: ExportNode, ctx: dict):
        self._export_filename = node.filename
        folium.LayerControl(collapsed=False).add_to(self._map)


    #  Helpers
    def _target(self, ctx: dict):
        #return  active layer FeatureGroup or map
        return ctx.get("layer", self._map)

    def _resolve(self, lat, lon, ctx: dict):
        #Resolve lat/lon — if lat is a string var name, look it up
        if isinstance(lat, str) or lon is None:
            var_name = lat
            val = self._symbol_table.get(var_name)
            seen = set()
            while isinstance(val, str) and val in self._symbol_table and val not in seen:
                seen.add(val)
                val = self._symbol_table[val]
            if isinstance(val, tuple):
                return val
            raise CodeGenError(f"Cannot resolve coordinate variable '{var_name}'")
        return (lat, lon)

    def _eval_value(self, val, ctx: dict):
        #Return the concrete value of a literal or variable reference.
        if isinstance(val, str):
            if val == "zoom":
                return self._zoom
            return self._symbol_table.get(val, val)
        return val

    def _compare(self, left, op: str, right) -> bool:
        try:
            if op == "==":  return left == right
            if op == "!=":  return left != right
            if op == ">":   return left >  right
            if op == "<":   return left <  right
            if op == ">=":  return left >= right
            if op == "<=":  return left <= right
        except TypeError:
            return False
        return False

    def _folium_color(self, color: str) -> str:
        #Map common color names to folium-accepted color names
        folium_colors = {
            "red", "blue", "green", "purple", "orange", "darkred",
            "lightred", "beige", "darkblue", "darkgreen", "cadetblue",
            "darkpurple", "white", "pink", "lightblue", "lightgreen",
            "gray", "black", "lightgray",
        }
        return color if color in folium_colors else "blue"

    def _distance_km(self, lat1, lon1, lat2, lon2):
        radius = 6371.0
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _add_interface(self):
        if self._map is None:
            return
        route = self._route_summaries[0] if self._route_summaries else {"distance": 0.0}
        start = self._campus_labels[0] if len(self._campus_labels) > 0 else "FAST NUCES Karachi Main Campus"
        end = self._campus_labels[1] if len(self._campus_labels) > 1 else "FAST NUCES Karachi City Campus"
        html = f"""
<style>
    .campusroute-panel {{
        position: fixed;
        top: 18px;
        left: 58px;
        z-index: 9999;
        width: 360px;
        max-width: calc(100vw - 92px);
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(15, 23, 42, 0.14);
        border-radius: 8px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
        font-family: Arial, Helvetica, sans-serif;
        color: #172033;
        overflow: hidden;
    }}
    .campusroute-head {{
        padding: 14px 16px 12px;
        background: #12355b;
        color: white;
    }}
    .campusroute-title {{
        font-size: 18px;
        font-weight: 700;
        margin: 0 0 4px;
    }}
    .campusroute-subtitle {{
        font-size: 12px;
        opacity: 0.88;
        margin: 0;
    }}
    .campusroute-body {{
        padding: 14px 16px 16px;
    }}
    .campusroute-distance {{
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 10px;
    }}
    .campusroute-distance strong {{
        font-size: 30px;
        color: #0f766e;
    }}
    .campusroute-distance span {{
        font-size: 13px;
        color: #475569;
    }}
    .campusroute-route {{
        font-size: 13px;
        line-height: 1.45;
        margin: 0 0 12px;
    }}
    .campusroute-route b {{
        color: #0f172a;
    }}
    .campusroute-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }}
    .campusroute-chip {{
        font-size: 12px;
        padding: 6px 8px;
        border-radius: 999px;
        background: #eef2ff;
        color: #1e3a8a;
        border: 1px solid #dbe4ff;
    }}
    @media (max-width: 640px) {{
        .campusroute-panel {{
            left: 12px;
            right: 12px;
            top: 12px;
            width: auto;
            max-width: none;
        }}
        .campusroute-distance strong {{
            font-size: 24px;
        }}
    }}
</style>
<div class="campusroute-panel">
    <div class="campusroute-head">
        <p class="campusroute-title">FAST Campus Distance Map</p>
        <p class="campusroute-subtitle">Generated by the CampusRoute compiler</p>
    </div>
    <div class="campusroute-body">
        <div class="campusroute-distance">
            <strong>{route["distance"]:.2f}</strong>
            <span>km approximate straight-line distance</span>
        </div>
        <p class="campusroute-route"><b>From:</b> {start}<br><b>To:</b> {end}</p>
        <div class="campusroute-chips">
            <span class="campusroute-chip">Blue: Main Campus</span>
            <span class="campusroute-chip">Red: City Campus</span>
            <span class="campusroute-chip">Orange: Route</span>
        </div>
    </div>
</div>
"""
        self._map.get_root().html.add_child(Element(html))
