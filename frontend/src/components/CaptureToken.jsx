// src/components/CaptureToken.jsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function CaptureToken() {
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const token = params.get("token");
    const next = params.get("next") || "/animais";
    if (token) {
      localStorage.setItem("access_token", token);
      // limpa fragment da URL
      const url = new URL(window.location.href);
      url.hash = "";
      window.history.replaceState({}, "", url.pathname + url.search);
      navigate(next);
    }
  }, [navigate]);

  return null;
}
