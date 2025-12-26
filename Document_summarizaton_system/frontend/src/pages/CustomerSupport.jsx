import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function CustomerSupport() {
  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard">
            <div className="contentHeader">
              <div className="heroLabel">CUSTOMER SUPPORT</div>
              <h1 className="contentTitle">We’re here to help</h1>
              <p className="contentSubtext">
                For project-related queries, contact the team members below.
              </p>
            </div>

            <div className="grid2">
              <div className="infoCard">
                <div className="infoTitle">Chauhan Om V.</div>
                <div className="infoMeta">Roll No: CE019</div>
                <a className="textLink" href="mailto:24ceubg903@ddu.ac.in">
                  24ceubg903@ddu.ac.in
                </a>
              </div>

              <div className="infoCard">
                <div className="infoTitle">Desai Moksh Hemanshu</div>
                <div className="infoMeta">Roll No: CE071</div>
                <a className="textLink" href="mailto:23ceuoz032@ddu.ac.in">
                  23ceuoz032@ddu.ac.in
                </a>
              </div>
            </div>

            <div className="contentDivider" />

            <div className="contentNote">
              <div className="noteTitle">Support hours</div>
              <p className="noteText">
                We respond as soon as possible. Please include your document
                type (PDF/DOCX), what you clicked, and any error message you
                see.
              </p>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
