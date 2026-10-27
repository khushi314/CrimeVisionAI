import React, {useEffect, useState} from 'react';
import {Send, MessageSquare, Loader2} from 'lucide-react';
import {askForensicChat} from '../services/api';
import {ModalityTab} from '../types/forensic';

interface ForensicChatPanelProps {
  mode: ModalityTab;
  sessionId: string;
  suggestions: string[];
}

interface ChatMessage {
  role: 'investigator' | 'system';
  content: string;
}

export const ForensicChatPanel: React.FC<ForensicChatPanelProps> = ({
  mode,
  sessionId,
  suggestions,
}) => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMessages([]);
    setQuestion('');
  }, [sessionId]);

  const submitQuery = async (qText: string) => {
    const trimmed = qText.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [...prev, {role: 'investigator', content: trimmed}]);
    setQuestion('');
    setLoading(true);
    try {
      const answer = await askForensicChat(mode, sessionId, trimmed);
      setMessages((prev) => [...prev, {role: 'system', content: answer}]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {role: 'system', content: `Query error: ${err?.message || 'Unable to query session.'}`},
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-lg border border-slate-800 bg-[#111827] p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-100 capitalize">
            Grounded Evidence Q&amp;A · {mode} Session
          </h3>
        </div>
        <span className="font-mono text-xs text-slate-400 tabular-nums">
          Context-locked · Zero-hallucination policy
        </span>
      </div>

      {/* Quick investigative prompts */}
      <div className="mt-3 flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => submitQuery(s)}
            disabled={loading}
            className="rounded border border-slate-700/80 bg-slate-900/70 px-2.5 py-1 text-left text-xs text-slate-300 transition hover:border-sky-500/50 hover:text-white disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      {messages.length > 0 && (
        <div className="mt-4 space-y-3">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`rounded border px-3.5 py-2.5 text-sm leading-relaxed ${
                msg.role === 'investigator'
                  ? 'border-slate-800 bg-slate-900/50 text-slate-200'
                  : 'border-sky-500/25 bg-sky-950/20 text-slate-100'
              }`}
            >
              <div className="mb-1 font-mono text-[11px] uppercase tracking-wider text-slate-400">
                {msg.role === 'investigator' ? 'Investigator Query' : 'Evidence-Grounded Response'}
              </div>
              <p className="whitespace-pre-line">{msg.content}</p>
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submitQuery(question);
        }}
        className="mt-4 flex gap-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            mode === 'video' || mode === 'audio'
              ? 'Ask about timestamps (e.g., "What happened at 00:05?") or cataloged objects...'
              : 'Ask strictly about objects, location, or hypotheses in this session...'
          }
          className="flex-1 rounded border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="inline-flex items-center gap-1.5 rounded bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Query
        </button>
      </form>
    </section>
  );
};
