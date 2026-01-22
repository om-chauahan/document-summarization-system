import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";

function renderStructuredSummary(text) {
  const src = (text || "").trim();
  if (!src)
    return <div className="settingsPlaceholderText">No summary stored.</div>;

  const lines = src.split(/\r?\n/).map((l) => l.trimEnd());
  const blocks = [];
  let current = null;

  const pushCurrent = () => {
    if (!current) return;
    if (current.title || current.items.length) blocks.push(current);
    current = null;
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;

    const bullet = line.match(/^[-•\*]\s+(.*)$/);
    const numbered = line.match(/^\d+[\.)]\s+(.*)$/);

    if (bullet || numbered) {
      if (!current) current = { title: "", items: [] };
      current.items.push((bullet?.[1] || numbered?.[1] || line).trim());
      continue;
    }

    pushCurrent();
    current = { title: line.replace(/^\*+|\*+$/g, ""), items: [] };
  }

  pushCurrent();

  if (!blocks.length) {
    return <div className="summaryRichPara">{src}</div>;
  }

  return (
    <div className="summaryRich">
      {blocks.map((b, idx) => (
        <section className="summaryRichSection" key={idx}>
          {idx > 0 && <div className="summaryRichDivider" aria-hidden="true" />}
          {b.title && <div className="summaryRichHeading">{b.title}</div>}
          {b.items.length > 0 && (
            <ul className="summaryRichList">
              {b.items.map((it, i) => (
                <li key={i}>{it}</li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}

export default function MyUploads() {
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState("");
  const [uploads, setUploads] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setStatus("loading");
      setError("");

      try {
        const res = await fetch(`${API_BASE}/api/uploads/`, {
          method: "GET",
          credentials: "include",
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data?.ok) {
          throw new Error(data?.error || "Failed to load uploads");
        }

        if (!mounted) return;
        setUploads(Array.isArray(data.uploads) ? data.uploads : []);
        setStatus("ready");
      } catch (e) {
        if (!mounted) return;
        setError(e?.message || "Failed to load uploads");
        setStatus("error");
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  async function openUpload(id) {
    setSelectedId(id);
    setSelected(null);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/uploads/${id}/`, {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok) {
        throw new Error(data?.error || "Failed to load upload");
      }
      setSelected(data.upload || null);
    } catch (e) {
      setError(e?.message || "Failed to load upload");
    }
  }

  const empty = status === "ready" && uploads.length === 0;

  return (
    <div className="page">
      <SiteHeader />

      <main className="legalPage">
        <div className="settingsWrap">
          <div className="settingsHeader">
            <div>
              <h1 className="settingsTitle">My uploads</h1>
              <p className="settingsSubtitle">
                Your documents and their generated summaries.
              </p>
            </div>

            <div className="settingsHeaderActions">
              <Link className="btnPrimary" to="/upload">
                New upload
              </Link>
            </div>
          </div>

          <div className="settingsGrid">
            <section className="settingsCard" aria-label="Uploads list">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Uploads</h2>
                <p className="settingsCardHelp">
                  Select an item to preview the saved summary.
                </p>
              </div>

              {status === "error" && (
                <div className="settingsAlert settingsAlertError">
                  {error || "Failed to load uploads."}
                </div>
              )}

              {status === "loading" && (
                <div className="settingsPlaceholder">
                  <div className="settingsPlaceholderBadge">Loading</div>
                  <p className="settingsPlaceholderText">
                    Fetching your uploads…
                  </p>
                </div>
              )}

              {empty && (
                <div className="settingsPlaceholder">
                  <div className="settingsPlaceholderBadge">No uploads</div>
                  <p className="settingsPlaceholderText">
                    Upload a document to generate and save a summary.
                  </p>
                </div>
              )}

              {status === "ready" && uploads.length > 0 && (
                <div className="settingsActions">
                  {uploads.map((u) => {
                    const active = selectedId === u.id;
                    const created = u.created_at
                      ? new Date(u.created_at).toLocaleString()
                      : "";
                    const meta = [created, u.detected_type]
                      .filter(Boolean)
                      .join(" • ");

                    return (
                      <button
                        key={u.id}
                        type="button"
                        onClick={() => openUpload(u.id)}
                        className="settingsAction"
                        aria-current={active ? "true" : "false"}
                        style={{
                          textAlign: "left",
                          cursor: "pointer",
                          boxShadow: active ? "var(--shadow-md)" : undefined,
                        }}
                      >
                        <div className="settingsActionTitle">
                          {u.original_name}
                        </div>
                        <div className="settingsActionDesc">{meta || " "}</div>
                        <div className="settingsChevron" aria-hidden="true">
                          ›
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>

            <section className="settingsCard" aria-label="Upload details">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Preview</h2>
                <p className="settingsCardHelp">
                  Saved summary for the selected upload.
                </p>
              </div>

              {!selected && (
                <div className="settingsPlaceholder">
                  <div className="settingsPlaceholderBadge">
                    Select an upload
                  </div>
                  <p className="settingsPlaceholderText">
                    Choose a document from the left to view its summary.
                  </p>
                </div>
              )}

              {selected && (
                <>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <div className="settingsPlaceholderBadge">
                      {selected.detected_type || "document"}
                    </div>
                    <div className="settingsPlaceholderBadge">
                      {(selected.size_bytes || 0).toLocaleString()} bytes
                    </div>
                    {selected.created_at && (
                      <div className="settingsPlaceholderBadge">
                        {new Date(selected.created_at).toLocaleString()}
                      </div>
                    )}
                  </div>

                  <div style={{ marginTop: 14 }}>
                    {renderStructuredSummary(selected.summary)}
                  </div>

                  <div
                    style={{
                      marginTop: 16,
                      display: "flex",
                      gap: 10,
                      flexWrap: "wrap",
                    }}
                  >
                    <a
                      className="btnOutline"
                      href={`${API_BASE}/api/uploads/${selected.id}/download/`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Download document
                    </a>
                    <Link className="btnOutline" to="/upload">
                      Upload another
                    </Link>
                  </div>
                </>
              )}
            </section>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
