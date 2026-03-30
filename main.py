"""KaraokePro - Karaoke Queue Management System.

Launch the server and open the browser.
"""
import webbrowser
import threading
import uvicorn
from config import load_config


def open_browser(port: int):
    """Open browser after a short delay to let the server start."""
    import time
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")


if __name__ == "__main__":
    config = load_config()
    port = config["port"]

    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run("app.server:app", host="0.0.0.0", port=port, reload=False)
