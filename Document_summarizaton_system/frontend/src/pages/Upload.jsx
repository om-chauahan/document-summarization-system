import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";
import { fetchMe, getStoredUser, storeUser } from "../lib/userSession";

function renderStructuredSummary(text) {
  const src = (text || "").trim();
  if (!src) return null;

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

    // Treat non-bullet lines as headings (the backend prompt asks for headings on their own lines).
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

export default function Upload() {
  const navigate = useNavigate();
  const resultsRef = useRef(null);
  const copyTimeoutRef = useRef(null);
  const typingTimerRef = useRef(null);
  const loadingTimerRef = useRef(null);
  const typingStartTimeoutRef = useRef(null);
  const [file, setFile] = useState(null);
  const [credits, setCredits] = useState(() => {
    const u = getStoredUser();
    return typeof u?.credits === "number" ? u.credits : null;
  });
  const [summary, setSummary] = useState("");
  const [displaySummary, setDisplaySummary] = useState("");
  const [summaryTitle, setSummaryTitle] = useState("AI Summary");
  const [loadingText, setLoadingText] = useState("");
  const [extractedText, setExtractedText] = useState("");
  const [extractedTextLength, setExtractedTextLength] = useState(null);
  const [isSummaryOpen, setIsSummaryOpen] = useState(true);
  const [isExtractedOpen, setIsExtractedOpen] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [error, setError] = useState("");
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedExtracted, setCopiedExtracted] = useState(false);

  // Refresh credits from backend session (if logged in).
  useEffect(() => {
    let mounted = true;
    fetchMe()
      .then((me) => {
        if (!mounted) return;
        if (me && typeof me.credits === "number") {
          setCredits(me.credits);
          storeUser(me);
        }
      })
      .catch(() => {
        // ignore
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Clean up any running typing animation timer.
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) {
        clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
      }
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      if (typingStartTimeoutRef.current) {
        clearTimeout(typingStartTimeoutRef.current);
        typingStartTimeoutRef.current = null;
      }
    };
  }, []);

  // Rotating loading sentences (type -> delete -> next) while the backend works.
  useEffect(() => {
    if (status !== "loading") {
      setLoadingText("");
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      return;
    }

    const sentences = [
      "Extracting text from your document",
      "Cleaning and normalizing text",
      "Detecting important names and entities",
      "Finding key details and numbers",
      "Extracting dates, IDs, and contact info",
      "Organizing content into sections",
      "Writing a clean structured summary",
      "Ensuring no details are missed",
      "Double-checking key fields",
      "Finalizing summary",
      "Preparing results for display",
    ];

    let sIdx = 0;
    let pos = 0;
    let deleting = false;
    let pauseTicks = 0;

    const tickMs = 40; // typing speed
    const pauseAfterType = 18; // pause when a sentence is fully typed
    const pauseAfterDelete = 6; // pause when fully deleted

    setLoadingText("");

    if (loadingTimerRef.current) {
      clearInterval(loadingTimerRef.current);
      loadingTimerRef.current = null;
    }

    loadingTimerRef.current = setInterval(() => {
      const sentence = sentences[sIdx] || "Generating summary";

      if (pauseTicks > 0) {
        pauseTicks -= 1;
        return;
      }

      if (!deleting) {
        pos = Math.min(sentence.length, pos + 1);
        setLoadingText(sentence.slice(0, pos));
        if (pos >= sentence.length) {
          deleting = true;
          pauseTicks = pauseAfterType;
        }
      } else {
        pos = Math.max(0, pos - 1);
        setLoadingText(sentence.slice(0, pos));
        if (pos <= 0) {
          deleting = false;
          sIdx = (sIdx + 1) % sentences.length;
          pauseTicks = pauseAfterDelete;
        }
      }
    }, tickMs);

    return () => {
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
    };
  }, [status]);

  // Typewriter effect after the final summary arrives (non-streaming backend).
  useEffect(() => {
    if (status !== "done" || !summary) return;

    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }

    setDisplaySummary("");

    // Slow, clear ChatGPT-like effect (but still capped so long outputs don't take forever).
    const minChunk = 2;
    const maxChunk = 10;
    const tickMs = 30;
    const maxTypingMs = 9000; // cap total animation time

    let i = 0;
    const startedAt = Date.now();
    typingTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const remaining = summary.length - i;
      if (remaining <= 0 || elapsed >= maxTypingMs) {
        // If we hit the cap, jump to full summary.
        setDisplaySummary(summary);
        clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
        return;
      }

      // Gradually increase chunk size for long summaries to keep it reasonable.
      const dynamic = Math.floor(remaining / 120);
      const chunk = Math.min(
        remaining,
        Math.max(minChunk, Math.min(maxChunk, dynamic)),
      );
      i += chunk;
      setDisplaySummary(summary.slice(0, i));
    }, tickMs);

    return () => {
      if (typingTimerRef.current) {
        clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
      }
    };
  }, [status, summary]);

  const fileHint = useMemo(() => {
    if (!file)
      return "PDF, TXT, DOCX, PNG/JPG • PDFs support OCR (scanned documents)";
    return `${file.name} • ${(file.size / 1024 / 1024).toFixed(2)} MB`;
  }, [file]);

  const extractedBytes = useMemo(() => {
    if (!extractedText) return 0;
    try {
      return new TextEncoder().encode(extractedText).length;
    } catch {
      try {
        return new Blob([extractedText]).size;
      } catch {
        return 0;
      }
    }
  }, [extractedText]);

  async function handleSummarize(e) {
    e.preventDefault();
    if (!file) return;

    setStatus("loading");
    setError("");
    setSummary("");
    setDisplaySummary("");
    setExtractedText("");
    setExtractedTextLength(null);

    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
    if (loadingTimerRef.current) {
      clearInterval(loadingTimerRef.current);
      loadingTimerRef.current = null;
    }
    if (typingStartTimeoutRef.current) {
      clearTimeout(typingStartTimeoutRef.current);
      typingStartTimeoutRef.current = null;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      // Django endpoint (non-streaming)
      const res = await fetch(`${API_BASE}/api/summarize/`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Failed to summarize");

      // Update credits (backend may return `credits` or `credits_remaining`).
      const nextCredits =
        typeof data?.credits === "number"
          ? data.credits
          : typeof data?.credits_remaining === "number"
            ? data.credits_remaining
            : null;
      if (typeof nextCredits === "number") {
        setCredits(nextCredits);
        const existing = getStoredUser();
        if (existing) {
          storeUser({ ...existing, credits: nextCredits });
        }
      }

      // As a source-of-truth, refresh credits from the session after summarization.
      // This guarantees the UI updates even if the API response shape changes.
      fetchMe()
        .then((me) => {
          if (me && typeof me.credits === "number") {
            setCredits(me.credits);
            storeUser(me);
          }
        })
        .catch(() => {
          // ignore
        });

      // Scroll FIRST (after a tiny delay), then set summary so the typing effect starts
      // when the user is already looking at the results.
      setDisplaySummary("");
      setExtractedText(data.extracted_text || "");
      setExtractedTextLength(
        typeof data.extracted_text_length === "number"
          ? data.extracted_text_length
          : null,
      );
      setIsSummaryOpen(true);
      setIsExtractedOpen(false);
      setStatus("done");
      setCopiedSummary(false);
      setCopiedExtracted(false);

      const resultKind = data?.result_kind || "";
      setSummaryTitle(
        resultKind === "image_description" ? "Image Description" : "AI Summary",
      );

      requestAnimationFrame(() => {
        // Small delay before scrolling so the user perceives "summary is ready".
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });

          // Start typing shortly after scroll begins.
          typingStartTimeoutRef.current = setTimeout(() => {
            const finalText =
              (data && typeof data.summary === "string" && data.summary) ||
              (data &&
                typeof data.image_description === "string" &&
                data.image_description) ||
              "";
            setSummary(finalText);
            typingStartTimeoutRef.current = null;
          }, 450);
        }, 250);
      });
    } catch (err) {
      setError(err.message || "Something went wrong");
      setStatus("error");
    }
  }

  return (
    <div className="page">
      <SiteHeader />

      {/* Upload Section */}
      <main className="uploadSection">
        <div className="uploadContent">
          <div className="uploadLeft">
            <div className="heroLabel">UPLOAD DOCUMENT</div>
            <h1 className="heroTitle">Upload your document</h1>
            <p className="heroDescription">
              Upload a document to generate a clean, readable summary in
              seconds. Supported: PDF, TXT, DOCX, PNG/JPG (OCR for scanned
              documents).
            </p>

            <form className="uploadForm" onSubmit={handleSummarize}>
              <label className="fileUploadLabel">
                <input
                  type="file"
                  accept=".pdf,.txt,.docx,.png,.jpg,.jpeg"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="fileInput"
                  disabled={status === "loading"}
                />
                <div
                  className={`fileUploadBox ${file ? "fileSelected" : ""} ${
                    status === "loading" ? "loading" : ""
                  }`}
                >
                  <div className="fileUploadIcon">
                    {status === "loading" ? "⏳" : file ? "✓" : "📄"}
                  </div>
                  <div className="fileUploadText">
                    <div className="fileUploadTitle">
                      {status === "loading"
                        ? "Processing your document..."
                        : file
                          ? file.name
                          : "Choose file to upload"}
                    </div>
                    <div className="fileUploadHint">{fileHint}</div>
                  </div>
                </div>
              </label>

              {status !== "loading" && (
                <button className="btnSubmit" type="submit" disabled={!file}>
                  Generate Summary
                </button>
              )}

              {status !== "loading" && (
                <div className="uploadMetaRow" aria-label="Usage details">
                  <div className="uploadMetaItem">
                    Credits: {typeof credits === "number" ? credits : "—"}
                  </div>
                  {status === "done" && extractedText ? (
                    <div className="uploadMetaItem">
                      Extracted: {extractedTextLength ?? extractedText.length}{" "}
                      chars
                      {" • "}
                      {extractedBytes.toLocaleString()} bytes
                    </div>
                  ) : null}
                </div>
              )}

              {status === "loading" && (
                <div className="loadingIndicator">
                  <div
                    className="loadingTypewriter"
                    aria-label="Generating summary"
                  >
                    <span className="loadingTypewriterText">
                      {loadingText || "Generating summary"}
                    </span>
                    <span
                      className="loadingTypewriterCursor"
                      aria-hidden="true"
                    />
                  </div>
                </div>
              )}
            </form>

            {error && <div className="errorMessage">⚠️ {error}</div>}
          </div>

          <div className="uploadRight heroIllustration">
            <div className="heroGradientBg" />
            <div className="heroAbstractShape heroShapeOne" />
            <div className="heroAbstractShape heroShapeTwo" />
            <div className="heroAbstractShape heroShapeThree" />
            <div className="heroAbstractShape heroShapeFour" />
            <div className="heroGridPattern" />

            <div className="uploadTypography">
              <h2 className="uploadTypoMain">
                Transform documents into insights.
              </h2>

              <p className="uploadTypoSub">
                Our AI-powered system extracts key information, identifies main
                points, and delivers concise summaries that save you time.
              </p>

              <div className="uploadFeatures">
                <div className="uploadFeature">
                  <div className="uploadFeatureIcon">⚡</div>
                  <div className="uploadFeatureContent">
                    <div className="uploadFeatureTitle">Fast Processing</div>
                    <div className="uploadFeatureDesc">
                      Summarize in seconds
                    </div>
                  </div>
                </div>
                <div className="uploadFeature">
                  <div className="uploadFeatureIcon">🎯</div>
                  <div className="uploadFeatureContent">
                    <div className="uploadFeatureTitle">Accurate Results</div>
                    <div className="uploadFeatureDesc">
                      AI-powered precision
                    </div>
                  </div>
                </div>
                <div className="uploadFeature">
                  <div className="uploadFeatureIcon">📊</div>
                  <div className="uploadFeatureContent">
                    <div className="uploadFeatureTitle">Multi-format</div>
                    <div className="uploadFeatureDesc">
                      PDF • TXT • DOCX • PNG/JPG (OCR)
                    </div>
                  </div>
                </div>
              </div>

              <div className="uploadStats">
                <div className="uploadStat">
                  <div className="uploadStatValue">10K+</div>
                  <div className="uploadStatLabel">Documents Processed</div>
                </div>
                <div className="uploadStat">
                  <div className="uploadStatValue">&lt;10s</div>
                  <div className="uploadStatLabel">Average Time</div>
                </div>
                <div className="uploadStat">
                  <div className="uploadStatValue">98%</div>
                  <div className="uploadStatLabel">Accuracy Rate</div>
                </div>
              </div>

              <div className="uploadTags">
                <span className="uploadTag">Secure</span>
                <span className="uploadTag">Reliable</span>
                <span className="uploadTag">Easy to Use</span>
              </div>
            </div>
          </div>
        </div>

        {(summary || extractedText) && (
          <section
            ref={resultsRef}
            className="resultsSection"
            aria-label="Extracted summary"
          >
            <div className="resultsInner">
              <div className="uploadMetaRow" aria-label="Credits remaining">
                <div className="uploadMetaItem">
                  Credits: {typeof credits === "number" ? credits : "—"}
                </div>
              </div>

              {summary && (
                <div className="summaryPanel summaryPanelLarge">
                  <div className="summaryPanelHeader">
                    <h3 className="summaryPanelTitle">{summaryTitle}</h3>
                    <div className="summaryPanelActions">
                      <button
                        type="button"
                        className="summaryPanelBtn"
                        onClick={() => setIsSummaryOpen((v) => !v)}
                      >
                        {isSummaryOpen ? "Hide" : "Show"}
                      </button>
                      <button
                        type="button"
                        className={`summaryPanelBtn summaryPanelBtnCopy ${
                          copiedSummary ? "isCopied" : ""
                        }`}
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(summary);
                            setCopiedSummary(true);
                            if (copyTimeoutRef.current) {
                              clearTimeout(copyTimeoutRef.current);
                            }
                            copyTimeoutRef.current = setTimeout(() => {
                              setCopiedSummary(false);
                              copyTimeoutRef.current = null;
                            }, 1400);
                          } catch {
                            // ignore
                          }
                        }}
                        aria-label={
                          copiedSummary ? "Copied" : "Copy summary to clipboard"
                        }
                      >
                        {copiedSummary ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>

                  {isSummaryOpen && (
                    <div className="summaryPanelBody">
                      {renderStructuredSummary(displaySummary) || (
                        <pre className="summaryPanelText">{displaySummary}</pre>
                      )}

                      {/* Blinking cursor while typing */}
                      {displaySummary &&
                        displaySummary.length < summary.length && (
                          <span className="typingCursor" aria-hidden="true" />
                        )}
                    </div>
                  )}
                </div>
              )}

              {extractedText && (
                <div
                  className="summaryPanel summaryPanelLarge"
                  style={{ marginTop: 16 }}
                >
                  <div className="summaryPanelHeader">
                    <h3 className="summaryPanelTitle">Extracted Text</h3>
                    <div className="summaryPanelActions">
                      <button
                        type="button"
                        className="summaryPanelBtn"
                        onClick={() => setIsExtractedOpen((v) => !v)}
                      >
                        {isExtractedOpen ? "Hide" : "Show"}
                      </button>
                      <button
                        type="button"
                        className={`summaryPanelBtn summaryPanelBtnCopy ${
                          copiedExtracted ? "isCopied" : ""
                        }`}
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(extractedText);
                            setCopiedExtracted(true);
                            if (copyTimeoutRef.current) {
                              clearTimeout(copyTimeoutRef.current);
                            }
                            copyTimeoutRef.current = setTimeout(() => {
                              setCopiedExtracted(false);
                              copyTimeoutRef.current = null;
                            }, 1400);
                          } catch {
                            // ignore
                          }
                        }}
                        aria-label={
                          copiedExtracted
                            ? "Copied"
                            : "Copy extracted text to clipboard"
                        }
                      >
                        {copiedExtracted ? "Copied" : "Copy"}
                      </button>
                      <button
                        type="button"
                        className="summaryPanelBtn summaryPanelBtnDanger"
                        onClick={() => {
                          setSummary("");
                          setExtractedText("");
                        }}
                      >
                        Clear
                      </button>
                    </div>
                  </div>

                  {isExtractedOpen && (
                    <div className="summaryPanelBody">
                      <pre className="summaryPanelText">{extractedText}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Footer Section */}
      <SiteFooter />
    </div>
  );
}
