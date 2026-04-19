from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles

from src.embeddings import embed_video, embed_audio, embed_query
from src.intent import classify_query
from src.search import search
from src.transcribe import transcribe_audio

app = FastAPI(title="Vibely API")


@app.post("/api/search")
async def api_search(
    mode: str = Form(...),
    query: str = Form(""),
    file: UploadFile | None = File(None),
    platform: str = Form(""),
    preset: str = Form(""),  # manual override: describe, reenact, vibe, quote
):
    """Search across all modalities. Accepts text queries or file uploads."""
    detected_intent = None
    transcript = None

    try:
        if mode == "text":
            if not query.strip():
                raise HTTPException(400, "query is required for text mode")
            # Use manual preset override or auto-classify
            if preset:
                detected_intent = preset
            else:
                detected_intent = classify_query(query)
            results = search(query=query, preset=detected_intent, platform=platform or None)

        elif mode in ("image", "video"):
            if file is None:
                raise HTTPException(400, f"file is required for {mode} mode")
            file_bytes = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            query_vector = embed_video(file_bytes, mime_type)
            detected_intent = "describe"
            results = search(query_vector=query_vector, preset="describe", platform=platform or None)

        elif mode == "audio":
            if file is None:
                raise HTTPException(400, "file is required for audio mode")
            file_bytes = await file.read()
            mime_type = file.content_type or "audio/webm"

            # Dual-path: transcribe for text matching + raw audio for acoustic matching
            suffix = ".webm" if "webm" in mime_type else ".mp4" if "mp4" in mime_type else ".wav"
            transcript = transcribe_audio(file_bytes, suffix=suffix)

            audio_query_vector = embed_audio(file_bytes, mime_type)
            text_query_vector = embed_query(transcript) if transcript else None

            detected_intent = "reenact"
            results = search(
                query_vector=audio_query_vector,
                text_query_vector=text_query_vector,
                audio_query_vector=audio_query_vector,
                preset="reenact",
                platform=platform or None,
            )

        else:
            raise HTTPException(400, f"unknown mode: {mode}")

    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "results": [r.model_dump() for r in results],
        "count": len(results),
        "query_mode": mode,
        "detected_intent": detected_intent,
        "transcript": transcript,
    }


# Serve frontend static files — must come after API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
