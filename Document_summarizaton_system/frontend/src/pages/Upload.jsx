import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [error, setError] = useState("");

  const fileHint = useMemo(() => {
    if (!file) return "PDF or DOCX (scanned PDFs supported via OCR)";
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
      setStatus("done");
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
              Upload a PDF or DOCX file to generate an AI-powered summary
              instantly. Our system supports text PDFs, DOCX files, and scanned
              documents via OCR.
            </p>

            <form className="uploadForm" onSubmit={handleSummarize}>
              <label className="fileUploadLabel">
                <input
                  type="file"
                  accept=".pdf,.docx"
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
                    <div className="uploadFeatureTitle">Multiple Formats</div>
                    <div className="uploadFeatureDesc">PDF • DOCX • OCR</div>
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

            {summary && (
              <div className="summaryCard">
                <div className="summaryCardHeader">
                  <h3 className="summaryCardTitle">Summary</h3>
                  <button
                    className="summaryCardClose"
                    onClick={() => setSummary("")}
                  >
                    ×
                  </button>
                </div>
                <div className="summaryCardContent">{summary}</div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer Section */}
      <SiteFooter />
    </div>
  );
}
