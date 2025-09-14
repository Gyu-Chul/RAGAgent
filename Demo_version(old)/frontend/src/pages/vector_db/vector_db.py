

from nicegui import ui
from src.apis.vector_db import apis
from src.pages.vector_db.result_log_panel import ResultLogPanel
import json

def vector_db_sidebar(repo_name: str):
    with ui.column().style('width:260px; padding:20px; border-right:1px solid #ccc;'):
        ui.button('🏠 홈으로', on_click=lambda: ui.navigate.to('/')).style('margin-bottom:20px; width:100%;')
        ui.label(repo_name).style('font-size:22px; font-weight:bold; margin-bottom:10px;')
        ui.button(f'⬅️ 레포지토리로 돌아가기', on_click=lambda: ui.navigate.to(f'/project/{repo_name}')).style(
            'margin-bottom:10px; width:100%;')

# --- 유틸: 마크다운 예약문자 무해화 + 코드블록 래핑 ---
def _fence_code(text: str, lang: str = "text") -> str:
    if text is None:
        text = ""
    # 코드블록 내부에 ``` 가 있으면 깨지지 않게 분리
    safe = text.replace("```", "`\u200b``")  # backtick + zero width space
    return f"```{lang}\n{safe}\n```"

def _inline(code: str) -> str:
    if code is None:
        code = ""
    return "`" + code.replace("`", "`\u200b") + "`"

def format_search_results(results: list[dict]) -> str:
    if not results:
        return json.dumps({"message": "⚠️ 검색 결과가 없습니다."}, ensure_ascii=False, indent=2)

    output_list = []
    for r in results:
        output_item = {
            "type": r.get("type", ""),
            "name": r.get("name", ""),
            "start_line": r.get("start_line", ""),
            "end_line": r.get("end_line", ""),
            "code": r.get("text") or r.get("code_preview") or "",
            "file_path": r.get("file_path", ""),
            "_source_file": r.get("_source_file", "")
        }
        output_list.append(output_item)

    # 그냥 텍스트지만 JSON처럼 보이도록 포맷
    return json.dumps(output_list, ensure_ascii=False, indent=2)

def render_vector_db(repo_name: str):
    log_panel = ResultLogPanel()

    async def handle_api_call(api_function, *args):
        result = await api_function(*args)
        log_panel.add_log(str(result))

    with ui.row().style('height:100vh; width:100vw; overflow:hidden;'):
        vector_db_sidebar(repo_name)

        with ui.row().style('flex:1; padding:20px; gap:30px; overflow:auto;'):
            with ui.column().style('gap:15px;'):
                ui.label('Vector DB Management').classes('text-h6 font-bold')
                ui.button('Connection Test', on_click=lambda: handle_api_call(apis.test_connection))
                ui.button('List All Collections', on_click=lambda: handle_api_call(apis.list_collections))
                ui.separator().style('margin: 10px 0;')

                with ui.card().tight():
                    with ui.card_section():
                        ui.label("컬렉션 생성").classes("font-bold")
                        create_name_input = ui.input('Collection Name').style('width: 250px;')
                        create_desc_input = ui.input('Description').style('width: 250px;')
                        version_select = ui.select(
                            options=[0, 1, 2, 3],
                            value=1,
                            label="Version"
                        ).style('width: 120px;')

                        ui.button(
                            'Create',
                            on_click=lambda: handle_api_call(
                                apis.create_collection,
                                create_name_input.value,
                                create_desc_input.value,
                                int(version_select.value)   # ✅ 버전 전달
                            )
                        )


                with ui.card().tight():
                    with ui.card_section():
                        ui.label("컬렉션 삭제").classes("font-bold")
                        delete_name_input = ui.input('Collection to Delete').style('width: 250px;')
                        ui.button('Delete', color='red',
                                  on_click=lambda: handle_api_call(apis.delete_collection,
                                                                   delete_name_input.value))


            with ui.column().style('gap:15px;'):
                ui.label('Entity Management').classes('text-h6 font-bold')

                with ui.card().tight():
                    with ui.card_section():
                        ui.label("엔티티 조회").classes("font-bold")
                        entity_coll_input = ui.input('Collection Name').style('width: 250px;')
                        with ui.row():
                            ui.button('Count Entities', on_click=lambda: handle_api_call(apis.count_entities,
                                                                                         entity_coll_input.value))
                            ui.button('View Entities', on_click=lambda: handle_api_call(apis.view_entities,
                                                                                        entity_coll_input.value))

                with ui.card().tight():
                    with ui.card_section():
                        ui.label("JSON 임베딩").classes("font-bold")
                        embed_coll_input = ui.input('Target Collection').style('width: 250px;')

                        async def on_upload(e):
                            coll_name = embed_coll_input.value.strip()
                            if not coll_name:
                                log_panel.add_log("❌ 컬렉션 이름을 먼저 입력하세요.")
                                return
                            log_panel.add_log("⏳ 임베딩 중... 잠시만 기다려주세요.")
                            await handle_api_call(apis.embed_json_file, coll_name, e.name, e.content)

                        ui.upload(label='Upload JSON', auto_upload=True, on_upload=on_upload, max_files=1).props(
                            'accept=".json"')

                # ───── 🔍 검색 기능 카드 추가 ─────
                with ui.card().tight():
                    with ui.card_section():
                        ui.label("벡터 검색").classes("font-bold")
                        search_coll_input = ui.input('Collection Name').style('width: 250px;')
                        search_query_input = ui.input('Query Text').style('width: 250px;')
                        search_filter_input = ui.input('Metadata Filter (옵션)').style('width: 250px;')

                        with ui.row():
                            async def on_basic_search():
                                log_panel.add_log("⏳ 기본 검색 중...")
                                message, results = await apis.search_basic(search_coll_input.value, search_query_input.value)
                                log_panel.add_log(message)
                                log_panel.add_log(format_search_results(results), as_code=True)


                            async def on_metadata_search():
                                log_panel.add_log("⏳ 메타데이터 필터 검색 중...")
                                message, results = await apis.search_with_metadata(
                                    search_coll_input.value, search_query_input.value, search_filter_input.value
                                )
                                log_panel.add_log(message)
                                log_panel.add_log(f"```text\n{format_search_results(results)}\n```")


                            ui.button('🔍 기본 검색', on_click=on_basic_search)
                            ui.button('🧩 메타데이터 검색', on_click=on_metadata_search)

            with ui.column().style('flex:1; min-width:300px; height:900px;'):
                ui.label('🪄 Result Log').classes('text-h6 font-bold mb-2')
                with ui.card().style('padding:10px; height:100%; overflow:auto;').classes('shadow-md'):
                    log_panel.render()