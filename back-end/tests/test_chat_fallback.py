import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)


def test_chat_returns_clear_fallback_when_no_relevant_context_found():
    response = client.post(
        '/api/chat',
        json={
            'message': '¿Dónde puedo encontrar la política de vacaciones para el año 2030?',
            'category': 'rrhh',
            'history': [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 'no encontré' in payload['answer'].lower() or 'no pude encontrar' in payload['answer'].lower()
    assert payload['sources'] == []


def test_chat_returns_answer_and_sources_when_context_is_found():
    response = client.post(
        '/api/chat',
        json={
            'message': '¿Qué dice la política de vacaciones?',
            'category': 'rh',
            'history': [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['answer']
    assert isinstance(payload['sources'], list)
