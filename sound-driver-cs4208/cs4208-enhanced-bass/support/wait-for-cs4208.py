#!/usr/bin/python3
"""Wait for the split bass PCM to be usable through ALSA before PipeWire."""
import ctypes
import ctypes.util
import time
from pathlib import Path
try:
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBookPro11,4':
        raise SystemExit(0)
except OSError:
    raise SystemExit(0)
alsa = ctypes.CDLL(ctypes.util.find_library('asound') or 'libasound.so.2')
alsa.snd_pcm_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
alsa.snd_pcm_open.restype = ctypes.c_int
alsa.snd_pcm_close.argtypes = [ctypes.c_void_p]
for attempt in range(120):
    for card in Path('/proc/asound').glob('card[0-9]*'):
        try:
            if card.is_symlink() or card.joinpath('id').read_text().strip() != 'PCH':
                continue
            codec = card.joinpath('codec#0').read_text()
            if 'Vendor Id: 0x10134208' not in codec or 'Subsystem Id: 0x106b8000' not in codec:
                continue
            if 'CS4208 Bass Stereo' not in card.joinpath('pcm2p/info').read_text():
                continue
            pcm = ctypes.c_void_p()
            if alsa.snd_pcm_open(ctypes.byref(pcm), b'hw:PCH,2', 0, 1) == 0:
                alsa.snd_pcm_close(pcm)
                print('CS4208 split bass PCM ready through ALSA.', flush=True)
                raise SystemExit(0)
        except OSError:
            continue
    time.sleep(.25)
print('CS4208 bass PCM unavailable after 30s; allowing PipeWire startup without it.', flush=True)
