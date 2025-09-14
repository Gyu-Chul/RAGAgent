from nicegui import ui
from src.services import milvus_controller as milvus

import shutil

def vector_db_panel():
    uploaded_file_path = {'path': None}

    # 결과 로그 영역
    with ui.column().style('border:1px solid #ccc; padding:10px; border-radius:10px; min-height:200px;') as result_box:
        ui.label('🪄 결과 로그').style('font-weight:bold; font-size:16px;')
        result_log_column = ui.column()

    def show_result(text: str):
        with result_log_column:
            ui.label(text).style('margin:3px 0; color: #444;').classes('text-sm')

    def clear_log():
        result_log_column.clear()


    ui.button('🧼 로그 초기화', on_click=clear_log).props('outline').style('margin-bottom:20px;')

    with ui.row().style('gap:40px;'):

        # ───────── 📁 컬렉션 관리 ─────────
        with ui.column().style('min-width:300px;'):
            ui.label('📁 컬렉션 관리').style('font-weight:bold; font-size:18px;')

            create_name_input = ui.input(label='📌 생성할 컬렉션 이름')
            create_desc_input = ui.input(label='📝 컬렉션 설명')
            ui.button('✅ 컬렉션 생성', on_click=lambda: show_result(
                milvus.create_collection(create_name_input.value, create_desc_input.value))
            ).props('outline')

            delete_name_input = ui.input(label='🗑️ 삭제할 컬렉션 이름')
            ui.button('❌ 컬렉션 삭제', on_click=lambda: show_result(
                milvus.delete_collection(delete_name_input.value))
            ).props('outline')

            count_name_input = ui.input(label='📊 엔티티 수 확인할 컬렉션')
            ui.button('🔢 엔티티 개수', on_click=lambda: show_result(
                milvus.count_entities(count_name_input.value))
            ).props('outline')

            ui.button('📄 컬렉션 목록', on_click=lambda: show_result(
                milvus.list_collection())
            ).props('outline')

        # ───────── 💠 엔티티 및 임베딩 ─────────
        with ui.column().style('min-width:300px;'):
            ui.label('💠 엔티티 / 임베딩').style('font-weight:bold; font-size:18px;')

            view_name_input = ui.input(label='👁️ 조회할 컬렉션 이름')
            ui.button('🔍 엔티티 보기', on_click=lambda: show_result(
                milvus.view_entities(view_name_input.value))
            ).props('outline')

            entity_del_coll_input = ui.input(label='🧹 삭제할 컬렉션')
            entity_id_input = ui.input(label='🔢 삭제할 엔티티 ID')
            ui.button('🚫 엔티티 삭제', on_click=lambda: show_result(
                milvus.delete_entity(entity_del_coll_input.value, entity_id_input.value))
            ).props('outline')

            emb_coll_input = ui.input(label='📌 임베딩할 컬렉션')



            def handle_upload(e):
                print('[DEBUG] 업로드 이벤트 발생')
                
                save_path = f'/tmp/{e.name}'
                
                with open(save_path, 'wb') as f:
                    shutil.copyfileobj(e.content, f)  # ✅ SpooledTemporaryFile → 파일로 복사

                uploaded_file_path['path'] = save_path
                show_result(f'✅ 파일 업로드 완료: {e.name}')
                show_result(f'📂 저장 경로: {save_path}')


                
            ui.upload(
                label='📤 JSON 업로드',
                auto_upload=True,
                on_upload=handle_upload,
                max_files=1
            )





            def handle_embedding():
                if uploaded_file_path['path']:
                    show_result(milvus.embedding(uploaded_file_path['path'], emb_coll_input.value))
                else:
                    show_result('❌ JSON 파일을 먼저 업로드하세요.')

            ui.button('📥 임베딩 추가', on_click=handle_embedding).props('outline')

        # ───────── 🔌 연결 확인 ─────────
        with ui.column().style('min-width:200px;'):
            ui.label('🔌 Milvus 연결').style('font-weight:bold; font-size:18px;')
            ui.button('🧪 연결 상태 확인', on_click=lambda: show_result(
                milvus.connection_test())
            ).props('outline')
