// Masonry grid of short-form result cards.

function PlatformBadge({ platform }) {
  const I = platform === "tiktok" ? window.Icon.TikTok : window.Icon.Instagram;
  return (
    <div className={`plat plat--${platform}`}>
      <I width="11" height="11" />
    </div>
  );
}

function fmtNum(n) {
  return n;
}

function ResultCard({ r, onOpen, i }) {
  const h = 220 + r.aspect * 140; // varied heights for masonry feel
  const [loaded, setLoaded] = React.useState(false);
  return (
    <article
      className="card"
      style={{ animationDelay: `${i * 35}ms` }}
      onClick={() => onOpen(r)}
    >
      <div className="card__media" style={{ height: `${h}px` }}>
        {!loaded && <div className="card__skel" />}
        <img
          src={r.thumb}
          alt=""
          onLoad={() => setLoaded(true)}
          style={{ opacity: loaded ? 1 : 0 }}
        />
        <div className="card__scrim" />
        <div className="card__top">
          <PlatformBadge platform={r.platform} />
          <div className="card__dur">
            <window.Icon.Play width="9" height="9" />
            {r.duration}
          </div>
        </div>
        <div className="card__play">
          <window.Icon.Play width="20" height="20" />
        </div>
        <div className="card__match">{r.matchReason}</div>
      </div>
      <div className="card__body">
        <div className="card__handle">{r.handle}</div>
        <div className="card__caption">{r.caption}</div>
        <div className="card__stats">
          <span>
            <window.Icon.Play width="11" height="11" /> {r.views}
          </span>
          <span>
            <window.Icon.Heart width="11" height="11" /> {r.likes}
          </span>
        </div>
      </div>
    </article>
  );
}

function ResultsGrid({ results, onOpen }) {
  return (
    <div className="grid">
      {results.map((r, i) => (
        <ResultCard key={r.id} r={r} onOpen={onOpen} i={i} />
      ))}
    </div>
  );
}

function ResultDetail({ result, onClose }) {
  if (!result) return null;
  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__card" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose}>
          <window.Icon.Close width="18" height="18" />
        </button>
        <div className="modal__video">
          <img src={result.thumb} alt="" />
          <div className="modal__scrim" />
          <button className="modal__play">
            <window.Icon.Play width="28" height="28" />
          </button>
          <div className="modal__vid-meta">
            <PlatformBadge platform={result.platform} />
            <span>{result.duration}</span>
          </div>
        </div>
        <div className="modal__body">
          <div className="modal__why">
            <window.Icon.Sparkle width="13" height="13" />
            <span>matched because</span>
            <strong>{result.matchReason}</strong>
          </div>
          <div className="modal__handle">{result.handle}</div>
          <p className="modal__caption">{result.caption}</p>
          <div className="modal__stats">
            <div>
              <div className="stat-num">{result.views}</div>
              <div className="stat-lbl">views</div>
            </div>
            <div>
              <div className="stat-num">{result.likes}</div>
              <div className="stat-lbl">likes</div>
            </div>
            <div>
              <div className="stat-num">{result.duration}</div>
              <div className="stat-lbl">length</div>
            </div>
          </div>
          <div className="modal__actions">
            <button className="btn btn--primary">
              <window.Icon.Play width="14" height="14" /> open on {result.platform === "tiktok" ? "TikTok" : "Instagram"}
            </button>
            <button className="btn btn--ghost">
              <window.Icon.Bookmark width="14" height="14" /> save
            </button>
            <button className="btn btn--ghost">
              <window.Icon.Share width="14" height="14" /> share
            </button>
          </div>
          <div className="modal__related">
            <div className="modal__related-title">Similar vibe</div>
            <div className="modal__related-row">
              {window.MOCK_RESULTS.filter((x) => x.id !== result.id)
                .slice(0, 4)
                .map((x) => (
                  <div key={x.id} className="mini" style={{ backgroundImage: `url(${x.thumb})` }}>
                    <div className="mini__scrim" />
                    <div className="mini__handle">{x.handle}</div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ResultsGrid, ResultDetail, PlatformBadge });
