import module_manager
module_manager.review()
import aubio 


win_s = 1024               # fft size
hop_s = win_s // 2          # hop size
sampleRate = 48000

src = aubio.source("Another One Bites The Dust.wav", sampleRate, hop_s)
source_tempo = aubio.tempo("default", win_s, hop_s, sampleRate)
beats = []

total_frames = 0
i= 0
for frame in src: 
    samples, read = src()
    is_beat = source_tempo(samples)
    if (is_beat):
        beats.append(i)
        i+=1
    total_frames+= read
"""
while True:
    samples, read = src()
        # do something with samples
    is_beat = source_tempo(samples)
    if (is_beat):
        this_beat = int(total_frames + is_beat[0] * hop_s)
        this_beat = (this_beat/float(sampleRate))
        beats.append(this_beat)
    total_frames += read
    if read < src.hop_size:
        break
"""

print(len(beats))