import React, { useEffect, useRef, useState } from 'react';
import styles from './ChatArea.module.css';
import { User, Bot, Volume2, Square, Database, Copy, Check, Globe, RefreshCw, Edit2, Download, FileText, AlertTriangle } from 'lucide-react';
import MarkdownIt from 'markdown-it';
import { useToast } from './Toast';

const md = new MarkdownIt();

// ---------------------------------------------------------------------------
// Robust language detector — no external library needed.
// Two-tier approach:
//   1. Strong German character check (umlauts, ß)
//   2. Score-based comparison using exclusive/common function words in both
//      languages, with a high relative threshold (20%) to prevent false positives.
// ---------------------------------------------------------------------------

const GERMAN_WORDS = [
  'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr',
  'mein', 'dein', 'sein', 'unser',
  'der', 'die', 'das', 'den', 'dem', 'des',
  'ein', 'eine', 'einen', 'einem', 'einer', 'eines',
  'ist', 'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'wurden',
  'haben', 'hat', 'hatte', 'kann', 'können', 'muss', 'müssen', 'soll', 'sollen',
  'und', 'nicht', 'oder', 'aber', 'auch', 'wenn', 'dann', 'dass', 'weil',
  'mit', 'von', 'zu', 'auf', 'bei', 'nach', 'seit', 'für',
  'hier', 'dort', 'bitte', 'danke', 'dank', 'vielen', 'ja', 'nein', 'doch', 'hallo',
  'heute', 'immer', 'jetzt', 'schon', 'sehr', 'wie', 'was', 'wer', 'wo', 'warum'
];

const ENGLISH_WORDS = [
  'the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', 'you', 'that',
  'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i',
  'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word',
  'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can',
  'said', 'there', 'use', 'an', 'each', 'which', 'she', 'do', 'how',
  'their', 'if', 'would', 'about', 'who', 'get', 'go', 'me', 'my', 'them',
  'your', 'youre', 'theyre', 'please', 'thanks'
];

const GERMAN_UMLAUT_RE = /[äöüÄÖÜß]/;

/**
 * Returns the Piper voice key best suited for the given text.
 * Defaults to English unless strong German signals are found.
 */
function detectVoice(text) {
  // Tier 1: umlauts / ß are an unambiguous German signal
  if (GERMAN_UMLAUT_RE.test(text)) return 'de_DE-thorsten-medium';

  // Tier 2: score-based token check
  const tokens = text.toLowerCase().replace(/[^a-z\s]/g, '').split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return 'en_US-lessac-medium';

  let deScore = 0;
  let enScore = 0;

  for (const token of tokens) {
    if (GERMAN_WORDS.includes(token)) deScore++;
    if (ENGLISH_WORDS.includes(token)) enScore++;
  }

  // If there are more or equal English words, default to English
  if (enScore >= deScore) return 'en_US-lessac-medium';
  if (deScore === 0) return 'en_US-lessac-medium';

  // Ensure German ratio threshold is high enough (20% of all tokens)
  const ratio = deScore / tokens.length;
  return ratio >= 0.20 ? 'de_DE-thorsten-medium' : 'en_US-lessac-medium';
}


/**
 * Detects if the given text is primarily written in a Right-to-Left (RTL) language
 * like Persian or Arabic by counting characters.
 */
function isRTL(text) {
  if (!text) return false;
  const rtlRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/g;
  const ltrRegex = /[a-zA-Z]/g;
  const rtlMatches = text.match(rtlRegex) || [];
  const ltrMatches = text.match(ltrRegex) || [];
  return rtlMatches.length > 0 && rtlMatches.length >= ltrMatches.length;
}

