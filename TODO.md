# TODO — Book Scanner

## Code drift from conversation log

The `scan_book.py` in the repo differs from the version documented in `bookscanner-conversation.md`:

- **Resolution**: repo uses `(1280, 720)`, conversation settled on `(640, 480)`
- **Grayscale decode**: conversation version converts to grayscale before `pyzbar.decode(gray)` — repo decodes the full RGB frame directly
- **Window creation order**: repo calls `cv2.namedWindow` *after* `cv2.imshow` (should be before, as in the conversation version)

These should be reconciled — the conversation version appears to be the more refined one.

## Next steps (from conversation plan)

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
