import { useState, useEffect } from 'react';

type Tab = 'console' | 'dashboard' | 'recent' | 'docs' | 'sdk' | 'architecture' | 'keys' | 'config';

export default function Console() {
  const [activeTab, setActiveTab] = useState<Tab>('console');
  
  // Investigation Console State
  const [url, setUrl] = useState('demo:local-fixture');
  const [bug, setBug] = useState('Parser crashes with IndexError when string has trailing space and negative sign at index 4.');
  const [isVerifying, setIsVerifying] = useState(false);
  const [stages, setStages] = useState<{ stage: string; message: string }[]>([]);
  const [proof, setProof] = useState<any>(null);
  const [error, setError] = useState('');

  // Real Data State
  const [executions, setExecutions] = useState<any[]>([]);
  const [serverConfig, setServerConfig] = useState<any>(null);

  // Settings State
  const [apiKey, setApiKey] = useState('');
  const [githubKey, setGithubKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [showGithubKey, setShowGithubKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<{
    hf_valid?: boolean;
    hf_user?: string | null;
    github_valid?: boolean;
    github_user?: string | null;
    errors?: string[];
  } | null>(null);

  useEffect(() => {
    // Load executions
    const savedExecs = localStorage.getItem('inevitable_executions');
    if (savedExecs) {
      setExecutions(JSON.parse(savedExecs));
    }
    // Load API key
    const savedKey = localStorage.getItem('inevitable_api_key');
    if (savedKey) setApiKey(savedKey);
    const savedGhKey = localStorage.getItem('inevitable_github_key');
    if (savedGhKey) setGithubKey(savedGhKey);
    const savedVal = localStorage.getItem('inevitable_validation');
    if (savedVal) {
      try { setValidationStatus(JSON.parse(savedVal)); } catch (e) {}
    }
    // Fetch server config
    const apiUrl = import.meta.env.VITE_API_URL || 'https://inevitable-uu2o.onrender.com';
    fetch(`${apiUrl}/api/v1/config`)
      .then(res => res.json())
      .then(data => setServerConfig(data))
      .catch(err => console.error("Could not load config", err));
  }, []);

  const saveApiKey = async () => {
    const trimmedApi = apiKey.trim();
    const trimmedGh = githubKey.trim();

    if (trimmedApi && !trimmedApi.startsWith('hf_')) {
      alert('Invalid Hugging Face token. It must start with "hf_".');
      return;
    }
    
    if (trimmedGh && !(trimmedGh.startsWith('ghp_') || trimmedGh.startsWith('github_pat_'))) {
      alert('Invalid GitHub token. It must start with "ghp_" or "github_pat_".');
      return;
    }

    if (!trimmedApi && !trimmedGh) {
      clearApiKeys();
      return;
    }

    setIsValidating(true);
    const apiUrl = import.meta.env.VITE_API_URL || 'https://inevitable-uu2o.onrender.com';

    try {
      const res = await fetch(`${apiUrl}/api/v1/keys/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: trimmedApi || undefined,
          github_key: trimmedGh || undefined,
        }),
      });

      const data = await res.json();
      setValidationStatus(data);
      localStorage.setItem('inevitable_validation', JSON.stringify(data));

      if (data.errors && data.errors.length > 0) {
        alert('Validation Failed:\n' + data.errors.join('\n'));
        return;
      }

      setApiKey(trimmedApi);
      setGithubKey(trimmedGh);
      localStorage.setItem('inevitable_api_key', trimmedApi);
      localStorage.setItem('inevitable_github_key', trimmedGh);

      let msg = 'Credentials verified and active!';
      if (data.hf_valid) msg += `\n• Hugging Face connected: ${data.hf_user}`;
      if (data.github_valid) msg += `\n• GitHub connected: @${data.github_user}`;
      alert(msg);
    } catch (e: any) {
      alert('Connection to backend validation service failed: ' + e.message);
    } finally {
      setIsValidating(false);
    }
  };

  const clearApiKeys = () => {
    localStorage.removeItem('inevitable_api_key');
    localStorage.removeItem('inevitable_github_key');
    localStorage.removeItem('inevitable_validation');
    setApiKey('');
    setGithubKey('');
    setValidationStatus(null);
    alert('All stored credentials have been securely purged from browser storage.');
  };

  const startVerification = async () => {
    setIsVerifying(true);
    setStages([]);
    setProof(null);
    setError('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'https://inevitable-uu2o.onrender.com';
      const response = await fetch(`${apiUrl}/api/v1/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repository_url: url,
          bug_description: bug,
          api_key: apiKey.trim() || undefined,
          github_key: githubKey.trim() || undefined,
        }),
      });

      if (!response.body) throw new Error('No response body received from server.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        
        buffer = parts.pop() || '';

        for (const part of parts) {
          const line = part.trim();
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.stage === 'error') {
                setError(data.message);
                setIsVerifying(false);
                return;
              } else if (data.stage === 'complete') {
                setProof(data.proof);
                setIsVerifying(false);
                // Save to local storage executions
                const execRecord = {
                  id: Date.now(),
                  date: new Date().toLocaleString(),
                  repository: url,
                  commit: data.proof.commit_sha,
                  status: data.proof.final_status
                };
                const updatedExecs = [execRecord, ...executions];
                setExecutions(updatedExecs);
                localStorage.setItem('inevitable_executions', JSON.stringify(updatedExecs));
                return;
              } else {
                setStages((prev) => [...prev, data]);
              }
            } catch (parseError) {
              console.error("Failed to parse SSE JSON:", line.slice(6));
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Connection failure');
      setIsVerifying(false);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        const verifiedCount = executions.filter(e => e.status === 'VERIFIED').length;
        const rate = executions.length > 0 ? ((verifiedCount / executions.length) * 100).toFixed(1) : '0.0';
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Project Dashboard</h1>
            <p className="dev-page-subtitle">Overview of your verification metrics and system health.</p>
            <div className="dev-grid-2">
              <div className="dev-panel">
                <h4 className="dev-heading-small text-muted mb-4">Total Executions</h4>
                <div style={{ fontSize: '3rem', fontWeight: 800 }}>{executions.length}</div>
                <div style={{ color: '#34D399', fontSize: '0.85rem', marginTop: '0.5rem' }}>Persisted locally</div>
              </div>
              <div className="dev-panel">
                <h4 className="dev-heading-small text-muted mb-4">Verification Success Rate</h4>
                <div style={{ fontSize: '3rem', fontWeight: 800 }}>{rate}%</div>
                <div style={{ color: rate === '100.0' ? '#34D399' : '#F87171', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                  {executions.length - verifiedCount} patches rejected or inconclusive
                </div>
              </div>
            </div>
            <div className="dev-panel mt-8">
              <h2 className="dev-panel-title">System Status</h2>
              <ul className="sidebar-nav">
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '1rem 0', borderBottom: '1px solid #222'}}>
                  <span>Gemma 4 Intelligence Node</span> <span style={{color: '#34D399'}}>Operational</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '1rem 0', borderBottom: '1px solid #222'}}>
                  <span>Pytest Subprocess Sandbox</span> <span style={{color: '#34D399'}}>Operational</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '1rem 0'}}>
                  <span>Source Evidence Extractor</span> <span style={{color: '#34D399'}}>Operational</span>
                </li>
              </ul>
            </div>
          </div>
        );
      
      case 'recent':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Recent Executions</h1>
            <p className="dev-page-subtitle">Audit log of all autonomous verifications executed locally.</p>
            <div className="dev-panel">
              {executions.length === 0 ? (
                <p className="text-muted text-center py-8">No executions found. Run an investigation first.</p>
              ) : (
                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #333', color: '#888' }}>
                      <th style={{ padding: '1rem 0' }}>Repository</th>
                      <th style={{ padding: '1rem 0' }}>Commit</th>
                      <th style={{ padding: '1rem 0' }}>Status</th>
                      <th style={{ padding: '1rem 0' }}>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {executions.map((exec) => (
                      <tr key={exec.id} style={{ borderBottom: '1px solid #222' }}>
                        <td className="mono" style={{ padding: '1rem 0', color: '#E5E5E5' }}>{exec.repository}</td>
                        <td className="mono" style={{ padding: '1rem 0', color: '#888' }}>{exec.commit.substring(0, 8)}</td>
                        <td style={{ padding: '1rem 0' }}>
                          <span className={`dev-badge dev-badge-${exec.status.toLowerCase()}`}>{exec.status}</span>
                        </td>
                        <td style={{ padding: '1rem 0', color: '#666' }}>{exec.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );

      case 'docs':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Documentation</h1>
            <p className="dev-page-subtitle">Core concepts and API integration guide.</p>
            <div className="dev-panel dev-prose" style={{lineHeight: 1.6}}>
              <h3>Proof-Carrying Patches</h3>
              <p className="mb-4 text-muted">A Proof-Carrying Patch is an artifact combining a unified diff with a cryptographically verifiable record of state machine transitions. Inevitable relies on deterministic evaluation rather than AI self-correction.</p>
              
              <h3>API Endpoints</h3>
              <div className="dev-code-block mb-4">
                <pre className="mono" style={{color: '#38BDF8'}}>POST /api/v1/verify</pre>
              </div>
              <p className="text-muted">Initiates the autonomous reasoning and sandbox execution pipeline. Requires `repository_url` and `bug_description`.</p>
            </div>
          </div>
        );

      case 'sdk':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">SDK Reference</h1>
            <p className="dev-page-subtitle">Language-specific libraries for Inevitable integration.</p>
            <div className="dev-panel dev-prose" style={{lineHeight: 1.6}}>
              <h3>Python SDK</h3>
              <p className="mb-4 text-muted">The reference implementation for interacting with the Inevitable verification engine.</p>
              <div className="dev-code-block mb-4">
                <pre className="mono" style={{color: '#A3A3A3'}}>pip install inevitable-sdk</pre>
              </div>
              
              <h3>Go SDK (Primary)</h3>
              <p className="mb-4 text-muted">The highly concurrent primary SDK for enterprise scale integrations.</p>
              <div className="dev-code-block mb-4">
                <pre className="mono" style={{color: '#A3A3A3'}}>go get github.com/inevitable/sdk-go</pre>
              </div>
            </div>
          </div>
        );

      case 'architecture':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Architecture</h1>
            <p className="dev-page-subtitle">Under the hood of the Inevitable verification engine.</p>
            <div className="dev-panel dev-prose" style={{lineHeight: 1.6}}>
              <h3>Hermetic Execution Sandbox</h3>
              <p className="mb-4 text-muted">All untrusted code and generated tests are executed inside an isolated Pytest subprocess. The environment is aggressively scrubbed of credentials to prevent exfiltration.</p>
              
              <h3>Deterministic State Machine</h3>
              <p className="mb-4 text-muted">Instead of asking the LLM if it succeeded, Inevitable runs a strict state machine comparing the baseline failure against the patched execution. A patch is only <strong>VERIFIED</strong> if the baseline exits non-zero and the patch exits zero.</p>
            </div>
          </div>
        );

      case 'keys':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">API Keys & Credentials</h1>
            <p className="dev-page-subtitle">Configure your provider credentials to enable live autonomous investigations. Private keys are securely handled.</p>
            <div className="dev-panel">
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem'}}>
                <h2 className="dev-panel-title" style={{margin: 0}}>Hugging Face / Gemma 4 Token</h2>
                {validationStatus?.hf_valid ? (
                  <span style={{fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.4)', padding: '0.2rem 0.6rem', borderRadius: '4px'}} className="mono">
                    ✓ ACTIVE: {validationStatus.hf_user}
                  </span>
                ) : apiKey ? (
                  <span style={{fontSize: '0.75rem', background: 'rgba(255, 255, 255, 0.05)', color: '#94a3b8', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '0.2rem 0.6rem', borderRadius: '4px'}} className="mono">
                    hf_••••{apiKey.slice(-4)}
                  </span>
                ) : null}
              </div>
              <div className="dev-form-group">
                <label>Hugging Face Access Token (for Gemma 4 live reasoning)</label>
                <div style={{display: 'flex', gap: '0.5rem'}}>
                  <input 
                    type={showApiKey ? "text" : "password"} 
                    className="dev-input mono" 
                    style={{flex: 1}}
                    placeholder="hf_xxxxxxxxxxxxxxxxxxxx" 
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                  <button 
                    type="button"
                    className="dev-btn-outline" 
                    onClick={() => setShowApiKey(!showApiKey)}
                    style={{minWidth: '70px', padding: '0 0.75rem', fontSize: '0.8rem'}}
                  >
                    {showApiKey ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', marginTop: '1.5rem'}}>
                <h2 className="dev-panel-title" style={{margin: 0}}>GitHub Personal Access Token</h2>
                {validationStatus?.github_valid ? (
                  <span style={{fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.4)', padding: '0.2rem 0.6rem', borderRadius: '4px'}} className="mono">
                    ✓ ACTIVE: @{validationStatus.github_user}
                  </span>
                ) : githubKey ? (
                  <span style={{fontSize: '0.75rem', background: 'rgba(255, 255, 255, 0.05)', color: '#94a3b8', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '0.2rem 0.6rem', borderRadius: '4px'}} className="mono">
                    ghp_••••{githubKey.slice(-4)}
                  </span>
                ) : null}
              </div>
              <div className="dev-form-group">
                <label>GitHub API Key (for cloning private repositories & rate limit bypass)</label>
                <div style={{display: 'flex', gap: '0.5rem'}}>
                  <input 
                    type={showGithubKey ? "text" : "password"} 
                    className="dev-input mono" 
                    style={{flex: 1}}
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" 
                    value={githubKey}
                    onChange={(e) => setGithubKey(e.target.value)}
                  />
                  <button 
                    type="button"
                    className="dev-btn-outline" 
                    onClick={() => setShowGithubKey(!showGithubKey)}
                    style={{minWidth: '70px', padding: '0 0.75rem', fontSize: '0.8rem'}}
                  >
                    {showGithubKey ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {validationStatus?.errors && validationStatus.errors.length > 0 && (
                <div style={{background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', padding: '0.75rem 1rem', margin: '1rem 0'}}>
                  <div style={{fontSize: '0.8rem', color: '#ef4444', fontWeight: 600, marginBottom: '0.25rem'}}>
                    ⚠️ Validation Issues Detected:
                  </div>
                  <ul style={{margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: '#fca5a5'}}>
                    {validationStatus.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '6px', padding: '0.75rem 1rem', margin: '1.25rem 0'}}>
                <div style={{fontSize: '0.8rem', color: '#10b981', fontWeight: 600, marginBottom: '0.25rem'}}>
                  🛡️ Zero-Leakage Guarantee
                </div>
                <p className="text-muted" style={{fontSize: '0.8rem', margin: 0, lineHeight: 1.5}}>
                  Your credentials are authenticated directly with Hugging Face and GitHub APIs. Subprocess test sandboxes are strictly stripped of all credentials before execution. Only valid keys will be accepted.
                </p>
              </div>

              <div style={{display: 'flex', gap: '1rem', marginTop: '1rem'}}>
                <button 
                  className="dev-btn-primary" 
                  onClick={saveApiKey}
                  disabled={isValidating}
                >
                  {isValidating ? "Validating Credentials..." : "Save & Verify Credentials"}
                </button>
                {(apiKey || githubKey) && (
                  <button 
                    className="dev-btn-outline" 
                    style={{borderColor: 'rgba(239, 68, 68, 0.4)', color: '#ef4444'}}
                    onClick={clearApiKeys}
                  >
                    Purge Stored Keys
                  </button>
                )}
              </div>
            </div>
          </div>
        );

      case 'config':
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Project Configuration</h1>
            <p className="dev-page-subtitle">Manage global sandbox limits and security restrictions loaded from the backend.</p>
            <div className="dev-panel">
              <h2 className="dev-panel-title">Execution Engine Rules</h2>
              {serverConfig ? (
                <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                  <label style={{display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#E5E5E5'}}>
                    <input type="checkbox" checked disabled /> 
                    <span>Enable SSRF Protection (Required)</span>
                  </label>
                  <label style={{display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#E5E5E5'}}>
                    <input type="checkbox" checked={!serverConfig.enable_untrusted_execution} disabled /> 
                    <span>Drop Environment Credentials in Subprocess (Required)</span>
                  </label>
                  <label style={{display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#E5E5E5'}}>
                    <input type="checkbox" checked={serverConfig.enable_untrusted_execution} disabled /> 
                    <span className="text-muted">Allow Arbitrary Untrusted Execution (Controlled by ENABLE_UNTRUSTED_EXECUTION)</span>
                  </label>
                  <div className="mt-4 text-muted mono" style={{fontSize: '0.8rem'}}>
                    MAX_EXECUTION_TIME_SECONDS = {serverConfig.max_execution_time_seconds}
                  </div>
                </div>
              ) : (
                <div className="text-muted">Loading configuration from server...</div>
              )}
            </div>
          </div>
        );

      case 'console':
      default:
        return (
          <div className="dev-content">
            <h1 className="dev-page-title">Proof-Carrying Verification</h1>
            <p className="dev-page-subtitle">
              Provide a repository and reproducible defect description to initiate an autonomous reasoning and verification cycle.
            </p>

            {!proof && !isVerifying && (
              <div className="dev-panel">
                <h2 className="dev-panel-title">Target Parameters</h2>
                <div className="dev-form-group">
                  <label>Repository URI</label>
                  <input
                    type="text"
                    className="dev-input mono"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="demo:local-fixture"
                  />
                </div>
                <div className="dev-form-group">
                  <label>Defect Description</label>
                  <textarea
                    className="dev-textarea mono"
                    rows={4}
                    value={bug}
                    onChange={(e) => setBug(e.target.value)}
                    placeholder="Describe the failure..."
                  />
                </div>
                <button className="dev-btn-primary" onClick={startVerification}>
                  Execute Investigation
                </button>
              </div>
            )}

            {isVerifying && (
              <div className="dev-panel">
                <h2 className="dev-panel-title">Execution Lifecycle</h2>
                <div className="dev-timeline">
                  {stages.map((s, i) => (
                    <div key={i} className={`dev-timeline-item ${i === stages.length - 1 ? 'active' : ''}`}>
                      <div className="dev-timeline-dot"></div>
                      <div className="dev-timeline-content">
                        <span className="mono stage-name">{s.stage}</span>
                        <span className="stage-msg">{s.message}</span>
                      </div>
                    </div>
                  ))}
                  <div className="dev-timeline-item active">
                    <div className="dev-timeline-dot pulse"></div>
                    <div className="dev-timeline-content">
                      <span className="mono stage-name">PROCESSING</span>
                      <span className="stage-msg">Awaiting subprocess completion...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="dev-alert dev-alert-error">
                <div className="alert-title">Execution Exception</div>
                <div className="mono alert-body">{error}</div>
                <button className="dev-btn-outline alert-action" onClick={() => setError('')}>Acknowledge</button>
              </div>
            )}

            {proof && (
              <div className="proof-report">
                <div className="dev-panel proof-header-panel">
                  <div className="proof-status-row">
                    <span className={`dev-badge dev-badge-${proof.final_status.toLowerCase()}`}>
                      {proof.final_status}
                    </span>
                    <span className="proof-reason">{proof.status_reason}</span>
                  </div>
                  <div className="proof-meta-grid mono">
                    <div><span className="meta-label">Commit SHA:</span> {proof.commit_sha}</div>
                    <div><span className="meta-label">Patch Hash:</span> {proof.patch_hash}</div>
                  </div>
                </div>

                <div className="dev-grid-2">
                  <div className="dev-panel">
                    <h2 className="dev-panel-title">Root-Cause Hypothesis</h2>
                    <div className="dev-prose">
                      <p>{proof.root_cause_hypothesis}</p>
                      <h4 className="dev-heading-small mt-4">Risks & Uncertainties</h4>
                      <p className="text-muted">{proof.risks_and_uncertainties}</p>
                    </div>
                  </div>

                  <div className="dev-panel">
                    <h2 className="dev-panel-title">Generated Patch Diff</h2>
                    <div className="dev-code-block">
                      <pre className="mono">
                        {proof.candidate_patch.split('\n').map((line: string, i: number) => {
                          let cls = '';
                          if (line.startsWith('+')) cls = 'diff-add';
                          else if (line.startsWith('-')) cls = 'diff-del';
                          else if (line.startsWith('@@')) cls = 'diff-meta';
                          return <div key={i} className={`diff-line ${cls}`}>{line}</div>;
                        })}
                      </pre>
                    </div>
                  </div>
                </div>

                <div className="dev-grid-2">
                  <div className="dev-panel">
                    <h2 className="dev-panel-title">Baseline Sandboxed Execution</h2>
                    <div className={`dev-execution-status ${proof.baseline_result?.exit_code === 0 ? 'passed' : 'failed'}`}>
                      EXIT CODE {proof.baseline_result?.exit_code} {proof.baseline_result?.exit_code === 0 ? '(PASSED)' : '(FAILED)'}
                    </div>
                    <div className="dev-terminal">
                      <pre className="mono">{proof.baseline_result?.stdout || proof.baseline_result?.stderr || 'No output'}</pre>
                    </div>
                  </div>

                  <div className="dev-panel">
                    <h2 className="dev-panel-title">Patched Sandboxed Execution</h2>
                    <div className={`dev-execution-status ${proof.patched_result?.exit_code === 0 ? 'passed' : 'failed'}`}>
                      EXIT CODE {proof.patched_result?.exit_code} {proof.patched_result?.exit_code === 0 ? '(PASSED)' : '(FAILED)'}
                    </div>
                    <div className="dev-terminal">
                      <pre className="mono">{proof.patched_result?.stdout || proof.patched_result?.stderr || 'No output'}</pre>
                    </div>
                  </div>
                </div>

                <div className="dev-panel">
                  <h2 className="dev-panel-title">Synthesized Regression Test Fixture</h2>
                  <div className="dev-code-block">
                    <pre className="mono">{proof.regression_test_source}</pre>
                  </div>
                </div>

                <div className="mt-8">
                  <h2 className="dev-section-title">Extracted Source Evidence</h2>
                  {proof.source_evidence && proof.source_evidence.map((ev: any, i: number) => (
                    <div className="dev-panel mb-4" key={i}>
                      <div className="dev-panel-header-flex">
                        <span className="mono file-path">{ev.file_path}</span>
                        <span className="mono line-range">Lines {ev.line_range}</span>
                      </div>
                      <div className="dev-code-block">
                        <pre className="mono">{ev.snippet}</pre>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="dev-actions-center">
                  <button className="dev-btn-outline" onClick={() => { setProof(null); setStages([]); }}>
                    Initialize New Run
                  </button>
                </div>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="dev-layout">
      {/* Developer Tool Sidebar */}
      <aside className="dev-sidebar">
        <div className="sidebar-section">
          <h4 className="sidebar-title">START HERE</h4>
          <ul className="sidebar-nav">
            <li className={activeTab === 'console' ? 'active' : ''} onClick={() => setActiveTab('console')}>Investigation Console</li>
            <li className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => setActiveTab('dashboard')}>Dashboard</li>
            <li className={activeTab === 'recent' ? 'active' : ''} onClick={() => setActiveTab('recent')}>Recent Executions</li>
          </ul>
        </div>
        <div className="sidebar-section">
          <h4 className="sidebar-title">RESOURCES</h4>
          <ul className="sidebar-nav">
            <li className={activeTab === 'docs' ? 'active' : ''} onClick={() => setActiveTab('docs')}>Documentation</li>
            <li className={activeTab === 'sdk' ? 'active' : ''} onClick={() => setActiveTab('sdk')}>SDK Reference</li>
            <li className={activeTab === 'architecture' ? 'active' : ''} onClick={() => setActiveTab('architecture')}>Architecture</li>
          </ul>
        </div>
        <div className="sidebar-section">
          <h4 className="sidebar-title">SETTINGS</h4>
          <ul className="sidebar-nav">
            <li className={activeTab === 'keys' ? 'active' : ''} onClick={() => setActiveTab('keys')}>API Keys</li>
            <li className={activeTab === 'config' ? 'active' : ''} onClick={() => setActiveTab('config')}>Project Config</li>
          </ul>
        </div>
      </aside>

      {/* Main Dev Console Content */}
      <main className="dev-main">
        <header className="dev-header">
          <div className="breadcrumbs">
            <span>Inevitable</span> <span className="separator">/</span> <span style={{textTransform: 'capitalize'}}>{activeTab === 'sdk' ? 'SDK Reference' : activeTab}</span>
          </div>
          {activeTab === 'console' && proof && <button className="dev-btn-outline">Copy Execution ID</button>}
        </header>

        {renderContent()}
      </main>
    </div>
  );
}
