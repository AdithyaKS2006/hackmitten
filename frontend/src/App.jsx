import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';
const HEADERS = {
  'Content-Type': 'application/json',
  'X-Role': 'analyst',
};

export default function App() {
  const [health, setHealth] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('mock');
  const [asOf, setAsOf] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evidenceData, setEvidenceData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHealth();
    fetchScenarios();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, { headers: HEADERS });
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchScenarios = async () => {
    try {
      const res = await fetch(`${API_BASE}/scenarios`, { headers: HEADERS });
      const data = await res.json();
      setScenarios(data);
      if (data.length > 0 && !selectedScenario) {
        setSelectedScenario(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const runAnalysis = async () => {
    if (!selectedScenario) return;
    setLoading(true);
    setError(null);
    setEvidenceData(null);
    try {
      const url = asOf
        ? `${API_BASE}/analyze/${selectedScenario}?as_of=${encodeURIComponent(asOf)}`
        : `${API_BASE}/analyze/${selectedScenario}`;
      const res = await fetch(url, { method: 'POST', headers: HEADERS });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Analysis request failed');
      }
      const data = await res.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inspectEvidence = async (evidenceId) => {
    try {
      const res = await fetch(
        `${API_BASE}/evidence/${evidenceId}?scenario=${selectedScenario}`,
        { headers: HEADERS }
      );
      const data = await res.json();
      setEvidenceData({ id: evidenceId, records: data });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <header>
        <div>
          <div className="logo-badge">AO-03 System</div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', marginTop: '6px' }}>
            Root Cause Evidence Engine
          </h1>
          <p className="tagline">
            Automated causal attribution & verifiable evidence extraction for microservices incidents
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {health && (
            <div className="status-pill">
              <span className="status-dot"></span>
              API Online ({health.mode || 'Ready'})
            </div>
          )}
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Left Column: Controls & Meta */}
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 className="card-title">Investigation Console</h2>

            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Select Incident Scenario
            </label>
            <select
              className="select-box"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name || sc.id}
                </option>
              ))}
              {scenarios.length === 0 && <option value="mock">mock (Default Scenario)</option>}
            </select>

            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Replay Timestamp (as_of optional)
            </label>
            <input
              type="text"
              placeholder="e.g. 2026-10-28T14:00:00Z"
              className="input-box"
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
            />

            <button
              className="btn-primary"
              onClick={runAnalysis}
              disabled={loading}
            >
              {loading ? 'Correlating Telemetry...' : 'Run Root Cause Analysis'}
            </button>

            {error && (
              <div style={{ marginTop: '14px', color: '#ef4444', fontSize: '13px', background: 'rgba(239,68,68,0.1)', padding: '10px', borderRadius: '6px' }}>
                Error: {error}
              </div>
            )}
          </div>

          {/* Redaction Guarantee Card */}
          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 className="card-title">PII Redaction Proof</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Raw telemetry text is sanitized in ingest before detection:
            </div>
            {analysis?.redaction_sample ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>RAW INGEST:</div>
                  <pre className="code-block">{analysis.redaction_sample.before}</pre>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#10b981' }}>SANITIZED:</div>
                  <pre className="code-block" style={{ color: '#10b981' }}>{analysis.redaction_sample.after}</pre>
                </div>
              </div>
            ) : (
              <pre className="code-block">Run analysis to view sample</pre>
            )}
          </div>

          {/* Inspect Evidence Modal / Card */}
          {evidenceData && (
            <div className="card">
              <div className="card-title">
                <span>Evidence #{evidenceData.id}</span>
                <button
                  onClick={() => setEvidenceData(null)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '16px' }}
                >
                  ✕
                </button>
              </div>
              <pre className="code-block" style={{ maxHeight: '200px' }}>
                {JSON.stringify(evidenceData.records, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Right Column: Candidates & Timeline */}
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <div className="card-title">
              <span>Ranked Root Cause Candidates</span>
              {analysis && (
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Scenario: {analysis.scenario_id}
                </span>
              )}
            </div>

            {!analysis && !loading && (
              <div style={{ color: 'var(--text-muted)', padding: '40px 0', textAlign: 'center' }}>
                Click "Run Root Cause Analysis" to isolate root causes and produce verifiable evidence.
              </div>
            )}

            {analysis?.unknown && (
              <div style={{ padding: '16px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', borderRadius: '8px', color: '#f59e0b' }}>
                <strong>Attribution Unknown:</strong> {analysis.unknown_reason}
              </div>
            )}

            {analysis?.candidates?.map((cand) => (
              <div key={cand.rank} className={`candidate-box rank-${cand.rank}`}>
                <div className="candidate-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: '800', fontSize: '16px' }}>#{cand.rank}</span>
                    <span style={{ fontSize: '15px', fontWeight: '700' }}>{cand.name}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span className="badge badge-hypothesis">{cand.label}</span>
                    <span className="badge badge-confidence">{cand.confidence} conf ({cand.score.toFixed(2)})</span>
                  </div>
                </div>

                <div style={{ fontSize: '13px', margin: '8px 0', color: '#cbd5e1' }}>
                  <ul style={{ paddingLeft: '18px' }}>
                    {cand.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '10px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Verifiable Evidence:</span>
                  {cand.evidence_ids.map((eid) => (
                    <button
                      key={eid}
                      onClick={() => inspectEvidence(eid)}
                      style={{
                        padding: '2px 8px',
                        background: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '4px',
                        color: '#38bdf8',
                        fontSize: '11px',
                        cursor: 'pointer',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {eid}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Incident Timeline */}
          {analysis?.timeline && (
            <div className="card">
              <h2 className="card-title">Correlated Incident Timeline</h2>
              <div className="timeline-list">
                {analysis.timeline.map((item, idx) => (
                  <div key={idx} className="timeline-item">
                    <span className="timeline-ts">{item.ts.substring(11, 19)}</span>
                    <div style={{ flex: 1 }}>
                      <span style={{ fontWeight: '700', marginRight: '8px', textTransform: 'uppercase', fontSize: '11px', color: '#94a3b8' }}>
                        [{item.service}] {item.kind}
                      </span>
                      <span className="timeline-summary">{item.summary}</span>
                    </div>
                    {item.evidence_ids?.length > 0 && (
                      <button
                        onClick={() => inspectEvidence(item.evidence_ids[0])}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#38bdf8',
                          cursor: 'pointer',
                          fontSize: '12px',
                          textDecoration: 'underline',
                        }}
                      >
                        Inspect
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
