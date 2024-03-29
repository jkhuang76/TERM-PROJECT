import aubio
import module_manager
import numpy as np


"""A simple example using aubio.source."""

import sys



samplerate = 0  # use original source samplerate
hop_size = 256  # number of frames to read in one block
src = aubio.source("88.wav", samplerate, hop_size)
total_frames = 0

while True:
    samples, read = src()  # read hop_size new samples from source
    total_frames += read   # increment total number of frames
    if read < hop_size:    # end of file reached
        break

fmt_string = "read {:d} frames at {:d}Hz from {:s}"
print(fmt_string.format(total_frames, src.samplerate, src.uri))
module_manager.review()