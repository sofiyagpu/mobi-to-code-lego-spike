# midi-to-code-lego-spike
"convert" any midi file melody to primehub compatible program 

```
docker build -t spike-song . && docker run -p 8000:8000 spike-song
```
open http://localhost:8000, pick a `.mid` file, get a `.py` for the SPIKE App 3 (Python).
