import React from 'react';

/**
 * Interactive SVG Dependency Graph
 * Computes hierarchical layers from edges, renders directed flow arrows,
 * highlights root cause & cascade victims with neon glow, and filters timeline on click.
 */
export default function DependencyGraph({ graph, anomalousServices, selectedService, onSelectService }) {
  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  if (nodes.length === 0) {
    return (
      <div className="card-empty-state">
        <p>No dependency topology available for this scenario.</p>
      </div>
    );
  }

  // Compute topological layers (callers above callees)
  const incomingCount = {};
  const outgoingMap = {};
  nodes.forEach((n) => {
    incomingCount[n] = 0;
    outgoingMap[n] = [];
  });
  edges.forEach(([u, v]) => {
    if (incomingCount[v] !== undefined) incomingCount[v]++;
    if (outgoingMap[u]) outgoingMap[u].push(v);
  });

  // Assign layers
  const layers = {};
  nodes.forEach((n) => {
    if (incomingCount[n] === 0) layers[n] = 0;
  });

  let changed = true;
  let iter = 0;
  while (changed && iter < 10) {
    changed = false;
    iter++;
    edges.forEach(([u, v]) => {
      const uLayer = layers[u] !== undefined ? layers[u] : 0;
      const vLayer = layers[v] !== undefined ? layers[v] : 0;
      if (vLayer <= uLayer) {
        layers[v] = uLayer + 1;
        changed = true;
      }
    });
  }

  // Group by layer
  const layerGroups = {};
  nodes.forEach((n) => {
    const l = layers[n] || 0;
    if (!layerGroups[l]) layerGroups[l] = [];
    layerGroups[l].push(n);
  });

  const sortedLayerKeys = Object.keys(layerGroups).map(Number).sort((a, b) => a - b);
  const width = 560;
  const height = 320;
  const layerHeight = height / (sortedLayerKeys.length + 1);

  // Position nodes
  const nodePositions = {};
  sortedLayerKeys.forEach((layerIdx, lIndex) => {
    const group = layerGroups[layerIdx];
    const y = layerHeight * (lIndex + 1);
    const spacing = width / (group.length + 1);
    group.forEach((node, nIndex) => {
      nodePositions[node] = {
        x: spacing * (nIndex + 1),
        y: y,
      };
    });
  });

  const getNodeStatus = (node) => {
    const status = anomalousServices?.[node];
    if (status === 'cause') return 'cause';
    if (status === 'victim') return 'victim';
    return 'healthy';
  };

  const getStatusColors = (status) => {
    switch (status) {
      case 'cause':
        return {
          fill: 'rgba(239, 68, 68, 0.15)',
          stroke: '#ef4444',
          glow: 'rgba(239, 68, 68, 0.6)',
          text: '#f87171',
          badge: 'CAUSE',
          badgeBg: '#ef4444',
        };
      case 'victim':
        return {
          fill: 'rgba(245, 158, 11, 0.15)',
          stroke: '#f59e0b',
          glow: 'rgba(245, 158, 11, 0.5)',
          text: '#fbbf24',
          badge: 'VICTIM',
          badgeBg: '#f59e0b',
        };
      default:
        return {
          fill: 'rgba(16, 185, 129, 0.08)',
          stroke: '#10b981',
          glow: 'rgba(16, 185, 129, 0.3)',
          text: '#34d399',
          badge: 'HEALTHY',
          badgeBg: '#059669',
        };
    }
  };

  return (
    <div className="dependency-graph-container">
      <div className="graph-header">
        <div>
          <h3 className="section-title">Service Dependency Topology</h3>
          <p className="section-subtitle">
            Causal propagation graph. Red indicates root cause, amber denotes cascade victims. Click a service to filter timeline.
          </p>
        </div>
        {selectedService && (
          <button className="btn-filter-clear" onClick={() => onSelectService(null)}>
            Filter: <strong>{selectedService}</strong> ✕
          </button>
        )}
      </div>

      <div className="svg-wrapper">
        <svg viewBox={`0 0 ${width} ${height}`} className="dependency-svg">
          <defs>
            <marker
              id="arrowhead-normal"
              markerWidth="8"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#475569" />
            </marker>
            <marker
              id="arrowhead-cascade"
              markerWidth="8"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#f59e0b" />
            </marker>
            <marker
              id="arrowhead-cause"
              markerWidth="8"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#ef4444" />
            </marker>
            <filter id="glow-cause" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="6" floodColor="#ef4444" floodOpacity="0.6" />
            </filter>
            <filter id="glow-victim" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#f59e0b" floodOpacity="0.5" />
            </filter>
          </defs>

          {/* Render directed edges */}
          {edges.map(([u, v], i) => {
            const p1 = nodePositions[u];
            const p2 = nodePositions[v];
            if (!p1 || !p2) return null;

            const uStatus = getNodeStatus(u);
            const vStatus = getNodeStatus(v);
            const isCascade = (uStatus === 'cause' || uStatus === 'victim') && (vStatus === 'victim' || vStatus === 'cause');
            const strokeColor = isCascade ? (uStatus === 'cause' ? '#ef4444' : '#f59e0b') : '#334155';
            const markerId = isCascade ? (uStatus === 'cause' ? 'url(#arrowhead-cause)' : 'url(#arrowhead-cascade)') : 'url(#arrowhead-normal)';

            // Offset endpoint to border of node box
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const offsetX = (dx / dist) * 45;
            const offsetY = (dy / dist) * 22;

            return (
              <g key={`edge-${i}`}>
                <line
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x - offsetX}
                  y2={p2.y - offsetY}
                  stroke={strokeColor}
                  strokeWidth={isCascade ? '2.5' : '1.5'}
                  strokeDasharray={isCascade ? 'none' : '4 3'}
                  markerEnd={markerId}
                  className={isCascade ? 'cascade-edge-active' : ''}
                />
              </g>
            );
          })}

          {/* Render Service Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node];
            if (!pos) return null;
            const status = getNodeStatus(node);
            const colors = getStatusColors(status);
            const isSelected = selectedService === node;

            return (
              <g
                key={node}
                transform={`translate(${pos.x}, ${pos.y})`}
                className={`graph-node ${status} ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectService(isSelected ? null : node)}
                style={{ cursor: 'pointer' }}
              >
                {/* Outer Glow */}
                <rect
                  x="-60"
                  y="-22"
                  width="120"
                  height="44"
                  rx="8"
                  fill={colors.fill}
                  stroke={isSelected ? '#38bdf8' : colors.stroke}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                  filter={status === 'cause' ? 'url(#glow-cause)' : status === 'victim' ? 'url(#glow-victim)' : 'none'}
                />

                {/* Node Status Tag Pill */}
                <rect
                  x="-52"
                  y="-30"
                  width="44"
                  height="14"
                  rx="4"
                  fill={colors.badgeBg}
                />
                <text
                  x="-30"
                  y="-20"
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="8"
                  fontWeight="800"
                  letterSpacing="0.5"
                >
                  {colors.badge}
                </text>

                {/* Service Name Label */}
                <text
                  x="0"
                  y="4"
                  textAnchor="middle"
                  fill="#f8fafc"
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="var(--font-sans)"
                >
                  {node}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-dot dot-cause"></span>
          <span>Root Cause Service</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-victim"></span>
          <span>Cascade Victim</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-healthy"></span>
          <span>Healthy Service</span>
        </div>
      </div>
    </div>
  );
}
