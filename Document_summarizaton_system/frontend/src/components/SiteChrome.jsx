import { Link } from "react-router-dom";

export function SiteHeader() {
  return (
    <header className="mainHeader">
      <div className="headerContent">
        <div className="headerLeft">
          <Link to="/" className="logo" style={{ textDecoration: "none" }}>
            DSS
          </Link>
        </div>

        <div className="headerRight">
          <Link to="/login" className="headerLink">
            Log In
          </Link>
          <Link to="/support" className="headerLink">
            Customer Support
          </Link>
          <Link to="/about" className="headerLink">
            About <span className="dropdownArrow">▼</span>
          </Link>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="footerSection">
      <div className="footerContent">
        <div className="footerTop">
          <span className="footerBrand">DSS</span>

          <div className="footerContent">
            <p className="footerText">
              10,000+ users in over 50 countries summarize their documents with
              DSS
            </p>
          </div>

          <div className="footerLinks">
            <Link to="/terms" className="footerLink">
              Terms &amp; Conditions
            </Link>
            <Link to="/privacy" className="footerLink">
              Privacy Policy
            </Link>
          </div>
        </div>

        <div className="footerBottom">
          <p className="footerCopy">
            © {new Date().getFullYear()} DSS. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
