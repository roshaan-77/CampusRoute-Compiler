# test cases

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.lexer    import Lexer, LexerError, TT
from src.parser   import Parser, ParseError
from src.semantic import SemanticAnalyzer, SemanticError
from src.icg import IntermediateCodeGenerator
from src.optimizer import Optimizer
from src.target_codegen import TargetCodeGenerator
from src.ast_nodes import (
    MapNode, MarkerNode, LabelNode, RouteNode,
    CircleNode, LetNode, LayerNode, ForNode, IfNode, ExportNode,
)

#  Helpers

def lex(src):
    return Lexer(src).tokenize()

def parse(src):
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse()

def analyse(src):
    program = parse(src)
    sa = SemanticAnalyzer()
    sa.analyse(program)
    return sa


MINIMAL = """
map center=(24.8607, 67.0011) zoom=10
export as "out.html"
"""



#  LEXER TESTS
class TestLexer:

    def test_keywords_recognized(self):
        tokens = lex("map marker label route circle rect polygon let layer for in if then end export as at from to radius")
        types = [t.type for t in tokens if t.type != TT.EOF]
        assert TT.MAP      in types
        assert TT.MARKER   in types
        assert TT.LABEL    in types
        assert TT.ROUTE    in types
        assert TT.CIRCLE   in types
        assert TT.RECT     in types
        assert TT.POLYGON  in types
        assert TT.LET      in types
        assert TT.LAYER    in types
        assert TT.FOR      in types
        assert TT.IN       in types
        assert TT.IF       in types
        assert TT.THEN     in types
        assert TT.END      in types
        assert TT.EXPORT   in types
        assert TT.AS       in types

    def test_string_literal(self):
        tokens = lex('"Hello World"')
        assert tokens[0].type  == TT.STRING
        assert tokens[0].value == "Hello World"

    def test_number_integer(self):
        tokens = lex("42")
        assert tokens[0].type  == TT.NUMBER
        assert tokens[0].value == 42.0

    def test_number_float(self):
        tokens = lex("3.14")
        assert tokens[0].type  == TT.NUMBER
        assert tokens[0].value == pytest.approx(3.14)

    def test_unit_km_converts_to_metres(self):
        tokens = lex("5km")
        assert tokens[0].type  == TT.NUMBER
        assert tokens[0].value == pytest.approx(5000.0)

    def test_unit_m_stays_metres(self):
        tokens = lex("500m")
        assert tokens[0].type  == TT.NUMBER
        assert tokens[0].value == pytest.approx(500.0)

    def test_bool_true(self):
        tokens = lex("true")
        assert tokens[0].type  == TT.BOOL
        assert tokens[0].value == True

    def test_bool_false(self):
        tokens = lex("false")
        assert tokens[0].type  == TT.BOOL
        assert tokens[0].value == False

    def test_operators(self):
        tokens = lex("== != >= <= > <")
        types = [t.type for t in tokens if t.type != TT.EOF]
        assert types == [TT.EQ, TT.NEQ, TT.GTE, TT.LTE, TT.GT, TT.LT]

    def test_comment_ignored(self):
        tokens = lex("// this is a comment\nmap")
        assert tokens[0].type == TT.MAP

    def test_ident(self):
        tokens = lex("myVariable")
        assert tokens[0].type  == TT.IDENT
        assert tokens[0].value == "myVariable"

    def test_unknown_char_raises(self):
        with pytest.raises(LexerError):
            lex("@@@")

    def test_unterminated_string_raises(self):
        with pytest.raises(LexerError):
            lex('"unterminated')

    def test_line_tracking(self):
        tokens = lex("map\nmarker")
        assert tokens[0].line == 1
        assert tokens[1].line == 2



#  PARSER TESTS


class TestParser:

    def test_parse_map(self):
        prog = parse("map center=(24.86, 67.00) zoom=10\nexport as \"out.html\"")
        assert isinstance(prog.statements[0], MapNode)
        assert prog.statements[0].zoom == 10

    def test_parse_marker(self):
        prog = parse(MINIMAL + 'marker "Uni" at (24.86, 67.00) color=red')
        markers = [s for s in prog.statements if isinstance(s, MarkerNode)]
        assert len(markers) == 1
        assert markers[0].label == "Uni"
        assert markers[0].color == "red"

    def test_parse_label(self):
        prog = parse(MINIMAL + 'label "Downtown" at (24.85, 67.01) size=large')
        labels = [s for s in prog.statements if isinstance(s, LabelNode)]
        assert labels[0].text == "Downtown"
        assert labels[0].size == "large"

    def test_parse_route(self):
        src = MINIMAL + '''
route "R1"
    from (24.86, 67.00)
    to   (24.90, 67.01)
    color=green style=dashed width=3
end
'''
        prog = parse(src)
        routes = [s for s in prog.statements if isinstance(s, RouteNode)]
        assert routes[0].name   == "R1"
        assert routes[0].color  == "green"
        assert routes[0].style  == "dashed"
        assert routes[0].width  == 3

    def test_parse_circle(self):
        prog = parse(MINIMAL + "circle at (24.86, 67.00) radius=5km color=orange opacity=0.4")
        circles = [s for s in prog.statements if isinstance(s, CircleNode)]
        assert circles[0].radius == pytest.approx(5000.0)

    def test_parse_let_coord(self):
        prog = parse(MINIMAL + "let loc = (24.86, 67.00)")
        lets = [s for s in prog.statements if isinstance(s, LetNode)]
        assert lets[0].name  == "loc"
        assert lets[0].value == pytest.approx((24.86, 67.00))

    def test_parse_let_bool(self):
        prog = parse(MINIMAL + "let show = true")
        lets = [s for s in prog.statements if isinstance(s, LetNode)]
        assert lets[0].value == True

    def test_parse_layer(self):
        src = MINIMAL + '''
layer "Zone A"
    marker "X" at (24.86, 67.00) color=blue
end
'''
        prog = parse(src)
        layers = [s for s in prog.statements if isinstance(s, LayerNode)]
        assert layers[0].name == "Zone A"
        assert len(layers[0].body) == 1

    def test_parse_for_loop(self):
        src = MINIMAL + '''
let stops = [(24.86, 67.00), (24.87, 67.01)]
for p in stops
    marker "Stop" at p color=red
end
'''
        prog = parse(src)
        fors = [s for s in prog.statements if isinstance(s, ForNode)]
        assert fors[0].var      == "p"
        assert fors[0].iterable == "stops"

    def test_parse_if(self):
        src = MINIMAL + '''
if zoom > 8 then
    label "City" at (24.86, 67.00) size=large
end
'''
        prog = parse(src)
        ifs = [s for s in prog.statements if isinstance(s, IfNode)]
        assert ifs[0].op    == ">"
        assert ifs[0].right == pytest.approx(8.0)

    def test_parse_export(self):
        prog = parse(MINIMAL)
        exports = [s for s in prog.statements if isinstance(s, ExportNode)]
        assert exports[0].filename == "out.html"

    def test_missing_end_raises(self):
        with pytest.raises(ParseError):
            parse(MINIMAL + 'layer "X"\n  marker "A" at (24.86, 67.00)\n')

    def test_unknown_statement_raises(self):
        with pytest.raises(ParseError):
            parse(MINIMAL + "foobar something")



