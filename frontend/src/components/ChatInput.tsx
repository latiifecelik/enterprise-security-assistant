import React, { useState, useRef } from "react";
import "./ChatInput.css";

interface ChatInputProps {
  onSend: (question: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const EXAMPLE_PROMPTS = [
  "How should I investigate repeated failed SSH logins?",
  "What logs should I review after a suspicious successful login?",
  "Explain password spraying using my security documents.",
  "What evidence should be preserved during incident triage?",
  "Which document discusses authentication incidents?",
];

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = "Ask about an incident or your security documents…",
}) => {
  const [value, setValue] = useState("");
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  };

  const handleExampleClick = (prompt: string) => {
    setValue(prompt);
    setShowExamples(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="chat-input-area">
      {/* Example prompts dropdown */}
      {showExamples && (
        <div className="examples-panel">
          <div className="examples-title">Example questions</div>
          {EXAMPLE_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              className="example-prompt"
              onClick={() => handleExampleClick(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-box">
        <button
          className="examples-toggle"
          onClick={() => setShowExamples(!showExamples)}
          title="Show example questions"
          disabled={disabled}
        >
          💡
        </button>
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          title="Send (Enter)"
        >
          {disabled ? "⏳" : "➤"}
        </button>
      </div>
      <div className="chat-input-hint">
        Enter to send · Shift+Enter for new line · 💡 for example questions
      </div>
    </div>
  );
};
