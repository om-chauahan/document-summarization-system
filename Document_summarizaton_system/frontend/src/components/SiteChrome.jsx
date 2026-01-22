import { Link } from "react-router-dom";
import { useEffect, useMemo, useRef, useState } from "react";
import { fetchMe, getStoredUser, logout, storeUser } from "../lib/userSession";
import { useNavigate } from "react-router-dom";
import { Icon } from "./Icons";

export function SiteHeader() {
  const navigate = useNavigate();
  const menuRef = useRef(null);
  const [user, setUser] = useState(() => getStoredUser());
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    // Refresh from backend if a session cookie exists.
    fetchMe()
      .then((u) => {
        if (!mounted) return;
        if (u) {
          setUser(u);
          storeUser(u);
        }
      })
      .catch(() => {
        // ignore
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;

    function onDown(e) {
      const el = menuRef.current;
      if (!el) return;
      if (el.contains(e.target)) return;
      setMenuOpen(false);
    }

    function onKey(e) {
      if (e.key === "Escape") setMenuOpen(false);
    }

    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const displayName = useMemo(() => {
    if (!user) return "";
    const name = `${user.first_name || ""} ${user.last_name || ""}`.trim();
    return name || user.username || "";
  }, [user]);

  async function handleLogout(e) {
    e.preventDefault();
    setMenuOpen(false);
    await logout();
    setUser(null);
    navigate("/", { replace: true });
  }

  function goProfile(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/profile");
  }

  function goSettings(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/settings");
  }

  function goSupport(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/support");
  }

  function goUploads(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/my-uploads");
  }

  function goBilling(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/billing");
  }

  function goSecurity(e) {
    e.preventDefault();
    setMenuOpen(false);
    navigate("/security");
  }

  return (
    <header className="mainHeader">
      <div className="headerContent">
        <div className="headerLeft">
          <Link to="/" className="logo" style={{ textDecoration: "none" }}>
            Synopsis
          </Link>
        </div>

        <div className="headerRight">
          <nav className="headerNav" aria-label="Primary">
            <Link to="/" className="headerLink">
              Home
            </Link>
            <Link to="/support" className="headerLink">
              Customer Support
            </Link>
            <Link to="/about" className="headerLink">
              About <span className="dropdownArrow">▼</span>
            </Link>
          </nav>

          <div className="headerActions" aria-label="Account">
            {displayName ? (
              <>
                <div className="userMenu" ref={menuRef}>
                  <button
                    type="button"
                    className="userChip"
                    onClick={() => setMenuOpen((v) => !v)}
                    aria-haspopup="menu"
                    aria-expanded={menuOpen ? "true" : "false"}
                    title={displayName}
                  >
                    <span className="userAvatar" aria-hidden="true">
                      {displayName.slice(0, 1).toUpperCase()}
                    </span>
                    <span className="userName">{displayName}</span>
                    <span className="userCaret" aria-hidden="true">
                      ▾
                    </span>
                  </button>

                  {menuOpen ? (
                    <div className="userMenuPanel" role="menu">
                      <div className="userMenuHeader">
                        <div className="userMenuTitle">Signed in as</div>
                        <div className="userMenuIdentity">{displayName}</div>
                      </div>

                      <div className="userMenuDivider" role="separator" />

                      <div className="userMenuSection">Account</div>

                      <button
                        type="button"
                        className="userMenuItem"
                        onClick={goProfile}
                        role="menuitem"
                      >
                        <span className="menuIcon" aria-hidden="true">
                          <Icon name="user" size={16} />
                        </span>
                        Profile
                      </button>

                      <button
                        type="button"
                        className="userMenuItem"
                        onClick={goSettings}
                        role="menuitem"
                      >
                        <span className="menuIcon" aria-hidden="true">
                          <Icon name="settings" size={16} />
                        </span>
                        Account settings
                      </button>

                      <button
                        type="button"
                        className="userMenuItem"
                        onClick={goUploads}
                        role="menuitem"
                      >
                        <span className="menuIcon" aria-hidden="true">
                          <Icon name="file" size={16} />
                        </span>
                        My uploads
                      </button>

                      <div className="userMenuSection">Plan</div>

                      <button
                        type="button"
                        className="userMenuItem"
                        onClick={goBilling}
                        role="menuitem"
                      >
                        <span className="menuIcon" aria-hidden="true">
                          <Icon name="card" size={16} />
                        </span>
                        Billing &amp; plan
                      </button>

                      <div className="userMenuSection">Security</div>

                      <button
                        type="button"
                        className="userMenuItem"
                        onClick={goSecurity}
                        role="menuitem"
                      >
                        <span className="menuIcon" aria-hidden="true">
                          <Icon name="lock" size={16} />
                        </span>
                        Security
                      </button>

                      <div className="userMenuDivider" role="separator" />

                      <button
                        type="button"
                        className="btnLogout"
                        onClick={handleLogout}
                        role="menuitem"
                      >
                        Log out
                      </button>
                    </div>
                  ) : null}
                </div>
              </>
            ) : (
              <Link to="/login" className="headerLink headerCta">
                Log In
              </Link>
            )}
          </div>
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
          <span className="footerBrand">Synopsis</span>

          <div className="footerContent">
            <p className="footerText">
              10,000+ users in over 50 countries summarize their documents with
              Synopsis
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
            © {new Date().getFullYear()} Synopsis. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
