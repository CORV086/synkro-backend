import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# Definiamo cosa ci manderà l'app Flutter
class MaterialeRequest(BaseModel):
    descrizione: str
    marca: str = ""
    diametro: str = ""
    misura: str = ""

@app.post("/analizza-materiale")
def analizza_materiale(req: MaterialeRequest):
    # Il server prende la chiave segreta dalle sue impostazioni di sistema
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chiave API non configurata sul server.")

    # Costruiamo il testo per Gemini
    input_utente = f"Descrizione: {req.descrizione}. Marca: {req.marca}. Diametro: {req.diametro}. Misura: {req.misura}."
    
    prompt = f"""
    Sei un esperto di materiali idraulici ed edili. Analizza queste informazioni: {input_utente}
    Trova il nome commerciale corretto e pulito del prodotto.
    
    Rispondi ESCLUSIVAMENTE con un oggetto JSON valido (non aggiungere testo o blocchi markdown ```json prima o dopo):
    {{
      "descrizione": "Nome preciso del prodotto completo di marca",
      "diametro": "diametro trovato o quello fornito",
      "misura": "misura trovata o quella fornita",
      "um": "Pz",
      "foto_path": "[https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=500](https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=500)"
    }}
    """

    # Chiamata HTTP interna dal server a Gemini (Endpoint stabile v1)
    url = f"[https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=){api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.statusCode != 200:
            raise HTTPException(status_code=400, detail=f"Errore Gemini: {response.text}")
        
        # Estraiamo il testo e puliamolo
        data = response.json()
        text_response = data['candidates'][0]['content']['parts'][0]['text']
        pulito = text_response.replace('```json', '').replace('```', '').strip()
        
        # Restituiamo il JSON direttamente a Flutter
        return json.loads(pulito)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))