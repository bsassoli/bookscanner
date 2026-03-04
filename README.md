# Book Scanner

ISBN barcode scanner for Raspberry Pi with AI Camera (IMX500). Scans book barcodes, decodes them with pyzbar, and fetches metadata (title, authors, publisher, year, pages) from Open Library and Google Books APIs.

## Requirements

- Raspberry Pi with AI Camera (IMX500)
- Raspberry Pi OS Bookworm
- Python 3.13

### System packages

```bash
sudo apt install -y python3-picamera2 libzbar0
```

### Python setup

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install opencv-python pyzbar requests setuptools python-dotenv
```

> The venv must use `--system-site-packages` so that the apt-installed `picamera2` is visible.

### Google Books API key (optional)

`scan_book.py` uses Open Library as primary source and Google Books as fallback. To enable the fallback, get a free API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (enable the Books API), then create a `.env` file:

```bash
echo 'GOOGLE_BOOKS_API_KEY=your_key_here' > .env
```

## Usage

### Camera mode (with display)

```bash
python3 scan_book.py
```

Opens a live camera feed window. Point a book barcode at the camera — metadata is printed to the terminal. Press `q` to quit.

### Manual mode (no camera needed)

```bash
python3 scan_book.py --manual
```

Type ISBNs at the prompt to look up book metadata. Useful for testing without camera hardware.

### Headless mode (SSH / no display)

```bash
python3 scan_isbn.py
```

Outputs raw ISBNs to stdout (status messages go to stderr). Designed for piping into other tools. Stop with `Ctrl+C`.

## Roadmap

- SQLite storage for scanned books
- Datasette web dashboard
- Cloudflare Tunnel for remote access
- systemd service for auto-start on boot
