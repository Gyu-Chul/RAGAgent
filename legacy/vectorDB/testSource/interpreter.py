from lexical_analyzer.lexicalAnalyzer_class import LexicalAnalyzer
from syntax_analyzer.syntaxAnalyzer_class import SyntaxAnalyzer
from semantic_analyzer.semanticAnalyzer_class import SemanticAnalyzer
import os
import ast
import sys
import inspect
import ctypes
from pympler import asizeof  # 전체 객체 크기 측정

# ✅ `ctypes`를 사용하여 숫자 객체 내부 정수 데이터의 주소, 크기, 타입을 가져오는 함수
def get_raw_integer_info(py_int_obj):
    """
    Python의 int 객체 내부에서 실제 정수 데이터가 저장된 메모리 주소, 크기, 타입을 가져옴.
    """
    # Python 정수 객체의 메모리 주소 (객체 자체)
    obj_address = id(py_int_obj)

    # `ctypes`를 사용하여 Python `int` 객체를 C의 long 타입 포인터로 변환
    c_int_p = ctypes.cast(obj_address, ctypes.POINTER(ctypes.c_long))

    # `PyLongObject`의 헤더 크기 계산 (보통 24바이트, 플랫폼에 따라 다름)
    header_size = ctypes.sizeof(ctypes.c_void_p) * 3  # CPython의 PyObject_VAR_HEAD 크기

    # 내부 정수 데이터(`ob_digit[0]`)의 실제 메모리 주소
    raw_integer_address = obj_address + header_size

    # 실제 원본 숫자의 크기 (보통 4~8 바이트)
    raw_integer_size = ctypes.sizeof(ctypes.c_long)

    return raw_integer_address, raw_integer_size, int  # Python에서 숫자는 항상 int


# ✅ 실제 데이터 사용 시 실행되는 함수
def log_number(value, obj_address, obj_type, obj_size, raw_info, total_size, line):
    raw_address, raw_size, raw_type = raw_info  # `get_raw_integer_info()`에서 가져온 값

    print(f"🔹 숫자 {value}")
    print(f"   ├─ 객체 메모리 주소: {hex(obj_address)}")
    print(f"   ├─ 객체 타입: {obj_type.__name__}")
    print(f"   ├─ 객체 크기: {obj_size} bytes")
    print(f"   ├─ 실제 원본 숫자의 메모리 주소: {hex(raw_address)}")
    print(f"   ├─ 실제 원본 숫자의 크기: {raw_size} bytes")
    print(f"   ├─ 실제 원본 숫자의 타입: {raw_type.__name__}")
    print(f"   ├─ 전체 객체 크기 (pympler asizeof): {total_size} bytes")
    print(f"   └─ 코드 줄 번호: {line}")
    return value


# ✅ 연산 수행 후 모든 과정 출력
def log_operator(left, right, op, line):
    if op == "Add":
        result = left + right
        symbol = "+"
    elif op == "Sub":
        result = left - right
        symbol = "-"
    elif op == "Mult":
        result = left * right
        symbol = "*"
    elif op == "Div":
        result = left / right
        symbol = "/"
    else:
        result = None
        symbol = "?"

    print(f"🔸 연산 ({left} {symbol} {right}) = {result} (코드 줄 번호: {line})")

    # 연산 결과도 로그 출력
    return log_number(result, id(result), type(result), sys.getsizeof(result),
                      get_raw_integer_info(result), asizeof.asizeof(result), line)

class Interpreter:
    
    def __init__(self):
        print("Interpreter class created in hab.py\n")

    def run(self):
        print("==== INTERPRETER.PY ====")
        baseDir = os.path.abspath(os.path.join(__file__, "../"))
        filePath = os.path.join(baseDir, "script.py")

        if not os.path.isfile(filePath):
            print(f"[ERROR] 파일이 존재하지 않습니다: {filePath}")
            raise "FileNotExist"

        lexicalAnalyzer = LexicalAnalyzer(filePath)
        syntaxAnalyzer = SyntaxAnalyzer(filePath)
        semanticAnalyzer = SemanticAnalyzer()

        lexicalAnalyzer.run()

        syntaxAnalyzer.run()
        print("==== Original Parse Tree ====")
        syntaxAnalyzer.printOriginalAstTree()

        semanticAnalyzer.run()
        print("==== INTERPRETER.PY OVER ====")

        exec(compile(syntaxAnalyzer.habAstTree, filename="<ast>", mode="exec"))