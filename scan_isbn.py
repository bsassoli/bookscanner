#!/usr/bin/env python3
"""
scan_isbn.py - Scansiona barcode con AI Camera e stampa ISBN su stdout.
Nessuna finestra grafica, funziona in SSH/headless.

Dipendenze:
    sudo apt install -y python3-picamera2 libzbar0
    pip install pyzbar

Utilizzo:
    python3 scan_isbn.py
"""

import sys
import numpy as np
from pyzbar import pyzbar

try:
    from picamera2 import Picamera2
except ImportError:
    print("[ERRORE] picamera2 non trovata: sudo apt install python3-picamera2", file=sys.stderr)
    sys.exit(1)


def main():
    print("[INFO] Avvio camera... punta il barcode. Ctrl+C per uscire.", file=sys.stderr)

    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
    picam2.configure(config)
    picam2.start()

    scanned = set()
    frame_count = 0

    try:
        while True:
            frame = picam2.capture_array()

            # Decodifica solo ogni 3 frame per risparmiare CPU
            if frame_count % 3 == 0:
                gray = np.dot(frame[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
                barcodes = pyzbar.decode(gray)
            else:
                barcodes = []
            frame_count += 1

            for barcode in barcodes:
                isbn = barcode.data.decode("utf-8").strip()
                if isbn and isbn not in scanned:
                    scanned.add(isbn)
                    print("\a", end="", file=sys.stderr, flush=True)
                    print(isbn)          # stampa su stdout, pulito
                    sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop()
        print("[INFO] Camera chiusa.", file=sys.stderr)


if __name__ == "__main__":
    main()

