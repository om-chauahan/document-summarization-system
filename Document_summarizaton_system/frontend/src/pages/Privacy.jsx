import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Privacy() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard">
            <div className="contentHeader">
              <div className="heroLabel">LEGAL</div>
              <h1 className="contentTitle">Privacy Policy</h1>
              <p className="contentSubtext">
                DSS respects privacy. This page explains what happens to data in
                this demo.
              </p>
            </div>

            <div className="stack">
              <section className="contentBlock">
                <h2 className="contentH2">Documents</h2>
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

              <section className="contentBlock">
                <h2 className="contentH2">Analytics and cookies</h2>
                <ul className="contentList">
                  <li>
                    This demo does not intentionally use tracking cookies for
                    advertising.
                  </li>
                </ul>
              </section>

              <section className="contentBlock">
                <h2 className="contentH2">Contact</h2>
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
