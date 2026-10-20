
import os
import re
import json
import uuid
from pathlib import Path

from flask import (
    Flask, request, render_template_string,
    redirect, url_for, flash, send_from_directory
)
from werkzeug.utils import secure_filename

# ==========================================
# VOICEVERSE AI - STORY THEATRE
# Laptop-only Flask application
# ==========================================

BASE = Path(__file__).resolve().parent
DATA = BASE / "voiceverse_data"
IMAGES = DATA / "images"

DATA.mkdir(exist_ok=True)
IMAGES.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = "voiceverse-local-secret"
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

ALLOWED = {".png", ".jpg", ".jpeg", ".webp"}


# ==========================================
# HTML PAGE
# ==========================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VoiceVerse AI - Story Theatre</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: radial-gradient(circle at top right,
        #25204d, #0b1020 55%);
    font-family: Segoe UI, Arial, sans-serif;
    color: #f4f6ff;
}

.wrap {
    max-width: 1100px;
    margin: auto;
    padding: 28px 16px 60px;
}

.pill {
    display: inline-block;
    background: #211e4a;
    border: 1px solid #514b94;
    padding: 7px 12px;
    border-radius: 30px;
    color: #dcd8ff;
    font-size: 12px;
}

h1 {
    font-size: clamp(32px, 5vw, 50px);
    line-height: 1.1;
}

.gradient { color: #a79cff; }

.lead, .muted, small {
    color: #aeb8d0;
    line-height: 1.6;
}

.card {
    background: #141b2e;
    border: 1px solid #2b3652;
    border-radius: 18px;
    padding: 20px;
    margin-top: 18px;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(250px, 1fr));
    gap: 14px;
}

label {
    display: block;
    font-weight: 600;
    margin: 14px 0 7px;
}

textarea, input, select {
    width: 100%;
    padding: 11px 12px;
    border: 1px solid #364260;
    background: #0e1527;
    color: #f4f6ff;
    border-radius: 10px;
    font: inherit;
}

textarea {
    min-height: 130px;
    resize: vertical;
}

.btn {
    border: 0;
    border-radius: 10px;
    padding: 12px 16px;
    background: linear-gradient(100deg, #8b7cff, #5c8dff);
    color: white;
    font-weight: 700;
    cursor: pointer;
    margin: 5px 5px 5px 0;
}

.secondary { background: #263451; }

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.tip, .flash {
    padding: 12px;
    border-radius: 10px;
    margin: 12px 0;
    line-height: 1.5;
}

.tip {
    background: #10182a;
    border: 1px solid #2b3652;
    color: #aeb8d0;
}

.flash {
    background: #48252d;
    border: 1px solid #8e4653;
}

.scene {
    background: #0e1527;
    border: 1px solid #2b3652;
    border-radius: 12px;
    padding: 12px;
    overflow-wrap: anywhere;
}

.scene img {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    background: #080d18;
    border-radius: 8px;
    display: block;
}

.scene p { line-height: 1.6; }

.scene textarea { min-height: 110px; }

.active { outline: 2px solid #9c8fff; }

.stage img {
    width: 100%;
    max-height: 520px;
    aspect-ratio: 16 / 9;
    object-fit: contain;
    background: #080d18;
    border-radius: 12px;
}

.storyline {
    font-size: 19px;
    line-height: 1.7;
    margin: 14px 0;
    white-space: pre-wrap;
}

.row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: end;
}

.row > div {
    flex: 1;
    min-width: 160px;
}

.status {
    color: #b9b0ff;
    min-height: 24px;
}

@media(max-width: 600px) {
    .card { padding: 15px; }
}
</style>
</head>

<body>
<main class="wrap">

<span class="pill">VOICEVERSE AI · STORY THEATRE</span>

<h1>Your story.<br>
<span class="gradient">Your scenes. Your voice.</span></h1>

<p class="lead">
Paste your English story, create scene prompts, generate images
using Bing or another image website, upload those images, and
play your story with browser narration.
</p>

{% with messages = get_flashed_messages() %}
{% if messages %}
{% for message in messages %}
<div class="flash">{{ message }}</div>
{% endfor %}
{% endif %}
{% endwith %}

{% if scenes is none %}

<section class="card">
<h2>1 · Enter your story</h2>

<form method="post" action="{{ url_for('prepare') }}">

<label>Story text</label>
<textarea name="story" required
placeholder="Paste your complete English story here..."></textarea>

<div class="grid">
<div>
<label>Main character appearance</label>
<input name="character"
placeholder="18-year-old boy, black hair, blue hoodie">
</div>

<div>
<label>Image style</label>
<select name="style">
<option>realistic cinematic</option>
<option>anime illustration</option>
<option>3D animated movie</option>
<option>watercolor storybook</option>
<option>fantasy cinematic</option>
</select>
</div>
</div>

<button class="btn" type="submit">
Create Scenes and Prompts
</button>
</form>

<div class="tip">
This app creates prompts. You must generate and download images
from an image website, then upload them into the matching scenes.
</div>
</section>

{% else %}

<section class="card">
<h2>2 · Generate and upload images</h2>

<a class="btn secondary" href="{{ url_for('index') }}">
Start New Story
</a>

<p class="muted">
Copy a scene prompt, generate an image, download it, and upload
it to the matching scene. Use the same character description
for every scene.
</p>

<div class="tip">
Image website:
<a style="color:#c5bcff"
target="_blank" rel="noopener"
href="https://www.bing.com/images/create">
Bing Image Creator
</a>
</div>

<div class="grid">
{% for s in scenes %}
<div class="scene" id="scene-{{ loop.index0 }}">

<h3>
Scene {{ loop.index }}
{% if s.filename %} ✓{% endif %}
</h3>

{% if s.filename %}
<img
src="{{ url_for('image_file', filename=s.filename) }}"
alt="Scene {{ loop.index }}">
{% else %}
<div style="aspect-ratio:16/9;display:grid;
place-items:center;background:#080d18;border-radius:8px">
Upload your generated image
</div>
{% endif %}

<p>{{ s.text }}</p>

<label>Image prompt</label>
<textarea id="prompt-{{ loop.index0 }}" readonly>{{ s.prompt }}</textarea>

<button
class="btn secondary copy-btn"
type="button"
data-index="{{ loop.index0 }}"
onclick="copyPrompt({{ loop.index0 }}, this)">
Copy Prompt
</button>

<form method="post"
action="{{ url_for('upload_image',
job_id=job_id, index=loop.index0) }}"
enctype="multipart/form-data">

