import { useEffect, useMemo, useState } from "react";
import { SiteFooter, SiteHeader } from "../components/SiteChrome";
import { API_BASE } from "../lib/auth";
import { fetchMe, getStoredUser } from "../lib/userSession";

function loadRazorpayCheckout() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const existing = document.querySelector(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]',
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(true));
      existing.addEventListener("error", () => resolve(false));
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function Billing() {
  const PLANS = [
    { id: "starter", name: "Starter", credits: 100, price: 10 },
    { id: "plus", name: "Plus", credits: 250, price: 20 },
    { id: "pro", name: "Pro", credits: 500, price: 35 },
  ];

  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const prefill = useMemo(() => {
    if (!user) return {};
    const name = `${user.first_name || ""} ${user.last_name || ""}`.trim();
    return {
      name: name || undefined,
      email: user.email || undefined,
      contact: user.username || undefined,
    };
  }, [user]);

  useEffect(() => {
    async function load() {
      const stored = getStoredUser();
      if (stored) {
        setUser(stored);
        setLoadingUser(false);
        return;
      }
      const me = await fetchMe();
      setUser(me);
      setLoadingUser(false);
    }
    load();
  }, []);

  async function startPayment(planId) {
    setError("");
    setSuccess("");
    setPaying(true);

    try {
      const orderRes = await fetch(
        `${API_BASE}/api/payments/razorpay/create-order/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ plan_id: planId }),
        },
      );

      const orderData = await orderRes.json().catch(() => ({}));
      if (!orderRes.ok || !orderData?.ok) {
        setError(orderData?.error || "Failed to start payment.");
        setPaying(false);
        return;
      }

      const ok = await loadRazorpayCheckout();
      if (!ok) {
        setError("Failed to load Razorpay Checkout.");
        setPaying(false);
        return;
      }

      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "Document Summarization System",
        description: `Credits top-up (Test)`,
        order_id: orderData.order_id,
        prefill,
        theme: {
          color:
            getComputedStyle(document.documentElement)
              .getPropertyValue("--primary-orange")
              .trim() || "#ff7a59",
        },
        handler: async (response) => {
          try {
            const verifyRes = await fetch(
              `${API_BASE}/api/payments/razorpay/verify/`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(response),
              },
            );
            const verifyData = await verifyRes.json().catch(() => ({}));
            if (!verifyRes.ok || !verifyData?.ok) {
              setError(verifyData?.error || "Payment verification failed.");
              return;
            }
            if (typeof verifyData?.credits === "number") {
              setUser((prev) =>
                prev ? { ...prev, credits: verifyData.credits } : prev,
              );
            }
            setSuccess("Payment successful! Credits added to your account.");
            setTimeout(() => setSuccess(""), 4000);
          } catch (e) {
            setError(e?.message || "Payment verification failed.");
          } finally {
            setPaying(false);
          }
        },
        modal: {
          ondismiss: () => {
            setPaying(false);
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.on("payment.failed", (resp) => {
        const desc = resp?.error?.description || resp?.error?.reason;
        setError(desc || "Payment failed.");
        setPaying(false);
      });
      rzp.open();
    } catch (e) {
      setError(e?.message || "Failed to start payment.");
      setPaying(false);
    }
  }

  return (
    <div className="page">
      <SiteHeader />

      <main className="legalPage">
        <div className="legalCard">
          <div className="legalHeader">
            <div className="legalKicker">
              <div className="legalIcon" aria-hidden="true">
                ₹
              </div>
              <div>
                <h1 className="legalTitle">Billing &amp; plan</h1>
                <p className="legalLead">
                  Top up credits securely via Razorpay.
                </p>
              </div>
              <div className="legalMeta">Test mode</div>
            </div>
          </div>

          <div className="legalBody">
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

            <div className="billingSummary">
              <div className="grid2">
                <div className="infoCard">
                  <div className="infoTitle">How billing works</div>
                  <div className="infoMeta">
                    One-time top-ups • No subscription
                  </div>
                  <div className="billingValue">Pay as you go</div>
                </div>
                <div className="infoCard">
                  <div className="infoTitle">Available credits</div>
                  <div className="infoMeta">Used for summarization</div>
                  <div className="billingValue">{user?.credits ?? "—"}</div>
                </div>
              </div>
            </div>

            <div className="contentDivider" role="presentation" />

            <div className="billingPlansHeader">
              <div>
                <div className="infoTitle" style={{ marginBottom: 2 }}>
                  Credit packs
                </div>
                <div className="infoMeta">
                  Choose a pack to top up instantly.
                </div>
              </div>
              {loadingUser ? (
                <div className="profileMuted">Loading account…</div>
              ) : null}
            </div>

            <div className="billingPlans" role="list">
              {PLANS.map((p) => (
                <div className="billingPlanCard" key={p.id} role="listitem">
                  <div className="billingPlanTop">
                    <div>
                      <div className="billingPlanName">{p.name}</div>
                      <div className="billingPlanMeta">{p.credits} credits</div>
                    </div>
                    <div className="billingPlanPrice">₹{p.price}</div>
                  </div>

                  <button
                    className="btnPrimary billingPlanBtn"
                    type="button"
                    onClick={() => startPayment(p.id)}
                    disabled={paying || loadingUser}
                  >
                    {paying ? "Opening payment…" : "Buy now"}
                  </button>
                </div>
              ))}
            </div>

            <div className="contentDivider" role="presentation" />

            <div className="billingPlansHeader">
              <div>
                <div className="infoTitle" style={{ marginBottom: 2 }}>
                  Usage &amp; pricing
                </div>
                <div className="infoMeta">
                  Credits are deducted per summary based on extracted text
                  bytes.
                </div>
              </div>
            </div>

            <div className="grid2">
              <div className="infoCard">
                <div className="infoTitle">Bytes → credits</div>
                <div className="infoMeta">Per summarization request</div>

                <div className="pricingTable" role="list">
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">0–1,024 bytes</div>
                    <div className="pricingVal">3 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">1,025–5,120 bytes</div>
                    <div className="pricingVal">5 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">5,121–10,240 bytes</div>
                    <div className="pricingVal">8 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">10,241–25,600 bytes</div>
                    <div className="pricingVal">12 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">25,601–51,200 bytes</div>
                    <div className="pricingVal">18 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">51,201–102,400 bytes</div>
                    <div className="pricingVal">25 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">102,401–256,000 bytes</div>
                    <div className="pricingVal">40 credits</div>
                  </div>
                  <div className="pricingRow" role="listitem">
                    <div className="pricingKey">256,001+ bytes</div>
                    <div className="pricingVal">60 credits</div>
                  </div>
                </div>
              </div>

              <div className="infoCard">
                <div className="infoTitle">First-time credits</div>
                <div className="infoMeta">Granted on your first login</div>
                <div className="billingValue">100</div>
                <div className="profileMuted">
                  Top up anytime from the packs above.
                </div>
              </div>
            </div>

            <div className="contentNote" style={{ marginTop: 14 }}>
              <div
                className="infoTitle"
                style={{ marginBottom: 6, fontSize: 16 }}
              >
                Note
              </div>
              <div className="infoMeta" style={{ marginBottom: 0 }}>
                Bytes are calculated from extracted text (UTF-8), not the
                original file size.
              </div>
            </div>
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
