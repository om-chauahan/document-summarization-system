import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell";

export default function Signup() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [mobile, setMobile] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [touched, setTouched] = useState({
    email: false,
    confirmPassword: false,
  });

  const isEmailValid = !email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isConfirmMatch = !confirmPassword || password === confirmPassword;
  const showEmailError = touched.email && !isEmailValid;
  const showConfirmError = touched.confirmPassword && !isConfirmMatch;

  function handleSubmit(e) {
    e.preventDefault();
    if (!isEmailValid || !isConfirmMatch) return;
    // UI-first: navigate to the tool page (backend auth not implemented).
    navigate("/upload");
  }

  function goLogin(e) {
    e.preventDefault();
    navigate("/login");
  }

  function handleGoogle(e) {
    e.preventDefault();
    // UI-only placeholder.
  }

  return (
    <AuthShell
      mode="signup"
      title="Create account"
      subtitle="Create an account to access your document workspace."
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

        <div className="authFieldRow">
          <label className="field" htmlFor="signup-first-name">
            <span className="fieldIcon" aria-hidden="true">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 12C14.4853 12 16.5 9.98528 16.5 7.5C16.5 5.01472 14.4853 3 12 3C9.51472 3 7.5 5.01472 7.5 7.5C7.5 9.98528 9.51472 12 12 12Z"
                  stroke="currentColor"
                  strokeWidth="1.7"
                />
                <path
                  d="M4.5 21C4.5 17.9624 7.96243 15.5 12 15.5C16.0376 15.5 19.5 17.9624 19.5 21"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                />
              </svg>
            </span>
            <input
              id="signup-first-name"
              className="fieldInput"
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder=" "
              autoComplete="given-name"
              required
            />
            <span className="fieldLabel">First name</span>
            <span className="fieldUnderline" aria-hidden="true" />
          </label>

          <label className="field" htmlFor="signup-last-name">
            <span className="fieldIcon" aria-hidden="true">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 12C14.4853 12 16.5 9.98528 16.5 7.5C16.5 5.01472 14.4853 3 12 3C9.51472 3 7.5 5.01472 7.5 7.5C7.5 9.98528 9.51472 12 12 12Z"
                  stroke="currentColor"
                  strokeWidth="1.7"
                />
                <path
                  d="M4.5 21C4.5 17.9624 7.96243 15.5 12 15.5C16.0376 15.5 19.5 17.9624 19.5 21"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                />
              </svg>
            </span>
            <input
              id="signup-last-name"
              className="fieldInput"
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder=" "
              autoComplete="family-name"
              required
            />
            <span className="fieldLabel">Last name</span>
            <span className="fieldUnderline" aria-hidden="true" />
          </label>
        </div>

        <label className="field" htmlFor="signup-mobile">
          <span className="fieldIcon" aria-hidden="true">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M8 4.5C8 3.67157 8.67157 3 9.5 3H14.5C15.3284 3 16 3.67157 16 4.5V19.5C16 20.3284 15.3284 21 14.5 21H9.5C8.67157 21 8 20.3284 8 19.5V4.5Z"
                stroke="currentColor"
                strokeWidth="1.7"
              />
              <path
                d="M11 18H13"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
              />
            </svg>
          </span>
          <input
            id="signup-mobile"
            className="fieldInput"
            type="tel"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder=" "
            autoComplete="tel"
            inputMode="tel"
            required
          />
          <span className="fieldLabel">Mobile no</span>
          <span className="fieldUnderline" aria-hidden="true" />
        </label>

        <label
          className={`field ${showEmailError ? "fieldError" : ""}`}
          htmlFor="signup-email"
        >
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
            id="signup-email"
            className="fieldInput"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => setTouched((t) => ({ ...t, email: true }))}
            placeholder=" "
            autoComplete="email"
            required
          />
          <span className="fieldLabel">Email</span>
          <span className="fieldUnderline" aria-hidden="true" />
          {showEmailError ? (
            <span className="fieldHelp" role="alert">
              Enter a valid email address
            </span>
          ) : null}
        </label>

        <label className="field" htmlFor="signup-password">
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
            id="signup-password"
            className="fieldInput"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder=" "
            autoComplete="new-password"
            required
          />
          <button
            type="button"
            className="fieldToggle"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            onClick={() => setShowPassword((s) => !s)}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
          <span className="fieldLabel">Password</span>
          <span className="fieldUnderline" aria-hidden="true" />
        </label>

        <label
          className={`field ${showConfirmError ? "fieldError" : ""}`}
          htmlFor="signup-confirm-password"
        >
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
                d="M10 15.2L11.3 16.5L14 13.8"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <input
            id="signup-confirm-password"
            className="fieldInput"
            type={showConfirmPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            onBlur={() => setTouched((t) => ({ ...t, confirmPassword: true }))}
            placeholder=" "
            autoComplete="new-password"
            required
          />
          <button
            type="button"
            className="fieldToggle"
            aria-label={
              showConfirmPassword
                ? "Hide confirm password"
                : "Show confirm password"
            }
            aria-pressed={showConfirmPassword}
            onClick={() => setShowConfirmPassword((s) => !s)}
          >
            {showConfirmPassword ? "Hide" : "Show"}
          </button>
          <span className="fieldLabel">Confirm password</span>
          <span className="fieldUnderline" aria-hidden="true" />
          {showConfirmError ? (
            <span className="fieldHelp" role="alert">
              Passwords don’t match
            </span>
          ) : null}
        </label>

        <button className="btnPrimary" type="submit">
          Create Account
        </button>

        <p className="authAlt">
          Already have an account?{" "}
          <Link to="/login" className="textLink" onClick={goLogin}>
            Log in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
