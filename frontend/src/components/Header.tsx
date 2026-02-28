"use client";

import { useEffect, useState } from "react";

interface Props {
    classNo: number | null;
    subject: string | null;
    language: "english" | "hindi";
    onClassChange: (v: number | null) => void;
    onSubjectChange: (v: string | null) => void;
    onLanguageChange: (v: "english" | "hindi") => void;
}

export default function Header({ classNo, subject, language, onClassChange, onSubjectChange, onLanguageChange }: Props) {
    const [online, setOnline] = useState<boolean | null>(null);

    useEffect(() => {
        const check = async () => {
            try {
                const r = await fetch(
                    (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/health/",
                    { signal: AbortSignal.timeout(3000) }
                );
                setOnline(r.ok);
            } catch { setOnline(false); }
        };
        check();
        const id = setInterval(check, 30_000);
        return () => clearInterval(id);
    }, []);

    const selectStyle: React.CSSProperties = {
        background: "#1a2238",
        border: "1px solid rgba(255,255,255,0.1)",
        color: "#e2e8f0",
        borderRadius: 8,
        fontSize: 12,
        fontWeight: 500,
        padding: "6px 10px",
        outline: "none",
        cursor: "pointer",
        fontFamily: "inherit",
        transition: "border-color 0.2s",
    };

    return (
        <header style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "10px 16px", flexShrink: 0, zIndex: 10,
            background: "rgba(13,17,32,0.85)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
        }}>
            {/* Logo */}
            <div style={{
                width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                background: "linear-gradient(135deg, #6c63ff 0%, #a78bfa 100%)",
                boxShadow: "0 0 16px rgba(108,99,255,0.5)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18,
            }}>📚</div>

            {/* Brand */}
            <div style={{ flexShrink: 0, lineHeight: 1.2 }}>
                <h1 style={{
                    fontSize: 13, fontWeight: 800,
                    background: "linear-gradient(135deg, #9f99ff, #c4b5fd)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                    letterSpacing: -0.3,
                }}>CBSE AI Tutor</h1>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                    <span style={{ fontSize: 10, color: "#64748b" }}>Classes 6–12</span>
                    <span style={{
                        width: 6, height: 6, borderRadius: "50%", display: "inline-block",
                        background: online === null ? "#fbbf24" : online ? "#34d399" : "#f87171",
                        boxShadow: online ? "0 0 5px #34d399" : undefined,
                    }} />
                    <span style={{ fontSize: 9, color: "#64748b" }}>
                        {online === null ? "checking" : online ? "live" : "offline"}
                    </span>
                </div>
            </div>

            {/* Selectors */}
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                {/* Class */}
                <select style={selectStyle} value={classNo ?? ""}
                    onChange={(e) => onClassChange(e.target.value ? parseInt(e.target.value) : null)}
                    onFocus={(e) => (e.currentTarget.style.borderColor = "#6c63ff")}
                    onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)")}>
                    <option value="">All Classes</option>
                    {[6, 7, 8, 9, 10, 11, 12].map((c) => <option key={c} value={c}>Class {c}</option>)}
                </select>

                {/* Subject */}
                <select style={selectStyle} value={subject ?? ""}
                    onChange={(e) => onSubjectChange(e.target.value || null)}
                    onFocus={(e) => (e.currentTarget.style.borderColor = "#6c63ff")}
                    onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)")}>
                    <option value="">All Subjects</option>
                    <option value="science">Science</option>
                    <option value="social_science">Social Science</option>
                </select>

                {/* Language toggle */}
                <div style={{ display: "flex", borderRadius: 8, overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)" }}>
                    {(["english", "hindi"] as const).map((lang) => (
                        <button key={lang} onClick={() => onLanguageChange(lang)}
                            style={{
                                padding: "6px 12px", fontSize: 11, fontWeight: 600,
                                cursor: "pointer", fontFamily: "inherit",
                                border: "none", outline: "none", transition: "all 0.2s",
                                background: language === lang
                                    ? "linear-gradient(135deg, #6c63ff, #a78bfa)"
                                    : "#1a2238",
                                color: language === lang ? "#fff" : "#64748b",
                                boxShadow: language === lang ? "0 0 10px rgba(108,99,255,0.4)" : undefined,
                            }}>
                            {lang === "english" ? "EN" : "हिं"}
                        </button>
                    ))}
                </div>
            </div>
        </header>
    );
}
