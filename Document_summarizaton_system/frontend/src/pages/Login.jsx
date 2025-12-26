import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";

export default function Login() {
  const navigate = useNavigate();
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
              <div className="heroLabel">WELCOME BACK</div>
              <h1 className="contentTitle">Log in to DSS</h1>
              <p className="contentSubtext">
                Access your document workspace and start summarizing.
              </p>
            </div>

            <form className="authForm" onSubmit={handleSubmit}>
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
                  placeholder="••••••••"
                  required
                />
              </label>

              <button className="btnPrimary" type="submit">
                Log In
              </button>

              <p className="authAlt">
                New to DSS?{" "}
                <Link to="/signup" className="textLink">
                  Create an account
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
