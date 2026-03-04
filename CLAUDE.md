# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi ISBN barcode scanner using the AI Camera (IMX500). Scans book barcodes via camera, decodes them with pyzbar, and fetches metadata from the Open Library API.

## Target Platform

Raspberry Pi with AI Camera (IMX500), running Python 3.13. Uses `picamera2` for camera access (system package, not pip-installable).

## Running

```bash
# Activate venv
source .venv/bin/activate

# Camera mode (requires Raspberry Pi with AI Camera attached)
python3 scan_book.py

# Manual ISBN entry (works anywhere, for testing without camera)
python3 scan_book.py --manual

# Headless/SSH mode - prints ISBNs to stdout, no GUI window
python3 scan_isbn.py
```

## Dependencies

System packages (apt):
- `python3-picamera2` - camera interface (imported at runtime, not in venv)
- `libzbar0` - barcode decoding C library

Python packages (pip, in .venv):
- `opencv-python` - frame display and drawing
- `pyzbar` - Python wrapper for zbar barcode decoding
- `requests` - Open Library API calls

## Architecture

Two standalone scripts, no shared modules:

- **`scan_book.py`** - Full-featured scanner with OpenCV GUI window. Shows live camera feed with barcode overlay, looks up book metadata (title, authors, publisher, pages) via Open Library API. Has `--manual` mode for testing without camera hardware.
- **`scan_isbn.py`** - Minimal headless scanner. Outputs raw ISBNs to stdout, all status messages to stderr. Designed for piping into other tools over SSH.

Both scripts track already-scanned ISBNs in a `set()` to avoid duplicate lookups within a session.

## External API

Open Library Books API: `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data` — no authentication required.

## Language

Code comments and UI strings are in Italian.
