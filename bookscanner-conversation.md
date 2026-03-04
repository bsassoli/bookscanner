# Raspberry Pi Book Scanner — Conversation Log

## Topic
Setting up a Raspberry Pi AI Camera (IMX500) to scan book barcodes, retrieve ISBN metadata, and display book info on stdout. Future goal: store data in SQLite and expose via Datasette dashboard through a Cloudflare Tunnel.

---

## Stack decided

- **pyzbar + OpenCV** — barcode decoding from camera feed
- **picamera2** — camera interface for IMX500 on Raspberry Pi OS (Bookworm)
- **Open Library API** — ISBN metadata lookup (title, authors, year, publisher)
- **SQLite + Datasette** — local storage + web dashboard (next phase)
- **Cloudflare Tunnel** — remote access to dashboard (next phase)

---

## Issues encountered and solutions

### 1. `ModuleNotFoundError: No module named 'pyzbar'`
Needed a virtual environment since Raspberry Pi OS uses an externally managed Python.
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install opencv-python pyzbar requests setuptools
```

### 2. `ModuleNotFoundError: No module named 'pkg_resources'`
`isbntools` is incompatible with Python 3.13 — depends on `pkg_resources` from `setuptools` in a broken way.  
**Solution:** replaced `isbntools` entirely with direct calls to the **Open Library API** using `requests`.
```bash
pip uninstall isbntools isbnlib -y
pip install requests
```

### 3. `picamera2 not found` inside venv
`picamera2` is installed system-wide via apt but not visible inside the venv.  
**Solution:** recreate venv with `--system-site-packages`:
```bash
deactivate
rm -rf .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install opencv-python pyzbar requests
```

### 4. `Camera frontend has timed out!`
Physical issue — ribbon cable not properly seated in CSI connector.  
**Solution:** full power off, reseat ribbon carefully, power back on.

### 5. `qt.qpa.xcb: could not connect to display`
Running over SSH without a display. Script was trying to open `cv2.imshow` window.  
**Solution:** connect via VNC viewer instead, or refactor script to headless mode.

### 6. `RuntimeError: Control AfMode is not advertised by libcamera`
IMX500 has a **fixed focus lens** — software autofocus control is not supported.  
**Solution:** manually rotate the physical lens ring using the plastic tool included in the box.

### 7. Preview image all blue
Classic RGB/BGR channel swap between picamera2 (RGB) and OpenCV (BGR).  
Already handled in script with `cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)` before display.

### 8. Camera window covers the terminal on VNC desktop
Add these lines to reposition and resize the OpenCV window:
```python
cv2.namedWindow("Scanner Libri  [q per uscire]", cv2.WINDOW_NORMAL)
cv2.moveWindow("Scanner Libri  [q per uscire]", 0, 0)
cv2.resizeWindow("Scanner Libri  [q per uscire]", 640, 480)
```

---

## Final script (`scan_book.py`)

```python
#!/usr/bin/env python3
"""
scan_book.py - Scanner di barcode ISBN con Raspberry Pi AI Camera (IMX500)

Installazione dipendenze:
    sudo apt install -y python3-picamera2 libzbar0
    pip install opencv-python pyzbar requests setuptools

Utilizzo:
    python3 scan_book.py           # con AI Camera
    python3 scan_book.py --manual  # inserimento ISBN manuale (test senza camera)
"""

import sys
import requests
import cv2
from pyzbar import pyzbar


def fetch_book_data(isbn: str) -> dict | None:
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        key = f"ISBN:{isbn}"
        if key not in data:
            return None
        return data[key]
    except requests.RequestException as e:
        print(f"[ERRORE] Chiamata API fallita: {e}", file=sys.stderr)
        return None


def print_book_data(isbn: str, dati: dict):
    autori = ", ".join(a["name"] for a in dati.get("authors", [])) or "N/D"
    anno = dati.get("publish_date", "N/D")
    editori = ", ".join(p["name"] for p in dati.get("publishers", [])) or "N/D"
    pagine = dati.get("number_of_pages", "N/D")

    print("\n" + "═" * 52)
    print(f"  ISBN     : {isbn}")
    print(f"  Titolo   : {dati.get('title', 'N/D')}")
    print(f"  Autori   : {autori}")
    print(f"  Anno     : {anno}")
    print(f"  Editore  : {editori}")
    print(f"  Pagine   : {pagine}")
    print("═" * 52 + "\n")


def scan_from_camera():
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("[ERRORE] picamera2 non trovata.", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Avvio AI Camera... premi 'q' per uscire.")

    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
    picam2.configure(config)
    picam2.start()

    cv2.namedWindow("Scanner Libri  [q per uscire]", cv2.WINDOW_NORMAL)
    cv2.moveWindow("Scanner Libri  [q per uscire]", 0, 0)
    cv2.resizeWindow("Scanner Libri  [q per uscire]", 640, 480)

    scanned_isbns = set()

    while True:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        barcodes = pyzbar.decode(gray)

        for barcode in barcodes:
            isbn = barcode.data.decode("utf-8").strip()
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, isbn, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            if isbn not in scanned_isbns:
                scanned_isbns.add(isbn)
                print(f"\n[SCAN] Barcode rilevato: {isbn}")
                print("[INFO] Recupero metadati da Open Library...")
                dati = fetch_book_data(isbn)
                if dati:
                    print_book_data(isbn, dati)
                else:
                    print(f"[WARN] Libro non trovato per ISBN: {isbn}\n")

        display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Scanner Libri  [q per uscire]", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    picam2.stop()
    cv2.destroyAllWindows()


def scan_from_input():
    print("[MANUAL] Modalità inserimento ISBN manuale. Digita 'q' per uscire.\n")
    while True:
        try:
            isbn = input("ISBN > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if isbn.lower() == "q" or not isbn:
            break
        dati = fetch_book_data(isbn)
        if dati:
            print_book_data(isbn, dati)
        else:
            print(f"[WARN] Nessun dato trovato per: {isbn}\n")


if __name__ == "__main__":
    if "--manual" in sys.argv:
        scan_from_input()
    else:
        scan_from_camera()
```

---

## Next steps

- Add SQLite storage to persist scanned books locally
- Set up Datasette to serve the SQLite database as a web UI
- Configure Cloudflare Tunnel to expose Datasette publicly
- Add a `systemd` service to auto-start the scanner on boot
