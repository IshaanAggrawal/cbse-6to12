"use client";

import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import Header from "@/components/Header";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import { askStream } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  imageSrc?: string;
  isStreaming?: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [classNo, setClassNo] = useState<number | null>(null);
  const [subject, setSubject] = useState<string | null>(null);
  const [language, setLanguage] = useState<"english" | "hindi">("english");

  // Handle suggestion chip clicks from ChatWindow
  useEffect(() => {
    const handler = (e: Event) => {
      const q = (e as CustomEvent<string>).detail;
      handleSend({ question: q });
    };
    window.addEventListener("suggestion-chip", handler);
    return () => window.removeEventListener("suggestion-chip", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [classNo, subject, language, isLoading]);

  const handleSend = useCallback(
    async ({
      question,
      imageBase64,
      imageMime,
    }: {
      question: string;
      imageBase64?: string;
      imageMime?: string;
    }) => {
      if (isLoading) return;

      // Add user message
      const userMsg: Message = {
        id: uuidv4(),
        role: "user",
        content: question,
        imageSrc: imageBase64
          ? `data:${imageMime ?? "image/jpeg"};base64,${imageBase64}`
          : undefined,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Placeholder streaming assistant message
      const assistantId = uuidv4();
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", isStreaming: true },
      ]);

      let fullText = "";

      await askStream(
        {
          question,
          class_no: classNo,
          subject,
          language,
          image_base64: imageBase64 ?? null,
          image_mime: imageMime ?? "image/jpeg",
          stream: true,
        },
        (token) => {
          fullText += token;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullText, isStreaming: true }
                : m
            )
          );
        },
        () => {
          // Done
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          );
          setIsLoading(false);
          // TTS for short answers
          if (fullText.length < 600 && window.speechSynthesis) {
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(fullText.slice(0, 500));
            utter.lang = language === "hindi" ? "hi-IN" : "en-IN";
            utter.rate = 0.9;
            window.speechSynthesis.speak(utter);
          }
        },
        (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                  ...m,
                  content: `⚠️ Error: ${err}. Make sure the backend is running at http://localhost:8000`,
                  isStreaming: false,
                }
                : m
            )
          );
          setIsLoading(false);
        }
      );
    },
    [classNo, subject, language, isLoading]
  );

  return (
    <main
      className="flex flex-col h-dvh"
      style={{ background: "var(--bg)" }}
    >
      <Header
        classNo={classNo}
        subject={subject}
        language={language}
        onClassChange={setClassNo}
        onSubjectChange={setSubject}
        onLanguageChange={setLanguage}
      />

      <ChatWindow messages={messages} isLoading={isLoading} />

      <InputBar
        onSend={handleSend}
        disabled={isLoading}
        language={language}
      />
    </main>
  );
}
