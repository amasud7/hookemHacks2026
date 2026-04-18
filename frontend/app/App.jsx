// Main App shell — composes everything. Tracks state, mode, query.
// Surfaces a state switcher in top-right so the reviewer can jump
// between the 7 states without performing each flow.

const { useEffect: useE2, useState: useS2, useRef: useR2 } = React;

function Header({ state, setState, onReset, tweaksOpen, setTweaksOpen, name }) {
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

// Tweaks panel — name picker + layout + accent
function TweaksPanel({ open, onClose, tweaks, setTweaks }) {
  if (!open) return null;
  const { name, accent, density, showMatchChip } = tweaks;
  const names = ["Vibely", "Recall", "Loop", "Grain", "Hum"];
  const accents = [
    { k: "terracotta", v: "oklch(0.68 0.16 55)" },
    { k: "peach", v: "oklch(0.74 0.14 45)" },
    { k: "clay", v: "oklch(0.6 0.13 40)" },
    { k: "olive", v: "oklch(0.6 0.09 110)" },
    { k: "ink", v: "oklch(0.28 0.02 60)" },
  ];
  return (
    <aside className="tweaks">
      <div className="tweaks__head">
        <strong>Tweaks</strong>
        <button onClick={onClose}><window.Icon.Close width="14" height="14" /></button>
      </div>
      <div className="tweaks__row">
        <label>product name</label>
        <div className="tweaks__chips">
          {names.map((n) => (
            <button
              key={n}
              className={`tchip ${name === n ? "tchip--on" : ""}`}
              onClick={() => setTweaks({ ...tweaks, name: n })}
            >{n}</button>
          ))}
        </div>
      </div>
      <div className="tweaks__row">
        <label>accent</label>
        <div className="tweaks__swatches">
          {accents.map((a) => (
            <button
              key={a.k}
              className={`swatch ${accent === a.v ? "swatch--on" : ""}`}
              style={{ background: a.v }}
              onClick={() => setTweaks({ ...tweaks, accent: a.v })}
              title={a.k}
            />
          ))}
        </div>
      </div>
      <div className="tweaks__row">
        <label>grid density</label>
        <div className="tweaks__chips">
          {["cozy", "default", "dense"].map((d) => (
            <button
              key={d}
              className={`tchip ${density === d ? "tchip--on" : ""}`}
              onClick={() => setTweaks({ ...tweaks, density: d })}
            >{d}</button>
          ))}
        </div>
      </div>
      <div className="tweaks__row">
        <label>show "why it matched" chip</label>
        <button
          className={`toggle ${showMatchChip ? "toggle--on" : ""}`}
          onClick={() => setTweaks({ ...tweaks, showMatchChip: !showMatchChip })}
        >
          <span className="toggle__knob" />
        </button>
      </div>
    </aside>
  );
}

function App() {
  const [state, setState] = useS2("empty"); // empty | typing | recording | image-uploaded | loading | results
  const [mode, setMode] = useS2("text");
  const [query, setQuery] = useS2("");
  const [uploadedImage, setUploadedImage] = useS2(null);
  const [recordingTime, setRecordingTime] = useS2(0);
  const [openResult, setOpenResult] = useS2(null);
  const [tweaksOpen, setTweaksOpen] = useS2(false);
  const [tweaks, setTweaks] = useS2(() => {
    try {
      return JSON.parse(localStorage.getItem("vibely-tweaks")) || {
        name: "Vibely",
        accent: "oklch(0.68 0.16 55)",
        density: "default",
        showMatchChip: true,
      };
    } catch {
      return { name: "Vibely", accent: "oklch(0.68 0.16 55)", density: "default", showMatchChip: true };
    }
  });

  useE2(() => {
    localStorage.setItem("vibely-tweaks", JSON.stringify(tweaks));
    document.documentElement.style.setProperty("--accent", tweaks.accent);
    document.documentElement.dataset.density = tweaks.density;
    document.documentElement.dataset.matchchip = tweaks.showMatchChip ? "on" : "off";
  }, [tweaks]);

  // Recording timer
  useE2(() => {
    if (state !== "recording") { setRecordingTime(0); return; }
    const id = setInterval(() => setRecordingTime((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  const handleSubmit = () => {
    setState("loading");
    setTimeout(() => setState("results"), 1400);
  };

  const handleReset = () => {
    setState("empty");
    setQuery("");
    setUploadedImage(null);
    setMode("text");
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
      setUploadedImage("https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=200&q=80");
      setState("image-uploaded");
    }
  };

  // Keep the 'image-uploaded' preview state coherent when triggered from the state switcher.
  useE2(() => {
    if (state === "image-uploaded" && !uploadedImage) {
      setUploadedImage("https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=200&q=80");
      setMode("image");
    }
    if (state === "typing" && !query) setQuery("that chicken on a tree video");
  }, [state]);

  return (
    <div className="app">
      <div className="topbar-outer">
        <Header
          state={state}
          setState={setState}
          onReset={handleReset}
          tweaksOpen={tweaksOpen}
          setTweaksOpen={setTweaksOpen}
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
            onSubmit={handleSubmit}
            recordingTime={recordingTime}
          />
        </div>

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
            <ResultsHeader query={query} uploadedImage={uploadedImage} mode={mode} />
            <window.ResultsGrid results={window.MOCK_RESULTS} onOpen={setOpenResult} />
          </>
        )}
      </main>

      <window.ResultDetail result={openResult} onClose={() => setOpenResult(null)} />
      <TweaksPanel open={tweaksOpen} onClose={() => setTweaksOpen(false)} tweaks={tweaks} setTweaks={setTweaks} />
    </div>
  );
}

function highlightMatch(text, q) {
  if (!q) return text;
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return text;
  return text.slice(0, i) + "<mark>" + text.slice(i, i + q.length) + "</mark>" + text.slice(i + q.length);
}

function ResultsHeader({ query, uploadedImage, mode }) {
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
          <span>128 posts</span>
          <span className="dotsep" />
          <span>across TikTok, Instagram</span>
          <span className="dotsep" />
          <span>indexed in 0.42s</span>
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
        <button className="filt">short (&lt;15s)</button>
        <button className="filt">last 7 days</button>
      </div>
    </div>
  );
}

function LoadingState({ query, uploadedImage }) {
  const steps = [
    "embedding your query",
    "searching 12.4M indexed posts",
    "ranking by vibe similarity",
    "preparing previews",
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
