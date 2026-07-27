from fastapi.testclient import TestClient

from app import main as app_module


def test_upload_and_ingest_accepts_regular_file_name(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.settings, "DATA_DIR", str(tmp_path))

    with TestClient(app_module.app) as client:
        file_path = tmp_path / "prueba_upload.md"
        file_path.write_text("# prueba\nContenido de prueba\n", encoding="utf-8")

        with file_path.open("rb") as handle:
            response = client.post(
                "/api/upload",
                files={"files": ("prueba_upload.md", handle, "text/markdown")},
                data={"category": "tecnologia"},
            )

        assert response.status_code == 200, response.text
        saved_path = tmp_path / "tecnologia" / "prueba_upload.md"
        assert saved_path.exists(), "El archivo debería haberse guardado en la carpeta de la categoría"

        ingest_response = client.post("/api/ingest")
        assert ingest_response.status_code == 200, ingest_response.text
        payload = ingest_response.json()
        assert payload["documents_processed"] >= 1
