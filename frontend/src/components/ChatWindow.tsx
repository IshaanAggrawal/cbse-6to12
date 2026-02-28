"use client";

import { useRef, useEffect } from "react";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    imageSrc?: string;
    isStreaming?: boolean;
}

interface Props {
    messages: Message[];
    isLoading: boolean;
}

const SUGGESTIONS = [
    "What is photosynthesis?",
    "Explain Newton's 2nd law",
    "Non-Cooperation Movement causes",
    "Difference between mitosis & meiosis",
    "Ohm's Law formula",
];

/** Inline bold/code formatter */
function formatContent(text: string) {
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**"))
            return <strong key={i}>{part.slice(2, -2)}</strong>;
        if (part.startsWith("`") && part.endsWith("`"))
            return (
                <code key={i} style={{
                    background: "#1a2238", color: "#9f99ff",
                    padding: "1px 5px", borderRadius: 4, fontSize: "0.82em"
                }}>{part.slice(1, -1)}</code>
            );
        return part;
    });
}

function TypingDots() {
    return (
        <div style={{ display: "flex", gap: 6, alignItems: "center", padding: "14px 18px" }}>
            {[0, 1, 2].map((i) => (
                <span key={i} className="animate-bounce-dot" style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: "linear-gradient(135deg, #6c63ff, #a78bfa)",
                    display: "inline-block",
                    animationDelay: `${i * 0.18}s`,
                }} />
            ))}
        </div>
    );
}

export default function ChatWindow({ messages, isLoading }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const isEmpty = messages.length === 0 && !isLoading;

    return (
        <div style={{
            flex: 1, overflowY: "auto", padding: "24px 20px",
            display: "flex", flexDirection: "column", gap: 12,
            scrollBehavior: "smooth",
        }}>
            {isEmpty && (
                <div className="animate-fade-up" style={{
                    flex: 1, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                    gap: 24, textAlign: "center", padding: "60px 16px",
                }}>
                    {/* Hero icon */}
                    <div style={{
                        width: 80, height: 80, borderRadius: 24,
                        background: "linear-gradient(135deg, #6c63ff 0%, #a78bfa 100%)",
                        boxShadow: "0 0 40px rgba(108,99,255,0.45)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 36,
                    }}>
                        🧠
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        <h2 style={{
                            fontSize: 26, fontWeight: 800,
                            background: "linear-gradient(135deg, #9f99ff, #a78bfa)",
                            WebkitBackgroundClip: "text",
                            WebkitTextFillColor: "transparent",
                            backgroundClip: "text",
                        }}>
                            Apna doubt poochho!
                        </h2>
                        <p style={{ fontSize: 13, color: "#64748b", maxWidth: 360, lineHeight: 1.7 }}>
                            Ask any CBSE Science or Social Science doubt — by{" "}
                            <span style={{ color: "#e2e8f0" }}>typing</span>,{" "}
                            <span style={{ color: "#e2e8f0" }}>voice 🎤</span>, or a{" "}
                            <span style={{ color: "#e2e8f0" }}>photo 📷</span> of your textbook.
                        </p>
                    </div>

                    {/* Suggestion chips */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 480 }}>
                        {SUGGESTIONS.map((q) => <SuggestionChip key={q} text={q} />)}
                    </div>
                </div>
            )}

            {messages.map((msg) => (
                <div key={msg.id} className="animate-fade-up" style={{
                    display: "flex",
                    flexDirection: msg.role === "user" ? "row-reverse" : "row",
                    alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                    gap: 10, maxWidth: "80%",
                }}>
                    {/* Avatar */}
                    <div style={{
                        width: 30, height: 30, borderRadius: "50%", flexShrink: 0,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 13, alignSelf: "flex-end",
                        background: msg.role === "user"
                            ? "linear-gradient(135deg, #6c63ff, #a78bfa)"
                            : "linear-gradient(135deg, #10b981, #0ea5e9)",
                        boxShadow: msg.role === "user"
                            ? "0 0 10px rgba(108,99,255,0.4)"
                            : "0 0 10px rgba(16,185,129,0.3)",
                    }}>
                        {msg.role === "user" ? "👤" : "🤖"}
                    </div>

                    {/* Bubble */}
                    <div style={{
                        padding: "12px 16px",
                        borderRadius: 18,
                        fontSize: 14, lineHeight: 1.65,
                        wordBreak: "break-word",
                        ...(msg.role === "user"
                            ? {
                                background: "linear-gradient(135deg, #6c63ff, #a78bfa)",
                                color: "#fff",
                                borderBottomRightRadius: 4,
                                boxShadow: "0 4px 20px rgba(108,99,255,0.35)",
                            }
                            : {
                                background: "#131929",
                                border: "1px solid rgba(255,255,255,0.09)",
                                borderBottomLeftRadius: 4,
                                color: "#e2e8f0",
                                whiteSpace: "pre-wrap",
                            }),
                    }}>
                        {msg.imageSrc && (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={msg.imageSrc} alt="Question"
                                style={{
                                    maxWidth: 200, borderRadius: 12, marginBottom: 8, display: "block",
                                    border: "1px solid rgba(255,255,255,0.1)"
                                }} />
                        )}
                        {msg.role === "assistant" ? formatContent(msg.content) : msg.content}
                        {msg.isStreaming && (
                            <span className="animate-caret" style={{
                                display: "inline-block", width: 2, height: 14, marginLeft: 4,
                                borderRadius: 2, background: "#9f99ff", verticalAlign: "middle",
                            }} />
                        )}
                    </div>
                </div>
            ))}

            {/* Typing indicator */}
            {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
                <div className="animate-fade-up" style={{ display: "flex", gap: 10, alignSelf: "flex-start" }}>
                    <div style={{
                        width: 30, height: 30, borderRadius: "50%",
                        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13,
                        background: "linear-gradient(135deg, #10b981, #0ea5e9)",
                        boxShadow: "0 0 10px rgba(16,185,129,0.3)",
                    }}>🤖</div>
                    <div style={{
                        background: "#131929", border: "1px solid rgba(255,255,255,0.09)",
                        borderRadius: 18, borderBottomLeftRadius: 4,
                    }}>
                        <TypingDots />
                    </div>
                </div>
            )}

            <div ref={bottomRef} />
        </div>
    );
}

function SuggestionChip({ text }: { text: string }) {
    return (
        <button
            onClick={() => window.dispatchEvent(new CustomEvent("suggestion-chip", { detail: text }))}
            style={{
                padding: "8px 14px", borderRadius: 999, fontSize: 12, cursor: "pointer",
                background: "rgba(108,99,255,0.1)",
                border: "1px solid rgba(108,99,255,0.35)",
                color: "#a5b4fc",
                fontFamily: "inherit",
                transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(108,99,255,0.22)";
                e.currentTarget.style.borderColor = "#6c63ff";
                e.currentTarget.style.color = "#c7d2fe";
                e.currentTarget.style.boxShadow = "0 0 12px rgba(108,99,255,0.3)";
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(108,99,255,0.1)";
                e.currentTarget.style.borderColor = "rgba(108,99,255,0.35)";
                e.currentTarget.style.color = "#a5b4fc";
                e.currentTarget.style.boxShadow = "none";
            }}
        >
            {text}
        </button>
    );
}
