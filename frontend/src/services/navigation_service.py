from nicegui import ui

class NavigationService:
    def __init__(self):
        self.current_page = "/"

    def navigate_to(self, path: str) -> None:
        self.current_page = path
        ui.navigate.to(path)

    def navigate_to_login(self) -> None:
        self.navigate_to("/login")

    def navigate_to_signup(self) -> None:
        self.navigate_to("/signup")

    def navigate_to_main(self) -> None:
        self.navigate_to("/main")

    def navigate_to_repositories(self) -> None:
        self.navigate_to("/repositories")

    def navigate_to_account(self) -> None:
        self.navigate_to("/account")

    def navigate_to_repository_options(self, repo_id: str) -> None:
        self.navigate_to(f"/admin/repository/{repo_id}")

    def navigate_to_vectordb(self, repo_id: str) -> None:
        self.navigate_to(f"/admin/vectordb/{repo_id}")

    def navigate_to_chat(self, repo_id: str) -> None:
        self.navigate_to(f"/chat/{repo_id}")

    def get_current_page(self) -> str:
        return self.current_page