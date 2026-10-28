/**
 * API client with automatic fallback to local mock data.
 * Adheres strictly to SPEC section 6 (no trailing slashes, X-Role header).
 */

import mockScenarios from './mock/scenarios.json';
import mockAnalyze from './mock/analyze.json';
import mockEvaluate from './mock/evaluate.json';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth(role = 'analyst') {
  try {
    const res = await fetch(`${API_BASE}/health`, {
      headers: { 'X-Role': role },
    });
    if (!res.ok) throw new Error('Health check failed');
    const data = await res.json();
    return { data, isMock: false };
  } catch (err) {
    return {
      data: { status: 'mock_mode', mode: 'offline_fallback', scenario_count: mockScenarios.length },
      isMock: true,
    };
  }
}

export async function fetchScenarios(role = 'analyst') {
  try {
    const res = await fetch(`${API_BASE}/scenarios`, {
      headers: { 'X-Role': role },
    });
    if (!res.ok) throw new Error('Failed to load scenarios');
    const data = await res.json();
    return { data, isMock: false };
  } catch (err) {
    return { data: mockScenarios, isMock: true };
  }
}

export async function analyzeScenario(scenarioId, asOf = null, role = 'analyst') {
  try {
    const url = asOf
      ? `${API_BASE}/analyze/${scenarioId}?as_of=${encodeURIComponent(asOf)}`
      : `${API_BASE}/analyze/${scenarioId}`;

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Role': role,
      },
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server returned ${res.status}`);
    }
    const data = await res.json();
    return { data, isMock: false };
  } catch (err) {
    console.warn('Backend unavailable or error; using mock fallback for analysis:', err);
    // If scenario is mock or syn_5, adjust mock
    const fallback = JSON.parse(JSON.stringify(mockAnalyze));
    fallback.scenario_id = scenarioId;
    if (scenarioId === 'syn_5') {
      fallback.unknown = true;
      fallback.unknown_reason = 'Only generic timeouts on checkout; no change records, no upstream anomaly. Cause is external.';
      fallback.candidates = [];
    }
    return { data: fallback, isMock: true, error: err.message };
  }
}

export async function fetchEvidence(evidenceId, scenarioId, role = 'analyst') {
  try {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}?scenario=${scenarioId}`, {
      headers: { 'X-Role': role },
    });
    if (!res.ok) throw new Error('Failed to load evidence');
    const data = await res.json();
    return { data, isMock: false };
  } catch (err) {
    return {
      data: [
        {
          id: evidenceId,
          type: 'telemetry_sample',
          scenario: scenarioId,
          message: `Redacted raw evidence record linked to candidate onset #${evidenceId}`,
          ts: new Date().toISOString(),
          status: 'verified_redacted',
        },
      ],
      isMock: true,
    };
  }
}

export async function fetchEvaluation(role = 'analyst') {
  try {
    const res = await fetch(`${API_BASE}/evaluate`, {
      headers: { 'X-Role': role },
    });
    if (!res.ok) throw new Error('Failed to load evaluation');
    const data = await res.json();
    return { data, isMock: false };
  } catch (err) {
    return { data: mockEvaluate, isMock: true };
  }
}
