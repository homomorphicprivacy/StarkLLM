import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import styles from './GlobalSearch.module.css';
import {
  Search, X, MessageCircle, FolderOpen, FileText, Database,
  ArrowRight, Loader, Command
} from 'lucide-react';

const RESULT_TYPE_ICONS = {
  chat: MessageCircle,
  workspace: FolderOpen,
  document: FileText,
  knowledge_base: Database,
};

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

export default function GlobalSearch({ token, workspaces, onClose, onNavigate }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const debouncedQuery = useDebounce(query, 280);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Fetch results
  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults(null);
      setError(null);
      setSelectedIndex(0);
      return;
    }

    const search = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `/api/v1/search/global?q=${encodeURIComponent(debouncedQuery.trim())}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error(`Search failed (${res.status})`);
        const data = await res.json();
        setResults(data);
        setSelectedIndex(0);
      } catch (e) {
        setError(e.message);
        setResults(null);
      } finally {
        setLoading(false);
      }
    };

    search();
  }, [debouncedQuery, token]);

  // Flatten results for keyboard nav
  const flatResults = useMemo(() => {
    return results
      ? [
          ...results.workspaces.map(r => ({ ...r, _group: 'workspaces' })),
          ...results.chats.map(r => ({ ...r, _group: 'chats' })),
          ...results.documents.map(r => ({ ...r, _group: 'documents' })),
        ]
      : [];
  }, [results]);

  const handleNavigate = useCallback((item) => {
    onClose();
    onNavigate(item);
  }, [onClose, onNavigate]);

  // Keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') { onClose(); return; }
    if (flatResults.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, flatResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const item = flatResults[selectedIndex];
      if (item) handleNavigate(item);
    }
  }, [flatResults, selectedIndex, handleNavigate, onClose]);

  // Close on backdrop click
  const handleBackdropClick = (e) => {
    if (containerRef.current && !containerRef.current.contains(e.target)) {
      onClose();
    }
  };

  const totalCount = results
    ? results.workspaces.length + results.chats.length + results.documents.length
    : 0;

  const hasResults = results && totalCount > 0;

  const renderGroup = (label, icon, items, groupKey) => {
    if (!items || items.length === 0) return null;
    const Icon = icon;
    let flatOffset = 0;
    if (groupKey === 'chats') flatOffset = results.workspaces.length;
    if (groupKey === 'documents') flatOffset = results.workspaces.length + results.chats.length;

    return (
      <div className={styles.group} key={groupKey}>
        <div className={styles.groupLabel}>
          <Icon size={12} />
          {label}
          <span className={styles.groupCount}>{items.length}</span>
        </div>
        {items.map((item, idx) => {
          const globalIdx = flatOffset + idx;
          const isSelected = globalIdx === selectedIndex;
          return (
            <button
              key={`${groupKey}-${item.id}`}
              className={`${styles.resultItem} ${isSelected ? styles.resultSelected : ''}`}
              onClick={() => handleNavigate(item)}
              onMouseEnter={() => setSelectedIndex(globalIdx)}
            >
              <div className={styles.resultIcon}>
                {groupKey === 'documents' && item.doc_type === 'knowledge_base'
                  ? <Database size={14} />
                  : <Icon size={14} />}
              </div>
              <div className={styles.resultBody}>
                <span className={styles.resultTitle}>{item.title || item.name}</span>
                {item.content_snippet && (
                  <span className={styles.contentSnippet}>{item.content_snippet}</span>
                )}
                {item.workspace_name && (
                  <span className={styles.resultMeta}>
                    {item.workspace_name}
                    {item.match_type === 'content' && groupKey === 'chats' && (
                      <span className={styles.matchBadge}>in messages</span>
                    )}
                    {item.match_type === 'content' && groupKey === 'documents' && (
                      <span className={styles.matchBadge}>in content</span>
                    )}
                    {item.doc_type === 'knowledge_base' && (
                      <span className={styles.kbBadge}>Knowledge Base</span>
                    )}
                  </span>
                )}
              </div>
              <ArrowRight size={13} className={styles.resultArrow} />
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.modal} ref={containerRef} onKeyDown={handleKeyDown}>

        {/* ── Search input ── */}
        <div className={styles.inputRow}>
          {loading
            ? <Loader size={16} className={styles.searchIconSpinner} />
            : <Search size={16} className={styles.searchIcon} />
          }
          <input
            ref={inputRef}
            type="text"
            className={styles.input}
            placeholder="Search chats, messages, workspaces, documents…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            aria-label="Global search"
            spellCheck={false}
            autoComplete="off"
          />
          {query && (
            <button className={styles.clearBtn} onClick={() => setQuery('')} title="Clear">
              <X size={14} />
            </button>
          )}
          <button className={styles.closeKbd} onClick={onClose} title="Close (Esc)">
            <kbd>Esc</kbd>
          </button>
        </div>

        {/* ── Body ── */}
        <div className={styles.body}>
          {/* Empty state — no query */}
          {!query.trim() && !results && (
            <div className={styles.emptyState}>
              <Search size={32} className={styles.emptyIcon} />
              <p className={styles.emptyTitle}>Search everything</p>
              <p className={styles.emptyHint}>
                Type to search across chats, messages, workspaces, and documents.
              </p>
              <div className={styles.kbdHints}>
                <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
                <span><kbd>↵</kbd> open</span>
                <span><kbd>Esc</kbd> close</span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className={styles.errorState}>
              <span>⚠️ {error}</span>
            </div>
          )}

          {/* No results */}
          {results && !hasResults && !loading && (
            <div className={styles.emptyState}>
              <Search size={28} className={styles.emptyIcon} />
              <p className={styles.emptyTitle}>No results found</p>
              <p className={styles.emptyHint}>Try a different keyword.</p>
            </div>
          )}

          {/* Results */}
          {hasResults && (
            <div className={styles.results}>
              {renderGroup('Workspaces', FolderOpen, results.workspaces, 'workspaces')}
              {renderGroup('Chats', MessageCircle, results.chats, 'chats')}
              {renderGroup('Documents', FileText, results.documents, 'documents')}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        {hasResults && (
          <div className={styles.footer}>
            <span>{totalCount} result{totalCount !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
}
