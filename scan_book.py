#!/usr/bin/env python3
"""
scan_book.py - Scanner di barcode ISBN con Raspberry Pi AI Camera (IMX500)
Usa picamera2 per il feed video, pyzbar per decodificare i barcode,
e Open Library API per recuperare i metadati del libro.

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


# ──────────────────────────────────────────────
# Lookup metadati da Open Library API
# ──────────────────────────────────────────────

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
    # Autori
    autori = ", ".join(a["name"] for a in dati.get("authors", [])) or "N/D"

    # Anno pubblicazione
    anno = dati.get("publish_date", "N/D")

    # Editori
    editori = ", ".join(p["name"] for p in dati.get("publishers", [])) or "N/D"

    # Numero pagine
    pagine = dati.get("number_of_pages", "N/D")

    print("\n" + "═" * 52)
    print(f"  ISBN     : {isbn}")
    print(f"  Titolo   : {dati.get('title', 'N/D')}")
    print(f"  Autori   : {autori}")
    print(f"  Anno     : {anno}")
    print(f"  Editore  : {editori}")
    print(f"  Pagine   : {pagine}")
    print("═" * 52 + "\n")


# ──────────────────────────────────────────────
# Modalità camera: picamera2 + pyzbar
# ──────────────────────────────────────────────

def scan_from_camera():
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("[ERRORE] picamera2 non trovata. Installa con: sudo apt install python3-picamera2", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Avvio AI Camera... premi 'q' per uscire.")

    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (1280, 720)}
    )

    picam2.configure(config)
    picam2.start()

    scanned_isbns = set()

    while True:
        frame = picam2.capture_array()
        barcodes = pyzbar.decode(frame)

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
        cv2.moveWindow("Scanner Libri  [q per uscire]", 0, 0)
        cv2.resizeWindow("Scanner Libri  [q per uscire]", 640, 480)
        
        cv2.namedWindow("Scanner Libri  [q per uscire]", cv2.WINDOW_NORMAL)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    picam2.stop()
    cv2.destroyAllWindows()
    print("[INFO] Camera chiusa.")


# ──────────────────────────────────────────────
# Modalità manuale: ISBN da tastiera (per test)
# ──────────────────────────────────────────────

def scan_from_input():
    print("[MANUAL] Modalità inserimento ISBN manuale. Digita 'q' per uscire.\n")
    while True:
        try:
            isbn = input("ISBN > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if isbn.lower() == "q" or not isbn:
            break
        print("[INFO] Recupero metadati da Open Library...")
        dati = fetch_book_data(isbn)
        if dati:
            print_book_data(isbn, dati)
        else:
            print(f"[WARN] Nessun dato trovato per: {isbn}\n")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if "--manual" in sys.argv:
        scan_from_input()
    else:
        scan_from_camera()

