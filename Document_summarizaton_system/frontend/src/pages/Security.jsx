import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";
import { fetchMe, getStoredUser } from "../lib/userSession";

export default function Security() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  // Check authentication
  useEffect(() => {
    const stored = getStoredUser();
    if (!stored) {
      fetchMe().then((me) => {
        if (!me) navigate("/login");
      });
    }
  }, [navigate]);

  function handleChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError("");
    setSuccess("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (formData.new_password !== formData.confirm_password) {
      setError("New passwords do not match.");
      return;
    }

    if (formData.new_password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/auth/change-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: formData.current_password,
          new_password: formData.new_password,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok) {
        setError(data?.error || "Failed to change password.");
        setLoading(false);
        return;
      }

      setSuccess("Password changed successfully!");
      setFormData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err?.message || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="legalPage">
        <div className="settingsWrap">
          <div className="settingsHeader">
            <div>
              <h1 className="settingsTitle">Security</h1>
              <p className="settingsSubtitle">
                Keep your account protected. Update your password regularly.
              </p>
            </div>
          </div>

          <div className="settingsGrid">
            <section className="settingsCard" aria-label="Change password">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Change password</h2>
                <p className="settingsCardHelp">
                  Use a strong password (at least 6 characters). Don’t reuse old
                  passwords.
                </p>
              </div>

              {success ? (
                <div className="profileAlert success" role="status">
                  <span className="profileAlertDot" aria-hidden="true" />
                  <span>{success}</span>
                </div>
              ) : null}

              {error ? (
                <div className="settingsAlert settingsAlertError" role="alert">
                  {error}
                </div>
              ) : null}

              <form onSubmit={handleSubmit} className="securityForm">
                <label className="field securityField">
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
                    className="fieldInput"
                    type={showCurrentPassword ? "text" : "password"}
                    name="current_password"
                    value={formData.current_password}
                    onChange={handleChange}
                    placeholder=" "
                    required
                  />
                  <button
                    type="button"
                    className="fieldToggle"
                    aria-label={
                      showCurrentPassword ? "Hide password" : "Show password"
                    }
                    onClick={() => setShowCurrentPassword((s) => !s)}
                  >
                    {showCurrentPassword ? "Hide" : "Show"}
                  </button>
                  <span className="fieldLabel">Current Password</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <label className="field securityField">
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
                    className="fieldInput"
                    type={showNewPassword ? "text" : "password"}
                    name="new_password"
                    value={formData.new_password}
                    onChange={handleChange}
                    placeholder=" "
                    required
                  />
                  <button
                    type="button"
                    className="fieldToggle"
                    aria-label={
                      showNewPassword ? "Hide password" : "Show password"
                    }
                    onClick={() => setShowNewPassword((s) => !s)}
                  >
                    {showNewPassword ? "Hide" : "Show"}
                  </button>
                  <span className="fieldLabel">New Password</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <label className="field securityField securityFieldLast">
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
                    className="fieldInput"
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirm_password"
                    value={formData.confirm_password}
                    onChange={handleChange}
                    placeholder=" "
                    required
                  />
                  <button
                    type="button"
                    className="fieldToggle"
                    aria-label={
                      showConfirmPassword ? "Hide password" : "Show password"
                    }
                    onClick={() => setShowConfirmPassword((s) => !s)}
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                  <span className="fieldLabel">Confirm New Password</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <div className="securityActions">
                  <button
                    className="btnPrimary"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? "Updating…" : "Update password"}
                  </button>
                </div>
              </form>
            </section>

            <section className="settingsCard" aria-label="Security tips">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Security tips</h2>
                <p className="settingsCardHelp">
                  A few best practices to keep your data safe.
                </p>
              </div>

              <ul className="securityTips">
                <li>Use a unique password for this account.</li>
                <li>Avoid sharing credentials or OTPs.</li>
                <li>Sign out on shared devices.</li>
              </ul>
            </section>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
