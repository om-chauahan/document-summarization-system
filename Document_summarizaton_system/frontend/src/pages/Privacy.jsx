import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Privacy() {
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
                      d="M12 2l8 4v6c0 5-3.4 9.4-8 10-4.6-.6-8-5-8-10V6l8-4Z"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M9.5 11.5l1.7 1.7 3.7-3.7"
                      stroke="currentColor"
                      strokeWidth="1.9"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
                <span className="heroLabel">LEGAL</span>
                <span className="legalMeta">Last updated: Jan 7, 2026</span>
              </div>

              <h1 className="contentTitle">Privacy Policy</h1>
              <p className="contentSubtext">
                Synopsis respects privacy. This page explains what happens to
                data in this demo.
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
                  <h2 className="contentH2">Documents</h2>
                </div>
                <ul className="contentList">
                  <li>
                    Uploaded documents are processed to generate a summary.
                  </li>
                  <li>
                    Avoid uploading sensitive personal or confidential
                    documents.
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
                        d="M8 8a4 4 0 0 1 8 0v3"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <path
                        d="M7 11h10a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Analytics and cookies</h2>
                </div>
                <ul className="contentList">
                  <li>
                    This demo does not intentionally use tracking cookies for
                    advertising.
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
                        d="M4 6.5C4 5.67 4.67 5 5.5 5h13C19.33 5 20 5.67 20 6.5v11c0 .83-.67 1.5-1.5 1.5h-13C4.67 19 4 18.33 4 17.5v-11Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M6.5 8l5.5 4 5.5-4"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h2 className="contentH2">Contact</h2>
                </div>
                <p className="contentP">
                  If you have questions, use the Customer Support page to
                  contact the project team.
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
