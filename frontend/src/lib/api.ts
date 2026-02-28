// src/lib/api.ts — API service layer for CBSE Tutor backend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface AskPayload {
    question: string;
    class_no?: number | null;
    subject?: string | null;
    session_id?: string | null;
    image_base64?: string | null;
    image_mime?: string;
    stream?: boolean;
    language?: "english" | "hindi";
}

export interface Source {
    chapter_title?: string;
    source?: string;
    score?: number;
}

export interface AskResponse {
    id: string;
    answer: string;
    from_cache: boolean;
    model_used: string;
    sources: Source[];
}

export interface Student {
    id: string;
    name?: string;
    class_no?: number;
    subject?: string;
    language?: string;
    created_at: string;
}

export interface ChatSession {
    id: string;
    student: string;
    class_no?: number;
    subject?: string;
    title?: string;
    message_count: number;
    created_at: string;
}

// ── Ask (streaming) ─────────────────────────────────────────────────────────
export async function askStream(
    payload: AskPayload,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: string) => void
) {
    try {
        const res = await fetch(`${API_BASE}/api/ask/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...payload, stream: true }),
        });

        if (!res.ok) {
            onError(`Server error ${res.status}`);
            return;
        }

        const reader = res.body?.getReader();
        if (!reader) { onError("No response stream"); return; }

        const decoder = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            onToken(decoder.decode(value, { stream: true }));
        }
        onDone();
    } catch (e: any) {
        onError(e?.message ?? "Network error");
    }
}

// ── Students ─────────────────────────────────────────────────────────────────
export async function createStudent(data: Partial<Student>): Promise<Student> {
    const res = await fetch(`${API_BASE}/api/students/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    return res.json();
}

// ── Sessions ──────────────────────────────────────────────────────────────────
export async function createSession(payload: {
    student: string;
    class_no?: number | null;
    subject?: string | null;
}): Promise<ChatSession> {
    const res = await fetch(`${API_BASE}/api/sessions/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return res.json();
}

export async function getSession(id: string): Promise<ChatSession & { messages: any[] }> {
    const res = await fetch(`${API_BASE}/api/sessions/${id}/`);
    return res.json();
}

// ── Health ─────────────────────────────────────────────────────────────────────
export async function healthCheck() {
    const res = await fetch(`${API_BASE}/api/health/`);
    return res.json();
}

// ── Image → base64 helper ─────────────────────────────────────────────────────
export function fileToBase64(file: File): Promise<{ b64: string; mime: string }> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const dataUrl = e.target?.result as string;
            const b64 = dataUrl.split(",")[1];
            resolve({ b64, mime: file.type || "image/jpeg" });
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
