import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);

  function handleSubmit(e) {
    e.preventDefault();
    // UI-first: navigate to the tool page (backend auth not implemented).
    navigate("/upload");
  }

  function goSignup(e) {
    e.preventDefault();
    navigate("/signup");
  }

  function handleGoogle(e) {
    e.preventDefault();
    // UI-only placeholder.
  }

  return (
    <AuthShell
      mode="login"
      title="Log in"
      subtitle="Use your email and password to access your workspace."
    >
      <form className="authForm" onSubmit={handleSubmit}>
        <button className="btnSocial" type="button" onClick={handleGoogle}>
          <span className="btnSocialIcon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              width="18"
              height="18"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M21.35 11.1H12v2.98h5.35c-.23 1.25-.95 2.31-2.03 3.02v2.01h3.28c1.92-1.77 3.03-4.38 3.03-7.45 0-.63-.06-1.22-.16-1.77z"
                fill="#4285F4"
              />
              <path
                d="M12 22c2.76 0 5.08-.91 6.77-2.48l-3.28-2.01c-.91.61-2.08.97-3.49.97-2.66 0-4.92-1.8-5.73-4.22H2.88v2.07A10 10 0 0 0 12 22z"
                fill="#34A853"
              />
              <path
                d="M6.27 14.26A5.99 5.99 0 0 1 6 12c0-.78.14-1.53.27-2.26V7.67H2.88A10 10 0 0 0 2 12c0 1.61.39 3.13 1.08 4.33l3.19-2.07z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.52c1.5 0 2.85.52 3.92 1.53l2.93-2.93C17.08 2.57 14.76 2 12 2A10 10 0 0 0 2.88 7.67l3.39 2.07C7.08 7.32 9.34 5.52 12 5.52z"
                fill="#EA4335"
              />
            </svg>
          </span>
          Continue with Google
        </button>

        <div className="authDivider" role="presentation">
          <span>or</span>
        </div>

        <label className="field" htmlFor="login-email">
          <span className="fieldIcon" aria-hidden="true">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 6.5C4 5.11929 5.11929 4 6.5 4H17.5C18.8807 4 20 5.11929 20 6.5V17.5C20 18.8807 18.8807 20 17.5 20H6.5C5.11929 20 4 18.8807 4 17.5V6.5Z"
                stroke="currentColor"
                strokeWidth="1.7"
              />
              <path
                d="M6.5 7.5L12 12L17.5 7.5"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <input
            id="login-email"
            className="fieldInput"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder=" "
            autoComplete="email"
            required
          />
          <span className="fieldLabel">Email</span>
          <span className="fieldUnderline" aria-hidden="true" />
        </label>

        <label className="field" htmlFor="login-password">
          <span className="fieldIcon" aria-hidden="true">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M7.5 10V8.4C7.5 5.9706 9.4706 4 11.9 4H12.1C14.5294 4 16.5 5.9706 16.5 8.4V10"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
              />
              <path
                d="M6.5 10H17.5C18.8807 10 20 11.1193 20 12.5V17.5C20 18.8807 18.8807 20 17.5 20H6.5C5.11929 20 4 18.8807 4 17.5V12.5C4 11.1193 5.11929 10 6.5 10Z"
                stroke="currentColor"
                strokeWidth="1.7"
              />
              <path
                d="M12 14V16"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
              />
            </svg>
          </span>
          <input
            id="login-password"
            className="fieldInput"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder=" "
            autoComplete="current-password"
            required
          />
          <span className="fieldLabel">Password</span>
          <span className="fieldUnderline" aria-hidden="true" />
        </label>

        <div className="authRow">
          <label className="authCheck">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            <span>Remember me</span>
          </label>

          <Link to="/support" className="textLink authForgot">
            Forgot password?
          </Link>
        </div>

        <button className="btnPrimary" type="submit">
          Log In
        </button>

        <p className="authHint">
          Note: authentication is UI-only right now; this continues to the
          upload page.
        </p>

        <p className="authAlt">
          New to Synopsis?{" "}
          <Link to="/signup" className="textLink" onClick={goSignup}>
            Create an account
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