const ChatMessageRenderer = React.memo(({
  msg,
  i,
  isRTL,
  editingIndex,
  editText,
  setEditText,
  handleCancelEdit,
  handleSaveEdit,
  copiedIndex,
  handleCopy,
  handleStartEdit,
  onEdit,
  onRegenerate,
  playingIndex,
  playAudio,
  onRetryMessage
}) => {
  return (
    <div className={`${styles.messageWrapper} ${msg.role === 'user' ? styles.user : ''} ${msg.role === 'system' ? styles.system : ''}`}>
      {msg.role !== 'system' && (
        <div className={`${styles.avatar} ${msg.role === 'assistant' ? styles.assistantAvatar : ''}`}>
          {msg.role === 'user' ? <User size={20} /> : <Bot size={20} color="white" />}
        </div>
      )}
      
      <div 
        className={`${styles.content} ${msg.role !== 'system' && isRTL(msg.content) ? styles.rtl : ''}`} 
        style={msg.role === 'system' ? { fontStyle: 'italic', color: 'var(--text-secondary)', background: 'transparent', border: 'none', margin: '0 auto' } : {}}
      >
        {msg.role !== 'system' ? (
          editingIndex === i ? (
            <div className={styles.editContainer}>
              <textarea 
                className={styles.editInput} 
                value={editText} 
                onChange={e => setEditText(e.target.value)}
                autoFocus
                rows={Math.min(10, editText.split('\n').length + 1)}
              />
              <div className={styles.editActions}>
                <button className={styles.editCancelBtn} onClick={handleCancelEdit}>Cancel</button>
                <button className={styles.editSaveBtn} onClick={() => handleSaveEdit(i)}>Save & Submit</button>
              </div>
            </div>
          ) : msg.role === 'assistant' && msg.content === '' ? (
            <div className={styles.thinking}>
              <span className={styles.dot}></span>
              <span className={styles.dot}></span>
              <span className={styles.dot}></span>
            </div>
          ) : (
            <>
              <div dangerouslySetInnerHTML={{ __html: md.render(msg.content) }} />
              {msg.role === 'assistant' && ((msg.wsSources && msg.wsSources.length > 0) || (msg.kbSources && msg.kbSources.length > 0) || (msg.webSources && msg.webSources.length > 0)) && (
                <div className={styles.sourcesContainer}>
                  {msg.wsSources && msg.wsSources.length > 0 && (
                    <div className={styles.sourceGroup} title="Retrieved from Workspace Documents">
                      <Database size={11} className={styles.sourceIcon} />
                      <span>Workspace: {msg.wsSources.join(', ')}</span>
                    </div>
                  )}
                  {msg.kbSources && msg.kbSources.length > 0 && (
                    <div className={styles.sourceGroup} title="Retrieved from Personal Knowledge Base">
                      <Database size={11} className={styles.sourceIcon} />
                      <span>Personal KB: {msg.kbSources.join(', ')}</span>
                    </div>
                  )}
                  {msg.webSources && msg.webSources.length > 0 && (
                    msg.webSources.map((src, si) => {
                      const title = typeof src === 'string' ? src : src.title;
                      const url = typeof src === 'string' ? '' : src.url;
                      let domain = '';
                      try { domain = new URL(url).hostname.replace('www.', ''); } catch {}
                      return url ? (
                        <a
                          key={si}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.webSourceLink}
                          title={url}
                        >
                          <Globe size={11} />
                          <span className={styles.webSourceTitle}>{title}</span>
                          {domain && <span className={styles.webSourceDomain}>{domain}</span>}
                        </a>
                      ) : (
                        <div key={si} className={styles.sourceGroup} style={{ backgroundColor: 'rgba(16, 185, 129, 0.06)', borderColor: 'rgba(16, 185, 129, 0.2)', color: 'var(--success)' }}>
                          <Globe size={11} style={{ color: 'var(--success)' }} />
                          <span>{title}</span>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </>
          )
        ) : (
          msg.content
        )}

        {msg.isError && (
          <div className={styles.chatErrorBox}>
            <AlertTriangle size={14} className={styles.chatErrorIcon} />
            <span style={{flex: 1}}>{msg.content}</span>
            {onRetryMessage && msg.failedText && (
              <button 
                className={styles.chatRetryBtn} 
                onClick={() => onRetryMessage(msg.failedText)}
              >
                <RefreshCw size={12} /> Retry
              </button>
            )}
          </div>
        )}
        
        {msg.role !== 'system' && !msg.isError && msg.content.length > 0 && (
          <div className={styles.messageActions}>
              <button 
                className={`${styles.actionBtn} ${copiedIndex === i ? styles.success : ''}`}
                onClick={() => handleCopy(msg.content, i)}
                title="Copy to clipboard"
              >
                {copiedIndex === i ? <Check size={14} /> : <Copy size={14} />}
              </button>
              
              {msg.role === 'user' && editingIndex !== i && onEdit && (
                <button 
                  className={styles.actionBtn} 
                  onClick={() => handleStartEdit(i, msg.content)}
                  title="Edit message"
                >
                  <Edit2 size={14} />
                </button>
              )}

              {msg.role === 'assistant' && onRegenerate && (
                <button 
                  className={styles.actionBtn} 
                  onClick={() => onRegenerate(i)}
                  title="Regenerate response"
                >
                  <RefreshCw size={14} />
                </button>
              )}
              
              {msg.role === 'assistant' && !isRTL(msg.content) && (
                <button 
                  className={`${styles.actionBtn} ${playingIndex === i ? styles.playing : ''}`} 
                  onClick={() => playAudio(msg.content, i)}
                  title={playingIndex === i ? "Stop audio" : "Play audio"}
                >
                  {playingIndex === i ? <Square size={14} fill="currentColor" /> : <Volume2 size={14} />}
                </button>
              )}
            </div>
          )}
        </div>
      {msg.role !== 'system' && msg.timestamp && (
        <span className={styles.timestamp}>
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );
});

export default function ChatArea({ messages, onRegenerate, onEdit, onExport, onSummarize, onRetryMessage }) {
  const toast = useToast();
  const scrollContainerRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  const [playingIndex, setPlayingIndex] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  const [editText, setEditText] = useState("");
  const currentAudioRef = useRef(null);
  const activePlayIndexRef = useRef(null);

  const handleStartEdit = (index, text) => {
    setEditingIndex(index);
    setEditText(text);
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditText("");
  };

  const handleSaveEdit = (index) => {
    if (editText.trim() && onEdit) {
      onEdit(index, editText);
    }
    setEditingIndex(null);
    setEditText("");
  };

  const handleCopy = async (text, index) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      // Instant scroll to bottom to keep up with streaming tokens
      container.scrollTop = container.scrollHeight;
      
      // Deferred scroll to capture any layout shifts from Markdown rendering or images
      const timer = setTimeout(() => {
        container.scrollTop = container.scrollHeight;
      }, 50);
      
      return () => clearTimeout(timer);
    }
  }, [messages]);

  // Clean up any playing audio when the component unmounts
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
    };
  }, []);

  const playAudio = async (text, index) => {
    // If the clicked message is already playing or loading, stop it and return
    if (activePlayIndexRef.current === index) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      activePlayIndexRef.current = null;
      setPlayingIndex(null);
      return;
    }

    // If another message is playing or loading, stop/cancel it first
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    activePlayIndexRef.current = index;
    setPlayingIndex(index);

    const voice = detectVoice(text);
    try {
      const response = await fetch('/api/v1/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice })
      });

      // If user clicked stop or clicked another message during the fetch, halt execution
      if (activePlayIndexRef.current !== index) {
        return;
      }

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `TTS failed (${response.status})`);
      }
      
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);

      // Event listeners to reset UI states when audio finishes naturally or pauses/errors
      const handleReset = () => {
        if (activePlayIndexRef.current === index) {
          activePlayIndexRef.current = null;
          setPlayingIndex(null);
        }
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };

      audio.addEventListener('ended', handleReset);
      audio.addEventListener('pause', handleReset);
      audio.addEventListener('error', (e) => {
        console.error("Audio playback error event:", e);
        handleReset();
      });

      currentAudioRef.current = audio;
      await audio.play();
    } catch (error) {
      console.error("Audio playback error:", error);
      if (activePlayIndexRef.current === index) {
        activePlayIndexRef.current = null;
        setPlayingIndex(null);
      }
      if (currentAudioRef.current) {
        currentAudioRef.current = null;
      }
      toast.error("Failed to play audio: " + error.message);
    }
  };

  const isWelcomeState = messages.length === 0 || (messages.length === 1 && (
    messages[0].content.includes('Start a new chat') || 
    messages[0].content.includes('Welcome') || 
    messages[0].content.includes('created')
  ));

  return (
    <div className={styles.container}>
      {isWelcomeState ? (
        <div className={styles.welcomeContainer}>
          <img src="/Logo.png" alt="StarkLLM" className={styles.welcomeLogo} />
          <h1 className={styles.welcomeTitle}>StarkLLM</h1>
          <p className={styles.welcomeSubtitle}>
            Private AI assistant with personal Knowledge Base and RAG retrieval.
          </p>
        </div>
      ) : (
        <>
          {(onExport || onSummarize) && messages.length > 1 && (
            <div className={styles.exportFloating}>
              {onSummarize && messages.length >= 3 && (
                <button
                  className={styles.exportBtn}
                  onClick={onSummarize}
                  title="Summarize this chat"
                >
                  <FileText size={18} />
                </button>
              )}
              {onExport && (
                <>
                  <button
                    className={styles.exportBtn}
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    title="Export chat"
                  >
                    <Download size={18} />
                  </button>
                  {showExportMenu && (
                    <div className={styles.exportMenu}>
                      <button onClick={() => { onExport('md'); setShowExportMenu(false); }}>
                        📄 Markdown (.md)
                      </button>
                      <button onClick={() => { onExport('txt'); setShowExportMenu(false); }}>
                        📝 Plain Text (.txt)
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          <div className={styles.messages} ref={scrollContainerRef}>
          {messages.map((msg, i) => (
            <ChatMessageRenderer
              key={i}
              msg={msg}
              i={i}
              isRTL={isRTL}
              editingIndex={editingIndex}
              editText={editText}
              setEditText={setEditText}
              handleCancelEdit={handleCancelEdit}
              handleSaveEdit={handleSaveEdit}
              copiedIndex={copiedIndex}
              handleCopy={handleCopy}
              handleStartEdit={handleStartEdit}
              onEdit={onEdit}
              onRegenerate={onRegenerate}
              playingIndex={playingIndex}
              playAudio={playAudio}
              onRetryMessage={onRetryMessage}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>
        </>
      )}
    </div>
  );
}