<label>Choose image</label>
<input type="file" name="image"
accept=".png,.jpg,.jpeg,.webp" required>

<button class="btn" type="submit">Upload Image</button>
</form>

<p class="status" id="copy-status-{{ loop.index0 }}"
aria-live="polite"></p>

</div>
{% endfor %}
</div>
</section>

<section class="card stage">
<h2>3 · Play your story</h2>

<p class="muted">
Narration uses the voice available in your laptop browser.
Available languages depend on Windows and your browser.
</p>

<div class="row">
<div>
<label>Voice speed</label>
<select id="rate">
<option value="0.65">Very slow</option>
<option value="0.8" selected>Slow and clear</option>
<option value="0.95">Normal-slow</option>
<option value="1">Normal</option>
</select>
</div>

<div>
<label>Voice language</label>
<select id="lang">
<option value="en">English</option>
<option value="ta">Tamil</option>
<option value="hi">Hindi</option>
</select>
</div>

<div>
<label>Target duration</label>
<select id="target">
<option value="30">About 30 seconds</option>
<option value="60">About 1 minute</option>
<option value="0" selected>Natural length</option>
</select>
</div>
</div>

<img id="stage-image" alt="Current story scene"
style="display:none">

<div id="stage-text" class="storyline">
Upload at least one image to start.
</div>

<button class="btn" id="play" type="button">▶ Play Story</button>
<button class="btn secondary" id="pause" type="button">Pause</button>
<button class="btn secondary" id="prev" type="button">← Previous</button>
<button class="btn secondary" id="next" type="button">Next →</button>

<p class="muted" id="counter"></p>
<p class="status" id="voice-status" aria-live="polite"></p>
</section>

<script>
"use strict";

const scenes = {{ scenes_json | safe }};
let current = 0;
let playing = false;
let utterance = null;
let playToken = 0;
let advanceTimer = null;

function ready() {
    return scenes
        .map((scene, index) => ({...scene, idx: index}))
        .filter(scene => scene.filename);
}

function setCopyStatus(index, message) {
    const status = document.getElementById("copy-status-" + index);
    if (status) status.textContent = message;
}

// Copy prompt: Clipboard API with fallback for local laptop use.
async function copyPrompt(index, button) {
    const box = document.getElementById("prompt-" + index);
    if (!box) return;

    const text = box.value;

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else {
            throw new Error("Clipboard API unavailable");
        }

        setCopyStatus(index, "Prompt copied successfully!");
        button.textContent = "Copied!";
        setTimeout(() => {
            button.textContent = "Copy Prompt";
        }, 1800);
        return;
    } catch (error) {
        // Continue to fallback.
    }

    // Fallback: select the text and request browser copy.
    box.focus();
    box.select();
    box.setSelectionRange(0, box.value.length);

    let success = false;
    try {
        success = document.execCommand("copy");
    } catch (error) {
        success = false;
    }

    if (success) {
        setCopyStatus(index, "Prompt copied successfully!");
        button.textContent = "Copied!";
        setTimeout(() => {
            button.textContent = "Copy Prompt";
        }, 1800);
    } else {
        setCopyStatus(index, "Text selected. Press Ctrl+C to copy.");
        alert("The prompt is selected. Press Ctrl+C, then paste it into Bing.");
    }
}

