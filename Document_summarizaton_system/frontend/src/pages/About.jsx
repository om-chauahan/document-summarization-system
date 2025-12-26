import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function About() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard">
            <div className="contentHeader">
              <div className="heroLabel">ABOUT DSS</div>
              <h1 className="contentTitle">Document Summarization System</h1>
              <p className="contentSubtext">
                DSS helps you understand long documents faster by turning them
                into short, meaningful summaries while keeping the core context
                intact.
              </p>
            </div>

            <div className="stack">
              <section className="contentBlock">
                <h2 className="contentH2">Vision</h2>
                <p className="contentP">
                  Make document understanding effortless for students,
                  researchers, and professionals — so information becomes
                  accessible, actionable, and easy to learn from.
                </p>
              </section>

              <section className="contentBlock">
                <h2 className="contentH2">Mission</h2>
                <p className="contentP">
                  Provide a clean, reliable platform that can summarize PDFs and
                  DOCX files quickly, highlight key points, and support scanned
                  documents through OCR.
                </p>
              </section>

              <section className="contentBlock">
                <h2 className="contentH2">What DSS adds</h2>
                <ul className="contentList">
                  <li>Simple upload → instant summary workflow</li>
                  <li>Support for PDF and DOCX, including OCR-ready files</li>
                  <li>Readable output focused on clarity and structure</li>
                  <li>Fast processing designed for everyday use</li>
                </ul>
              </section>

              <section className="contentBlock">
                <h2 className="contentH2">Conclusion</h2>
                <p className="contentP">
                  DSS is built to save time and improve understanding — helping
                  users focus on insights instead of reading everything line by
                  line.
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
