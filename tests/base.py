from urllib.parse import urljoin


class BaseTestEndpoints:
    api_path: str = ""

    def _endpoint(self, path: str) -> str:
        path = path.lstrip("/")
        return urljoin(self.api_path, path)
