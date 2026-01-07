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
  const heroTitle = mode === "login" ? "Synopsis" : "Synopsis";
  const heroText =
    mode === "login"
      ? "Upload documents, extract text reliably, and get clean structured summaries in seconds."
      : "Start summarizing your documents with a premium, distraction-free workflow.";

  const features = useMemo(() => {
    return [
      {
        title: "Multi-format input",
        text: "PDF, DOCX, TXT, and images (OCR) — one workflow.",
      },
      {
        title: "Cleaner summaries",
        text: "Structured output with less noise and better signal.",
      },
      {
        title: "Fast workflow",
        text: "Upload → extract → summarize, with a polished experience.",
      },
    ];
  }, []);

  const trustText = "Built for students, teams, and busy professionals.";

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
                  <div className="authHeroStatValue">Smart extraction</div>
                  <div className="authHeroStatLabel">
                    <span className="authFormatInline">
                      <span className="authFormatInlineItem">
                        <span
                          className="authFormatInlineIcon isPdf"
                          aria-hidden="true"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M7 3h7l3 3v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M14 3v4a2 2 0 0 0 2 2h4"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </span>
                        PDF
                      </span>

                      <span className="authFormatInlineItem">
                        <span
                          className="authFormatInlineIcon isDocx"
                          aria-hidden="true"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M7 3h7l3 3v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M8 10h8M8 13h8M8 16h6"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                            />
                          </svg>
                        </span>
                        DOCX
                      </span>

                      <span className="authFormatInlineItem">
                        <span
                          className="authFormatInlineIcon isTxt"
                          aria-hidden="true"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M7 3h7l3 3v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M8 11h8M8 14h8"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                            />
                          </svg>
                        </span>
                        TXT
                      </span>

                      <span className="authFormatInlineItem">
                        <span
                          className="authFormatInlineIcon isPng"
                          aria-hidden="true"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <rect
                              x="4"
                              y="6"
                              width="16"
                              height="12"
                              rx="2"
                              stroke="currentColor"
                              strokeWidth="1.8"
                            />
                            <path
                              d="M7 15l3-3 3 3 2-2 3 3"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M9 10.2h.01"
                              stroke="currentColor"
                              strokeWidth="3"
                              strokeLinecap="round"
                            />
                          </svg>
                        </span>
                        PNG
                      </span>

                      <span className="authFormatInlineItem">
                        <span
                          className="authFormatInlineIcon isJpg"
                          aria-hidden="true"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <rect
                              x="4"
                              y="6"
                              width="16"
                              height="12"
                              rx="2"
                              stroke="currentColor"
                              strokeWidth="1.8"
                            />
                            <path
                              d="M8 14.5l2.6-2.6L14 15.3"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M15 12l2 2.2"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                            />
                          </svg>
                        </span>
                        JPG
                      </span>
                    </span>
                  </div>
                </div>
                <div className="authHeroDivider" />
                <div className="authHeroStat">
                  <div className="authHeroStatValue">Structured output</div>
                  <div className="authHeroStatLabel">
                    Clean sections made for quick reading
                  </div>
                </div>
              </div>

              <div className="authHeroFeatures" aria-label="Highlights">
                {features.map((f) => (
                  <div className="authHeroFeature" key={f.title}>
                    <div className="authHeroFeatureIcon" aria-hidden="true">
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M20 6L9 17l-5-5"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                    <div className="authHeroFeatureBody">
                      <div className="authHeroFeatureTitle">{f.title}</div>
                      <div className="authHeroFeatureText">{f.text}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="authHeroTrust" aria-label="Trust">
                <span className="authHeroTrustText">{trustText}</span>
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
