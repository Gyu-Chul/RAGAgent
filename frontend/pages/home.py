from nicegui import ui

def render():
    with ui.row().style("height: 100vh; width: 100vw; justify-content: center; align-items: center; background-color: #fdfdfd;"):
        with ui.column().style("align-items: center; padding: 30px; border: 2px solid #ccc; border-radius: 15px; box-shadow: 0 0 10px #ccc; min-width: 350px;"):

            # GitAI 로고 + 타이틀
            with ui.row().style("align-items: center; justify-content: center; margin-bottom: 40px;"):
                ui.image('./static/gitai_logo.png').style("width: 60px; height: 60px; margin-right: 10px;")
                ui.label("GitAI").style("font-size: 28px; font-weight: bold;")

            ui.label("연결된 레포지토리").style("font-size: 22px; font-weight: bold; margin-bottom: 20px;")

            # 프로젝트 버튼들
            for name in ["HAB", "JEYSPORT"]:
                ui.button(name, on_click=lambda n=name: ui.notify(f"{n} 프로젝트 클릭!")).style("width: 250px; height: 50px; margin: 10px; font-size: 16px;")

            # New Connect 버튼
            def connect_repo():
                with ui.dialog() as dialog, ui.card():
                    ui.label("새 레포지토리 연결").style("font-weight: bold; font-size: 18px;")
                    repo_input = ui.input("Git 레포지토리 링크")
                    ui.button("연결 시도", on_click=lambda: ui.notify(f"입력된 주소: {repo_input.value}"))
                    ui.button("닫기", on_click=dialog.close)
                dialog.open()

            ui.button("NEW CONNECT", on_click=connect_repo).props("outline color=blue").style("width: 250px; height: 50px; margin-top: 30px; font-size: 16px;")
