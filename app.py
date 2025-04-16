from flask import Flask, request, jsonify, send_file
import os
import requests
from dotenv import load_dotenv
import time

from flask_cors import CORS

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)  # Soluciona el error de CORS entre React y Flask

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

@app.route("/")
def home():
    return jsonify({"message": "Servidor de transcripción activo 🚀"}), 200

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        audio = request.files.get("audio")
        if not audio:
            return jsonify({"error": "No se envió ningún archivo de audio"}), 400

        # Guardar archivo temporal
        audio_path = "temp_audio.wav"
        audio.save(audio_path)

        # Subir a AssemblyAI
        with open(audio_path, "rb") as f:
            upload_res = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=f
            )
        upload_url = upload_res.json()["upload_url"]

        # Enviar a transcripción
        transcript_req = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json={"audio_url": upload_url, "language_code": "es"},
            headers={"authorization": ASSEMBLYAI_API_KEY}
        )
        transcript_id = transcript_req.json()["id"]

        # Esperar a que esté lista
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        while True:
            poll_res = requests.get(polling_endpoint, headers={"authorization": ASSEMBLYAI_API_KEY})
            status = poll_res.json()["status"]
            if status == "completed":
                text = poll_res.json()["text"]
                break
            elif status == "error":
                return jsonify({"error": poll_res.json()["error"]}), 500
            time.sleep(1)

        # Guardar en archivo .txt
        output_path = "transcription.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Enviar como archivo descargable
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Limpieza (aunque falle)
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

# Ejecutar
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
