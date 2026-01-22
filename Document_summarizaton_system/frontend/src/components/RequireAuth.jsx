import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { fetchMe, getStoredUser, storeUser } from "../lib/userSession";

export default function RequireAuth({ children }) {
  const location = useLocation();
  const [status, setStatus] = useState("checking"); // checking | authed | guest

  useEffect(() => {
    let mounted = true;

    async function check() {
      // Fast path: local user present.
      const stored = getStoredUser();
      if (stored) {
        if (!mounted) return;
        setStatus("authed");
        return;
      }

      // Slow path: backend session.
      const me = await fetchMe().catch(() => null);
      if (!mounted) return;

      if (me) {
        storeUser(me);
        setStatus("authed");
      } else {
        setStatus("guest");
      }
    }

    check();
    return () => {
      mounted = false;
    };
  }, []);

  if (status === "checking") {
    // Keep it minimal; avoids flashing protected pages.
    return null;
  }

  if (status === "guest") {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  return children;
}
