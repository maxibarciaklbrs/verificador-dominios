import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app_fastapi:app",  # ← Import string, no el objeto directamente
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
