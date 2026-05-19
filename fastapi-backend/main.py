from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import requests
import json

app = FastAPI()

@app.get("/generate")
def stream_ollama_request(prompt: str, model: str = "ministral-3:3b"):
    """Envoie une requête de streaming à l'instance Ollama et la relaie au client"""
    url = "http://ollama:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    def event_generator():
        # On utilise stream=True pour ne pas attendre la fin de la génération
        response = requests.post(url, json=payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                # On décode la ligne et on la renvoie immédiatement au client
                # On ajoute \n pour faciliter la lecture côté client
                yield line.decode('utf-8') + "\n"

    # StreamingResponse permet de maintenir la connexion ouverte
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    # Note: En dehors de Docker, "ollama" devra redevenir "localhost"
    print("Ce script doit être lancé via uvicorn pour exposer l'API.")