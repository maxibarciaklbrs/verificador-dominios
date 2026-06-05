#!/bin/bash

sudo systemctl start nginx

tmux has-session -t fastapi 2>/dev/null

if [ $? -ne 0 ]; then
    tmux new-session -d -s fastapi \
        "cd $(pwd) && source venv/bin/activate && uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
else
    echo "Sesión tmux fastapi ya existe."
fi