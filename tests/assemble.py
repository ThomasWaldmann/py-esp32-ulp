from esp32_ulp.assemble import Assembler, TEXT, DATA, BSS, REL, ABS
from esp32_ulp.assemble import SymbolTable
from esp32_ulp.nocomment import remove_comments

src = """\

start:  wait 42
        ld r0, r1, 0
        st  r0,  r1,0
        halt
end:
"""


def test_parse_line():
    a = Assembler()
    lines = src.splitlines()
    # note: line number = index + 1
    assert a.parse_line(lines[0]) == None
    assert a.parse_line(lines[1]) == ('start', 'wait', ('42', ))
    assert a.parse_line(lines[2]) == (None, 'ld', ('r0', 'r1', '0', ))
    assert a.parse_line(lines[3]) == (None, 'st', ('r0', 'r1', '0', ))
    assert a.parse_line(lines[4]) == (None, 'halt', ())
    assert a.parse_line(lines[5]) == ('end', None, ())


def test_parse():
    a = Assembler()
    lines = remove_comments(src)
    result = a.parse(lines)
    assert None not in result


def test_assemble():
    a = Assembler()
    a.assemble(src)
    assert a.symbols.has_sym('start')
    assert a.symbols.has_sym('end')
    assert a.symbols.get_sym('start') == (REL, TEXT, 0)
    assert a.symbols.get_sym('end') == (REL, TEXT, 4)
    assert len(b''.join(a.sections[TEXT])) == 16  # 4 instructions * 4B
    assert len(a.sections[DATA]) == 0
    assert a.offsets[BSS] == 0


def test_symbols():
    st = SymbolTable({}, {})
    for entry in [
        ('rel_t4', REL, TEXT, 4),
        ('abs_t4', ABS, TEXT, 4),
        ('rel_d4', REL, DATA, 4),
        ('abs_d4', ABS, DATA, 4),
    ]:
        st.set_sym(*entry)
    # PASS 1 ========================================================
    st.set_pass(1)
    assert st.has_sym('abs_t4')
    assert st.get_sym('abs_t4') == (ABS, TEXT, 4)
    assert not st.has_sym('notexist')
    assert st.get_sym('notexist') == (REL, TEXT, 0)  # pass1 -> dummy
    assert st.resolve_absolute('abs_t4') == 4
    assert st.resolve_absolute('abs_d4') == 4
    assert st.resolve_absolute('rel_t4') == 4
    assert st.resolve_absolute('rel_d4') == 4
    st.set_from(TEXT, 8)
    assert st.resolve_relative('abs_t4') == -4
    assert st.resolve_relative('abs_d4') == -4
    assert st.resolve_relative('rel_t4') == -4
    assert st.resolve_relative('rel_d4') == -4
    # PASS 2 ========================================================
    st.set_bases({TEXT: 100, DATA: 200})
    st.set_pass(2)
    assert st.has_sym('abs_t4')
    assert st.get_sym('abs_t4') == (ABS, TEXT, 4)
    assert not st.has_sym('notexist')
    try:
        st.get_sym('notexist')  # pass2 -> raises
    except KeyError:
        raised = True
    else:
        raised = False
    assert raised
    assert st.resolve_absolute('abs_t4') == 4
    assert st.resolve_absolute('abs_d4') == 4
    assert st.resolve_absolute('rel_t4') == 100 + 4
    assert st.resolve_absolute('rel_d4') == 200 + 4
    st.set_from(TEXT, 8)
    assert st.resolve_relative('abs_t4') == 4 - 108
    assert st.resolve_relative('abs_d4') == 4 - 108
    assert st.resolve_relative('rel_t4') == 104 - 108
    assert st.resolve_relative('rel_d4') == 204 - 108


test_parse_line()
test_parse()
test_assemble()
test_symbols()
