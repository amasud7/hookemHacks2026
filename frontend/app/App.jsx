// Main App shell — composes everything. Tracks state, mode, query.
// Surfaces a state switcher in top-right so the reviewer can jump
// between the 7 states without performing each flow.

const { useEffect: useE2, useState: useS2, useRef: useR2 } = React;

function Header({ state, setState, onReset, name }) {
  const stateList = [
    { id: "empty", label: "landing" },
    { id: "typing", label: "typing" },
    { id: "recording", label: "audio" },
    { id: "image-uploaded", label: "image" },
    { id: "loading", label: "loading" },
    { id: "results", label: "results" },
  ];
  return (
    <header className="topbar">
      <div className="topbar__left" onClick={onReset}>
        <div className="wordmark">
          <span className="wordmark__dot" />
          <span className="wordmark__name">{name}</span>
        </div>
      </div>
      <nav className="topbar__nav">
        <div className="topbar__nav-wrap">
        </div>
      </nav>
      <div className="topbar__right">
        <div className="state-switcher">
          <span className="state-switcher__lbl">preview</span>
          {stateList.map((s) => (
            <button
              key={s.id}
              className={`state-switcher__btn ${state === s.id ? "is-on" : ""}`}
              onClick={() => setState(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}

function App() {
  const [state, setState] = useS2("empty");
  const [mode, setMode] = useS2("text");
  const [query, setQuery] = useS2("");
  const [uploadedImage, setUploadedImage] = useS2(null);
  const [uploadedFile, setUploadedFile] = useS2(null);
  const [recordingTime, setRecordingTime] = useS2(0);
  const [openResult, setOpenResult] = useS2(null);
  const [results, setResults] = useS2([]);
  const [searchError, setSearchError] = useS2(null);
  const [detectedIntent, setDetectedIntent] = useS2(null);
  const [lastPayload, setLastPayload] = useS2(null);
  const [tweaks] = useS2({ name: "Vibely" });

  // Recording timer
  useE2(() => {
    if (state !== "recording") { setRecordingTime(0); return; }
    const id = setInterval(() => setRecordingTime((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  const handleSubmit = async (payload, overridePreset) => {
    setState("loading");
    setSearchError(null);
    if (!overridePreset) setLastPayload(payload);

    try {
      const formData = new FormData();
      formData.append("mode", payload.kind || "text");

      if (payload.kind === "text" || (!payload.file && query.trim())) {
        formData.append("query", query);
        if (!formData.has("mode") || formData.get("mode") !== "text") {
          formData.set("mode", "text");
        }
      }
      if (payload.file) {
        formData.append("file", payload.file);
      }
      if (overridePreset) {
        formData.append("preset", overridePreset);
      }

      const res = await fetch("/api/search", {
        method: "POST",
        body: formData,
        headers: { "ngrok-skip-browser-warning": "true" },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Search failed: ${res.status}`);
      }
      const data = await res.json();

      setResults(data.results || []);
      setDetectedIntent(data.detected_intent || null);
      if (data.transcript) setQuery(data.transcript);
      setState("results");
    } catch (err) {
      console.error("Search error:", err);
      setSearchError(err.message);
      setState("empty");
    }
  };

  const handleOverrideIntent = (newPreset) => {
    const payload = lastPayload || { kind: "text" };
    setDetectedIntent(newPreset);
    handleSubmit(payload, newPreset);
  };

  const handleReset = () => {
    setState("empty");
    setQuery("");
    setUploadedImage(null);
    setUploadedFile(null);
    setMode("text");
    setResults([]);
    setSearchError(null);
  };

  const handlePickTrending = (q) => {
    setQuery(q);
    setMode("text");
    setState("typing");
  };

  const handlePickMode = (m) => {
    setMode(m);
    if (m === "audio") setState("recording");
    else if (m === "image") {
      setState("image-uploaded");
    }
  };

  // Keep preview state coherent when triggered from the state switcher
  useE2(() => {
    if (state === "typing" && !query) setQuery("that chicken on a tree video");
  }, [state]);

  return (
    <div className="app">
      <div className="topbar-outer">
        <Header
          state={state}
          setState={setState}
          onReset={handleReset}
          name={tweaks.name}
        />
      </div>

      <main className="main">
        {state === "empty" && (
          <div className="hero-above" />
        )}

        <div className={`search-wrap ${state === "empty" ? "search-wrap--big" : "search-wrap--compact"}`}>
          <window.SearchPill
            state={state}
            setState={setState}
            query={query}
            setQuery={setQuery}
            mode={mode}
            setMode={setMode}
            uploadedImage={uploadedImage}
            setUploadedImage={setUploadedImage}
            uploadedFile={uploadedFile}
            setUploadedFile={setUploadedFile}
            onSubmit={handleSubmit}
            recordingTime={recordingTime}
          />
        </div>

        {searchError && (
          <div style={{
            maxWidth: 780, margin: "16px auto 0", padding: "12px 16px",
            background: "oklch(0.95 0.05 25)", border: "1px solid oklch(0.85 0.1 25)",
            borderRadius: 12, fontSize: 13, color: "oklch(0.4 0.15 25)"
          }}>
            Search failed: {searchError}
          </div>
        )}

        {state === "empty" && (
          <window.Landing onPickTrending={handlePickTrending} onPickMode={handlePickMode} />
        )}

        {state === "typing" && query && (
          <div className="suggest">
            <div className="suggest__head">suggestions</div>
            {window.TRENDING.filter((t) =>
              t.toLowerCase().includes(query.toLowerCase().split(" ")[0] || "")
            )
              .slice(0, 5)
              .map((t, i) => (
                <button key={i} className="suggest__item" onClick={() => handlePickTrending(t)}>
                  <window.Icon.Search width="13" height="13" />
                  <span dangerouslySetInnerHTML={{ __html: highlightMatch(t, query) }} />
                </button>
              ))}
            <div className="suggest__foot">
              press <kbd>&#9166;</kbd> to search for "<em>{query}</em>"
            </div>
          </div>
        )}

        {state === "loading" && <LoadingState query={query} uploadedImage={uploadedImage} />}

        {state === "results" && (
          <>
            <ResultsHeader query={query} uploadedImage={uploadedImage} mode={mode} count={results.length} />
            {detectedIntent && (
              <IntentBar intent={detectedIntent} onOverride={handleOverrideIntent} />
            )}
            <window.ResultsGrid results={results} onOpen={setOpenResult} />
          </>
        )}
      </main>

      <window.ResultDetail result={openResult} onClose={() => setOpenResult(null)} />
    </div>
  );
}

const INTENT_INFO = {
  describe: { label: "Describing", desc: "visual-heavy search", icon: "\ud83d\udc41" },
  reenact:  { label: "Reenacting", desc: "audio-heavy search", icon: "\ud83c\udfb5" },
  vibe:     { label: "Vibing", desc: "balanced search", icon: "\u2728" },
  quote:    { label: "Quoting", desc: "text-heavy search", icon: "\ud83d\udcac" },
};

function IntentBar({ intent, onOverride }) {
  const presets = ["describe", "reenact", "vibe", "quote"];
  return (
    <div className="intent-bar">
      <span className="intent-bar__label">search mode</span>
      <div className="intent-bar__chips">
        {presets.map((p) => {
          const info = INTENT_INFO[p];
          const active = intent === p;
          return (
            <button
              key={p}
              className={`intent-chip ${active ? "intent-chip--active" : ""}`}
              onClick={() => onOverride(p)}
            >
              <span className="intent-chip__icon">{info.icon}</span>
              <span className="intent-chip__label">{info.label}</span>
              {active && <span className="intent-chip__desc">{info.desc}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function highlightMatch(text, q) {
  if (!q) return text;
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return text;
  return text.slice(0, i) + "<mark>" + text.slice(i, i + q.length) + "</mark>" + text.slice(i + q.length);
}

function ResultsHeader({ query, uploadedImage, mode, count }) {
  const label = uploadedImage ? "visually similar to your image" : query || "your search";
  return (
    <div className="results-head">
      <div className="results-head__left">
        <div className="results-head__eyebrow">results for</div>
        <h2 className="results-head__q">
          {uploadedImage && <img className="results-head__thumb" src={uploadedImage} alt="" />}
          "{label}"
        </h2>
        <div className="results-head__meta">
          <span>{count} post{count !== 1 ? "s" : ""}</span>
          <span className="dotsep" />
          <span>across TikTok, Instagram</span>
        </div>
      </div>
      <div className="results-head__filters">
        <button className="filt filt--on">all</button>
        <button className="filt">
          <window.Icon.TikTok width="11" height="11" /> tiktok
        </button>
        <button className="filt">
          <window.Icon.Instagram width="11" height="11" /> instagram
        </button>
      </div>
    </div>
  );
}

function LoadingState({ query, uploadedImage }) {
  const steps = [
    "embedding your query",
    "searching indexed posts",
    "ranking by vibe similarity",
    "preparing results",
  ];
  const [active, setActive] = useS2(0);
  useE2(() => {
    const id = setInterval(() => setActive((a) => (a + 1) % steps.length), 450);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="loading">
      <div className="loading__card">
        <div className="loading__orb">
          <div className="orb-ring orb-ring--1" />
          <div className="orb-ring orb-ring--2" />
          <div className="orb-ring orb-ring--3" />
          <window.Icon.Sparkle width="22" height="22" />
        </div>
        <div className="loading__q">
          {uploadedImage && <img src={uploadedImage} alt="" />}
          <span>{uploadedImage ? "visual reference" : `"${query || "your search"}"`}</span>
        </div>
        <ul className="loading__steps">
          {steps.map((s, i) => (
            <li key={s} className={i < active ? "is-done" : i === active ? "is-active" : ""}>
              <span className="loading__dot" />
              {s}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

window.App = App;
