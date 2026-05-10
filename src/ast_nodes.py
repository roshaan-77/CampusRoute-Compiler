#AST node definitions.
# Each node = one construct in the language.

from dataclasses import dataclass, field
from typing import Any

#  Base
@dataclass
class ASTNode:
    line: int = 0

#  Top-level program
@dataclass
class ProgramNode(ASTNode):
    statements: list = field(default_factory=list)

#  Map initialization
@dataclass
class MapNode(ASTNode):
    lat: float = 0.0
    lon: float = 0.0
    zoom: int = 10
    theme: str = "light"

#  Marker
@dataclass
class MarkerNode(ASTNode):
    label: str = ""
    lat: float = 0.0
    lon: float = 0.0
    color: str = "blue"
    icon: str = "pin"

#  Label
@dataclass
class LabelNode(ASTNode):
    text: str = ""
    lat: float = 0.0
    lon: float = 0.0
    size: str = "medium"
    color: str = "black"

#  Route
@dataclass
class RouteNode(ASTNode):
    name: str = ""
    from_lat: float = 0.0
    from_lon: float = 0.0
    to_lat: float = 0.0
    to_lon: float = 0.0
    color: str = "blue"
    style: str = "solid"
    width: int = 2
    
#  Shapes
@dataclass
class CircleNode(ASTNode):
    lat: float = 0.0
    lon: float = 0.0
    radius: float = 1000.0      #m
    color: str = "blue"
    opacity: float = 0.4

@dataclass
class RectNode(ASTNode):
    lat1: float = 0.0
    lon1: float = 0.0
    lat2: float = 0.0
    lon2: float = 0.0
    color: str = "blue"
    opacity: float = 0.4

@dataclass
class PolygonNode(ASTNode):
    points: list = field(default_factory=list)   # list of coord tuples
    color: str = "blue"
    opacity: float = 0.4

#  Variable declaration
@dataclass
class LetNode(ASTNode):
    name: str = ""
    value: Any = None           # tuple for coord, str for string, bool/int/float otherwise

#  Layer block
@dataclass
class LayerNode(ASTNode):
    name: str = ""
    body: list = field(default_factory=list)



#  For loop
@dataclass
class ForNode(ASTNode):
    var: str = ""               # loop variable name
    iterable: str = ""          # name of the list variable
    body: list = field(default_factory=list)

#  Conditional
@dataclass
class IfNode(ASTNode):
    left: Any = None            # variable name (str) or literal
    op: str = ""                # ==  !=  >  <  >=  <=
    right: Any = None           # literal value
    then_body: list = field(default_factory=list)

#  Export
@dataclass
class ExportNode(ASTNode):
    filename: str = "output.html"