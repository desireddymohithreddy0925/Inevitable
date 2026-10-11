import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import VerificationMeshCanvas from '../components/VerificationMeshCanvas';

// Interactive 3D Tilt Card Component
function TiltCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState('');
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -12;
    const rotateY = ((x - centerX) / centerX) * 12;

    setTransform(`perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.03, 1.03, 1.03)`);
    setGlarePosition({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
    });
  };

  const handleMouseLeave = () => {
    setTransform('perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)');
  };

  return (
    <div
      ref={cardRef}
      className="tilt-card"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ transform }}
    >
      <div
        className="glare"
        style={{
          background: `radial-gradient(circle at ${glarePosition.x}% ${glarePosition.y}%, rgba(255,255,255,0.25), transparent 60%)`,
        }}
      />
      <div className="card-icon">{icon}</div>
      <h3 className="card-title">{title}</h3>
      <p className="card-desc">{description}</p>
    </div>
  );
}

export default function Landing() {
  const featuresRef = useRef<HTMLDivElement>(null);

  const scrollToFeatures = () => {
    featuresRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="landing-bg">
      {/* 3D Liquid Background Canvas using Tertiary Colors */}
      <div className="bg-mesh">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
      </div>
      <div className="bg-grid"></div>
      <VerificationMeshCanvas />

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-orb-container">
          <div className="hero-orb" />
        </div>

        <div className="hero-content">
          <div className="badge">Zero-Trust AI Software Verification</div>
          <h1 className="hero-title">
            Don't trust the patch.<br />
            <span>Prove it.</span>
          </h1>
          <p className="hero-subtitle">
            The world's first autonomous verification engine that generates <strong>Proof-Carrying Patches</strong>. 
            AI synthesizes fixes; deterministic execution harnesses prove regression elimination before it touches your codebase.
          </p>
          <div className="hero-cta mb-4">
            <Link to="/console" className="btn-primary" style={{ textDecoration: 'none' }}>
              Launch Console <span>→</span>
            </Link>
            <button className="btn-secondary" onClick={scrollToFeatures}>
              Explore What It Does
            </button>
          </div>
          
          {/* Interactive Terminal Demo */}
          <div className="mock-terminal mt-8">
             <div className="terminal-header">
                <span className="dot dot-red"></span>
                <span className="dot dot-yellow"></span>
                <span className="dot dot-green"></span>
                <span className="terminal-title">inevitable verify --repo demo:local-fixture</span>
             </div>
             <div className="terminal-body mono">
                <p><span style={{color: '#8B5CF6'}}>$</span> inevitable verify --repo demo:local-fixture</p>
                <p style={{color: '#64748B'}}>Initializing hermetic sandbox...</p>
                <p style={{color: '#3B82F6'}}>➜ Reproducing bug against baseline</p>
                <p style={{color: '#EF4444'}}>✖ Baseline failed: Parser crashes with IndexError</p>
                <p style={{color: '#10B981'}}>✔ Synthesized patch with Gemma 4</p>
                <p style={{color: '#3B82F6'}}>➜ Verifying patch in strict isolation</p>
                <p style={{color: '#10B981'}}>✔ VERIFIED: Exit code 0. Proof artifact generated.</p>
             </div>
          </div>
        </div>
      </section>

      {/* 3D Features Showcase / What the tool does */}
      <section className="features-section" ref={featuresRef}>
        <div className="section-header">
          <h2 className="section-title">The Proof-Carrying Paradigm</h2>
          <p className="section-subtitle">
            Hover over the 3D cards to explore our multi-stage verification architecture.
          </p>
        </div>

        <div className="features-grid">
          <TiltCard
            icon="🔍"
            title="Repository Inspection"
            description="Bounded AST & git inspection scans repository state while preventing SSRF, directory traversal, and private network poisoning."
          />
          <TiltCard
            icon="🧠"
            title="Gemma 4 Intelligence"
            description="Reasoning models synthesize targeted fault localization hypotheses, structured reproduction test proposals, and clean unified diffs."
          />
          <TiltCard
            icon="🛡️"
            title="Hermetic Sandboxing"
            description="Executes disposable pytest worktrees with scrubbed environment credentials, strict timeout groups, and bounded output constraints."
          />
          <TiltCard
            icon="📜"
            title="Proof Artifacts"
            description="Produces cryptographically hashed verification bundles. The status is deterministically bound to real exit codes, never AI prose."
          />
        </div>
        
        <div style={{ textAlign: 'center', marginTop: '6rem' }}>
            <Link to="/console" className="btn-primary" style={{ textDecoration: 'none', padding: '1.25rem 4rem' }}>
              Start Verification Now
            </Link>
        </div>
      </section>
    </div>
  );
}
