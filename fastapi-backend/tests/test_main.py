import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_stream_ollama_success(mocker):
    """
    Test d'intégration : Vérifie que le endpoint /generate 
    reçoit et relaie correctement un flux de données simulé.
    """
    
    # 1. Préparation du faux flux provenant d'Ollama
    # Chaque ligne simule un JSON envoyé par Ollama en mode stream
    mock_chunks = [
        b'{"model":"ministral-3:3b", "response":"Le", "done":false}',
        b'{"model":"ministral-3:3b", "response":" ciel", "done":false}',
        b'{"model":"ministral-3:3b", "response":" est bleu.", "done":true}'
    ]

    # 2. Mock de la réponse de 'requests'
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    # On simule la méthode iter_lines() utilisée dans votre main.py
    mock_response.iter_lines.return_value = iter(mock_chunks)
    
    # On patche requests.post pour qu'il renvoie notre faux objet response
    mocker.patch("requests.post", return_value=mock_response)

    # 3. Exécution de la requête sur notre API FastAPI
    # On utilise stream=True côté client TestClient également
    with client.stream("GET", "/generate", params={"prompt": "Bonjour"}) as response:
        assert response.status_code == 200
        
        # On récupère les lignes envoyées par FastAPI
        # Comme vous avez mis yield line + "\n", on vérifie le contenu
        all_content = "".join(list(response.iter_lines()))
        
        # Vérifications
        assert "ministral-3:3b" in all_content
        assert "est bleu" in all_content
        assert len(all_content) > 0

def test_stream_ollama_connection_error(mocker):
    """
    Vérifie le comportement si Ollama est injoignable.
    """
    # On simule une erreur réseau (ConnectionError)
    import requests
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError())

    # Selon votre implémentation actuelle, cela lèvera une exception 
    # car vous n'avez pas encore de bloc try/except autour du requests.post
    with pytest.raises(requests.exceptions.ConnectionError):
        client.get("/generate", params={"prompt": "test"})