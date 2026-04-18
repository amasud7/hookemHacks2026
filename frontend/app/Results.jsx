// Masonry grid of short-form result cards.
// Handles both mock data shape and API response shape.

function PlatformBadge({ platform }) {
  const key = platform === "tiktok" ? "TikTok" : platform === "instagram" ? "Instagram" : null;
  if (!key || !window.Icon[key]) return null;
  const I = window.Icon[key];
  return (
    <div className={`plat plat--${platform}`}>
      <I width="11" height="11" />
    </div>
  );
}

function ResultCard({ r, onOpen, i }) {
  const handle = r.handle || (r.creator ? (r.creator.startsWith("@") ? r.creator : `@${r.creator}`) : "");
  const caption = r.caption || "Untitled";
  const thumb = r.thumb || null;
  const matchReason = r.matchReason || (r.score != null ? `${Math.round(r.score * 100)}% match` : "vibe match");
  const aspect = r.aspect || 0.9;
  const h = 220 + aspect * 140;
  const [loaded, setLoaded] = React.useState(false);

  return (
    <article
      className="card"
      style={{ animationDelay: `${i * 35}ms` }}
      onClick={() => onOpen(r)}
    >
      <div className="card__media" style={{ height: `${h}px` }}>
        {thumb ? (
          <>
            {!loaded && <div className="card__skel" />}
            <img
              src={thumb}
              alt=""
              onLoad={() => setLoaded(true)}
              style={{ opacity: loaded ? 1 : 0 }}
            />
          </>
        ) : (
          <div className="card__placeholder">
            <PlatformBadge platform={r.platform} />
            <div className="card__placeholder-caption">{caption}</div>
          </div>
        )}
        <div className="card__scrim" />
        <div className="card__top">
          <PlatformBadge platform={r.platform} />
          {r.duration && (
            <div className="card__dur">
              <window.Icon.Play width="9" height="9" />
              {r.duration}
            </div>
          )}
        </div>
        <div className="card__play">
          <window.Icon.Play width="20" height="20" />
        </div>
        <div className="card__match">{matchReason}</div>
      </div>
      <div className="card__body">
        {handle && <div className="card__handle">{handle}</div>}
        <div className="card__caption">{caption}</div>
        {(r.views || r.likes) && (
          <div className="card__stats">
            {r.views && (
              <span>
                <window.Icon.Play width="11" height="11" /> {r.views}
              </span>
            )}
            {r.likes && (
              <span>
                <window.Icon.Heart width="11" height="11" /> {r.likes}
              </span>
            )}
          </div>
        )}
      </div>
    </article>
  );
}

function ResultsGrid({ results, onOpen }) {
  return (
    <div className="grid">
      {results.map((r, i) => (
        <ResultCard key={r.content_id || r.id || i} r={r} onOpen={onOpen} i={i} />
      ))}
    </div>
  );
}

function ResultDetail({ result, onClose }) {
  if (!result) return null;
  const handle = result.handle || (result.creator ? (result.creator.startsWith("@") ? result.creator : `@${result.creator}`) : "");
  const matchReason = result.matchReason || (result.score != null ? `${Math.round(result.score * 100)}% match` : "vibe match");
  const platformLabel = result.platform === "tiktok" ? "TikTok" : result.platform === "instagram" ? "Instagram" : result.platform;

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__card" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose}>
          <window.Icon.Close width="18" height="18" />
        </button>
        <div className="modal__video">
          {result.thumb ? (
            <img src={result.thumb} alt="" />
          ) : (
            <div className="card__placeholder" style={{ minHeight: "100%" }}>
              <div className="card__placeholder-caption" style={{ fontSize: "22px" }}>{result.caption}</div>
            </div>
          )}
          <div className="modal__scrim" />
          <button className="modal__play">
            <window.Icon.Play width="28" height="28" />
          </button>
          {result.duration && (
            <div className="modal__vid-meta">
              <PlatformBadge platform={result.platform} />
              <span>{result.duration}</span>
            </div>
          )}
        </div>
        <div className="modal__body">
          <div className="modal__why">
            <window.Icon.Sparkle width="13" height="13" />
            <span>matched because</span>
            <strong>{matchReason}</strong>
          </div>
          {handle && <div className="modal__handle">{handle}</div>}
          <p className="modal__caption">{result.caption}</p>
          <div className="modal__stats">
            <div>
              <div className="stat-num">{result.views || "\u2014"}</div>
              <div className="stat-lbl">views</div>
            </div>
            <div>
              <div className="stat-num">{result.likes || "\u2014"}</div>
              <div className="stat-lbl">likes</div>
            </div>
            <div>
              <div className="stat-num">{result.duration || "\u2014"}</div>
              <div className="stat-lbl">length</div>
            </div>
          </div>
          <div className="modal__actions">
            {result.url ? (
              <a href={result.url} target="_blank" rel="noopener noreferrer" className="btn btn--primary">
                <window.Icon.Play width="14" height="14" /> open on {platformLabel}
              </a>
            ) : (
              <button className="btn btn--primary">
                <window.Icon.Play width="14" height="14" /> open on {platformLabel}
              </button>
            )}
            <button className="btn btn--ghost">
              <window.Icon.Bookmark width="14" height="14" /> save
            </button>
            <button className="btn btn--ghost">
              <window.Icon.Share width="14" height="14" /> share
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ResultsGrid, ResultDetail, PlatformBadge });
