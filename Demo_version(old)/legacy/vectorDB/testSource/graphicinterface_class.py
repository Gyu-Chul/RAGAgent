from window.window_class import Window
from graphic_utility.graphicUtility_class import BasicDiagram
import wx

class GraphicInterface:
    
    def __init__(self):
        print("GraphicInterface class created in hab.py\n")

    def run(self):
        print("==== GRAPHICINTERFACE.PY ====")
        diagram = BasicDiagram()

        x_offset = 100
        y_offset = 100

        while True:
            print("\n도형을 추가할 번호를 선택하세요:")
            print("1. 원 (Circle)")
            print("2. 사각형 (Rectangle)")
            print("3. 화살표 (Arrow)")
            print("4. 텍스트 (Text)")
            print("5. 표 (Table)")
            print("0. 종료 (exit)")

            try:
                choice = int(input("선택: ").strip())
            except ValueError:
                print("숫자를 입력해주세요.")
                continue

            if choice == 0:
                break

            elif choice == 1:
                radius = int(input("반지름: "))
                diagram.Circle(x_offset, y_offset, radius)

            elif choice == 2:
                width = int(input("너비: "))
                height = int(input("높이: "))
                diagram.Rectangle(x_offset, y_offset, width, height)

            elif choice == 3:
                x1 = int(input("시작 x: "))
                y1 = int(input("시작 y: "))
                x2 = int(input("끝 x: "))
                y2 = int(input("끝 y: "))
                diagram.Arrow(x1, y1, x2, y2)

            elif choice == 4:
                text = input("텍스트 내용: ")
                font_size = int(input("폰트 크기 (기본 12): ") or "12")
                diagram.Text(x_offset, y_offset, text, font_size)

            elif choice == 5:
                rows = int(input("행(row) 수: "))
                cols = int(input("열(col) 수: "))
                contents = []
                print("각 셀에 들어갈 텍스트를 입력하세요:")
                for r in range(rows):
                    row_data = []
                    for c in range(cols):
                        cell = input(f"({r+1},{c+1}) 셀 내용: ")
                        row_data.append(cell)
                    contents.append(row_data)
                diagram.Table(x_offset, y_offset, rows, cols, contents=contents)

            else:
                print("잘못된 선택입니다. 다시 입력해주세요.")
                continue

            # 도형 겹치지 않도록 위치 조정
            x_offset += 100
            y_offset += 100

        app = wx.App(False)
        frame = Window(diagram)
        frame.Show()
        app.MainLoop()
        print("==== GRAPHICINTERFACE.PY OVER ====")