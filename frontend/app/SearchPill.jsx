// SearchPill — the hero interaction.
// Floating pill w/ mode chips: Text / Image / Video / Audio
// Handles typing, recording, image-uploaded, loading states.

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
  onSubmit,
  recordingTime,
}) {
  const inputRef = useRef(null);
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

  const handleMode = (m) => {
    setMode(m);
    if (m === "audio") setState("recording");
    else if (m === "image") {
      setUploadedImage("https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=200&q=80");
      setState("image-uploaded");
    } else {
      setState("typing");
    }
  };

  const handleSubmit = () => {
    if (state === "recording") {
      onSubmit({ kind: "voice" });
    } else if (hasImage || query.trim()) {
      onSubmit({ kind: mode, q: query });
    }
  };

  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  return (
    <div className={`pill pill--${state}`}>
      {/* Uploaded image chip row */}
      {hasImage && (
        <div className="pill__attach">
          <div className="attach-chip">
            <img src={uploadedImage} alt="" />
            <div className="attach-chip__meta">
              <div className="attach-chip__name">reference.jpg</div>
              <div className="attach-chip__sub">searching visually similar…</div>
            </div>
            <button
              className="attach-chip__x"
              onClick={() => {
                setUploadedImage(null);
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
            <div className="rec-label">listening…</div>
          </div>
        )}

        {/* Submit / Mic button */}
        <button
          className={`pill__send ${
            isRecording ? "pill__send--stop" : hasImage || query.trim() ? "pill__send--go" : "pill__send--idle"
          }`}
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isRecording ? (
            <span className="stop-square" />
          ) : hasImage || query.trim() ? (
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
