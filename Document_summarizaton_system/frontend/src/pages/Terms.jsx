import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Terms() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard legalCard">
            <div className="contentHeader legalHeader">
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
                    <path
                      d="M8 12h8"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                    <path
                      d="M8 15.5h6"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
                <span className="heroLabel">LEGAL</span>
                <span className="legalMeta">Last updated: Jan 7, 2026</span>
              </div>

              <h1 className="contentTitle">Terms &amp; Conditions</h1>
              <p className="contentSubtext">
                These terms describe how Synopsis can be used in this project
                demo.
              </p>
            </div>

            <div className="stack">
              <section className="contentBlock legalBlock">
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
                        d="M20 6L9 17l-5-5"
                        stroke="currentColor"
                        strokeWidth="1.9"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Use of the service</h2>
                </div>
                <ul className="contentList">
                  <li>
                    Use Synopsis only for lawful and academic/project purposes.
                  </li>
                  <li>
                    Do not upload documents that you do not have permission to
                    share.
                  </li>
                </ul>
              </section>

              <section className="contentBlock legalBlock">
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
                        d="M12 2a7 7 0 0 0-7 7v4a3 3 0 0 0 3 3h1v3h6v-3h1a3 3 0 0 0 3-3V9a7 7 0 0 0-7-7Z"
                        stroke="currentColor"
                        strokeWidth="1.7"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M10 11h4"
                        stroke="currentColor"
                        strokeWidth="1.7"
                        strokeLinecap="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Content and responsibility</h2>
                </div>
                <ul className="contentList">
                  <li>
                    Summaries are generated automatically and may contain
                    mistakes.
                  </li>
                  <li>
                    Always verify important information from the original
                    document.
                  </li>
                </ul>
              </section>

              <section className="contentBlock legalBlock">
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
                        d="M12 3v9"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <path
                        d="M12 21a8 8 0 1 0 0-16"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <path
                        d="M12 12l4 2"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Availability</h2>
                </div>
                <ul className="contentList">
                  <li>
                    This is a student project; uptime and performance are not
                    guaranteed.
                  </li>
                </ul>
              </section>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