function stopSpeech() {
    playing = false;
    playToken++;

    if (advanceTimer !== null) {
        clearTimeout(advanceTimer);
        advanceTimer = null;
    }

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
}

function show(index) {
    const available = ready();

    if (!available.length) {
        document.getElementById("stage-text").textContent =
            "Upload at least one image first.";
        document.getElementById("stage-image").style.display = "none";
        return false;
    }

    current = Math.max(0, Math.min(index, available.length - 1));

    const scene = available[current];
    const image = document.getElementById("stage-image");

    image.src = "/uploaded-image/" + encodeURIComponent(scene.filename);
    image.style.display = "block";

    document.getElementById("stage-text").textContent = scene.text;
    document.getElementById("counter").textContent =
        "Scene " + (current + 1) + " of " + available.length;

    document.querySelectorAll(".scene").forEach(card => {
        card.classList.remove("active");
    });

    const card = document.getElementById("scene-" + scene.idx);
    if (card) card.classList.add("active");

    return true;
}

function getVoice(language) {
    const voices = window.speechSynthesis.getVoices();

    const prefix = language === "ta" ? "ta" :
                   language === "hi" ? "hi" : "en";

    return voices.find(v => v.lang.toLowerCase() ===
                    (prefix === "ta" ? "ta-in" :
                     prefix === "hi" ? "hi-in" : "en-us"))
        || voices.find(v => v.lang.toLowerCase().startsWith(prefix))
        || null;
}

function speakCurrent(token) {
    const available = ready();

    if (!playing || token !== playToken) return;

    if (current >= available.length) {
        playing = false;
        document.getElementById("counter").textContent = "Story finished!";
        document.getElementById("voice-status").textContent =
            "Narration complete.";
        return;
    }

    const scene = available[current];
    show(current);

    if (!("speechSynthesis" in window) ||
        !("SpeechSynthesisUtterance" in window)) {
        playing = false;
        document.getElementById("voice-status").textContent =
            "Speech is unavailable. Try Microsoft Edge or Google Chrome.";
        return;
    }

    const language = document.getElementById("lang").value;
    const rate = Number(document.getElementById("rate").value);
    const target = Number(document.getElementById("target").value);

    utterance = new SpeechSynthesisUtterance(scene.text);
    utterance.lang = language === "ta" ? "ta-IN" :
                     language === "hi" ? "hi-IN" : "en-US";
    utterance.rate = rate;

    const voice = getVoice(language);
    if (voice) utterance.voice = voice;

    document.getElementById("voice-status").textContent =
        "Playing scene " + (current + 1) + "...";

    utterance.onend = function() {
        if (!playing || token !== playToken) return;

        if (current + 1 >= available.length) {
            playing = false;
            document.getElementById("counter").textContent = "Story finished!";
            document.getElementById("voice-status").textContent =
                "Narration complete.";
            return;
        }

        let wait = 250;

        if (target > 0) {
            const pauseBetweenScenes = 300;
            wait = pauseBetweenScenes;
        }

        advanceTimer = setTimeout(function() {
            if (!playing || token !== playToken) return;
            current++;
            speakCurrent(token);
        }, wait);
    };

    utterance.onerror = function(event) {
        if (token !== playToken) return;
        playing = false;
        document.getElementById("voice-status").textContent =
            "Voice stopped: " + (event.error || "unknown error");
    };

    window.speechSynthesis.speak(utterance);
}

document.getElementById("play").addEventListener("click", function() {
    if (!ready().length) {
        alert("Upload at least one generated image first.");
        return;
    }

    stopSpeech();

    if (current >= ready().length) current = 0;

    playing = true;
    const token = playToken;
    speakCurrent(token);
});

document.getElementById("pause").addEventListener("click", function() {
    stopSpeech();
    document.getElementById("voice-status").textContent = "Playback paused.";
});

document.getElementById("prev").addEventListener("click", function() {
    stopSpeech();
    show(current - 1);
    document.getElementById("voice-status").textContent = "Previous scene.";
});

document.getElementById("next").addEventListener("click", function() {
    stopSpeech();
    show(current + 1);
    document.getElementById("voice-status").textContent = "Next scene.";
});

