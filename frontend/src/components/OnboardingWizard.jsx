import React, { useState, useEffect, useCallback } from 'react';
import styles from './OnboardingWizard.module.css';
import { CheckCircle2, XCircle, RefreshCw, Server, Cpu, Brain, Zap, TerminalSquare } from 'lucide-react';

export default function OnboardingWizard({ token, onComplete }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/v1/dashboard/system-status', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
        
        // Check if completely healthy
        const allHealthy = 
          json.backend?.status === 'online' &&
          json.ollama?.status === 'online' &&
          json.text_model?.status === 'online' &&
          json.embedding_model?.status === 'online';
          
        if (allHealthy) {
          // If we fetched and everything is healthy, instantly complete onboarding!
          onComplete();
        }
      } else {
        setErrorMsg(`Server returned ${res.status}`);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to connect to backend.');
    }
    setLoading(false);
  }, [token, onComplete]);

  // Initial fetch on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleSkip = () => {
    onComplete();
  };

  const StatusItem = ({ label, status, error, icon: Icon, iconColor }) => {
    const isOnline = status === 'online';
    
    return (
      <div className={`${styles.statusItem} ${!isOnline ? styles.statusItemError : ''}`}>
        <div className={styles.statusHeader}>
          <div className={styles.statusIcon} style={{ background: `${iconColor}22`, color: iconColor }}>
            <Icon size={18} />
          </div>
          <div className={styles.statusLabel}>{label}</div>
          <div className={styles.statusBadge}>
            {isOnline ? (
              <span className={styles.badgeSuccess}><CheckCircle2 size={16} /> Ready</span>
            ) : (
              <span className={styles.badgeError}><XCircle size={16} /> {status || 'Unknown'}</span>
            )}
          </div>
        </div>
        {!isOnline && error && (
          <div className={styles.actionableBox}>
            <div className={styles.actionableTitle}>Action Required:</div>
            <div className={styles.actionableText}>
              <TerminalSquare size={14} />
              {error}
            </div>
          </div>
        )}
      </div>
    );
  };

  // If we are currently checking and have no data, show a full screen loader.
  // Note: if it's perfectly healthy on mount, it will trigger onComplete() immediately
  // so the user barely sees this loader.
  if (loading && !data) {
    return (
      <div className={styles.wizardContainer}>
        <div className={styles.loaderBox}>
          <RefreshCw size={24} className={styles.spinning} />
          <p>Running system readiness checks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wizardContainer}>
      <div className={styles.wizardCard}>
        <div className={styles.wizardHeader}>
          <h2>Welcome to StarkLLM</h2>
          <p>Let's make sure your local AI environment is fully set up before we begin.</p>
        </div>

        <div className={styles.wizardBody}>
          {errorMsg ? (
            <div className={styles.criticalError}>
              <strong>Critical Error:</strong> {errorMsg}
              <p>Cannot reach the StarkLLM backend API. Make sure the server is running.</p>
            </div>
          ) : (
            <div className={styles.statusList}>
              <StatusItem
                icon={Server}
                iconColor="#6366f1"
                label="Backend API Server"
                status={data?.backend?.status}
                error={data?.backend?.error}
              />
              <StatusItem
                icon={Cpu}
                iconColor="#06b6d4"
                label="Ollama Engine"
                status={data?.ollama?.status}
                error={data?.ollama?.error}
              />
              <StatusItem
                icon={Brain}
                iconColor="#8b5cf6"
                label={`Text Model (${data?.text_model?.name || 'Required'})`}
                status={data?.text_model?.status}
                error={data?.text_model?.error}
              />
              <StatusItem
                icon={Zap}
                iconColor="#f59e0b"
                label={`Embedding Model (${data?.embedding_model?.name || 'Required'})`}
                status={data?.embedding_model?.status}
                error={data?.embedding_model?.error}
              />
            </div>
          )}
        </div>

        <div className={styles.wizardFooter}>
          <button className={styles.skipBtn} onClick={handleSkip}>
            Skip / Proceed anyway
          </button>
          
          <button 
            className={`${styles.recheckBtn} ${loading ? styles.spinningBtn : ''}`}
            onClick={fetchStatus}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? styles.spinning : ''} />
            {loading ? 'Checking...' : 'Re-check Status'}
          </button>
        </div>
      </div>
    </div>
  );
}
