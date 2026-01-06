import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "./SiteChrome";

/**
 * AuthShell
 * - Wraps login/signup in the same premium split layout.
 * - Provides a flip animation when navigating between /login and /signup.
 *
 * Contract:
 * - children: the auth form content (right panel)
 * - mode: "login" | "signup" (controls copy + flip direction)
 */
export default function AuthShell({ mode, title, subtitle, children }) {
  const navigate = useNavigate();
  const location = useLocation();

  const [flipClass, setFlipClass] = useState("");

  const shellRef = useRef(null);

  // Keep this stable for the component lifetime.
  const oppositePath = useMemo(() => {
    return mode === "login" ? "/signup" : "/login";
  }, [mode]);

  // Flip animation intentionally disabled (instant navigation only).
  useEffect(() => {
    // Clear any stale class if present.
    if (flipClass) setFlipClass("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  function handleGlowMove(e) {
    // Shared hover glow across login/signup
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    el.style.setProperty("--glow-x", `${x}%`);
    el.style.setProperty("--glow-y", `${y}%`);
  }

  const heroLabel = mode === "login" ? "WELCOME BACK" : "GET STARTED";
  const heroTitle =
    mode === "login"
      ? "Document Summarization System"
      : "Create your DSS account";
  const heroText =
    mode === "login"
      ? "Upload PDFs, extract text reliably, and get clean structured summaries in seconds."
      : "Create an account to save your workspace and summarize documents faster.";

  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div
            ref={shellRef}
            className={`authSplit authFlipRoot ${flipClass}`.trim()}
          >
            <section className="authSplitLeft" aria-label="Auth introduction">
              <div className="authHeroBg" aria-hidden="true">
                <span className="authOrb authOrbA" />
                <span className="authOrb authOrbB" />
                <span className="authOrb authOrbC" />
                <span className="authShimmer" />
              </div>

              <div className="authHeroTop">
                <div className="heroLabel">{heroLabel}</div>
                <h1 className="authHeroTitle">{heroTitle}</h1>
                <p className="authHeroText">{heroText}</p>
              </div>

              <div className="authHeroStats">
                <div className="authHeroStat">
                  <div className="authHeroStatValue">PDF → Text</div>
                  <div className="authHeroStatLabel">
                    Hybrid extraction with OCR fallback
                  </div>
                </div>
                <div className="authHeroDivider" />
                <div className="authHeroStat">
                  <div className="authHeroStatValue">Local AI</div>
                  <div className="authHeroStatLabel">
                    Ollama-powered summaries
                  </div>
                </div>
              </div>

              {/* Left-side CTA removed per request */}
            </section>

            <section
              className="contentCard authCard authSplitRight"
              aria-label="Auth form"
              onMouseMove={handleGlowMove}
            >
              <div className="authHeader">
                <h2 className="authTitle">{title}</h2>
                {subtitle ? <p className="contentSubtext">{subtitle}</p> : null}
              </div>

              {children}
            </section>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
