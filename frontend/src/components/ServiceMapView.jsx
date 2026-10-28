import React, { useState } from 'react';
import DependencyGraph from './DependencyGraph';

export default function ServiceMapView({
  graph,
  anomalousServices = {},
  selectedService,
  onSelectService,
  onNavigateToConsole,
}) {
  const [activeService, setActiveService] = useState(selectedService || 'payment');

  const serviceSpecs = {
    payment: {
      name: 'Payment Service',
      role: 'Root Cause (Injected)',
      type: 'Core Financial Processing',
      language: 'Python / Django',
      p99Latency: '2450ms',
      errorRate: '18.4%',
      status: 'Critical Failure',
      statusColor: '#e04848',
      callers: ['checkout'],
      dependencies: ['db', 'user'],
      details: 'Connection pool exhausted (pool_size=5). Queries to database timed out after 5000ms threshold.',
    },
    checkout: {
      name: 'Checkout Service',
      role: 'Cascade Victim',
      type: 'Order Fulfillment Workflow',
      language: 'Go / gRPC',
      p99Latency: '1820ms',
      errorRate: '12.1%',
      status: 'Degraded (Cascade)',
      statusColor: '#d9822b',
      callers: ['frontend'],
      dependencies: ['payment', 'cart'],
      details: 'Downstream HTTP call to /payment/charge timed out, queuing checkout transactions.',
    },
    frontend: {
      name: 'Frontend Gateway',
      role: 'Cascade Victim',
      type: 'Ingress Reverse Proxy',
      language: 'Node.js / Express',
      p99Latency: '1940ms',
      errorRate: '9.3%',
      status: 'Degraded (Cascade)',
      statusColor: '#d9822b',
      callers: ['External Users'],
      dependencies: ['checkout'],
      details: 'User requests experiencing high latency as checkout pipeline stalled.',
    },
    cart: {
      name: 'Cart Service',
      role: 'Healthy Service',
      type: 'Session Storage & Cache',
      language: 'Java / Spring Boot',
      p99Latency: '42ms',
      errorRate: '0.0%',
      status: 'Normal Operation',
      statusColor: '#22a06b',
      callers: ['checkout'],
      dependencies: ['user'],
      details: 'Memory and CPU utilization within nominal baseline; zero errors detected.',
    },
    user: {
      name: 'User Profile Service',
      role: 'Healthy Service',
      type: 'Authentication & Metadata',
      language: 'Go / REST',
      p99Latency: '35ms',
      errorRate: '0.0%',
      status: 'Normal Operation',
      statusColor: '#22a06b',
      callers: ['payment', 'cart'],
      dependencies: ['db'],
      details: 'Identity verification requests executing within 40ms SLA.',
    },
    db: {
      name: 'Database Cluster',
      role: 'Healthy Infrastructure',
      type: 'PostgreSQL Relational DB',
      language: 'PostgreSQL 15',
      p99Latency: '15ms',
      errorRate: '0.0%',
      status: 'Normal Operation',
      statusColor: '#22a06b',
      callers: ['payment', 'user'],
      dependencies: [],
      details: 'Active connections throttled by client-side pool clamp; database CPU normal at 22%.',
    },
  };

  const currentSpec = serviceSpecs[activeService] || serviceSpecs['payment'];

  const handleNodeClick = (svc) => {
    setActiveService(svc);
    if (onSelectService) onSelectService(svc);
  };

  return (
    <div className="servicemap-page-container">
      {/* Header Bar */}
      <div className="servicemap-header-card">
        <div>
          <div className="servicemap-pretitle">MICROSERVICE ARCHITECTURE MAP</div>
          <h2 className="servicemap-title">Full Dependency Topology & Blast Radius</h2>
          <p className="servicemap-subtitle">
            Causal propagation graph mapping RPC/HTTP dependencies and propagating incident impact across microservices.
          </p>
        </div>
        <div className="servicemap-stats-row">
          <div className="stat-pill">
            <span className="stat-label">Total Services:</span>
            <span className="stat-val">6</span>
          </div>
          <div className="stat-pill crit">
            <span className="stat-label">Root Cause:</span>
            <span className="stat-val">1 (payment)</span>
          </div>
          <div className="stat-pill warn">
            <span className="stat-label">Cascades:</span>
            <span className="stat-val">2 (checkout, frontend)</span>
          </div>
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="servicemap-split-grid">
        {/* Left: Expanded Dependency Graph */}
        <div className="servicemap-graph-col">
          <DependencyGraph
            graph={graph}
            anomalousServices={anomalousServices}
            selectedService={activeService}
            onSelectService={handleNodeClick}
          />
        </div>

        {/* Right: Service Inspector Detail Card */}
        <div className="servicemap-inspector-col">
          <div className="service-inspector-card">
            <div className="inspector-header">
              <div>
                <span
                  className="inspector-status-badge"
                  style={{ backgroundColor: currentSpec.statusColor }}
                >
                  {currentSpec.status}
                </span>
                <h3 className="inspector-service-name">{currentSpec.name}</h3>
                <span className="inspector-role-text">{currentSpec.role}</span>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="inspector-metrics-grid">
              <div className="spec-metric-box">
                <span className="spec-metric-label">P99 Latency</span>
                <span className="spec-metric-val">{currentSpec.p99Latency}</span>
              </div>
              <div className="spec-metric-box">
                <span className="spec-metric-label">Error Rate</span>
                <span className="spec-metric-val">{currentSpec.errorRate}</span>
              </div>
              <div className="spec-metric-box">
                <span className="spec-metric-label">Runtime Engine</span>
                <span className="spec-metric-val">{currentSpec.language}</span>
              </div>
              <div className="spec-metric-box">
                <span className="spec-metric-label">Architecture Role</span>
                <span className="spec-metric-val">{currentSpec.type}</span>
              </div>
            </div>

            {/* Diagnostic Details */}
            <div className="inspector-diagnostic-box">
              <h4 className="diag-heading">Operational Diagnostics</h4>
              <p className="diag-text">{currentSpec.details}</p>
            </div>

            {/* Upstream & Downstream Links */}
            <div className="topology-relations-box">
              <div className="relation-col">
                <span className="relation-title">Direct Callers (Upstream):</span>
                <div className="relation-tags">
                  {currentSpec.callers.length > 0 ? (
                    currentSpec.callers.map((c) => (
                      <span
                        key={c}
                        className="service-link-chip"
                        onClick={() => handleNodeClick(c)}
                      >
                        {c}
                      </span>
                    ))
                  ) : (
                    <span className="none-text">None</span>
                  )}
                </div>
              </div>

              <div className="relation-col">
                <span className="relation-title">Dependencies (Downstream):</span>
                <div className="relation-tags">
                  {currentSpec.dependencies.length > 0 ? (
                    currentSpec.dependencies.map((d) => (
                      <span
                        key={d}
                        className="service-link-chip"
                        onClick={() => handleNodeClick(d)}
                      >
                        {d}
                      </span>
                    ))
                  ) : (
                    <span className="none-text">None</span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Action Button */}
            <div className="inspector-footer">
              <button
                className="btn-filter-console"
                onClick={() => {
                  if (onSelectService) onSelectService(activeService);
                  if (onNavigateToConsole) onNavigateToConsole();
                }}
              >
                Inspect {currentSpec.name} in Console →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
