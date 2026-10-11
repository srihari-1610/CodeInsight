from core.samples import SAMPLES
from core.static_analysis import analyze_static, c_like_loop_depth


def test_python_nested_loops_and_recursion():
    code = "def f(n):\n    for i in range(n):\n        for j in range(n):\n            for k in range(n):\n                pass\n    return f(n - 1) if n else 0\n"
    rep = analyze_static(code, "Python")
    assert rep.loop_depth == 3
    assert rep.recursive_functions == ["f"]
    assert any("Loop nesting depth is 3" in n for n in rep.notes)


def test_python_comprehension_counts_as_loops():
    assert analyze_static("x = [a + b for a in range(3) for b in range(3)]", "Python").loop_depth == 2


def test_python_input_in_loop_flagged_but_not_in_range_header():
    flagged = analyze_static("for _ in range(3):\n    x = input()\n", "Python")
    assert any("input()" in n for n in flagged.notes)
    ok = analyze_static("for _ in range(int(input())):\n    pass\n", "Python")
    assert not any("input()" in n for n in ok.notes)


def test_python_syntax_error_reported():
    rep = analyze_static("def broken(:\n", "Python")
    assert rep.parse_error and rep.loop_depth is None


def test_cpp_braced_nesting():
    assert c_like_loop_depth("int main(){ for(int i=0;i<n;i++){ for(int j=0;j<n;j++){ x++; } } }") == 2


def test_cpp_braceless_nesting():
    assert c_like_loop_depth("for (int i=0;i<n;i++) for (int j=0;j<n;j++) s++;") == 2


def test_cpp_do_while_is_one_level():
    assert c_like_loop_depth("do { x++; } while (x < 5);") == 1


def test_cpp_ignores_comments_and_strings():
    assert c_like_loop_depth('// for(;;){}\nconst char* s = "while(1){}"; /* for(;;) */ int x;') == 0


def test_cpp_brace_init_inside_braceless_loop_not_miscounted():
    assert c_like_loop_depth("for (int i=0;i<n;i++) v.push_back({i, i});") == 1


def test_cpp_recursion_detected():
    code = "int fib(int n){ if(n<2) return n; return fib(n-1)+fib(n-2); }\nint main(){ return fib(5); }"
    assert analyze_static(code, "C++").recursive_functions == ["fib"]


def test_cpp_io_notes():
    code = "int main(){ for(int i=0;i<n;i++){ cin >> x; cout << x << endl; } }"
    notes = " ".join(analyze_static(code, "C++").notes)
    assert "sync_with_stdio" in notes and "endl" in notes


def test_java_depth_and_scanner_note():
    code = "public class A { public static void main(String[] a){ Scanner s = new Scanner(System.in); for(int i=0;i<3;i++){ for(int j=0;j<3;j++){ System.out.println(i);} } } }"
    rep = analyze_static(code, "Java")
    assert rep.loop_depth == 2
    assert any("Scanner" in n for n in rep.notes)


def test_bundled_samples():
    by_title = {s["title"].split(" - ")[0]: s for s in SAMPLES}
    assert analyze_static(by_title["Dijkstra shortest paths"]["code"], "C++").loop_depth == 2
    assert analyze_static(by_title["Longest Increasing Subsequence O(n^2)"]["code"], "C++").loop_depth == 2
    assert analyze_static(by_title["Two Sum (hash map)"]["code"], "Python").loop_depth == 1