#  SEMANTIC TESTS


class TestSemantic:

    def test_valid_program_passes(self):
        sa = analyse(MINIMAL)
        assert sa.errors == []

    def test_missing_map_raises(self):
        with pytest.raises(SemanticError, match="No 'map' declaration"):
            analyse('export as "out.html"')

    def test_map_not_first_raises(self):
        with pytest.raises(SemanticError, match="must be the first"):
            analyse('let x = (24.86, 67.00)\nmap center=(24.86,67.00) zoom=10\nexport as "out.html"')

    def test_missing_export_raises(self):
        with pytest.raises(SemanticError, match="No 'export' declaration"):
            analyse("map center=(24.86, 67.00) zoom=10")

    def test_invalid_zoom_raises(self):
        with pytest.raises(SemanticError, match="zoom"):
            analyse("map center=(24.86, 67.00) zoom=99\nexport as \"out.html\"")

    def test_invalid_latitude_raises(self):
        with pytest.raises(SemanticError, match="latitude"):
            analyse(MINIMAL + 'marker "X" at (95.0, 67.00) color=red')

    def test_invalid_longitude_raises(self):
        with pytest.raises(SemanticError, match="longitude"):
            analyse(MINIMAL + 'marker "X" at (24.86, 200.00) color=red')

    def test_undefined_variable_raises(self):
        with pytest.raises(SemanticError, match="undefined variable"):
            analyse(MINIMAL + 'marker "X" at ghost color=red')

    def test_duplicate_layer_raises(self):
        src = MINIMAL + 'layer "Zone"\nend\nlayer "Zone"\nend\n'
        with pytest.raises(SemanticError, match="duplicate layer"):
            analyse(src)

    def test_loop_over_non_list_raises(self):
        src = MINIMAL + 'let pt = (24.86, 67.00)\nfor p in pt\nmarker "X" at p color=red\nend\n'
        with pytest.raises(SemanticError, match="not a list"):
            analyse(src)

    def test_invalid_opacity_raises(self):
        with pytest.raises(SemanticError, match="opacity"):
            analyse(MINIMAL + "circle at (24.86, 67.00) radius=1km color=blue opacity=1.5")

    def test_unknown_color_warns(self):
        sa = analyse(MINIMAL + 'marker "X" at (24.86, 67.00) color=ultraviolet')
        assert any("ultraviolet" in w for w in sa.warnings)

    def test_variable_used_in_marker(self):
        src = MINIMAL + 'let loc = (24.86, 67.00)\nmarker "X" at loc color=red\n'
        sa = analyse(src)
        assert sa.errors == []

    def test_symbol_table_tracks_type_and_scope(self):
        sa = analyse(MINIMAL + 'let loc = (24.86, 67.00)\n')
        assert sa.type_table["loc"] == "coordinate"
        assert sa.scope_table["loc"] == "global"


class TestFinalPhases:

    def test_icg_generates_tac(self):
        program = parse(MINIMAL + 'marker "X" at (24.86, 67.00) color=red\n')
        tac = IntermediateCodeGenerator().generate(program)
        assert any(inst.op == "MARKER" for inst in tac)

    def test_optimizer_uses_three_techniques(self):
        src = '''
map center=(24.86, 67.00) zoom=11
let a = (24.86, 67.00)
let b = a
if zoom >= 12 then
    marker "Hidden" at b color=red
end
export as "out.html"
'''
        program = parse(src)
        SemanticAnalyzer().analyse(program)
        icg = IntermediateCodeGenerator()
        tac = icg.generate(program)
        optimizer = Optimizer()
        optimized = optimizer.optimize(tac)
        report = optimizer.format_report()
        assert "Constant folding" in report
        assert "Copy propagation" in report
        assert "Dead code elimination" in report
        assert not any(inst.op == "MARKER" and inst.arg1 == "Hidden" for inst in optimized)

    def test_target_code_generation(self):
        program = parse(MINIMAL)
        SemanticAnalyzer().analyse(program)
        tac = IntermediateCodeGenerator().generate(program)
        code = TargetCodeGenerator().generate(tac)
        assert any(line.startswith("CREATE_MAP") for line in code)
        assert any(line.startswith("EXPORT_HTML") for line in code)
