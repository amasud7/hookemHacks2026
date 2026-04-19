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

function fmtNum(n) {
  if (n == null || n === 0) return null;
  if (typeof n === "string") return n;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function ResultCard({ r, onOpen, i }) {
  const handle = r.handle || (r.creator ? (r.creator.startsWith("@") ? r.creator : `@${r.creator}`) : "");
  const caption = r.caption || "Untitled";
  const thumb = r.thumb || null;
  const videoUrl = r.video_url || null;
  const matchReason = r.matchReason || (r.score != null ? `${Math.round(r.score * 100)}% match` : "vibe match");
  const aspect = r.aspect || 0.9;
  const h = 220 + aspect * 140;
  const [loaded, setLoaded] = React.useState(false);
  const [hovered, setHovered] = React.useState(false);
  const videoRef = React.useRef(null);

  // Autoplay on hover
  React.useEffect(() => {
    if (!videoRef.current) return;
    if (hovered) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {});
    } else {
      videoRef.current.pause();
    }
  }, [hovered]);

  return (
    <article
      className="card"
      style={{ animationDelay: `${i * 35}ms` }}
      onClick={() => onOpen(r)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="card__media" style={{ height: `${h}px` }}>
        {videoUrl ? (
          <>
            {thumb && !hovered && (
              <img
                src={thumb}
                alt=""
                onLoad={() => setLoaded(true)}
                style={{ opacity: 1, position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", zIndex: 1 }}
              />
            )}
            <video
              ref={videoRef}
              src={videoUrl}
              muted
              loop
              playsInline
              preload="metadata"
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            />
          </>
        ) : thumb ? (
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
        {!hovered && (
          <div className="card__play">
            <window.Icon.Play width="20" height="20" />
          </div>
        )}
        <div className="card__match">{matchReason}</div>
      </div>
      <div className="card__body">
        {handle && <div className="card__handle">{handle}</div>}
        <div className="card__caption">{caption}</div>
        {(fmtNum(r.views) || fmtNum(r.likes)) && (
          <div className="card__stats">
            {fmtNum(r.views) && (
              <span>
                <window.Icon.Play width="11" height="11" /> {fmtNum(r.views)}
              </span>
            )}
            {fmtNum(r.likes) && (
              <span>
                <window.Icon.Heart width="11" height="11" /> {fmtNum(r.likes)}
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

function ProductCard({ product }) {
  return (
    <div className="product">
      <div className="product__name">{product.name}</div>
      <div className="product__listings">
        {product.listings && product.listings.map((l, i) => (
          <a key={i} href={l.link} target="_blank" rel="noopener noreferrer" className="product__listing">
            {l.thumbnail && <img src={l.thumbnail} alt="" className="product__thumb" />}
            <div className="product__info">
              <div className="product__title">{l.title}</div>
              <div className="product__price">{l.price}</div>
              <div className="product__source">{l.source}</div>
            </div>
          </a>
        ))}
        {(!product.listings || product.listings.length === 0) && (
          <div className="product__empty">No listings found</div>
        )}
      </div>
    </div>
  );
}

function ResultDetail({ result, onClose }) {
  if (!result) return null;
  const handle = result.handle || (result.creator ? (result.creator.startsWith("@") ? result.creator : `@${result.creator}`) : "");
  const matchReason = result.matchReason || (result.score != null ? `${Math.round(result.score * 100)}% match` : "vibe match");
  const platformLabel = result.platform === "tiktok" ? "TikTok" : result.platform === "instagram" ? "Instagram" : result.platform;

  const videoRef = React.useRef(null);
  const [products, setProducts] = React.useState(null);
  const [loadingProducts, setLoadingProducts] = React.useState(false);

  const identifyProducts = async () => {
    const video = videoRef.current;
    if (!video) return;

    // Capture current frame to canvas
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    const blob = await new Promise((r) => canvas.toBlob(r, "image/jpeg", 0.9));
    const form = new FormData();
    form.append("file", blob, "frame.jpg");

    setLoadingProducts(true);
    try {
      const res = await fetch("/api/products", { method: "POST", body: form });
      const data = await res.json();
      setProducts(data.products || []);
    } catch (e) {
      console.error("Product analysis failed:", e);
      setProducts([]);
    }
    setLoadingProducts(false);
  };

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal__card" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={onClose}>
          <window.Icon.Close width="18" height="18" />
        </button>
        <div className="modal__video">
          {result.video_url ? (
            <video
              ref={videoRef}
              src={result.video_url}
              autoPlay
              loop
              playsInline
              controls
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            />
          ) : result.thumb ? (
            <img src={result.thumb} alt="" />
          ) : (
            <div className="card__placeholder" style={{ minHeight: "100%" }}>
              <div className="card__placeholder-caption" style={{ fontSize: "22px" }}>{result.caption}</div>
            </div>
          )}
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
              <div className="stat-num">{fmtNum(result.views) || "\u2014"}</div>
              <div className="stat-lbl">views</div>
            </div>
            <div>
              <div className="stat-num">{fmtNum(result.likes) || "\u2014"}</div>
              <div className="stat-lbl">likes</div>
            </div>
            <div>
              <div className="stat-num">{fmtNum(result.comments) || "\u2014"}</div>
              <div className="stat-lbl">comments</div>
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
            {result.video_url && (
              <button className="btn btn--shop" onClick={identifyProducts} disabled={loadingProducts}>
                {loadingProducts ? "Analyzing..." : "Identify Products"}
              </button>
            )}
            <button className="btn btn--ghost">
              <window.Icon.Bookmark width="14" height="14" /> save
            </button>
            <button className="btn btn--ghost">
              <window.Icon.Share width="14" height="14" /> share
            </button>
          </div>

          {products !== null && (
            <div className="modal__products">
              <h3 className="modal__products-title">Products Found</h3>
              {products.length === 0 ? (
                <p className="product__empty">No purchasable products detected in this frame.</p>
              ) : (
                products.map((p, i) => <ProductCard key={i} product={p} />)
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ResultsGrid, ResultDetail, PlatformBadge });
