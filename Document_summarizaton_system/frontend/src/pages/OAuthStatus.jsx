import React from "react";

export default function OAuthStatus() {
  return (
    <div className="oauth-status-page">
      <h2>OAuth Status</h2>
      <p>
        Google sign-in has been removed from this build. The button is shown as
        a placeholder.
      </p>
      <a href="/login" className="btn">
        Back to Login
      </a>
    </div>
  );
}
