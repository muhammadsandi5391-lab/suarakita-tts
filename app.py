from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)

# Empat suara neural dengan karakter asli berbeda.
# Ardi/Gadis: Bahasa Indonesia; Dimas/Siti: Bahasa Jawa.
VOICES = {
    "ardi": {"name": "Ardi", "locale": "Bahasa Indonesia", "voice": "id-ID-ArdiNeural"},
    "gadis": {"name": "Gadis", "locale": "Bahasa Indonesia", "voice": "id-ID-GadisNeural"},
    "dimas": {"name": "Dimas", "locale": "Bahasa Jawa", "voice": "jv-ID-DimasNeural"},
    "siti": {"name": "Siti", "locale": "Bahasa Jawa", "voice": "jv-ID-SitiNeural"}
}

PREVIEW_TEXT = {
    "ardi": "Halo, nama saya Ardi. Saya akan membacakan teks ini dengan suara yang natural.",
    "gadis": "Halo, nama saya Gadis. Saya akan membacakan teks ini dengan suara yang natural.",
    "dimas": "Sugeng enjing. Jenengku Dimas. Aku bakal maca tulisan iki nganggo basa Jawa.",
    "siti": "Sugeng enjing. Jenengku Siti. Aku bakal maca tulisan iki nganggo basa Jawa."
}

def create_audio(text, voice_id, output_path):
    async def run():
        communicator = edge_tts.Communicate(
            text=text,
            voice=VOICES[voice_id]["voice"]
        )
        await communicator.save(output_path)
    asyncio.run(run())

def audio_response(text, voice_id, filename, attachment):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp.close()
    try:
        create_audio(text, voice_id, temp.name)
        response = send_file(
            temp.name,
            as_attachment=attachment,
            download_name=filename,
            mimetype="audio/mpeg"
        )
        response.call_on_close(
            lambda: os.path.exists(temp.name) and os.remove(temp.name)
        )
        return response
    except Exception:
        if os.path.exists(temp.name):
            os.remove(temp.name)
        raise

@app.get("/")
def home():
    return render_template("index.html", voices=VOICES)

@app.post("/preview")
def preview():
    voice_id = request.form.get("voice", "gadis")
    if voice_id not in VOICES:
        return jsonify(error="Pilihan suara tidak valid."), 400
    try:
        return audio_response(
            PREVIEW_TEXT[voice_id], voice_id, "preview-suarakita.mp3", False
        )
    except Exception:
        return jsonify(error="Preview gagal. Periksa koneksi lalu coba lagi."), 500

@app.post("/generate")
def generate():
    text = request.form.get("narration", "").strip()
    voice_id = request.form.get("voice", "gadis")
    if not text:
        return jsonify(error="Kolom narasi masih kosong."), 400
    if voice_id not in VOICES:
        return jsonify(error="Pilihan suara tidak valid."), 400
    if len(text) > 100000:
        return jsonify(error="Teks terlalu panjang. Bagi menjadi beberapa bagian."), 413
    try:
        return audio_response(text, voice_id, "suarakita-narasi.mp3", True)
    except Exception:
        return jsonify(error="Gagal membuat audio. Coba lagi beberapa saat."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
