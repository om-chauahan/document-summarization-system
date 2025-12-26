import { Link } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Home() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="heroSection">
        <div className="heroContent">
          <div className="heroLeft">
            <div className="heroLabel">DOCUMENT SUMMARIZATION SYSTEM</div>

            <h1 className="heroTitle">Summarize better with DSS</h1>

            <p className="heroDescription">
              Software that's powerful, not overpowering. Seamlessly process
              your documents, extract key information, and generate concise
              summaries on one AI-powered platform that grows with your needs.
            </p>

            <div className="heroActions">
              <Link
                to="/signup"
                className="btnDemoLarge"
                style={{ textDecoration: "none", display: "inline-block" }}
              >
                Get started free
              </Link>
            </div>

            <p className="heroSubtext">get started with free tools.</p>
          </div>

          <div className="heroRight heroIllustration">
            <div className="heroTypography">
              <h2 className="typoMain">Understand documents at a glance.</h2>

              <p className="typoSub">
                Turn long PDFs, reports, and research papers into short,
                meaningful summaries — without losing context.
              </p>

              <p className="typoMid">
                Built for students, researchers, and professionals who value
                clarity.
              </p>

              <div className="typoLines">
                <div className="line strong">Accurate summaries</div>
                <div className="line light">Key points • Action items</div>
                <div className="line medium">Fast processing</div>
                <div className="line light">PDF • DOCX • OCR-ready</div>
              </div>

              <div className="typoHighlights">
                <span className="typoTag">Fast</span>
                <span className="typoTag">Consistent</span>
                <span className="typoTag">Readable</span>
                <span className="typoTag">Structured</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
