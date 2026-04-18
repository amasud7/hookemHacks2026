// SearchPill — the hero interaction.
// Floating pill w/ mode chips: Text / Image / Video / Audio
// Handles typing, recording, image-uploaded, loading states.
// Supports real file uploads and microphone recording.

const { useState, useEffect, useRef } = React;

function ModeChip({ active, icon, label, onClick, accent }) {
  const I = window.Icon[icon];
  return (
    <button
      onClick={onClick}
      className={`mode-chip ${active ? "mode-chip--active" : ""}`}
      style={active ? { "--chip-accent": accent } : undefined}
    >
      <I width="15" height="15" />
      <span className="mode-chip__label">{label}</span>
    </button>
  );
}

function VoiceWave({ active }) {
  const bars = 28;
  return (
    <div className={`voice-wave ${active ? "voice-wave--on" : ""}`}>
      {[...Array(bars)].map((_, i) => (
        <span
          key={i}
          style={{
            animationDelay: `${i * 40}ms`,
            height: `${20 + Math.abs(Math.sin(i * 0.6)) * 70}%`,
          }}
        />
      ))}
    </div>
  );
}

function SearchPill({
  state,
  setState,
  query,
  setQuery,
  mode,
  setMode,
  uploadedImage,
  setUploadedImage,
  uploadedFile,
  setUploadedFile,
  onSubmit,
  recordingTime,
}) {
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const submitAfterStopRef = useRef(false);
  const isRecording = state === "recording";
  const isLoading = state === "loading";
  const hasImage = !!uploadedImage;

  useEffect(() => {
    if (state === "typing" && inputRef.current) {
      inputRef.current.focus();
    }
  }, [state]);

  const modes = [
    { id: "text", icon: "Text", label: "Text", accent: "oklch(0.68 0.16 55)" },
    { id: "image", icon: "Image", label: "Image", accent: "oklch(0.68 0.14 90)" },
    { id: "video", icon: "Video", label: "Video", accent: "oklch(0.62 0.14 170)" },
    { id: "audio", icon: "Audio", label: "Audio", accent: "oklch(0.62 0.16 320)" },
  ];

  const placeholder = {
    text: "Describe it in your own words, hum the sound, or paste a still \u2014 we'll find the post you half-remember.",
    image: "drop an image \u2014 we'll find videos that match",
    video: "upload a clip \u2014 we'll find the same moment elsewhere",
    audio: "hum it, play it, or upload the sound",
  }[mode];

  // --- File upload ---
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadedFile(file);
    if (file.type.startsWith("image/")) {
      setUploadedImage(URL.createObjectURL(file));
      setState("image-uploaded");
    } else {
      setUploadedImage(null);
      setState("image-uploaded");
    }
    // Reset the input so the same file can be re-selected
    e.target.value = "";
  };

  // --- Audio recording ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const file = new File([blob], "recording.webm", { type: blob.type });
        setUploadedFile(file);
        stream.getTracks().forEach((t) => t.stop());

        if (submitAfterStopRef.current) {
          submitAfterStopRef.current = false;
          onSubmit({ kind: "audio", file });
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setState("recording");
    } catch (err) {
      console.error("Mic access denied:", err);
      alert("Microphone access is required for audio search.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  };

  // --- Mode selection ---
  const handleMode = (m) => {
    setMode(m);
    if (m === "audio") {
      startRecording();
    } else if (m === "image" || m === "video") {
      fileInputRef.current.accept = m === "image" ? "image/*" : "video/*";
      fileInputRef.current.click();
    } else {
      setState("typing");
    }
  };

  // --- Submit ---
  const handleSubmit = () => {
    if (state === "recording") {
      submitAfterStopRef.current = true;
      stopRecording();
    } else if (uploadedFile) {
      onSubmit({ kind: mode, file: uploadedFile });
    } else if (query.trim()) {
      onSubmit({ kind: "text", q: query });
    }
  };

  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  return (
    <div className={`pill pill--${state}`}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        style={{ display: "none" }}
        onChange={handleFileSelect}
      />

      {/* Uploaded image chip row */}
      {hasImage && (
        <div className="pill__attach">
          <div className="attach-chip">
            <img src={uploadedImage} alt="" />
            <div className="attach-chip__meta">
              <div className="attach-chip__name">{uploadedFile ? uploadedFile.name : "reference.jpg"}</div>
              <div className="attach-chip__sub">searching visually similar\u2026</div>
            </div>
            <button
              className="attach-chip__x"
              onClick={() => {
                setUploadedImage(null);
                setUploadedFile(null);
                setState("empty");
                setMode("text");
              }}
            >
              <window.Icon.Close width="13" height="13" />
            </button>
          </div>
        </div>
      )}

      {/* Non-image file indicator */}
      {!hasImage && uploadedFile && state === "image-uploaded" && (
        <div className="pill__attach">
          <div className="attach-chip">
            <div style={{ width: 40, height: 40, borderRadius: 9, background: "var(--bg-3)", display: "grid", placeItems: "center" }}>
              <window.Icon.Video width="18" height="18" />
            </div>
            <div className="attach-chip__meta">
              <div className="attach-chip__name">{uploadedFile.name}</div>
              <div className="attach-chip__sub">searching by video content\u2026</div>
            </div>
            <button
              className="attach-chip__x"
              onClick={() => {
                setUploadedFile(null);
                setState("empty");
                setMode("text");
              }}
            >
              <window.Icon.Close width="13" height="13" />
            </button>
          </div>
        </div>
      )}

      {/* Main input row */}
      <div className="pill__main">
        {!isRecording ? (
          <>
            <div className="pill__search-icon">
              <window.Icon.Search width="18" height="18" />
            </div>
            <input
              ref={inputRef}
              className="pill__input"
              placeholder={placeholder}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (state === "empty" && e.target.value) setState("typing");
                if (state === "typing" && !e.target.value && !hasImage) setState("empty");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              disabled={isLoading}
            />
            {isLoading && (
              <div className="pill__thinking">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
                <span className="pill__thinking-text">reading your vibe</span>
              </div>
            )}
          </>
        ) : (
          <div className="pill__recording">
            <div className="rec-dot" />
            <div className="rec-time">{fmtTime(recordingTime)}</div>
            <VoiceWave active />
            <div className="rec-label">listening\u2026</div>
          </div>
        )}

        {/* Submit / Stop button */}
        <button
          className={`pill__send ${
            isRecording ? "pill__send--stop" : hasImage || uploadedFile || query.trim() ? "pill__send--go" : "pill__send--idle"
          }`}
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isRecording ? (
            <span className="stop-square" />
          ) : hasImage || uploadedFile || query.trim() ? (
            <window.Icon.ArrowUp width="18" height="18" />
          ) : (
            <window.Icon.Sparkle width="17" height="17" />
          )}
        </button>
      </div>

      {/* Mode chip row */}
      <div className="pill__modes">
        <div className="pill__modes-group">
          {modes.map((m) => (
            <ModeChip
              key={m.id}
              icon={m.icon}
              label={m.label}
              active={mode === m.id}
              accent={m.accent}
              onClick={() => handleMode(m.id)}
            />
          ))}
        </div>
        <div className="pill__hint">
          <kbd>&#9166;</kbd> to search
        </div>
      </div>
    </div>
  );
}

window.SearchPill = SearchPill;
