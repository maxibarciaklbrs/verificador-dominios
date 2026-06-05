#!/bin/bash

tmux kill-session -t fastapi 2>/dev/null

tmux new-session -d -s fastapi \
    "cd $(pwd) && source venv/bin/activate && uvicorn main:app --host 127.0.0.1 --port 8000 --reload"