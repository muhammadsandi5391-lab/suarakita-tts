from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)

VOICES = {
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"}
}
VIBES = {
    "ceria": {"rate": "+12%", "pitch": "+8Hz"},
    "sedih": {"rate": "-12%", "pitch": "-5Hz"},
    "puitis": {"rate": "-5%", "pitch": "+2Hz"},
    "tenang": {"rate": "-8%", "pitch": "-1Hz"},
    "tegas": {"rate": "+3%", "pitch": "-2Hz"},
    "netral": {"rate": "+0%", "pitch": "+0Hz"}
}

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/generate")
def generate():
    text = request.form.get("narration", "").strip()
    language = request.form.get("language", "id")
    gender = request.form.get("gender", "female")
    vibe = request.form.get("vibe", "netral")
    if not text:
        return jsonify(error="Kolom narasi masih kosong."), 400
    if language not in VOICES or gender not in VOICES[language] or vibe not in VIBES:
        return jsonify(error="Pilihan suara tidak valid."), 400
    if len(text) > 100000:
        return jsonify(error="Teks terlalu panjang untuk satu proses. Bagi menjadi beberapa bagian."), 413

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    async def create_audio():
        await edge_tts.Communicate(
            text=text,
            voice=VOICES[language][gender],
            rate=VIBES[vibe]["rate"],
            pitch=VIBES[vibe]["pitch"]
        ).save(tmp.name)

    try:
        asyncio.run(create_audio())
        response = send_file(tmp.name, as_attachment=True,
                             download_name="narasi-suara.mp3",
                             mimetype="audio/mpeg")
        response.call_on_close(lambda: os.path.exists(tmp.name) and os.remove(tmp.name))
        return response
    except Exception as exc:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
        return jsonify(error="Gagal membuat audio. Coba lagi beberapa saat."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
