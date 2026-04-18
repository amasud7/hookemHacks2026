from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles

from src.embeddings import embed_video, embed_audio
from src.search import search

app = FastAPI(title="Vibely API")


@app.post("/api/search")
async def api_search(
    mode: str = Form(...),
    query: str = Form(""),
    file: UploadFile | None = File(None),
    platform: str = Form(""),
):
    """Search across all modalities. Accepts text queries or file uploads."""
    try:
        if mode == "text":
            if not query.strip():
                raise HTTPException(400, "query is required for text mode")
            results = search(query=query, platform=platform or None)

        elif mode in ("image", "video"):
            if file is None:
                raise HTTPException(400, f"file is required for {mode} mode")
            file_bytes = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            query_vector = embed_video(file_bytes, mime_type)
            results = search(query_vector=query_vector, platform=platform or None)

        elif mode == "audio":
            if file is None:
                raise HTTPException(400, "file is required for audio mode")
            file_bytes = await file.read()
            mime_type = file.content_type or "audio/webm"
            query_vector = embed_audio(file_bytes, mime_type)
            results = search(query_vector=query_vector, platform=platform or None)

        else:
            raise HTTPException(400, f"unknown mode: {mode}")

    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "results": [r.model_dump() for r in results],
        "count": len(results),
        "query_mode": mode,
    }


# Serve frontend static files — must come after API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
