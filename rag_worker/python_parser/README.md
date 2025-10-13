# **Python 소스 코드 분석기 (Repository Parser)**

지정된 Git Repository의 Python 소스 코드를 분석하여, 각 파일을 의미 있는 코드 블록(청크)으로 분해하고 구조화된 데이터(JSON)로 저장하는 역할을 합니다. 소스코드를 RAG의 Vector DB에 들어갈 데이터로 전처리하는 과정에서 사용됩니다.

## **주요 기능 및 구성 요소**

이 분석기는 세 가지 핵심 구성 요소로 이루어져 있습니다.

### **1\. FileScanner: 파일 탐색기 🕵️‍♀️**

* **역할**: 지정된 디렉토리에서 분석할 가치가 있는 Python 파일(\*.py) 목록을 찾아내는 역할을 합니다.  
* **주요 기능**:  
  * **불필요한 디렉토리 제외**: .git, .venv, \_\_pycache\_\_ 등 분석에 필요 없는 폴더는 스캔 대상에서 자동으로 제외하여 효율성을 높입니다.  
  * **불필요한 파일 제외**: 내용이 없는 \_\_init\_\_.py 파일처럼 의미 없는 파일은 결과에서 제외합니다. (단, 코드가 포함된 \_\_init\_\_.py는 분석 대상에 포함됩니다.)  
  * **안정적인 결과**: 탐색된 파일 목록을 항상 정렬하여 반환하므로, 실행할 때마다 일관된 순서를 보장합니다.

### **2\. PythonASTParser: 코드 구조 분석기 🔬**

* **역할**: Python 소스 코드를 단순한 텍스트가 아닌, 문법 구조(AST)를 기반으로 분석하여 의미 있는 단위(클래스, 함수 등)로 분해(Chunking)합니다.  
* **주요 기능**:  
  * **AST(추상 구문 트리) 기반 분석**: Python의 내장 ast 모듈을 사용하여 코드를 문법적으로 해석합니다. 이를 통해 주석이나 단순 텍스트가 아닌 실제 코드 구조를 정확히 파악합니다.  
  * **다양한 코드 블록 식별**: 하나의 Python 파일을 다음과 같은 유형의 청크로 분리합니다.  
    * module: import 구문  
    * script: 클래스나 함수 외부에 있는 최상위 레벨의 실행 코드  
    * class: 클래스 정의  
    * function: 함수 정의 (def)  
    * async\_function: 비동기 함수 정의 (async def)  
  * **상세 정보 추출**: 각 코드 청크에 대해 유형, 이름, 시작/종료 라인 번호, 원본 코드, 파일 경로 등의 상세한 메타데이터를 추출하여 반환합니다.

### **3\. RepositoryParserService: 전체 프로세스 서비스**

* **역할**: 전체 Git 저장소를 대상으로 파일 스캔부터 파싱, 결과 저장까지의 모든 과정을 총괄하는 서비스입니다.  
* **주요 기능**:  
  * **통합 워크플로우**: FileScanner를 호출하여 파일 목록을 얻고, 각 파일을 PythonChunker (내부적으로 PythonASTParser 사용)에 전달하여 순차적으로 분석을 실행합니다.  
  * **결과 저장**: 분석이 완료된 각 코드 파일의 청크 데이터를 원래 디렉토리 구조를 유지하며 .json 파일로 저장하는 옵션을 제공합니다.  
  * **통계 제공**: 전체 파일 수, 성공적으로 분석된 파일 수, 실패한 파일 수, 생성된 총 청크 수 등 작업 결과를 요약하여 반환합니다.

## **동작 과정 (Workflow)**

1. **RepositoryParserService** 에 분석할 저장소의 이름(repo\_name)을 전달하여 parse\_repository() 메서드를 호출합니다.  
2. 서비스는 **FileScanner** 를 이용해 해당 저장소 내의 모든 유효한 Python 파일 목록을 가져옵니다.  
3. 서비스는 파일 목록을 순회하며 각 파일을 **PythonChunker** (내부 PythonASTParser)에 전달합니다.  
4. **PythonASTParser** 는 파일을 AST로 변환하고, 코드 구조를 분석하여 import, class, function 등의 코드 청크 리스트를 생성합니다.  
5. **RepositoryParserService** 는 모든 파일의 분석 결과를 취합하고, save\_json=True 옵션이 켜져 있으면 결과를 parsed\_repository/{repo\_name} 폴더에 JSON 파일로 저장합니다.  
6. 최종적으로 분석 통계가 포함된 결과를 반환하며 프로세스가 종료됩니다.

## **출력 예시 (.json 파일)**

my\_module.py 파일이 분석되면, parsed\_repository/my\_repo/my\_module.json 파일에 다음과 같은 형식의 데이터가 저장됩니다.

```bash
\[  
  {  
    "type": "module",  
    "name": "",  
    "start\_line": 1,  
    "end\_line": 2,  
    "code": "import os\\nfrom pathlib import Path",  
    "file\_path": "repository/my\_repo/my\_module.py"  
  },  
  {  
    "type": "class",  
    "name": "MyClass",  
    "start\_line": 5,  
    "end\_line": 10,  
    "code": "class MyClass:\\n    def \_\_init\_\_(self, name):\\n        self.name \= name\\n\\n    def greet(self):\\n        return f\\"Hello, {self.name}\\"",  
    "file\_path": "repository/my\_repo/my\_module.py"  
  },  
  {  
    "type": "script",  
    "name": "",  
    "start\_line": 13,  
    "end\_line": 14,  
    "code": "instance \= MyClass(\\"World\\")\\nprint(instance.greet())",  
    "file\_path": "repository/my\_repo/my\_module.py"  
  }  
\]  
```