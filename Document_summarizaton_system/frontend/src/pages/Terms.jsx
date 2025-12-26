import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Terms() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard">
            <div className="contentHeader">
              <div className="heroLabel">LEGAL</div>
              <h1 className="contentTitle">Terms &amp; Conditions</h1>
              <p className="contentSubtext">
                These terms describe how DSS can be used in this project demo.
              </p>
            </div>

            <div className="stack">
              <section className="contentBlock">
                <h2 className="contentH2">Use of the service</h2>
                <ul className="contentList">
                  <li>Use DSS only for lawful and academic/project purposes.</li>
                  <li>
                    Do not upload documents that you do not have permission to
                    share.
                  </li>
                </ul>
              </section>

              <section className="contentBlock">
                <h2 className="contentH2">Content and responsibility</h2>
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

              <section className="contentBlock">
                <h2 className="contentH2">Availability</h2>
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
