import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    // UI-first: navigate to the tool page (backend auth not implemented).
    navigate("/upload");
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="contentSection">
        <div className="contentContainer">
          <div className="contentCard authCard">
            <div className="authHeader">
              <div className="heroLabel">GET STARTED</div>
              <h1 className="contentTitle">Create your DSS account</h1>
              <p className="contentSubtext">
                Start summarizing PDFs and DOCX files in minutes.
              </p>
            </div>

            <form className="authForm" onSubmit={handleSubmit}>
              <label className="field">
                <span className="fieldLabel">Full name</span>
                <input
                  className="fieldInput"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </label>

              <label className="field">
                <span className="fieldLabel">Email</span>
                <input
                  className="fieldInput"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                />
              </label>

              <label className="field">
                <span className="fieldLabel">Password</span>
                <input
                  className="fieldInput"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  required
                />
              </label>

              <button className="btnPrimary" type="submit">
                Create Account
              </button>

              <p className="authAlt">
                Already have an account?{" "}
                <Link to="/login" className="textLink">
                  Log in
                </Link>
              </p>
            </form>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
