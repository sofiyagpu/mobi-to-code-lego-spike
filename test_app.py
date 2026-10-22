import io

import mido

from app import app, melody

# аккорд до-ми-соль, пауза, ля 440
mid = mido.MidiFile()
tr = mido.MidiTrack()
mid.tracks.append(tr)
tr += [mido.Message("note_on", note=n, velocity=64, time=0) for n in (60, 64, 67)]
tr += [mido.Message("note_off", note=60, time=480), mido.Message("note_off", note=64), mido.Message("note_off", note=67)]
tr.append(mido.Message("note_on", note=69, velocity=64, time=480))
tr.append(mido.Message("note_off", note=69, time=480))

assert melody(mid) == [(392, 500), (0, 500), (440, 500)], melody(mid)

buf = io.BytesIO()
mid.save(file=buf)
res = app.test_client().post("/convert", data={"file": (io.BytesIO(buf.getvalue()), "song.mid")})
assert res.status_code == 200 and b"(440, 500)" in res.data
assert app.test_client().post("/convert", data={"file": (io.BytesIO(b"junk"), "x.mid")}).status_code == 400
print("ok")
