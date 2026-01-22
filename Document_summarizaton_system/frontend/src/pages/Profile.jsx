import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";
import { fetchMe, getStoredUser, storeUser } from "../lib/userSession";

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    mobile: "",
  });

  useEffect(() => {
    async function loadUser() {
      const stored = getStoredUser();
      if (stored) {
        setUser(stored);
        setFormData({
          first_name: stored.first_name || "",
          last_name: stored.last_name || "",
          email: stored.email || "",
          mobile: stored.username || "",
        });
        setLoading(false);
        return;
      }

      const me = await fetchMe();
      if (me) {
        setUser(me);
        setFormData({
          first_name: me.first_name || "",
          last_name: me.last_name || "",
          email: me.email || "",
          mobile: me.username || "",
        });
        storeUser(me);
        setLoading(false);
      } else {
        navigate("/login");
      }
    }
    loadUser();
  }, [navigate]);

  function handleChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError("");
    setSuccess("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${API_BASE}/api/auth/profile/`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok) {
        setError(data?.error || "Failed to update profile.");
        setSaving(false);
        return;
      }

      if (data?.user) {
        setUser(data.user);
        storeUser(data.user);
        setFormData({
          first_name: data.user.first_name || "",
          last_name: data.user.last_name || "",
          email: data.user.email || "",
          mobile: data.user.username || "",
        });
      }

      setSuccess("Profile updated successfully!");
      setEditing(false);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err?.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (user) {
      setFormData({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        email: user.email || "",
        mobile: user.username || "",
      });
    }
    setEditing(false);
    setError("");
    setSuccess("");
  }

  if (loading) {
    return (
      <div className="page">
        <SiteHeader />
        <main className="profilePage">
          <div className="profileShell">
            <div className="profileCard">
              <div className="profileLoading">
                <div className="profileSkeletonAvatar" aria-hidden="true" />
                <div style={{ flex: 1 }}>
                  <div className="profileSkeletonLine" aria-hidden="true" />
                  <div
                    className="profileSkeletonLine short"
                    aria-hidden="true"
                  />
                </div>
              </div>
              <p className="profileMuted">Loading your profile…</p>
            </div>
          </div>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="profilePage">
        <div className="profileShell">
          <section className="profileHero" aria-label="Profile header">
            <div className="profileHeroLeft">
              <div className="profileAvatar" aria-hidden="true">
                {(formData.first_name || "U").slice(0, 1).toUpperCase()}
              </div>
              <div className="profileHeroText">
                <h1 className="profileTitle">Profile</h1>
                <p className="profileSubtitle">
                  Manage your personal information and account details.
                </p>
              </div>
            </div>

            <div className="profileHeroRight">
              {!editing ? (
                <button
                  className="btnPrimary profileEditBtn"
                  onClick={() => setEditing(true)}
                >
                  Edit profile
                </button>
              ) : (
                <div className="profilePill" aria-label="Editing mode">
                  Editing
                </div>
              )}
            </div>
          </section>

          <section className="profileCard" aria-label="Profile details">
            {(success || error) && (
              <div className="profileAlerts">
                {success ? (
                  <div className="profileAlert success" role="status">
                    <span className="profileAlertDot" aria-hidden="true" />
                    <span>{success}</span>
                  </div>
                ) : null}
                {error ? (
                  <div className="profileAlert error" role="alert">
                    <span className="profileAlertDot" aria-hidden="true" />
                    <span>{error}</span>
                  </div>
                ) : null}
              </div>
            )}

            <form onSubmit={handleSubmit} className="profileForm">
              <div className="profileGrid">
                <label className="field">
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
                    className="fieldInput"
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder=" "
                    disabled={!editing}
                    required
                  />
                  <span className="fieldLabel">First Name</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <label className="field">
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
                    className="fieldInput"
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    placeholder=" "
                    disabled={!editing}
                    required
                  />
                  <span className="fieldLabel">Last Name</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <label className="field profileSpan2">
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
                    className="fieldInput"
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder=" "
                    disabled={!editing}
                    required
                  />
                  <span className="fieldLabel">Email</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>

                <label className="field profileSpan2">
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
                    className="fieldInput"
                    type="tel"
                    name="mobile"
                    value={formData.mobile}
                    onChange={handleChange}
                    placeholder=" "
                    disabled={!editing}
                    required
                  />
                  <span className="fieldLabel">Mobile Number</span>
                  <span className="fieldUnderline" aria-hidden="true" />
                </label>
              </div>

              <div className="profileFooter">
                {!editing ? (
                  <p className="profileMuted">
                    Tip: Click “Edit profile” to update your details.
                  </p>
                ) : (
                  <div className="profileActions">
                    <button
                      className="btnPrimary"
                      type="submit"
                      disabled={saving}
                    >
                      {saving ? "Saving…" : "Save changes"}
                    </button>
                    <button
                      type="button"
                      className="btnOutline"
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </form>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
