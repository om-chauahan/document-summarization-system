import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function About() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard aboutCard">
            <div className="contentHeader aboutHeader">
              <div className="legalKicker">
                <span className="legalIcon" aria-hidden="true">
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M4.5 7.5C4.5 6.12 5.62 5 7 5h10c1.38 0 2.5 1.12 2.5 2.5v9c0 1.38-1.12 2.5-2.5 2.5H7c-1.38 0-2.5-1.12-2.5-2.5v-9Z"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M8 9h8M8 12h8M8 15h6"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
                <span className="heroLabel">ABOUT SYNOPSIS</span>
                <span className="legalMeta">Fast • Structured • Clean</span>
              </div>

              <h1 className="contentTitle">Synopsis</h1>
              <p className="contentSubtext">
                Synopsis helps you understand long documents faster by turning
                them into short, meaningful summaries while keeping the core
                context intact.
              </p>
            </div>

            <div className="stack">
              <section className="contentBlock aboutBlock">
                <div className="legalBlockHead">
                  <span className="legalBlockIcon" aria-hidden="true">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M12 4.5c5.5 0 9.5 5 9.5 7.5S17.5 19.5 12 19.5 2.5 14.5 2.5 12 6.5 4.5 12 4.5Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Vision</h2>
                </div>
                <p className="contentP">
                  Make document understanding effortless for students,
                  researchers, and professionals — so information becomes
                  accessible, actionable, and easy to learn from.
                </p>
              </section>

              <section className="contentBlock aboutBlock">
                <div className="legalBlockHead">
                  <span className="legalBlockIcon" aria-hidden="true">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M12 3l7 4v6c0 4.7-3.2 8.7-7 9-3.8-.3-7-4.3-7-9V7l7-4Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M9.5 12l1.6 1.6L15.5 9.2"
                        stroke="currentColor"
                        strokeWidth="1.9"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Mission</h2>
                </div>
                <p className="contentP">
                  Provide a clean, reliable platform that can summarize
                  documents quickly, highlight key points, and deliver
                  structured output.
                </p>
              </section>

              <section className="contentBlock aboutBlock">
                <div className="legalBlockHead">
                  <span className="legalBlockIcon" aria-hidden="true">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M12 21s-7-4.4-7-10V6l7-3 7 3v5c0 5.6-7 10-7 10Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M9 12l2 2 4-4"
                        stroke="currentColor"
                        strokeWidth="1.9"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">What Synopsis adds</h2>
                </div>
                <ul className="contentList">
                  <li>Simple upload → instant summary workflow</li>
                  <li>
                    Supports common document formats (PDF, DOCX, TXT, images)
                  </li>
                  <li>Readable output focused on clarity and structure</li>
                  <li>Fast processing designed for everyday use</li>
                </ul>
              </section>

              <section className="contentBlock aboutBlock">
                <div className="legalBlockHead">
                  <span className="legalBlockIcon" aria-hidden="true">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M7 6h10M7 10h10M7 14h6"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <path
                        d="M6 4.5h12A2.5 2.5 0 0 1 20.5 7v10A2.5 2.5 0 0 1 18 19.5H6A2.5 2.5 0 0 1 3.5 17V7A2.5 2.5 0 0 1 6 4.5Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Conclusion</h2>
                </div>
                <p className="contentP">
                  Synopsis is built to save time and improve understanding —
                  helping users focus on insights instead of reading everything
                  line by line.
                </p>
              </section>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
