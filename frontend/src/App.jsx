import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import SubHeader from './components/SubHeader';
import ActionBar from './components/ActionBar';
import ReplaySlider from './components/ReplaySlider';
import DependencyGraph from './components/DependencyGraph';
import RankedCauses from './components/RankedCauses';
import Timeline from './components/Timeline';
import EvidenceDrawer from './components/EvidenceDrawer';
import EvaluationView from './components/EvaluationView';
import SafetyPanel from './components/SafetyPanel';
import PostIncidentReport from './components/PostIncidentReport';
import IncidentsView from './components/IncidentsView';
import ServiceMapView from './components/ServiceMapView';
import SettingsView from './components/SettingsView';
import NetworkBackground from './components/NetworkBackground';
import { fetchHealth, fetchScenarios, analyzeScenario, fetchEvidence } from './api';

export default function App() {
  const [currentNav, setCurrentNav] = useState('dashboard');
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
  const [asOf, setAsOf] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize app data
  useEffect(() => {
    initApp();
  }, [role]);

  const initApp = async () => {
    const healthRes = await fetchHealth(role);
    setHealth(healthRes.data);
    setIsMockMode(healthRes.isMock);

    const scRes = await fetchScenarios(role);
    if (scRes.data?.length > 0) {
      setScenarios(scRes.data);
      if (!selectedScenario) {
        setSelectedScenario(scRes.data[0].id);
      }
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
      const res = await analyzeScenario(scenarioId, asOfTimestamp, role);
      if (res.data) {
        setAnalysis(res.data);
      }
      const currentSc = scenarios.find((s) => s.id === scenarioId);
      setScenarioMeta({
        time_range: currentSc?.time_range || ['2026-10-28T13:30:00Z', '2026-10-28T14:30:00Z'],
        incident_start: res.data?.timeline?.[0]?.ts || '2026-10-28T13:55:00Z',
      });
    } catch (err) {
      console.warn('API notice:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectEvidence = async (evidenceId) => {
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

  return (
    <div className="techinova-layout-root">
      {/* Super Creative Interactive Network & Server Telemetry Canvas */}
      <NetworkBackground />

      {/* 1. Left Sidebar with Visible Light Borders */}
      <Sidebar
        currentNav={currentNav}
        onNavChange={(nav) => setCurrentNav(nav)}
      />

      {/* 2. Main Right Container */}
      <div className="app-main-viewport">
        {/* Top Navbar with Interactive Search, Notifications & Account Menus */}
        <TopNav
          onSearch={setSearchQuery}
          role={role}
          onRoleChange={setRole}
          onNavigate={setCurrentNav}
          onSelectScenario={(scId) => {
            setSelectedScenario(scId);
            setSelectedService(null);
            setAsOf(null);
            setCurrentNav('dashboard');
          }}
          onSelectService={(svc) => {
            setSelectedService(svc);
            setCurrentNav('dashboard');
          }}
        />

        {/* View 1: Main Investigation Dashboard */}
        {currentNav === 'dashboard' && (
          <>
            {/* Sub-Header with Engine Info & Actions */}
            <SubHeader
              role={role}
              onRoleChange={setRole}
              health={health}
              isMockMode={isMockMode}
              onOpenReport={() => setCurrentNav('reports')}
              analysisReady={Boolean(analysis)}
            />

            {/* Action Bar (Scenario Dropdown + Tabs) */}
            <ActionBar
              scenarios={scenarios}
              selectedScenario={selectedScenario}
              onSelectScenario={(newId) => {
                setSelectedScenario(newId);
                setSelectedService(null);
                setAsOf(null);
              }}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            {/* Tab 1: Investigation Console */}
            {activeTab === 'investigation' && (
              <div className="tab-investigation-body">
                {/* Incident Replay Scrubber */}
                <ReplaySlider
                  meta={scenarioMeta}
                  currentAsOf={asOf}
                  onAsOfChange={setAsOf}
                  loading={loading}
                />

                {/* Split 2-Column Grid: Topology on Left, Ranked Hypotheses on Right */}
                <div className="investigation-split-row">
                  <div className="split-column-left">
                    <DependencyGraph
                      graph={analysis?.graph}
                      anomalousServices={analysis?.anomalous_services}
                      selectedService={selectedService}
                      onSelectService={setSelectedService}
                    />
                  </div>

                  <div className="split-column-right">
                    <RankedCauses
                      candidates={analysis?.candidates}
                      unknown={analysis?.unknown}
                      unknownReason={analysis?.unknown_reason}
                      onInspectEvidence={handleInspectEvidence}
                    />
                  </div>
                </div>

                {/* Timeline Section */}
                {analysis?.timeline && analysis.timeline.length > 0 && (
                  <div className="timeline-section-wrapper">
                    <Timeline
                      timeline={analysis.timeline}
                      selectedService={selectedService}
                      onInspectEvidence={handleInspectEvidence}
                      topCandidateEvidenceIds={analysis?.candidates?.[0]?.evidence_ids || []}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Benchmark Evaluation */}
            {activeTab === 'evaluation' && (
              <div className="tab-evaluation-body">
                <EvaluationView role={role} />
              </div>
            )}

            {/* Tab 3: Safety & Governance */}
            {activeTab === 'safety' && (
              <div className="tab-safety-body">
                <SafetyPanel
                  redactionSample={analysis?.redaction_sample}
                  role={role}
                  onRoleChange={setRole}
                />
              </div>
            )}
          </>
        )}

        {/* View 2: Incidents Catalog */}
        {currentNav === 'incidents' && (
          <div className="tab-page-wrapper">
            <IncidentsView
              scenarios={scenarios}
              selectedScenario={selectedScenario}
              onSelectScenario={setSelectedScenario}
              onNavigateToConsole={() => {
                setCurrentNav('dashboard');
                setActiveTab('investigation');
              }}
            />
          </div>
        )}

        {/* View 3: Service Dependency Map */}
        {currentNav === 'servicemap' && (
          <div className="tab-page-wrapper">
            <ServiceMapView
              graph={analysis?.graph}
              anomalousServices={analysis?.anomalous_services}
              selectedService={selectedService}
              onSelectService={setSelectedService}
              onNavigateToConsole={() => {
                setCurrentNav('dashboard');
                setActiveTab('investigation');
              }}
            />
          </div>
        )}

        {/* View 4: Embedded Post-Incident Report */}
        {currentNav === 'reports' && (
          <div className="tab-page-wrapper report-view-embedded">
            <div className="report-embedded-header-bar">
              <button
                className="btn-back-to-dash"
                onClick={() => setCurrentNav('dashboard')}
              >
                ← Return to Dashboard
              </button>
              <div className="report-nav-tag">Audited Incident Dossier</div>
            </div>

            <PostIncidentReport
              analysis={analysis}
              onClose={() => setCurrentNav('dashboard')}
              isEmbedded={true}
            />
          </div>
        )}

        {/* View 5: System Settings */}
        {currentNav === 'settings' && (
          <div className="tab-page-wrapper">
            <SettingsView
              role={role}
              onRoleChange={setRole}
              health={health}
            />
          </div>
        )}
      </div>

      {/* Evidence Drawer Slide-over */}
      {evidenceData && (
        <EvidenceDrawer
          evidenceData={evidenceData}
          onClose={() => setEvidenceData(null)}
        />
      )}
    </div>
  );
}
