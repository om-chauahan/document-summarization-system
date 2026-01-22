import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";
import { fetchMe, getStoredUser, logout } from "../lib/userSession";

export default function Settings() {
  const navigate = useNavigate();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [showDeletePassword, setShowDeletePassword] = useState(false);

  // Check authentication
  useEffect(() => {
    const stored = getStoredUser();
    if (!stored) {
      fetchMe().then((me) => {
        if (!me) navigate("/login");
      });
    }
  }, [navigate]);

  async function handleDeleteAccount() {
    if (!deletePassword) {
      setDeleteError("Please enter your password to confirm account deletion.");
      return;
    }

    setDeleting(true);
    setDeleteError("");

    try {
      const res = await fetch(`${API_BASE}/api/auth/delete-account/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ password: deletePassword }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok) {
        setDeleteError(data?.error || "Failed to delete account.");
        setDeleting(false);
        return;
      }

      // Logout and redirect
      await logout();
      navigate("/login", {
        state: { message: "Your account has been deleted." },
      });
    } catch (err) {
      setDeleteError(err?.message || "Failed to delete account.");
      setDeleting(false);
    }
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="legalPage">
        <div className="settingsWrap">
          <div className="settingsHeader">
            <div>
              <h1 className="settingsTitle">Account settings</h1>
              <p className="settingsSubtitle">
                Manage your profile, security, and account preferences.
              </p>
            </div>
            <div className="settingsHeaderActions">
              <button
                className="btnPrimary"
                type="button"
                onClick={async () => {
                  await logout();
                  navigate("/login");
                }}
              >
                Sign out
              </button>
            </div>
          </div>

          <div className="settingsGrid">
            <section className="settingsCard" aria-label="Account preferences">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Account preferences</h2>
                <p className="settingsCardHelp">
                  Update your personal details and security settings.
                </p>
              </div>

              <div className="settingsActions">
                <a className="settingsAction" href="/profile">
                  <span className="settingsActionTitle">Edit profile</span>
                  <span className="settingsActionDesc">
                    Name, email, and mobile.
                  </span>
                  <span className="settingsChevron" aria-hidden="true">
                    →
                  </span>
                </a>

                <a className="settingsAction" href="/security">
                  <span className="settingsActionTitle">Security</span>
                  <span className="settingsActionDesc">
                    Password and sign-in protection.
                  </span>
                  <span className="settingsChevron" aria-hidden="true">
                    →
                  </span>
                </a>
              </div>
            </section>

            <section className="settingsCard" aria-label="Notifications">
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Notifications</h2>
                <p className="settingsCardHelp">
                  Notification preferences will be available in a future update.
                </p>
              </div>

              <div className="settingsPlaceholder">
                <div className="settingsPlaceholderBadge">Coming soon</div>
                <p className="settingsPlaceholderText">
                  We’ll add email and in-app notification controls here.
                </p>
              </div>
            </section>

            <section
              className="settingsCard settingsDanger"
              aria-label="Danger zone"
            >
              <div className="settingsCardHead">
                <h2 className="settingsCardTitle">Danger zone</h2>
                <p className="settingsCardHelp">
                  Deleting your account is irreversible. Please be certain.
                </p>
              </div>

              {!showDeleteConfirm ? (
                <button
                  className="btnPrimary settingsDangerBtn"
                  type="button"
                  onClick={() => setShowDeleteConfirm(true)}
                >
                  Delete account
                </button>
              ) : (
                <div className="settingsDangerPanel">
                  <p className="settingsDangerText">
                    Confirm deletion by entering your password.
                  </p>

                  {deleteError ? (
                    <div
                      className="settingsAlert settingsAlertError"
                      role="alert"
                    >
                      {deleteError}
                    </div>
                  ) : null}

                  <label className="field settingsField">
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
                      type={showDeletePassword ? "text" : "password"}
                      value={deletePassword}
                      onChange={(e) => setDeletePassword(e.target.value)}
                      placeholder=" "
                      required
                    />
                    <button
                      type="button"
                      className="fieldToggle"
                      aria-label={
                        showDeletePassword ? "Hide password" : "Show password"
                      }
                      onClick={() => setShowDeletePassword((s) => !s)}
                    >
                      {showDeletePassword ? "Hide" : "Show"}
                    </button>
                    <span className="fieldLabel">
                      Enter your password to confirm
                    </span>
                    <span className="fieldUnderline" aria-hidden="true" />
                  </label>

                  <div className="settingsDangerActions">
                    <button
                      className="btnPrimary settingsDangerBtn"
                      type="button"
                      onClick={handleDeleteAccount}
                      disabled={deleting || !deletePassword}
                    >
                      {deleting ? "Deleting..." : "Confirm Delete Account"}
                    </button>
                    <button
                      className="btnPrimary settingsSecondaryBtn"
                      type="button"
                      onClick={() => {
                        setShowDeleteConfirm(false);
                        setDeletePassword("");
                        setDeleteError("");
                      }}
                      disabled={deleting}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
