import React from "react";
import "./home.css";

export default function Home() {
  return (
    <div className="page">
      
      <header className="mainHeader">
        <div className="headerContent">
          <div className="headerLeft">
            <div className="logo">DSS</div>
          </div>

          <div className="headerRight">
            <a href="#" className="headerLink">
              Log In
            </a>
            <a href="#" className="headerLink">
              Customer Support
            </a>
            <a href="#" className="headerLink">
              About <span className="dropdownArrow">▼</span>
            </a>
          </div>
        </div>
      </header>

      
      <main className="heroSection">
        <div className="heroContent">
          
          <div className="heroLeft">
            <div className="heroLabel">DOCUMENT SUMMARIZATION SYSTEM</div>

            <h1 className="heroTitle">Summarize better with DSS</h1>

            <p className="heroDescription">
              Software that's powerful, not overpowering. Seamlessly process
              your documents, extract key information, and generate concise
              summaries on one AI-powered platform that grows with your needs.
            </p>

            <div className="heroActions">
              <button className="btnDemoLarge">        Get started free        </button>
              
            </div>

            <p className="heroSubtext">
            get started with free
              tools.
            </p>
          </div>

          
          <div className="heroRight heroIllustration">
            <div className="heroTypography">
              <h2 className="typoMain">Understand documents at a glance.</h2>

              <p className="typoSub">
                Turn long PDFs, reports, and research papers into short,
                meaningful summaries — without losing context.
              </p>

              <p className="typoMid">
                Built for students, researchers, and professionals who value
                clarity.
              </p>

              <div className="typoLines">
                <div className="line strong">Accurate summaries</div>
                <div className="line light">Key points • Action items</div>
                <div className="line medium">Fast processing</div>
                <div className="line light">PDF • DOCX • OCR-ready</div>
              </div>

              <div className="typoHighlights">
                <span className="typoTag">Fast</span>
                <span className="typoTag">Consistent</span>
                <span className="typoTag">Readable</span>
                <span className="typoTag">Structured</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      
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
        <a href="#" className="footerLink">
          Terms & Conditions
        </a>
        <a href="#" className="footerLink">
          Privacy Policy
        </a>
      </div>
    </div>

    <div className="footerBottom">
      <p className="footerCopy">
        © {new Date().getFullYear()} DSS. All rights
        reserved.
      </p>
    </div>
  </div>
</footer>

    </div>
  );
}
