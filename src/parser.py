# Recursive-descent parser
from src.lexer import Token, TT
from src.ast_nodes import (
    ProgramNode, MapNode, MarkerNode, LabelNode, RouteNode,
    CircleNode, RectNode, PolygonNode, LetNode, LayerNode,
    ForNode, IfNode, ExportNode,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    
    #  Helpers

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TT.EOF:
            self.pos += 1
        return tok

    def check(self, *types) -> bool:
        return self.peek().type in types

    def match(self, *types) -> bool:
        if self.check(*types):
            self.advance()
            return True
        return False

    def expect(self, ttype: str, msg: str = "") -> Token:
        if self.peek().type == ttype:
            return self.advance()
        tok = self.peek()
        hint = msg or f"expected {ttype}"
        raise ParseError(
            f"[Parse Error] Line {tok.line}: {hint} — got {tok.type} ({tok.value!r})"
        )

    def error(self, msg: str):
        tok = self.peek()
        raise ParseError(f"[Parse Error] Line {tok.line}: {msg}")

    def current_line(self) -> int:
        return self.peek().line

    
    #  Entry point

    def parse(self) -> ProgramNode:
        stmts = []
        while not self.check(TT.EOF):
            stmts.append(self._statement())
        return ProgramNode(statements=stmts)

    
    #  Statement dispatcher

    def _statement(self):
        tok = self.peek()

        if tok.type == TT.MAP:      return self._map()
        if tok.type == TT.MARKER:   return self._marker()
        if tok.type == TT.LABEL:    return self._label()
        if tok.type == TT.ROUTE:    return self._route()
        if tok.type == TT.CIRCLE:   return self._circle()
        if tok.type == TT.RECT:     return self._rect()
        if tok.type == TT.POLYGON:  return self._polygon()
        if tok.type == TT.LET:      return self._let()
        if tok.type == TT.LAYER:    return self._layer()
        if tok.type == TT.FOR:      return self._for()
        if tok.type == TT.IF:       return self._if()
        if tok.type == TT.EXPORT:   return self._export()

        self.error(f"Unexpected token '{tok.value}' — not a valid statement start")

    
    #  map center=(lat,lon) zoom=N theme=T
    def _map(self) -> MapNode:
        line = self.current_line()
        self.expect(TT.MAP)
        node = MapNode(line=line)

        while not self.check(TT.EOF) and self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "center":
                node.lat, node.lon = self._coord()
            elif key == "zoom":
                node.zoom = int(self.expect(TT.NUMBER).value)
            elif key == "theme":
                node.theme = self._ident_or_string()
            else:
                self.error(f"Unknown map attribute: '{key}'")

        return node

    
    #  marker "Name" at COORD color=X icon=Y
    def _marker(self) -> MarkerNode:
        line = self.current_line()
        self.expect(TT.MARKER)
        label = self.expect(TT.STRING, "expected marker label string").value
        self.expect(TT.AT)
        coord = self._coord_or_var()          # tuple (lat,lon) or string var name
        node = MarkerNode(line=line, label=label)
        self._apply_coord(node, coord)

        while self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "color":  node.color = self._ident_or_string()
            elif key == "icon": node.icon  = self._ident_or_string()
            else: self.error(f"Unknown marker attribute: '{key}'")

        return node

    
    #  label "Text" at COORD size=X color=Y
    def _label(self) -> LabelNode:
        line = self.current_line()
        self.expect(TT.LABEL)
        text = self.expect(TT.STRING, "expected label text string").value
        self.expect(TT.AT)
        coord = self._coord_or_var()
        node = LabelNode(line=line, text=text)
        self._apply_coord(node, coord)

        while self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "size":    node.size  = self._ident_or_string()
            elif key == "color": node.color = self._ident_or_string()
            else: self.error(f"Unknown label attribute: '{key}'")

        return node

    
    #  route "Name"
    #      from COORD to COORD
    #      color=X style=Y width=N
    #  end
    def _route(self) -> RouteNode:
        line = self.current_line()
        self.expect(TT.ROUTE)
        name = self.expect(TT.STRING, "expected route name string").value
        node = RouteNode(line=line, name=name)

        self.expect(TT.FROM)
        fc = self._coord_or_var()
        self._apply_coord_from(node, fc)

        self.expect(TT.TO)
        tc = self._coord_or_var()
        self._apply_coord_to(node, tc)

        while self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "color":   node.color = self._ident_or_string()
            elif key == "style": node.style = self._ident_or_string()
            elif key == "width": node.width = int(self.expect(TT.NUMBER).value)
            else: self.error(f"Unknown route attribute: '{key}'")

        self.expect(TT.END)
        return node

    
    #  circle at COORD radius=Xkm ...
    def _circle(self) -> CircleNode:
        line = self.current_line()
        self.expect(TT.CIRCLE)
        self.expect(TT.AT)
        coord = self._coord_or_var()
        node = CircleNode(line=line)
        self._apply_coord(node, coord)

        # parse attributes: radius, color, opacity
        # radius can be introduced by the RADIUS keyword token OR as an ident attr
        while True:
            if self.check(TT.RADIUS):
                self.advance()
                self.expect(TT.EQUALS)
                node.radius = self.expect(TT.NUMBER).value
            elif self._is_attr():
                key = self.advance().value
                self.expect(TT.EQUALS)
                if key == "color":    node.color   = self._ident_or_string()
                elif key == "opacity":node.opacity = self.expect(TT.NUMBER).value
                else: self.error(f"Unknown circle attribute: '{key}'")
            else:
                break

        return node

    
    #  rect from COORD to COORD ...
    
    def _rect(self) -> RectNode:
        line = self.current_line()
        self.expect(TT.RECT)
        self.expect(TT.FROM)
        c1 = self._coord_or_var()
        self.expect(TT.TO)
        c2 = self._coord_or_var()
        node = RectNode(line=line)
        # store as separate fields
        if isinstance(c1, str):
            node.lat1 = c1; node.lon1 = None
        else:
            node.lat1, node.lon1 = c1
        if isinstance(c2, str):
            node.lat2 = c2; node.lon2 = None
        else:
            node.lat2, node.lon2 = c2

        while self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "color":    node.color   = self._ident_or_string()
            elif key == "opacity":node.opacity = self.expect(TT.NUMBER).value
            else: self.error(f"Unknown rect attribute: '{key}'")

        return node

    
    #  polygon [COORD, ...] ...
    def _polygon(self) -> PolygonNode:
        line = self.current_line()
        self.expect(TT.POLYGON)
        self.expect(TT.LBRACKET)
        points = []
        while not self.check(TT.RBRACKET):
            points.append(self._coord())
            if not self.match(TT.COMMA):
                break
        self.expect(TT.RBRACKET)
        node = PolygonNode(line=line, points=points)

        while self._is_attr():
            key = self.advance().value
            self.expect(TT.EQUALS)
            if key == "color":    node.color   = self._ident_or_string()
            elif key == "opacity":node.opacity = self.expect(TT.NUMBER).value
            else: self.error(f"Unknown polygon attribute: '{key}'")

        return node

    #  let name = value
    def _let(self) -> LetNode:
        line = self.current_line()
        self.expect(TT.LET)
        name = self.expect(TT.IDENT, "expected variable name").value
        self.expect(TT.EQUALS)

        if self.check(TT.LPAREN):
            value = self._coord()
        elif self.check(TT.STRING):
            value = self.advance().value
        elif self.check(TT.BOOL):
            value = self.advance().value
        elif self.check(TT.NUMBER):
            value = self.advance().value
        elif self.check(TT.IDENT):
            value = self.advance().value
        elif self.check(TT.LBRACKET):
            self.advance()
            value = []
            while not self.check(TT.RBRACKET):
                value.append(self._coord())
                if not self.match(TT.COMMA):
                    break
            self.expect(TT.RBRACKET)
        else:
            self.error("Invalid value in let declaration")

        return LetNode(line=line, name=name, value=value)

    
    #  layer "Name" ... end

    def _layer(self) -> LayerNode:
        line = self.current_line()
        self.expect(TT.LAYER)
        name = self.expect(TT.STRING, "expected layer name string").value
        body = []
        while not self.check(TT.END) and not self.check(TT.EOF):
            body.append(self._statement())
        self.expect(TT.END)
        return LayerNode(line=line, name=name, body=body)

    
    #  for var in list ... end
    def _for(self) -> ForNode:
        line = self.current_line()
        self.expect(TT.FOR)
        var = self.expect(TT.IDENT, "expected loop variable name").value
        self.expect(TT.IN)
        iterable = self.expect(TT.IDENT, "expected iterable variable name").value
        body = []
        while not self.check(TT.END) and not self.check(TT.EOF):
            body.append(self._statement())
        self.expect(TT.END)
        return ForNode(line=line, var=var, iterable=iterable, body=body)

    
    #  if left op right then ... end
    def _if(self) -> IfNode:
        line = self.current_line()
        self.expect(TT.IF)
        left = self._value_or_ident()
        op_tok = self.advance()
        if op_tok.type not in (TT.EQ, TT.NEQ, TT.GT, TT.LT, TT.GTE, TT.LTE):
            raise ParseError(
                f"[Parse Error] Line {op_tok.line}: expected comparison operator, "
                f"got {op_tok.type} ({op_tok.value!r})"
            )
        op = op_tok.value
        right = self._value_or_ident()
        self.expect(TT.THEN)
        body = []
        while not self.check(TT.END) and not self.check(TT.EOF):
            body.append(self._statement())
        self.expect(TT.END)
        return IfNode(line=line, left=left, op=op, right=right, then_body=body)

    
    #  export as "filename"
    def _export(self) -> ExportNode:
        line = self.current_line()
        self.expect(TT.EXPORT)
        self.expect(TT.AS)
        filename = self.expect(TT.STRING, "expected export filename string").value
        return ExportNode(line=line, filename=filename)

    
    #  Coordinate helpers
    def _coord(self) -> tuple:
        # """Parse (lat, lon) coordinate. Returns (float, float)
        self.expect(TT.LPAREN)
        lat = self.expect(TT.NUMBER, "expected latitude number").value
        self.expect(TT.COMMA)
        lon = self.expect(TT.NUMBER, "expected longitude number").value
        self.expect(TT.RPAREN)
        return (lat, lon)

    def _coord_or_var(self):
        # """Parse literal coord or variable name.
        # Returns (float, float) tuple OR str variable name."""
        if self.check(TT.LPAREN):
            return self._coord()
        elif self.check(TT.IDENT):
            return self.advance().value    # just the string name
        else:
            self.error("expected coordinate (lat, lon) or variable name")

    def _apply_coord(self, node, coord):
        # """Store coord (tuple or var name) into node.lat / node.lon."""
        if isinstance(coord, str):
            node.lat = coord    # var name stored in lat; lon stays 0.0 as sentinel
            node.lon = None     # None signals "variable reference"
        else:
            node.lat, node.lon = coord

    def _apply_coord_from(self, node, coord):
        if isinstance(coord, str):
            node.from_lat = coord
            node.from_lon = None
        else:
            node.from_lat, node.from_lon = coord

    def _apply_coord_to(self, node, coord):
        if isinstance(coord, str):
            node.to_lat = coord
            node.to_lon = None
        else:
            node.to_lat, node.to_lon = coord

    def _ident_or_string(self) -> str:
        if self.check(TT.IDENT):
            return self.advance().value
        elif self.check(TT.STRING):
            return self.advance().value
        else:
            self.error("expected identifier or string value")

    def _value_or_ident(self):
        if self.check(TT.NUMBER):  return self.advance().value
        if self.check(TT.STRING):  return self.advance().value
        if self.check(TT.BOOL):    return self.advance().value
        if self.check(TT.IDENT):   return self.advance().value
        self.error("expected value or variable name")

    def _is_attr(self) -> bool:
        # """True if next two tokens look like  ident =  (attribute assignment)."""
        return (
            self.peek().type == TT.IDENT
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].type == TT.EQUALS
        )
