import sounddevice as sd
from scipy.io.wavfile import write
import wave
import json
from vosk import Model, KaldiRecognizer

# -------------------
# RECORD AUDIO
# -------------------
fs = 16000  # Vosk works best at 16kHz
seconds = 3

print("Recording...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()
print("Done!")

write("test.wav", fs, audio)

# -------------------
# LOAD MODEL
# -------------------
model = Model("model")

wf = wave.open("test.wav", "rb")

rec = KaldiRecognizer(model, wf.getframerate())

# -------------------
# PROCESS AUDIO
# -------------------
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break

    if rec.AcceptWaveform(data):
        print(rec.Result())