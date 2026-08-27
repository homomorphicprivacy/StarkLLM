import React, { useRef } from 'react';
import styles from './SummaryModal.module.css';
import { X, Copy, Check, Loader, FileText } from 'lucide-react';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

export default function SummaryModal({ chatTitle, summary, loading, error, onClose, onCopy, copied }) {
  const contentRef = useRef(null);

  return (
    <div className={styles.backdrop} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-label="Chat Summary">

        {/* ── Header ── */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIcon}>
              <FileText size={16} />
            </div>
            <div>
              <h3 className={styles.title}>Chat Summary</h3>
              {chatTitle && (
                <p className={styles.subtitle}>{chatTitle}</p>
              )}
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        {/* ── Body ── */}
        <div className={styles.body} ref={contentRef}>
          {loading && (
            <div className={styles.loadingState}>
              <Loader size={24} className={styles.spinner} />
              <p className={styles.loadingText}>Generating summary…</p>
              <p className={styles.loadingHint}>Your local LLM is reading the conversation.</p>
            </div>
          )}

          {error && !loading && (
            <div className={styles.errorState}>
              <span className={styles.errorIcon}>⚠️</span>
              <p className={styles.errorTitle}>Summary failed</p>
              <p className={styles.errorMsg}>{error}</p>
            </div>
          )}

          {summary && !loading && (
            <div
              className={styles.summaryContent}
              dangerouslySetInnerHTML={{ __html: md.render(summary) }}
            />
          )}
        </div>

        {/* ── Footer ── */}
        {summary && !loading && (
          <div className={styles.footer}>
            <p className={styles.footerNote}>Generated locally · not stored</p>
            <button
              className={`${styles.copyBtn} ${copied ? styles.copied : ''}`}
              onClick={onCopy}
              title="Copy summary"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