window.speechSynthesis?.getVoices();

if (ready().length) {
    show(0);
}
</script>

{% endif %}

</main>
</body>
</html>
"""


# ==========================================
# STORY HELPERS
# ==========================================

def split_story(story, max_scenes=6):
    story = re.sub(r"\s+", " ", story).strip()

    if not story:
        return []

    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", story)
        if part.strip()
    ]

    if len(sentences) <= max_scenes:
        return sentences

    groups = [[] for _ in range(max_scenes)]

    for index, sentence in enumerate(sentences):
        group_index = min(
            index * max_scenes // len(sentences),
            max_scenes - 1
        )
        groups[group_index].append(sentence)

    return [" ".join(group) for group in groups if group]


def make_prompt(text, character, style):
    character = character.strip() or (
        "a fictional character with consistent appearance across scenes"
    )

    return (
        f"Create one {style} movie still in widescreen 16:9. "
        f"Main character appearance: {character}. "
        f"Show this story moment visually: {text}. "
        "Clear visible action, expressive natural face, detailed setting, "
        "cinematic lighting. No captions, readable text, logos or watermark. "
        "Keep face, age, hairstyle and clothing consistent across scenes."
    )


def load_scenes(job_id):
    # Prevent path traversal.
    if not re.fullmatch(r"[a-f0-9]{12}", job_id):
        return None

    path = DATA / f"{job_id}.json"

    if not path.is_file():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ==========================================
# ROUTES
# ==========================================

@app.route("/")
def index():
    return render_template_string(HTML, scenes=None)


@app.route("/prepare", methods=["POST"])
def prepare():
    story = request.form.get("story", "").strip()

    if not story:
        flash("Please paste your story first.")
        return redirect(url_for("index"))

    if len(story) > 50000:
        flash("Story is too long. Please keep it under 50,000 characters.")
        return redirect(url_for("index"))

    character = request.form.get("character", "")
    style = request.form.get("style", "realistic cinematic")

    scenes = [
        {
            "text": text,
            "prompt": make_prompt(text, character, style),
            "filename": ""
        }
        for text in split_story(story, 6)
    ]

    if not scenes:
        flash("No story sentences were found.")
        return redirect(url_for("index"))

    job_id = uuid.uuid4().hex[:12]
    path = DATA / f"{job_id}.json"
    path.write_text(
        json.dumps(scenes, ensure_ascii=False),
        encoding="utf-8"
    )

    return redirect(url_for("story_page", job_id=job_id))


@app.route("/story/<job_id>")
def story_page(job_id):
    scenes = load_scenes(job_id)

    if scenes is None:
        flash("Story session not found. Please start a new story.")
        return redirect(url_for("index"))

    return render_template_string(
        HTML,
        scenes=scenes,
        scenes_json=json.dumps(scenes, ensure_ascii=False),
        job_id=job_id
    )


@app.route("/upload/<job_id>/<int:index>", methods=["POST"])
def upload_image(job_id, index):
    scenes = load_scenes(job_id)

    if scenes is None:
        flash("Story session not found. Please start again.")
        return redirect(url_for("index"))

    if not 0 <= index < len(scenes):
        flash("Invalid scene.")
        return redirect(url_for("story_page", job_id=job_id))

    image = request.files.get("image")

    if not image or not image.filename:
        flash("Please choose an image first.")
        return redirect(url_for("story_page", job_id=job_id))

    safe_name = secure_filename(image.filename)
    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED:
        flash("Please use PNG, JPG, JPEG or WEBP images.")
        return redirect(url_for("story_page", job_id=job_id))

    filename = f"{job_id}_scene_{index + 1}{extension}"
    destination = IMAGES / filename

    image.save(destination)

    scenes[index]["filename"] = filename

    (DATA / f"{job_id}.json").write_text(
        json.dumps(scenes, ensure_ascii=False),
        encoding="utf-8"
    )

    flash(f"Image uploaded successfully for Scene {index + 1}.")
    return redirect(url_for("story_page", job_id=job_id))


@app.route("/uploaded-image/<path:filename>")
def image_file(filename):
    # Only serve files stored in our image folder.
    return send_from_directory(IMAGES, filename, as_attachment=False)


# ==========================================
# RUN ON THIS LAPTOP ONLY
# ==========================================

if __name__ == "__main__":
    print("=" * 45)
    print("VOICEVERSE AI STORY THEATRE")
    print("Running on this laptop only.")
    print("Open: http://127.0.0.1:5000")
    print("Press CTRL+C in the terminal to stop.")
    print("=" * 45)

    app.run(host="127.0.0.1", port=5000, debug=False)
