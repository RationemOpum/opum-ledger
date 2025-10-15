#!/usr/bin/env python3
"""Run the Ledger Service Server using uvicorn."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("tmw_ledger.app:app", host="127.0.0.1", port=8000, log_level="debug", reload=True)
