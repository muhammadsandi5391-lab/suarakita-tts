from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)

# Edge Neural voices. Presets below stylize these base voices; they are not
# separate trained anime character models.
VOICES = {
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"}
}

# 24 free style presets: pitch/rate processing on the available neural voices.
CHARACTERS = {
    "girl_kawaii": ("female", 18, 8), "girl_genki": ("female", 12, 18),
    "girl_soft": ("female", 8, -8), "girl_calm": ("female", -4, -12),
    "girl_ojou": ("female", 14, -4), "girl_tsundere": ("female", 10, 7),
    "girl_dere": ("female", 6, 3), "girl_mature": ("female", -8, -8),
    "girl_mysterious": ("female", -12, -10), "girl_hero": ("female", 4, 15),
    "girl_magical": ("female", 16, 4), "girl_narrator": ("female", -2, -5),
    "boy_shounen": ("male", 10, 15), "boy_cool": ("male", -8, -8),
    "boy_deep": ("male", -18, -10), "boy_soft": ("male", -4, -8),
    "boy_genki": ("male", 8, 18), "boy_hero": ("male", -2, 12),
    "boy_villain": ("male", -14, -5), "boy_prince": ("male", 2, -5),
    "boy_mysterious": ("male", -12, -12), "boy_comedy": ("male", 12, 12),
    "boy_narrator": ("male", -6, -4), "boy_young": ("male", 6, 8)
}

VIBES = {
    "netral": (0, 0), "ceria": (4, 8), "sedih": (-4, -12),
    "marah": (-2, 14), "romantis": (3, -8), "heroik": (-3, 10),
    "lembut": (2, -10), "dramatis": (-5, -5), "puitis": (1, -7)
}

PREVIEW_TEXT = {
    "id": "Halo! Ini contoh suara karakter SuaraKita. Bagaimana menurutmu?",
    "en": "Hello! This is a voice character preview from SuaraKita."
}

def fmt(value, unit):
    return f"{value:+d}{unit}"

def synthesize(text, language, character, vibe, output_path):
    gender, base_pitch, base_rate = CHARACTERS[character]
    vibe_pitch, vibe_rate = VIBES[vibe]
    pitch = max(-50, min(50, base_pitch + vibe_pitch))
    rate = max(-50, min(50, base_rate + vibe_rate))

    async def create():
        communicate = edge_tts.Communicate(
            text=text,
            voice=VOICES[language][gender],
            rate=fmt(rate, "%"),
            pitch=fmt(pitch, "Hz")
        )
        await communicate.save(output_path)

    asyncio.run(create())

def make_audio_response(text, language, character, vibe, filename):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    try:
        synthesize(text, language, character, vibe, tmp.name)
        response = send_file(tmp.name, as_attachment=True,
                             download_name=filename, mimetype="audio/mpeg")
        response.call_on_close(lambda: os.path.exists(tmp.name) and os.remove(tmp.name))
        return response
    except Exception:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
        raise

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/preview")
def preview():
    language = request.form.get("language", "id")
    character = request.form.get("character", "girl_kawaii")
    vibe = request.form.get("vibe", "netral")
    if language not in VOICES or character not in CHARACTERS or vibe not in VIBES:
        return jsonify(error="Pilihan suara tidak valid."), 400
    text = PREVIEW_TEXT[language]
    try:
        return make_audio_response(text, language, character, vibe, "preview-suarakita.mp3")
    except Exception:
        return jsonify(error="Preview gagal dibuat. Coba lagi sebentar."), 500

@app.post("/generate")
def generate():
    text = request.form.get("narration", "").strip()
    language = request.form.get("language", "id")
    character = request.form.get("character", "girl_kawaii")
    vibe = request.form.get("vibe", "netral")
    if not text:
        return jsonify(error="Kolom narasi masih kosong."), 400
    if language not in VOICES or character not in CHARACTERS or vibe not in VIBES:
        return jsonify(error="Pilihan suara tidak valid."), 400
    if len(text) > 100000:
        return jsonify(error="Teks terlalu panjang untuk satu proses. Bagi menjadi beberapa bagian."), 413
    try:
        return make_audio_response(text, language, character, vibe, "suarakita-narasi.mp3")
    except Exception:
        return jsonify(error="Gagal membuat audio. Coba lagi beberapa saat."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
