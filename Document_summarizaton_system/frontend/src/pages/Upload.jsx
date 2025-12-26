import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./home.css";

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState("");
  const [isSummaryOpen, setIsSummaryOpen] = useState(true);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [error, setError] = useState("");

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
      setIsSummaryOpen(true);
      setStatus("done");
    } catch (err) {
      setError(err.message || "Something went wrong");
      setStatus("error");
    }
  }

  return (
    <div className="page">
      {/* Main Header */}
      <header className="mainHeader">
        <div className="headerContent">
          <div className="headerLeft">
            <div
              className="logo"
              onClick={() => navigate("/")}
              style={{ cursor: "pointer" }}
            >
              DSS
            </div>
          </div>
          <div className="headerRight">
            <a href="#" className="headerLink">
              Log In
            </a>
            <a href="#" className="headerLink">
              Customer Support
            </a>
            <a href="#" className="headerLink">
              About <span className="dropdownArrow">▼</span>
            </a>
          </div>
        </div>
      </header>

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

            {summary && (
              <section className="summaryPanel" aria-label="Document summary">
                <div className="summaryPanelHeader">
                  <h3 className="summaryPanelTitle">Summary</h3>
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
                      className="summaryPanelBtn summaryPanelBtnDanger"
                      onClick={() => setSummary("")}
                    >
                      Clear
                    </button>
                  </div>
                </div>

                {isSummaryOpen && (
                  <div className="summaryPanelBody">
                    <pre className="summaryPanelText">{summary}</pre>
                  </div>
                )}
              </section>
            )}
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
      </main>

      {/* Footer Section */}
      <footer className="footerSection">
        <div className="footerContent">
          <div className="footerTop">
            <span className="footerBrand">DSS</span>
            <div className="footerContent">
              <p className="footerText">
                10,000+ users in over 50 countries summarize their documents
                with DSS
              </p>
            </div>
            <div className="footerLinks">
              <a href="#" className="footerLink">
                Terms & Conditions
              </a>
              <a href="#" className="footerLink">
                Privacy Policy
              </a>
            </div>
          </div>
          <div className="footerBottom">
            <p className="footerCopy">
              © {new Date().getFullYear()} DSS. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
