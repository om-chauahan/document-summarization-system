import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Upload() {
  const navigate = useNavigate();
  const resultsRef = useRef(null);
  const copyTimeoutRef = useRef(null);
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState("");
  const [extractedText, setExtractedText] = useState("");
  const [isSummaryOpen, setIsSummaryOpen] = useState(true);
  const [isExtractedOpen, setIsExtractedOpen] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [error, setError] = useState("");
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedExtracted, setCopiedExtracted] = useState(false);

  const fileHint = useMemo(() => {
    if (!file) return "PDF only • Text PDFs + scanned PDFs (OCR)";
    return `${file.name} • ${(file.size / 1024 / 1024).toFixed(2)} MB`;
  }, [file]);

  async function handleSummarize(e) {
    e.preventDefault();
    if (!file) return;

    setStatus("loading");
    setError("");
    setSummary("");
    setExtractedText("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      // Django endpoint
      const res = await fetch("http://127.0.0.1:8000/api/summarize/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Failed to summarize");

      setSummary(data.summary || "");
      setExtractedText(data.extracted_text || "");
      setIsSummaryOpen(true);
      setIsExtractedOpen(false);
      setStatus("done");
      setCopiedSummary(false);
      setCopiedExtracted(false);

      // Smooth-scroll to the results section so the user immediately sees the summary.
      // Use rAF so the DOM updates (section renders) before scrolling.
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
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
              Upload a PDF to generate a clean, readable summary in seconds. We
              support both text-based PDFs and scanned PDFs via OCR.
            </p>

            <form className="uploadForm" onSubmit={handleSummarize}>
              <label className="fileUploadLabel">
                <input
                  type="file"
                  accept=".pdf"
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

              {status === "loading" && (
                <div className="loadingIndicator">
                  <div className="loadingBar">
                    <div className="loadingBarFill" />
                  </div>
                  <p className="loadingText">Analyzing your document...</p>
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
                    <div className="uploadFeatureTitle">PDF Ready</div>
                    <div className="uploadFeatureDesc">
                      Text PDFs • Scanned PDFs (OCR)
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
              {summary && (
                <div className="summaryPanel summaryPanelLarge">
                  <div className="summaryPanelHeader">
                    <h3 className="summaryPanelTitle">AI Summary (BART)</h3>
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
                      <pre className="summaryPanelText">{summary}</pre>
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
