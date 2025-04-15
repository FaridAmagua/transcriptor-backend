# app.py

from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

app = Flask(__name__)

# Ruta principal para probar que el servidor funciona
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Servidor de transcripción en línea 🚀"}), 200

# Ruta para transcribir un audio vía AssemblyAI
@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        # Obtener archivo de audio
        audio = request.files.get("audio")
        if not audio:
            return jsonify({"error": "No se envió ningún archivo de audio"}), 400

        # Guardar temporalmente el archivo
        audio.save("temp_audio.wav")

        # Subir el audio a AssemblyAI
        with open("temp_audio.wav", "rb") as f:
            response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": os.getenv("ASSEMBLYAI_API_KEY")},
                data=f
            )
        upload_url = response.json()["upload_url"]

        # Enviar a transcripción
        json_data = {
            "audio_url": upload_url,
            "language_code": "es"  # Puedes cambiar esto según el idioma
        }

        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json=json_data,
            headers={"authorization": os.getenv("ASSEMBLYAI_API_KEY")}
        )

        transcript_id = transcript_response.json()["id"]

        # Esperar a que termine la transcripción
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        while True:
            polling_response = requests.get(polling_endpoint, headers={"authorization": os.getenv("ASSEMBLYAI_API_KEY")})
            status = polling_response.json()["status"]

            if status == "completed":
                return jsonify({"transcription": polling_response.json()["text"]}), 200
            elif status == "error":
                return jsonify({"error": polling_response.json()["error"]}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Iniciar la app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
