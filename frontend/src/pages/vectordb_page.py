from nicegui import ui
from src.components.header import Header
from src.data.dummy_data import DummyDataService

class VectorDBPage:
    def __init__(self, repo_id: str, auth_service):
        self.repo_id = repo_id
        self.auth_service = auth_service
        self.data_service = DummyDataService()
        self.repository = self.data_service.get_repository(repo_id)
        self.selected_collection = None

    def render(self):
        if not self.repository:
            return self.render_not_found()

        with ui.column().classes('w-full min-h-screen'):
            Header(self.auth_service).render()

            with ui.row().classes('w-full flex-1'):
                self.render_sidebar()
                self.render_main_content()

    def render_not_found(self):
        with ui.column().classes('w-full min-h-screen items-center justify-center'):
            ui.html('<h2 class="text-2xl font-bold text-gray-600">Repository Not Found</h2>')
            ui.button('Back to Repositories', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-primary mt-4')

    def render_sidebar(self):
        collections = self.data_service.get_vectordb_collections(self.repo_id)

        with ui.column().classes('rag-sidebar w-80 p-6 gap-4'):
            with ui.row().classes('items-center gap-3 mb-4'):
                ui.icon('storage').classes('text-purple-600 text-xl')
                ui.html('<h2 class="text-lg font-semibold">Vector Collections</h2>')

            ui.button('Create Collection', icon='add', on_click=self.show_create_collection_dialog).classes('rag-button-primary w-full')

            with ui.column().classes('gap-2 mt-4'):
                for collection in collections:
                    self.render_collection_item(collection)

            ui.separator().classes('my-4')

            with ui.column().classes('gap-2'):
                ui.button('Repository Options', icon='settings', on_click=lambda: ui.navigate.to(f'/admin/repository/{self.repo_id}')).classes('rag-button-secondary w-full')
                ui.button('Back to Repositories', icon='arrow_back', on_click=lambda: ui.navigate.to('/repositories')).classes('rag-button-secondary w-full')

    def render_collection_item(self, collection):
        is_selected = self.selected_collection and self.selected_collection["id"] == collection["id"]
        button_classes = "w-full text-left p-3 rounded-lg transition-colors"
        if is_selected:
            button_classes += " bg-purple-100 border-purple-300"
        else:
            button_classes += " hover:bg-gray-100"

        with ui.button(on_click=lambda c=collection: self.select_collection(c)).classes(button_classes):
            with ui.column().classes('gap-1'):
                with ui.row().classes('items-center gap-2 w-full'):
                    ui.icon('storage').classes('text-purple-600')
                    ui.html(f'<span class="font-medium">{collection["name"]}</span>')
                    self.render_collection_status_badge(collection["status"])

                ui.html(f'<div class="text-sm text-gray-600 truncate">{collection["description"]}</div>')

                with ui.row().classes('items-center gap-3 text-xs text-gray-500 mt-1'):
                    ui.html(f'<span>{collection["entity_count"]:,} entities</span>')
                    ui.html(f'<span>{collection["dimension"]}D</span>')

    def render_main_content(self):
        with ui.column().classes('flex-1 p-6 gap-6'):
            if not self.selected_collection:
                self.render_overview()
            else:
                self.render_collection_details()

    def render_overview(self):
        with ui.column().classes('gap-6'):
            self.render_header()
            self.render_stats_overview()
            self.render_recent_collections()

    def render_header(self):
        with ui.card().classes('rag-card'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('storage').classes('text-purple-600 text-3xl')
                with ui.column().classes('flex-1'):
                    ui.html(f'<h1 class="text-2xl font-bold">Vector Database</h1>')
                    ui.html(f'<p class="text-gray-600">Managing vector collections for {self.repository["name"]}</p>')

                ui.button('Create Collection', icon='add', on_click=self.show_create_collection_dialog).classes('rag-button-primary')

    def render_stats_overview(self):
        collections = self.data_service.get_vectordb_collections(self.repo_id)
        total_entities = sum(c["entity_count"] for c in collections)

        with ui.row().classes('gap-6'):
            stats = [
                {"title": "Total Collections", "value": len(collections), "icon": "storage", "color": "purple"},
                {"title": "Total Entities", "value": f"{total_entities:,}", "icon": "memory", "color": "blue"},
                {"title": "Avg Dimension", "value": "768", "icon": "hub", "color": "green"},
                {"title": "Index Type", "value": "HNSW", "icon": "account_tree", "color": "orange"}
            ]

            for stat in stats:
                with ui.card().classes(f'rag-stat-card bg-gradient-to-br from-{stat["color"]}-500 to-{stat["color"]}-600 flex-1'):
                    ui.icon(stat["icon"]).classes('text-3xl mb-2')
                    ui.html(f'<div class="text-2xl font-bold">{stat["value"]}</div>')
                    ui.html(f'<div class="text-sm opacity-90">{stat["title"]}</div>')

    def render_recent_collections(self):
        collections = self.data_service.get_vectordb_collections(self.repo_id)

        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">All Collections</h3>')

            with ui.grid(columns=1).classes('gap-4'):
                for collection in collections:
                    with ui.card().classes('border hover:shadow-lg transition-all cursor-pointer p-4').on('click', lambda c=collection: self.select_collection(c)):
                        with ui.row().classes('items-start justify-between'):
                            with ui.column().classes('flex-1 gap-2'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('storage').classes('text-purple-600')
                                    ui.html(f'<h4 class="font-semibold">{collection["name"]}</h4>')
                                    self.render_collection_status_badge(collection["status"])

                                ui.html(f'<p class="text-sm text-gray-600">{collection["description"]}</p>')

                                with ui.row().classes('items-center gap-4 text-sm text-gray-500'):
                                    ui.html(f'<span>📊 {collection["entity_count"]:,} entities</span>')
                                    ui.html(f'<span>🔢 {collection["dimension"]} dimensions</span>')
                                    ui.html(f'<span>🔍 {collection["index_type"]} index</span>')

                            with ui.column().classes('gap-2'):
                                ui.button('View Details', icon='visibility', on_click=lambda c=collection: self.select_collection(c)).classes('rag-button-primary text-xs')
                                ui.button('Manage', icon='settings', on_click=lambda c=collection: self.show_collection_options(c)).classes('rag-button-secondary text-xs')

    def render_collection_details(self):
        collection = self.selected_collection

        with ui.column().classes('gap-6'):
            with ui.row().classes('items-center gap-4 mb-4'):
                ui.button(icon='arrow_back', on_click=lambda: self.select_collection(None)).classes('rag-button-secondary')
                ui.icon('storage').classes('text-purple-600 text-2xl')
                ui.html(f'<h2 class="text-2xl font-bold">{collection["name"]}</h2>')
                self.render_collection_status_badge(collection["status"])

            with ui.row().classes('gap-6'):
                with ui.column().classes('flex-1 gap-6'):
                    self.render_collection_info()
                    self.render_entity_browser()

                with ui.column().classes('w-80 gap-6'):
                    self.render_collection_actions()
                    self.render_collection_metrics()

    def render_collection_info(self):
        collection = self.selected_collection

        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Collection Information</h3>')

            info_items = [
                ("Name", collection["name"]),
                ("Description", collection["description"]),
                ("Entity Count", f'{collection["entity_count"]:,}'),
                ("Dimension", collection["dimension"]),
                ("Index Type", collection["index_type"]),
                ("Status", collection["status"].title())
            ]

            with ui.column().classes('gap-3'):
                for label, value in info_items:
                    with ui.row().classes('items-center justify-between py-2 border-b'):
                        ui.label(label).classes('font-medium text-gray-700')
                        ui.label(str(value)).classes('text-gray-600')

    def render_entity_browser(self):
        with ui.card().classes('rag-card'):
            with ui.row().classes('items-center justify-between mb-4'):
                ui.html('<h3 class="text-lg font-semibold">Entity Browser</h3>')
                ui.input(placeholder='Search entities...').classes('rag-input w-64')

            sample_entities = [
                {"id": "ent_001", "content": "class TransformerModel(nn.Module):", "source": "models/transformer.py", "score": 0.95},
                {"id": "ent_002", "content": "def train_model(config, data_loader):", "source": "training/train.py", "score": 0.89},
                {"id": "ent_003", "content": "# Installation Guide\n\nThis project requires Python 3.8+", "source": "README.md", "score": 0.82},
                {"id": "ent_004", "content": "API_KEY = os.getenv('OPENAI_API_KEY')", "source": "config/settings.py", "score": 0.78},
                {"id": "ent_005", "content": "async def process_embeddings(texts):", "source": "utils/embeddings.py", "score": 0.75}
            ]

            with ui.column().classes('gap-3 max-h-80 overflow-y-auto'):
                for entity in sample_entities:
                    with ui.card().classes('border p-3 hover:bg-gray-50'):
                        with ui.row().classes('items-start justify-between'):
                            with ui.column().classes('flex-1 gap-1'):
                                ui.html(f'<code class="text-sm bg-gray-100 px-2 py-1 rounded">{entity["content"][:60]}{"..." if len(entity["content"]) > 60 else ""}</code>')
                                with ui.row().classes('items-center gap-2 text-xs text-gray-500'):
                                    ui.icon('description').classes('text-gray-400')
                                    ui.label(entity["source"])
                            with ui.column().classes('items-end gap-1'):
                                ui.label(f'{entity["score"]:.2f}').classes('text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded')
                                ui.button(icon='more_vert').classes('text-gray-400')

    def render_collection_actions(self):
        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Actions</h3>')

            actions = [
                ("Rebuild Index", "refresh", self.rebuild_index),
                ("Export Data", "download", self.export_collection),
                ("Import Data", "upload", self.import_data),
                ("Duplicate Collection", "content_copy", self.duplicate_collection),
                ("Delete Collection", "delete", self.delete_collection)
            ]

            with ui.column().classes('gap-2'):
                for label, icon, action in actions:
                    button_class = 'rag-button-secondary w-full text-left justify-start'
                    if label == "Delete Collection":
                        button_class = 'bg-red-100 text-red-700 hover:bg-red-200 w-full text-left justify-start px-4 py-2 rounded-lg'

                    ui.button(label, icon=icon, on_click=action).classes(button_class)

    def render_collection_metrics(self):
        with ui.card().classes('rag-card'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Performance Metrics</h3>')

            metrics = [
                {"label": "Query Latency", "value": "12ms", "trend": "down"},
                {"label": "Index Size", "value": "2.4GB", "trend": "stable"},
                {"label": "Memory Usage", "value": "1.8GB", "trend": "up"},
                {"label": "Hit Rate", "value": "94.5%", "trend": "up"}
            ]

            with ui.column().classes('gap-3'):
                for metric in metrics:
                    with ui.row().classes('items-center justify-between py-2'):
                        ui.label(metric["label"]).classes('text-sm text-gray-600')
                        with ui.row().classes('items-center gap-2'):
                            ui.label(metric["value"]).classes('font-medium')
                            trend_icon = "trending_up" if metric["trend"] == "up" else "trending_down" if metric["trend"] == "down" else "trending_flat"
                            trend_color = "text-green-600" if metric["trend"] == "up" else "text-red-600" if metric["trend"] == "down" else "text-gray-600"
                            ui.icon(trend_icon).classes(f'{trend_color} text-sm')

    def render_collection_status_badge(self, status):
        colors = {
            'ready': 'bg-green-100 text-green-800',
            'building': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800'
        }
        ui.html(f'<span class="px-2 py-1 rounded-full text-xs {colors.get(status, "bg-gray-100 text-gray-800")}">{status}</span>')

    def select_collection(self, collection):
        self.selected_collection = collection
        ui.update()

    def show_create_collection_dialog(self):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.html('<h3 class="text-lg font-semibold mb-4">Create New Collection</h3>')

            with ui.column().classes('gap-4'):
                name_input = ui.input('Collection Name', placeholder='e.g., code_embeddings').classes('rag-input w-full')
                description_input = ui.textarea('Description', placeholder='Describe what this collection stores').classes('rag-input w-full')
                dimension_input = ui.number('Dimension', value=768, min=1, max=4096).classes('rag-input w-full')
                index_select = ui.select(['HNSW', 'IVF_FLAT', 'IVF_SQ8'], value='HNSW', label='Index Type').classes('w-full')

                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Cancel', on_click=dialog.close).classes('rag-button-secondary')
                    ui.button('Create Collection', on_click=lambda: self.create_collection(
                        name_input.value,
                        description_input.value,
                        dimension_input.value,
                        index_select.value,
                        dialog
                    )).classes('rag-button-primary')

        dialog.open()

    def create_collection(self, name, description, dimension, index_type, dialog):
        if not name:
            ui.notify('Please enter a collection name', color='red')
            return

        ui.notify(f'Collection "{name}" created successfully!', color='green')
        dialog.close()

    def show_collection_options(self, collection):
        ui.notify(f'Collection options for {collection["name"]}', color='blue')

    def rebuild_index(self):
        ui.notify('Rebuilding index...', color='blue')

    def export_collection(self):
        ui.notify('Exporting collection data...', color='blue')

    def import_data(self):
        ui.notify('Import data feature coming soon', color='blue')

    def duplicate_collection(self):
        ui.notify('Duplicating collection...', color='blue')

    def delete_collection(self):
        ui.notify('Collection deletion is not available in demo mode', color='blue')