# TODO — Book Scanner

## Completed

- ~~**Code drift from conversation log**~~: resolved — resolution lowered to 640x480, grayscale decode, window creation order fixed, frame skipping (every 3rd frame), audio feedback (terminal bell)
- ~~**Google Books fallback**~~: `scan_book.py` now falls back to Google Books API when Open Library has no result (requires API key in `.env`)

## Next steps

### 1. SQLite storage
- Add a local SQLite database to persist scanned books
- Schema: ISBN, title, authors, publisher, year, pages, scan timestamp
- Insert on scan (deduplicate by ISBN)
- Both `scan_book.py` and `scan_isbn.py` should write to the same DB

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
