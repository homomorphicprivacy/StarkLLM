import React, { useEffect, useState, useRef } from 'react';
import { MessageSquare, Settings, Database, Code, Shield, BrainCircuit, Activity, Clock, Plus, ArrowRight, TrendingUp, MessageCircle, Zap, FileText } from 'lucide-react';
import styles from './Dashboard.module.css';
import DateTimeWidget from './DateTimeWidget';
import MarketPricesWidget from './MarketPricesWidget';
import SystemStatusWidget from './SystemStatusWidget';
import EmptyState from './EmptyState';

export default function Dashboard({ token, username, workspaces, onNewWorkspace, onViewChange, onSelectWorkspace }) {
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const getHeaders = () => ({ Authorization: `Bearer ${token}` });

  useEffect(() => {
    if (!token) return;
    const fetchStats = async () => {
      setLoadingStats(true);
      try {
        const res = await fetch('/api/v1/dashboard/stats', { headers: getHeaders() });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (_) {}
      setLoadingStats(false);
    };
    fetchStats();
  }, [token]);

  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = canvas.parentElement.clientWidth;
      canvas.height = canvas.parentElement.clientHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.radius = Math.random() * 2.5 + 1.5;
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvas.width) this.vx = -this.vx;
        if (this.y < 0 || this.y > canvas.height) this.vy = -this.vy;
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(212, 175, 55, 0.95)';
        ctx.fill();
      }
    }

    const particleCount = 45;
    const particles = Array.from({ length: particleCount }, () => new Particle());

    const drawLines = () => {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.hypot(dx, dy);

          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(212, 175, 55, ${0.45 * (1 - dist / 120)})`;
            ctx.lineWidth = 1.1;
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.update();
        p.draw();
      });
      drawLines();
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);



  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  const statCards = [
    {
      label: 'Workspaces',
      value: loadingStats ? '—' : (stats?.workspaces ?? workspaces.length),
      icon: MessageSquare,
      color: '#6366f1',
      glow: 'rgba(99,102,241,0.2)',
      action: () => onViewChange('chat'),
      actionLabel: 'Open Chat',
    },
    {
      label: 'Chats',
      value: loadingStats ? '—' : (stats?.chats ?? 0),
      icon: MessageCircle,
      color: '#a78bfa',
      glow: 'rgba(167,139,250,0.2)',
      action: () => onViewChange('chat'),
      actionLabel: 'Go to Chat',
    },
    {
      label: 'KB Folders',
      value: loadingStats ? '—' : (stats?.kb_folders ?? 0),
      icon: Database,
      color: '#8b5cf6',
      glow: 'rgba(139,92,246,0.2)',
      action: () => onViewChange('knowledge-base'),
      actionLabel: 'Open KB',
    },
    {
      label: 'Indexed Documents',
      value: loadingStats ? '—' : (stats?.kb_documents ?? 0),
      icon: FileText,
      color: '#06b6d4',
      glow: 'rgba(6,182,212,0.2)',
      action: () => onViewChange('knowledge-base'),
      actionLabel: 'View Docs',
    },
    {
      label: 'RAG Status',
      value: 'Active',
      icon: Zap,
      color: '#22c55e',
      glow: 'rgba(34,197,94,0.2)',
      action: () => onViewChange('settings'),
      actionLabel: 'Configure',
    },
  ];



  const quickActions = [
    { label: 'New Workspace', icon: MessageSquare, color: '#6366f1', onClick: onNewWorkspace },
    { label: 'Open Chat', icon: MessageSquare, color: '#818cf8', onClick: () => onViewChange('chat') },
    { label: 'Knowledge Base', icon: Database, color: '#8b5cf6', onClick: () => onViewChange('knowledge-base') },
    { label: 'Settings', icon: Zap, color: '#06b6d4', onClick: () => onViewChange('settings') },
  ];

  return (
    <div className={styles.page}>
      <canvas ref={canvasRef} className={styles.neuralNetCanvas} />
      {/* ── Hero header ── */}
      <div className={styles.hero}>
        <div className={styles.heroContent}>
          <p className={styles.heroGreeting}>{greeting}, {username || 'User'} 👋</p>
          <h1 className={styles.heroTitle}>Your StarkLLM Dashboard</h1>
          <p className={styles.heroSubtitle}>
            Private AI assistant with full Knowledge Base and RAG retrieval support.
          </p>
        </div>
        <img src="/Logo.png" alt="StarkLLM" className={styles.heroLogo} />
      </div>

      {/* ── Stat cards ── */}
      <div className={styles.statsGrid}>
        {statCards.map(({ label, value, icon: Icon, color, glow, action, actionLabel }) => (
          <button key={label} className={styles.statCard} style={{ '--card-glow': glow }} onClick={action}>
            <div className={styles.statIconWrap} style={{ background: `${color}1a`, boxShadow: `0 0 16px ${glow}` }}>
              <Icon size={20} color={color} />
            </div>
            <div className={styles.statBody}>
              <span className={styles.statValue}>{value}</span>
              <span className={styles.statLabel}>{label}</span>
            </div>
            <span className={styles.statAction} style={{ color }}>
              {actionLabel} <ArrowRight size={13} />
            </span>
          </button>
        ))}
      </div>

      {/* ── Widgets row ── */}
      <div className={styles.widgetsRow}>
        <DateTimeWidget />
        <MarketPricesWidget />
        <SystemStatusWidget token={token} />
      </div>

      {/* ── Two-column layout ── */}
      <div className={styles.twoCol}>

        {/* Quick Actions */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <TrendingUp size={16} />
            Quick Actions
          </div>
          <div className={styles.actionGrid}>
            {quickActions.map(({ label, icon: Icon, color, onClick }) => (
              <button key={label} className={styles.actionBtn} onClick={onClick}>
                <div className={styles.actionIcon} style={{ background: `${color}1a`, color }}>
                  <Icon size={18} />
                </div>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Workspace overview */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <Clock size={16} />
            Workspaces
            <button
              className={styles.cardAction}
              onClick={onNewWorkspace}
            >
              <Plus size={14} /> New
            </button>
          </div>
          {workspaces.length === 0 ? (
            <EmptyState 
              icon={MessageSquare} 
              title="No workspaces yet." 
              action={{ label: 'Create First Workspace', onClick: onNewWorkspace }} 
            />
          ) : (
            <div className={styles.wsList}>
              {workspaces.slice(0, 6).map(ws => (
                <div
                  key={ws.id}
                  className={styles.wsRow}
                  onClick={() => {
                    if (onSelectWorkspace) onSelectWorkspace(ws);
                    onViewChange('chat');
                  }}
                >
                  <div className={styles.wsRowIcon}><MessageSquare size={14} /></div>
                  <span className={styles.wsRowName}>{ws.name}</span>
                  <ArrowRight size={13} className={styles.wsRowArrow} />
                </div>
              ))}
              {workspaces.length > 6 && (
                <p className={styles.wsMore} onClick={() => onViewChange('chat')}>
                  +{workspaces.length - 6} more — open chat to see all
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── RAG features banner ── */}
      <div className={styles.featureBanner} onClick={() => onViewChange('settings')} style={{ cursor: 'pointer' }}>
        <div className={styles.featureBannerContent}>
          <Zap size={20} className={styles.featureBannerIcon} />
          <div>
            <strong>Advanced RAG Active</strong>
            <p>Semantic Chunking · Query Rewriting · Hybrid Search (TF-IDF + Vector) · Context Compression</p>
          </div>
        </div>
        <button className="btn-secondary" onClick={(e) => { e.stopPropagation(); onViewChange('settings'); }} style={{ fontSize: '0.8rem', padding: '7px 14px' }}>
          Configure
        </button>
      </div>
    </div>
  );
}
