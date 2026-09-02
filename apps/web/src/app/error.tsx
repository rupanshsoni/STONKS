"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body style={{ background: "#04091B", color: "#F8F8F8", fontFamily: "system-ui, sans-serif", display: "grid", "placeItems": "center", minHeight: "100dvh" }}>
        <div style={{ maxWidth: 480, padding: 24, textAlign: "center" }}>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>Something broke on the desk</h1>
          <p style={{ color: "#A8B0D0", fontSize: 14, marginTop: 8 }}>
            {error.message || "An unexpected error occurred."}
          </p>
          <button
            onClick={reset}
            style={{ marginTop: 16, padding: "8px 16px", borderRadius: 6, border: "1px solid #4DA3FF", background: "rgba(77,163,255,0.1)", color: "#4DA3FF", cursor: "pointer" }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
