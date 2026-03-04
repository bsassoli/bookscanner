# TODO — Book Scanner

## Completed

- ~~**Code drift from conversation log**~~: resolved — resolution lowered to 640x480, grayscale decode, window creation order fixed, frame skipping (every 3rd frame), audio feedback (terminal bell)
- ~~**Google Books fallback**~~: `scan_book.py` now falls back to Google Books API when Open Library has no result (requires API key in `.env`)
- ~~**SQLite storage for `scan_book.py`**~~: new `db.py` module with `init_db()`/`save_book()`, `scan_book.py` persists scanned books to `books.db` (deduplicated by ISBN, tracks API source)

## Next steps

### 1. SQLite storage for `scan_isbn.py`
- Wire `scan_isbn.py` to use `db.py` so headless mode also persists to `books.db`

### 2. Datasette web dashboard
- Install Datasette (`pip install datasette`)
- Serve the SQLite DB as a browsable/searchable web UI
- Consider `datasette-dashboards` plugin for a custom view

### 3. Cloudflare Tunnel
- Install `cloudflared` on the Pi
- Configure a tunnel to expose Datasette publicly
- Set up as a systemd service so the tunnel persists across reboots

### 4. Auto-start on boot
- Create a `systemd` service unit for the scanner script
- Decide which script to auto-start (likely `scan_isbn.py` for headless operation)
- Optionally a second unit for Datasette
