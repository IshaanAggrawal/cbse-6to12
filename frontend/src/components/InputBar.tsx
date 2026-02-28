"use client";

import { useRef, useState } from "react";
import { fileToBase64 } from "@/lib/api";

interface Props {
    onSend: (payload: { question: string; imageBase64?: string; imageMime?: string }) => void;
    disabled?: boolean;
    language: "english" | "hindi";
}

function IconCamera() {
    return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
        </svg>
    );
}

function IconMic() {
    return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
    );
}

function IconSend() {
    return (
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
    );
}

function WaveBars() {
    return (
        <span style={{ display: "flex", alignItems: "center", gap: 2, height: 16 }}>
            {[0, 1, 2, 3, 4].map((i) => (
                <span key={i} style={{
                    width: 2, borderRadius: 2, height: "100%",
                    background: "#f87171",
                    animation: `waveBar 0.8s ease-in-out infinite`,
                    animationDelay: `${i * 0.12}s`,
                }} />
            ))}
        </span>
    );
}

export default function InputBar({ onSend, disabled, language }: Props) {
    const [text, setText] = useState("");
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [imageBase64, setImageBase64] = useState<string | null>(null);
    const [imageMime, setImageMime] = useState("image/jpeg");
    const [isRecording, setIsRecording] = useState(false);
    const [focused, setFocused] = useState(false);

    const fileRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);

    function autoResize() {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 120) + "px";
    }

    function handleKeyDown(e: React.KeyboardEvent) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    }

    function handleSend() {
        const q = text.trim();
        if (!q || disabled) return;
        onSend({ question: q, imageBase64: imageBase64 ?? undefined, imageMime });
        setText("");
        clearImage();
        if (textareaRef.current) textareaRef.current.style.height = "auto";
    }

    async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        const { b64, mime } = await fileToBase64(file);
        setImageBase64(b64); setImageMime(mime);
        setImagePreview(URL.createObjectURL(file));
    }

    function clearImage() {
        setImageBase64(null); setImagePreview(null); setImageMime("image/jpeg");
        if (fileRef.current) fileRef.current.value = "";
    }

    function toggleVoice() {
        if (isRecording) { recognitionRef.current?.stop(); return; }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SR) { alert("Voice input requires Chrome browser."); return; }
        const rec = new SR();
        recognitionRef.current = rec;
        rec.lang = language === "hindi" ? "hi-IN" : "en-IN";
        rec.interimResults = true;
        rec.onstart = () => setIsRecording(true);
        rec.onend = () => {
            setIsRecording(false);
            if (textareaRef.current?.value.trim()) setTimeout(handleSend, 300);
        };
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        rec.onresult = (event: any) => {
            let t = "";
            for (let i = event.resultIndex; i < event.results.length; i++) t += event.results[i][0].transcript;
            setText(t); autoResize();
        };
        rec.onerror = () => setIsRecording(false);
        rec.start();
    }

    const canSend = !!text.trim() && !disabled;

    return (
        <div style={{
            padding: "8px 16px 16px",
            flexShrink: 0,
            background: "#0d1120",
            borderTop: "1px solid rgba(255,255,255,0.07)",
        }}>
            {/* Image preview */}
            {imagePreview && (
                <div className="animate-fade-in" style={{ display: "flex", alignItems: "center", gap: 8, paddingBottom: 8 }}>
                    <div style={{ position: "relative" }}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={imagePreview} alt="Selected"
                            style={{
                                width: 56, height: 56, objectFit: "cover", borderRadius: 10,
                                border: "1px solid rgba(255,255,255,0.1)"
                            }} />
                        <button onClick={clearImage} style={{
                            position: "absolute", top: -6, right: -6,
                            width: 18, height: 18, borderRadius: "50%",
                            background: "#f87171", border: "none", color: "#fff",
                            fontSize: 9, cursor: "pointer", display: "flex",
                            alignItems: "center", justifyContent: "center",
                        }}>✕</button>
                    </div>
                </div>
            )}

            {/* Input row */}
            <div style={{
                display: "flex", gap: 8, alignItems: "flex-end",
                padding: "10px 14px",
                borderRadius: 14,
                background: "#131929",
                border: `1px solid ${focused ? "#6c63ff" : "rgba(255,255,255,0.1)"}`,
                boxShadow: focused ? "0 0 0 3px rgba(108,99,255,0.15)" : "none",
                transition: "border-color 0.2s, box-shadow 0.2s",
            }}>
                <textarea
                    ref={textareaRef}
                    value={text}
                    onChange={(e) => { setText(e.target.value); autoResize(); }}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    placeholder={language === "hindi" ? "अपना सवाल यहाँ लिखें…" : "Type your doubt here… (Shift+Enter for new line)"}
                    rows={1}
                    style={{
                        flex: 1, background: "transparent", border: "none",
                        outline: "none", color: "#e2e8f0", fontSize: 14,
                        lineHeight: 1.6, resize: "none", minHeight: 24, maxHeight: 120,
                        fontFamily: "inherit",
                    }}
                />

                {/* Camera */}
                <ActionBtn onClick={() => fileRef.current?.click()} title="Upload photo" active={!!imagePreview}>
                    <IconCamera />
                </ActionBtn>

                {/* Mic */}
                <div style={{ position: "relative" }}>
                    <ActionBtn onClick={toggleVoice} title="Voice input" danger={isRecording}>
                        {isRecording ? <WaveBars /> : <IconMic />}
                    </ActionBtn>
                    {isRecording && (
                        <span className="animate-pulse-ring" style={{
                            position: "absolute", inset: 0, borderRadius: 8,
                            border: "2px solid #f87171", opacity: 0.5,
                        }} />
                    )}
                </div>

                {/* Send */}
                <button onClick={handleSend} disabled={!canSend} style={{
                    width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    border: "none", cursor: canSend ? "pointer" : "not-allowed",
                    color: "#fff",
                    background: canSend
                        ? "linear-gradient(135deg, #6c63ff, #a78bfa)"
                        : "#1a2238",
                    boxShadow: canSend ? "0 0 14px rgba(108,99,255,0.45)" : "none",
                    opacity: canSend ? 1 : 0.4,
                    transition: "all 0.2s",
                    transform: canSend ? "scale(1)" : "scale(0.95)",
                }}>
                    <IconSend />
                </button>
            </div>

            {isRecording && (
                <p className="animate-fade-in" style={{
                    textAlign: "center", fontSize: 11, marginTop: 6,
                    color: "#f87171", fontWeight: 500,
                }}>
                    🔴 Listening… tap mic to stop
                </p>
            )}

            <input ref={fileRef} type="file" accept="image/*"
                style={{ display: "none" }} onChange={handleFileChange} />
        </div>
    );
}

function ActionBtn({ onClick, title, children, active, danger }: {
    onClick: () => void; title: string; children: React.ReactNode;
    active?: boolean; danger?: boolean;
}) {
    const [hovered, setHovered] = useState(false);
    return (
        <button onClick={onClick} title={title} style={{
            width: 36, height: 36, borderRadius: 8, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            border: "none", cursor: "pointer",
            background: hovered || active ? "rgba(108,99,255,0.15)" : "transparent",
            color: danger ? "#f87171" : active ? "#9f99ff" : hovered ? "#e2e8f0" : "#64748b",
            transition: "all 0.15s",
        }}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {children}
        </button>
    );
}
