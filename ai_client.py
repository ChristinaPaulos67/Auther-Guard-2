"""Multi-AI client: Claude, Gemini, DeepSeek, GPT, Grok + local fallback."""
import json
import os
import urllib.request
import urllib.error
from typing import Dict

AI_MODELS = {
    "Claude": {"color": "#c47e4a", "icon": "🤖", "provider": "Anthropic"},
    "Gemini": {"color": "#4285f4", "icon": "✨", "provider": "Google"},
    "DeepSeek": {"color": "#00b4d8", "icon": "🔍", "provider": "DeepSeek AI"},
    "GPT": {"color": "#10a37f", "icon": "💬", "provider": "OpenAI"},
    "Grok": {"color": "#8e44ad", "icon": "🌌", "provider": "xAI"},
    "Local": {"color": "#94a3b8", "icon": "📚", "provider": "Offline knowledge"},
}

SPACE_WEATHER_SYSTEM = (
    "You are Auther Guard AI, an expert space-weather and terrestrial-weather assistant. "
    "Explain clearly for students and researchers. Use plain language when asked; "
    "include quantitative context when helpful. Never invent live NOAA values — "
    "reason from parameters the user provides."
)

LOCAL_KB = {
    "geomagnetic storm": (
        "A geomagnetic storm is a temporary disturbance of Earth's magnetosphere caused by "
        "solar wind shocks and southward interplanetary magnetic field (IMF Bz). "
        "Intensity is often summarized by the Kp index (0–9) and Dst (more negative = stronger). "
        "Effects include auroras, GPS errors, power-grid GICs, and satellite anomalies."
    ),
    "solar wind": (
        "The solar wind is a continuous stream of charged particles from the Sun, typically "
        "300–800 km/s. Fast streams and coronal mass ejections can compress the magnetosphere "
        "and drive storms when combined with southward Bz."
    ),
    "kp index": (
        "Kp is a planetary geomagnetic activity index on a 0–9 scale, reported every 3 hours. "
        "Kp ≥ 5 indicates a geomagnetic storm (G1+). Higher Kp means stronger auroras and "
        "greater operational impacts."
    ),
    "cme": (
        "A coronal mass ejection (CME) is a large expulsion of plasma and magnetic field from "
        "the Sun. Earth-directed CMEs can cause major geomagnetic storms 1–4 days after launch."
    ),
    "flare": (
        "Solar flares are classified A, B, C, M, X by soft X-ray peak flux. X-class flares can "
        "cause HF radio blackouts and contribute to radiation hazards for aviation and astronauts."
    ),
}


class MultiAIClient:
    def __init__(self, keys: Dict[str, str] | None = None):
        self.keys = {
            "Claude": os.environ.get("ANTHROPIC_API_KEY", ""),
            "Gemini": os.environ.get("GOOGLE_API_KEY", ""),
            "DeepSeek": os.environ.get("DEEPSEEK_API_KEY", ""),
            "GPT": os.environ.get("OPENAI_API_KEY", ""),
            "Grok": os.environ.get("XAI_API_KEY", ""),
        }
        if keys:
            self.keys.update({k: v for k, v in keys.items() if v})

    def set_key(self, model: str, key: str):
        if model in self.keys:
            self.keys[model] = key

    def _post_json(self, url: str, headers: dict, payload: dict, timeout=30) -> dict:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def ask_claude(self, system: str, user: str) -> str:
        key = self.keys.get("Claude") or ""
        if not key:
            return self._local(user, "[Claude] No API key — local knowledge mode.\n\n")
        try:
            data = self._post_json(
                "https://api.anthropic.com/v1/messages",
                {
                    "Content-Type": "application/json",
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                },
                {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            return data["content"][0]["text"]
        except Exception as e:
            return f"[Claude Error] {e}"

    def ask_gemini(self, system: str, user: str) -> str:
        key = self.keys.get("Gemini") or ""
        if not key:
            return self._local(user, "[Gemini] No API key — local knowledge mode.\n\n")
        try:
            data = self._post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
                {"Content-Type": "application/json"},
                {"contents": [{"parts": [{"text": f"{system}\n\nUser: {user}"}]}]},
            )
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"[Gemini Error] {e}"

    def ask_deepseek(self, system: str, user: str) -> str:
        key = self.keys.get("DeepSeek") or ""
        if not key:
            return self._local(user, "[DeepSeek] No API key — local knowledge mode.\n\n")
        try:
            data = self._post_json(
                "https://api.deepseek.com/chat/completions",
                {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 1024,
                },
            )
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[DeepSeek Error] {e}"

    def ask_gpt(self, system: str, user: str) -> str:
        key = self.keys.get("GPT") or ""
        if not key:
            return self._local(user, "[GPT] No API key — local knowledge mode.\n\n")
        try:
            data = self._post_json(
                "https://api.openai.com/v1/chat/completions",
                {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 1024,
                },
            )
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[GPT Error] {e}"

    def ask_grok(self, system: str, user: str) -> str:
        key = self.keys.get("Grok") or ""
        if not key:
            return self._local(user, "[Grok] No API key — local knowledge mode.\n\n")
        try:
            data = self._post_json(
                "https://api.x.ai/v1/chat/completions",
                {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                {
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 1024,
                },
            )
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Grok Error] {e}"

    def _local(self, user: str, prefix: str = "") -> str:
        q = user.lower()
        for key, ans in LOCAL_KB.items():
            if key in q:
                return prefix + ans
        return (
            prefix
            + "Local knowledge mode (no external API key). "
            "Ask about geomagnetic storms, solar wind, Kp index, CMEs, or solar flares. "
            "Set an API key in Settings for full model answers."
        )

    def ask(self, model: str, user: str, system: str = None) -> str:
        system = system or SPACE_WEATHER_SYSTEM
        if model == "Local":
            return self._local(user)
        dispatch = {
            "Claude": self.ask_claude,
            "Gemini": self.ask_gemini,
            "DeepSeek": self.ask_deepseek,
            "GPT": self.ask_gpt,
            "Grok": self.ask_grok,
        }
        fn = dispatch.get(model)
        return fn(system, user) if fn else self._local(user)
