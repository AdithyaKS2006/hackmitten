import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import DependencyGraph from './components/DependencyGraph';
import ReplaySlider from './components/ReplaySlider';
import RankedCauses from './components/RankedCauses';
import Timeline from './components/Timeline';
import EvidenceDrawer from './components/EvidenceDrawer';
import EvaluationView from './components/EvaluationView';
import SafetyPanel from './components/SafetyPanel';
import PostIncidentReport from './components/PostIncidentReport';
import { fetchHealth, fetchScenarios, analyzeScenario, fetchEvidence } from './api';

export default function App() {
  const [role, setRole] = useState('analyst');
  const [activeTab, setActiveTab] = useState('investigation');
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('mock');
  const [scenarioMeta, setScenarioMeta] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);
  const [isMockMode, setIsMockMode] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const [asOf, setAsOf] = useState(null);

  // Initialize app
  useEffect(() => {
    initApp();
  }, [role]);

  const initApp = async () => {
    const healthRes = await fetchHealth(role);
    setHealth(healthRes.data);
    setIsMockMode(healthRes.isMock);

    const scRes = await fetchScenarios(role);
    setScenarios(scRes.data);
    if (scRes.data?.length > 0 && !selectedScenario) {
      setSelectedScenario(scRes.data[0].id);
    }
  };

  // Run analysis when scenario or asOf changes
  useEffect(() => {
    if (selectedScenario) {
      runAnalysis(selectedScenario, asOf);
    }
  }, [selectedScenario, asOf, role]);

  const runAnalysis = async (scenarioId, asOfTimestamp) => {
    setLoading(true);
    setError(null);
    try {
      const startT = performance.now();
      const res = await analyzeScenario(scenarioId, asOfTimestamp, role);
      const elapsed = Math.round(performance.now() - startT);
      if (res.error) {
        console.warn('Backend warning:', res.error);
      }
      const enriched = { ...res.data, execution_ms: elapsed };
      setAnalysis(enriched);

      // Extract time_range / incident metadata if available
      const currentSc = scenarios.find((s) => s.id === scenarioId);
      setScenarioMeta({
        time_range: currentSc?.time_range || ['2026-10-28T13:30:00Z', '2026-10-28T14:30:00Z'],
        incident_start: enriched.timeline?.[0]?.ts || '2026-10-28T13:55:00Z',
      });
    } catch (err) {
      setError(err.message || 'Failed to analyze scenario');
    } finally {
      setLoading(false);
    }
  };

  // Inspect raw evidence modal
  const handleInspectEvidence = async (evidenceId, serviceName = '') => {
    try {
      const res = await fetchEvidence(evidenceId, selectedScenario, role);
      setEvidenceData({
        id: evidenceId,
        scenario: selectedScenario,
        records: res.data,
      });
    } catch (err) {
      console.error('Failed to inspect evidence:', err);
    }
  };

  const topEvidenceIds = analysis?.candidates?.[0]?.evidence_ids || [];

  return (
    <div className="ao-app-root">
      {/* Top Header & Navigation */}
      <Header
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        onSelectScenario={(newId) => {
          setSelectedScenario(newId);
          setSelectedService(null);
          setAsOf(null);
        }}
        role={role}
        onRoleChange={setRole}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        isMockMode={isMockMode}
        onOpenReport={() => setShowReport(true)}
        analysisReady={Boolean(analysis)}
      />

      {/* Main Content Area */}
      <main className="main-viewport">
        {error && (
          <div className="global-error-banner">
            <span>⚠️ API Notice: {error} (Falling back to local verified telemetry)</span>
            <button className="btn-close-banner" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* TAB 1: Investigation Console */}
        {activeTab === 'investigation' && (
          <div className="investigation-dashboard">
            {/* Top Bar: Replay Scrubber Slider */}
            <section className="section-replay-slider">
              <ReplaySlider
                meta={scenarioMeta}
                currentAsOf={asOf}
                onAsOfChange={setAsOf}
                loading={loading}
              />
            </section>

            {/* Split Grid: Left Column Topology & Graph, Right Column Causal Attributions */}
            <div className="investigation-split-grid">
              {/* Left Column: Dependency Graph & Telemetry Filters */}
              <div className="split-col-left">
                <div className="glass-card">
                  <DependencyGraph
                    graph={analysis?.graph}
                    anomalousServices={analysis?.anomalous_services}
                    selectedService={selectedService}
                    onSelectService={setSelectedService}
                  />
                </div>

                <div className="glass-card timeline-card-wrapper">
                  <Timeline
                    timeline={analysis?.timeline}
                    selectedService={selectedService}
                    onInspectEvidence={handleInspectEvidence}
                    topCandidateEvidenceIds={topEvidenceIds}
                  />
                </div>
              </div>

              {/* Right Column: Ranked Hypotheses */}
              <div className="split-col-right">
                <div className="glass-card causes-card-wrapper">
                  <RankedCauses
                    candidates={analysis?.candidates}
                    unknown={analysis?.unknown}
                    unknownReason={analysis?.unknown_reason}
                    onInspectEvidence={handleInspectEvidence}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Benchmark Evaluation */}
        {activeTab === 'evaluation' && (
          <div className="evaluation-dashboard">
            <EvaluationView role={role} />
          </div>
        )}

        {/* TAB 3: Safety & Governance */}
        {activeTab === 'safety' && (
          <div className="safety-dashboard">
            <SafetyPanel
              redactionSample={analysis?.redaction_sample}
              role={role}
              onRoleChange={setRole}
            />
          </div>
        )}
      </main>

      {/* Evidence Drawer Modal */}
      {evidenceData && (
        <EvidenceDrawer
          evidenceData={evidenceData}
          onClose={() => setEvidenceData(null)}
        />
      )}

      {/* Printable Post-Incident Report */}
      {showReport && (
        <PostIncidentReport
          analysis={analysis}
          onClose={() => setShowReport(false)}
        />
      )}

      {/* Footer */}
      <footer className="ao-footer">
        <div className="footer-content">
          <span>AO-03 Root Cause Evidence Engine &copy; 2026</span>
          <span className="footer-divider">•</span>
          <span>Offline-First Multi-Modal Telemetry Ingestion</span>
          <span className="footer-divider">•</span>
          <span>Zero Black-Box LLM Hallucinations</span>
          <span className="footer-divider">•</span>
          <span>Verifiable Evidence Guarantee (Rules 1-8)</span>
        </div>
      </footer>
    </div>
  );
}
