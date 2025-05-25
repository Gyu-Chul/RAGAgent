from nicegui import ui

def chat_area():
    chat_title = ui.label().style('color:#888; font-size:18px; margin-bottom:10px;')
    message_area = ui.column().style(
        'border:1px solid #ddd; border-radius:8px; '
        'padding:20px; height:400px; overflow-y:auto; margin-bottom:10px;'
    )
    chat_input = ui.input('채팅 입력란').style('width:80%;').props('outlined')
    send_button = ui.button('전송')
    return chat_title, message_area, chat_input, send_button