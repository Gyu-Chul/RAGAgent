from nicegui import ui

def setup_theme():
    ui.add_head_html('''
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --secondary-color: #64748b;
            --success-color: #059669;
            --warning-color: #d97706;
            --error-color: #dc2626;
            --background: #ffffff;
            --surface: #f8fafc;
            --card: #ffffff;
            --border: #e2e8f0;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--background);
            color: var(--text-primary);
        }

        .rag-header {
            background: linear-gradient(135deg, var(--primary-color), #3b82f6);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .rag-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }

        .rag-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transform: translateY(-1px);
        }

        .rag-button-primary {
            background: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }

        .rag-button-primary:hover {
            background: var(--primary-hover) !important;
            transform: translateY(-1px) !important;
        }

        .rag-button-secondary {
            background: var(--surface) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }

        .rag-button-secondary:hover {
            background: var(--border) !important;
        }

        .rag-input {
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            background: var(--background) !important;
            transition: border-color 0.2s ease !important;
        }

        .rag-input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        }

        .rag-sidebar {
            background: var(--surface);
            border-right: 1px solid var(--border);
            min-height: 100vh;
        }

        .rag-chat-bubble {
            max-width: 70%;
            padding: 1rem;
            border-radius: 12px;
            margin: 0.5rem 0;
        }

        .rag-chat-user {
            background: var(--primary-color);
            color: white;
            margin-left: auto;
        }

        .rag-chat-bot {
            background: var(--surface);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .rag-stat-card {
            background: linear-gradient(135deg, var(--primary-color), #3b82f6);
            color: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }

        .rag-table {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        .nicegui-content {
            padding: 0 !important;
            max-width: none !important;
        }

        .q-page-container {
            padding: 0 !important;
        }

        .q-header {
            background: var(--primary-color) !important;
        }

        .q-btn {
            text-transform: none !important;
        }
    </style>
    ''')

    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">')