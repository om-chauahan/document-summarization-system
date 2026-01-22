// Lightweight inline SVG icon set (no external deps)

export function Icon({ name, size = 16, className = "", ...props }) {
  const shared = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    className,
    ...props,
  };

  switch (name) {
    case "user":
      return (
        <svg {...shared}>
          <path
            d="M12 12c2.761 0 5-2.239 5-5s-2.239-5-5-5-5 2.239-5 5 2.239 5 5 5Z"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M4 21c0-3.866 3.582-7 8-7s8 3.134 8 7"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );

    case "settings":
      return (
        <svg {...shared}>
          <path
            d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="M19.4 15a7.97 7.97 0 0 0 .1-1 7.97 7.97 0 0 0-.1-1l2-1.6-2-3.4-2.4 1a7.85 7.85 0 0 0-1.7-1l-.3-2.6H9l-.3 2.6c-.6.2-1.2.5-1.7 1l-2.4-1-2 3.4 2 1.6a7.97 7.97 0 0 0-.1 1c0 .3 0 .7.1 1l-2 1.6 2 3.4 2.4-1c.5.4 1.1.8 1.7 1l.3 2.6h6l.3-2.6c.6-.2 1.2-.5 1.7-1l2.4 1 2-3.4-2-1.6Z"
            stroke="currentColor"
            strokeWidth="1.3"
            strokeLinejoin="round"
          />
        </svg>
      );

    case "file":
      return (
        <svg {...shared}>
          <path
            d="M14 2H7a3 3 0 0 0-3 3v14a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V8l-6-6Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M14 2v6h6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
      );

    case "card":
      return (
        <svg {...shared}>
          <path
            d="M3.5 8.5h17"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M5 6h14a2.5 2.5 0 0 1 2.5 2.5v9A2.5 2.5 0 0 1 19 20H5A2.5 2.5 0 0 1 2.5 17.5v-9A2.5 2.5 0 0 1 5 6Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M7 16h4"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );

    case "lock":
      return (
        <svg {...shared}>
          <path
            d="M7.5 10V8.5A4.5 4.5 0 0 1 12 4a4.5 4.5 0 0 1 4.5 4.5V10"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M7 10h10a2.5 2.5 0 0 1 2.5 2.5v5A2.5 2.5 0 0 1 17 20H7A2.5 2.5 0 0 1 4.5 17.5v-5A2.5 2.5 0 0 1 7 10Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M12 14v3"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );

    default:
      return null;
  }
}
