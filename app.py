import io
from pathlib import Path

import mido
from flask import Flask, request, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # лимит загрузки 5 мб

PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MIDI → SPIKE</title>
<style>
  body { margin: 0; font-family: Inter, -apple-system, Segoe UI, sans-serif; background: #f8f9fa; color: #202124; }
  header { background: #fff; border-bottom: 1px solid #dadce0; padding: 14px 24px; font-weight: 700; font-size: 20px; }
  header span { color: #20beff; }
  main { max-width: 560px; margin: 48px auto; padding: 0 16px; }
  .card { background: #fff; border: 1px solid #dadce0; border-radius: 8px; padding: 32px; }
  h1 { font-size: 22px; margin: 0 0 8px; }
  p { color: #5f6368; margin: 0 0 24px; font-size: 14px; }
  input[type=file] { display: block; width: 100%; margin-bottom: 20px; font-size: 14px; }
  input::file-selector-button { border: 1px solid #dadce0; background: #fff; border-radius: 20px; padding: 8px 16px; margin-right: 12px; cursor: pointer; }
  button { background: #202124; color: #fff; border: 0; border-radius: 20px; padding: 10px 24px; font-size: 14px; font-weight: 600; cursor: pointer; }
  button:hover { background: #20beff; }
</style></head><body>
<header>spike<span>song</span></header>
<main><div class="card">
  <h1>Песня → Prime Hub</h1>
  <p>Загрузите MIDI-файл и получите Python-скрипт для LEGO SPIKE Prime.</p>
  <form method="post" action="/convert" enctype="multipart/form-data">
    <input type="file" name="file" accept=".mid,.midi,.mobi" required>
    <button type="submit">Выгрузить скрипт</button>
  </form>
</div></main></body></html>"""

TEMPLATE = """from hub import sound
import runloop

# (частота гц, длительность мс), 0 = пауза
SONG = {song}


async def main():
    for f, d in SONG:
        if f:
            await sound.beep(f, d, 100)
        else:
            await runloop.sleep_ms(d)


runloop.run(main())
"""


def melody(mid):
    # собираем ноты без барабанов
    t, on, notes = 0.0, {}, []
    for m in mid:  # время уже в секундах с учётом темпа
        t += m.time
        if m.type not in ("note_on", "note_off") or m.channel == 9:
            continue
        key = (m.channel, m.note)
        if m.type == "note_on" and m.velocity:
            on[key] = t
        elif key in on:
            notes.append((on.pop(key), t, m.note))

    # самая высокая нота из одновременных
    # перекрывающиеся ноты просто отбрасываются, нужен skyline если мелодия теряется
    notes.sort(key=lambda n: (n[0], -n[2]))
    out, cur = [], 0.0
    for s, e, p in notes:
        if s < cur:
            continue
        rest = round((s - cur) * 1000)
        if rest >= 10:
            out.append((0, rest))
        out.append((round(440 * 2 ** ((p - 69) / 12)), max(1, round((e - s) * 1000))))
        cur = e
    return out


def to_script(data):
    song = melody(mido.MidiFile(file=io.BytesIO(data)))
    if not song:
        raise ValueError("в файле нет нот")
    return TEMPLATE.format(song="[\n" + "".join(f"    {n},\n" for n in song) + "]")


@app.get("/")
def index():
    return PAGE


@app.post("/convert")
def convert():
    f = request.files.get("file")
    if not f:
        return "файл не выбран", 400
    try:
        script = to_script(f.read())
    except Exception as e:  # битый или не midi файл
        return f"не удалось прочитать файл: {e}", 400
    name = Path(f.filename or "song").stem + ".py"
    return send_file(io.BytesIO(script.encode()), as_attachment=True, download_name=name, mimetype="text/x-python")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
