import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { fetchMe, getStoredUser, storeUser } from "../lib/userSession";

export default function Home() {
  const navigate = useNavigate();

  async function handleGetStarted(e) {
    e.preventDefault();

    // Fast path: if we already have a stored user, assume logged-in.
    const stored = getStoredUser();
    if (stored) {
      navigate("/upload");
      return;
    }

    // Slow path: ask the backend if a valid session exists.
    const me = await fetchMe().catch(() => null);
    if (me) {
      storeUser(me);
      navigate("/upload");
      return;
    }

    navigate("/login");
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="heroSection">
        <div className="heroContent">
          <div className="heroLeft">
            <div className="heroLabel">SYNOPSIS</div>

            <h1 className="heroTitle">Summarize better with Synopsis</h1>

            <p className="heroDescription">
              Software that's powerful, not overpowering. Seamlessly process
              your documents, extract key information, and generate concise
              summaries on one AI-powered platform that grows with your needs.
            </p>

            <div className="heroActions">
              <a
                href="/login"
                className="btnDemoLarge"
                style={{ textDecoration: "none", display: "inline-block" }}
                onClick={handleGetStarted}
              >
                Get started free
              </a>
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
                <div className="line light">PDF • DOCX • TXT • PNG • JPG</div>
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
