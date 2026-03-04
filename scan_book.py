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

import os
import sys
import requests
import cv2
from dotenv import load_dotenv
from pyzbar import pyzbar

from db import init_db, save_book

load_dotenv()


# ──────────────────────────────────────────────
# Lookup metadati da Open Library API
# ──────────────────────────────────────────────

def fetch_from_openlibrary(isbn: str) -> dict | None:
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
        print(f"[ERRORE] Open Library API fallita: {e}", file=sys.stderr)
        return None


def fetch_from_google_books(isbn: str) -> dict | None:
    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    if api_key:
        url += f"&key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("totalItems", 0) == 0:
            return None
        vol = data["items"][0]["volumeInfo"]
        # Normalizza al formato usato da print_book_data
        return {
            "title": vol.get("title", "N/D"),
            "authors": [{"name": a} for a in vol.get("authors", [])],
            "publish_date": vol.get("publishedDate", "N/D"),
            "publishers": [{"name": vol["publisher"]}] if vol.get("publisher") else [],
            "number_of_pages": vol.get("pageCount", "N/D"),
        }
    except requests.RequestException as e:
        print(f"[ERRORE] Google Books API fallita: {e}", file=sys.stderr)
        return None


def fetch_book_data(isbn: str) -> tuple[dict, str] | None:
    dati = fetch_from_openlibrary(isbn)
    if dati:
        return dati, "openlibrary"
    print("[INFO] Non trovato su Open Library, provo Google Books...", file=sys.stderr)
    dati = fetch_from_google_books(isbn)
    if dati:
        return dati, "google"
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

def scan_from_camera(conn):
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("[ERRORE] picamera2 non trovata. Installa con: sudo apt install python3-picamera2", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Avvio AI Camera... premi 'q' per uscire.")

    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )

    picam2.configure(config)
    picam2.start()

    scanned_isbns = set()
    frame_count = 0
    barcodes = []

    cv2.namedWindow("Scanner Libri  [q per uscire]", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Scanner Libri  [q per uscire]", 640, 480)
    cv2.moveWindow("Scanner Libri  [q per uscire]", 0, 0)

    while True:
        frame = picam2.capture_array()

        # Decodifica solo ogni 3 frame per risparmiare CPU
        if frame_count % 3 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            barcodes = pyzbar.decode(gray)
        frame_count += 1

        for barcode in barcodes:
            isbn = barcode.data.decode("utf-8").strip()

            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, isbn, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            if isbn not in scanned_isbns:
                scanned_isbns.add(isbn)
                print("\a", end="", flush=True)
                print(f"\n[SCAN] Barcode rilevato: {isbn}")
                print("[INFO] Recupero metadati da Open Library...")
                risultato = fetch_book_data(isbn)
                if risultato:
                    dati, source = risultato
                    print_book_data(isbn, dati)
                    _save_to_db(conn, isbn, dati, source)
                else:
                    print(f"[WARN] Libro non trovato per ISBN: {isbn}\n")

        display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Scanner Libri  [q per uscire]", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    picam2.stop()
    cv2.destroyAllWindows()
    print("[INFO] Camera chiusa.")


# ──────────────────────────────────────────────
# Modalità manuale: ISBN da tastiera (per test)
# ──────────────────────────────────────────────

def _save_to_db(conn, isbn: str, dati: dict, source: str):
    """Estrae i campi dal dizionario metadati e salva nel database."""
    autori = ", ".join(a["name"] for a in dati.get("authors", [])) or None
    editore = ", ".join(p["name"] for p in dati.get("publishers", [])) or None
    pagine = dati.get("number_of_pages")
    pagine = int(pagine) if pagine and pagine != "N/D" else None
    save_book(
        conn,
        isbn=isbn,
        title=dati.get("title"),
        authors=autori,
        publish_date=dati.get("publish_date"),
        publisher=editore,
        pages=pagine,
        source=source,
    )


def scan_from_input(conn):
    print("[MANUAL] Modalità inserimento ISBN manuale. Digita 'q' per uscire.\n")
    while True:
        try:
            isbn = input("ISBN > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if isbn.lower() == "q" or not isbn:
            break
        print("[INFO] Recupero metadati da Open Library...")
        risultato = fetch_book_data(isbn)
        if risultato:
            dati, source = risultato
            print_book_data(isbn, dati)
            _save_to_db(conn, isbn, dati, source)
        else:
            print(f"[WARN] Nessun dato trovato per: {isbn}\n")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    conn = init_db()
    if "--manual" in sys.argv:
        scan_from_input(conn)
    else:
        scan_from_camera(conn)
    conn.close()

