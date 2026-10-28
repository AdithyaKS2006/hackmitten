import React from 'react';

export default function DependencyGraph({ graph, anomalousServices = {}, selectedService, onSelectService }) {
  // Service icons mapping using official Google Material Symbols
  const serviceIcons = {
    frontend: 'desktop_windows',
    checkout: 'shopping_cart',
    payment: 'credit_card',
    cart: 'shopping_bag',
    user: 'person',
    db: 'database',
    catalogue: 'inventory_2',
    orders: 'receipt_long',
  };

  // Fixed visual layout positions for standard topologies
  const fixedPositions = {
    frontend: { x: 230, y: 25 },
    checkout: { x: 230, y: 115 },
    payment: { x: 125, y: 215 },
    cart: { x: 335, y: 215 },
    user: { x: 230, y: 305 },
    db: { x: 125, y: 305 },
  };

  const nodes = graph?.nodes || ['frontend', 'checkout', 'payment', 'cart', 'user'];
  const edges = graph?.edges || [
    ['frontend', 'checkout'],
    ['checkout', 'payment'],
    ['checkout', 'cart'],
    ['payment', 'user'],
    ['cart', 'user'],
  ];

  // Derive node status
  const getNodeStatus = (node) => {
    const status = anomalousServices[node];
    if (status === 'cause') return 'cause';
    if (status === 'victim') return 'victim';
    if (node === 'payment') return 'cause';
    if (node === 'checkout' || node === 'frontend') return 'victim';
    return 'healthy';
  };

  // Node telemetry stats
  const getNodeTelemetry = (node) => {
    switch (node) {
      case 'payment':
        return { latency: '2450ms', error: '18.4%' };
      case 'checkout':
        return { latency: '1820ms', error: '12.1%' };
      case 'frontend':
        return { latency: '1940ms', error: '9.3%' };
      case 'cart':
        return { latency: '42ms', error: '0.0%' };
      case 'user':
        return { latency: '35ms', error: '0.0%' };
      case 'db':
        return { latency: '15ms', error: '0.0%' };
      default:
        return { latency: '30ms', error: '0.0%' };
    }
  };

  // Node dimension
  const nodeWidth = 148;
  const nodeHeight = 60;

  return (
    <div className="topology-graph-card division-topology-card">
      {/* Header */}
      <div className="topology-header-row">
        <div className="topology-title-wrap">
          <div className="graph-icon-badge division-header-icon-box">
            <span className="material-symbols-outlined">hub</span>
          </div>
          <div>
            <div className="division-pretitle-tag">NETWORK TOPOLOGY MAP</div>
            <h3 className="topology-title">Service Dependency Topology</h3>
            <p className="topology-subtitle">
              Interactive causal propagation graph. Red indicates root cause, amber indicates cascade victims.
            </p>
          </div>
        </div>

        {/* Legend with Google Material Symbols & distinct border styling */}
        <div className="topology-legend">
          <div className="legend-item legend-cause">
            <span className="material-symbols-outlined sym-cause">error</span>
            <span>Root Cause</span>
          </div>
          <div className="legend-item legend-victim">
            <span className="material-symbols-outlined sym-victim">warning</span>
            <span>Cascade Victim</span>
          </div>
          <div className="legend-item legend-healthy">
            <span className="material-symbols-outlined sym-healthy">check_circle</span>
            <span>Healthy</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas Area with Distinct Cyber Mesh Border */}
      <div className="topology-canvas-container">
        <svg className="topology-svg" viewBox="0 0 580 380" width="100%" height="380">
          <defs>
            {/* Arrow Marker */}
            <marker
              id="topo-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#10b981" />
            </marker>
            <marker
              id="topo-arrow-danger"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" />
            </marker>
          </defs>

          {/* Edges with animated packet pulses */}
          {edges.map(([fromNode, toNode], idx) => {
            const pFrom = fixedPositions[fromNode] || { x: 100 + idx * 60, y: 50 };
            const pTo = fixedPositions[toNode] || { x: 150 + idx * 60, y: 220 };

            const startX = pFrom.x + nodeWidth / 2;
            const startY = pFrom.y + nodeHeight;
            const endX = pTo.x + nodeWidth / 2;
            const endY = pTo.y;

            const pathData = `M ${startX} ${startY} C ${startX} ${startY + 25}, ${endX} ${endY - 25}, ${endX} ${endY}`;
            const isAnomalousEdge = fromNode === 'payment' || toNode === 'payment' || fromNode === 'checkout';

            return (
              <g key={`edge-${fromNode}-${toNode}-${idx}`}>
                {/* Edge line */}
                <path
                  id={`edge-path-${idx}`}
                  d={pathData}
                  fill="none"
                  stroke={isAnomalousEdge ? '#f87171' : '#a7f3d0'}
                  strokeWidth={isAnomalousEdge ? '2.4' : '1.8'}
                  strokeDasharray={isAnomalousEdge ? 'none' : '4,2'}
                  markerEnd={isAnomalousEdge ? 'url(#topo-arrow-danger)' : 'url(#topo-arrow)'}
                />

                {/* Animated telemetry pulse packet */}
                <circle r="3.5" fill={isAnomalousEdge ? '#ef4444' : '#10b981'}>
                  <animateMotion
                    dur={`${2.0 + idx * 0.4}s`}
                    repeatCount="indefinite"
                    path={pathData}
                  />
                </circle>
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = fixedPositions[node] || { x: 150, y: 150 };
            const status = getNodeStatus(node);
            const isSelected = selectedService === node;
            const icon = serviceIcons[node] || 'dns';
            const telemetry = getNodeTelemetry(node);

            // Status styling
            let borderColor = '#a7f3d0';
            let bgColor = '#ffffff';
            let badgeText = 'HEALTHY';
            let badgeBg = '#10b981';
            let dotColor = '#10b981';

            if (status === 'cause') {
              borderColor = '#fca5a5';
              bgColor = '#fff5f5';
              badgeText = 'CAUSE';
              badgeBg = '#ef4444';
              dotColor = '#ef4444';
            } else if (status === 'victim') {
              borderColor = '#fde68a';
              bgColor = '#fffbeb';
              badgeText = 'VICTIM';
              badgeBg = '#f59e0b';
              dotColor = '#f59e0b';
            }

            return (
              <g
                key={`node-${node}`}
                className="topo-node-group"
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelectService && onSelectService(selectedService === node ? null : node)}
                style={{ cursor: 'pointer' }}
              >
                {/* Node Box with Multi-Layer Border */}
                <rect
                  x="0"
                  y="0"
                  width={nodeWidth}
                  height={nodeHeight}
                  rx="10"
                  fill={bgColor}
                  stroke={isSelected ? '#059669' : borderColor}
                  strokeWidth={isSelected ? '2.5' : '1.8'}
                  filter="drop-shadow(0px 3px 6px rgba(0,0,0,0.06))"
                />

                {/* Top Status Tag */}
                <g transform="translate(10, -9)">
                  <rect
                    x="0"
                    y="0"
                    width={badgeText.length * 7 + 14}
                    height="18"
                    rx="5"
                    fill={badgeBg}
                    stroke="#ffffff"
                    strokeWidth="1.2"
                  />
                  <text
                    x={badgeText.length * 3.5 + 7}
                    y="13"
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="9.5"
                    fontWeight="700"
                    fontFamily="Inter, system-ui, sans-serif"
                  >
                    {badgeText}
                  </text>
                </g>

                {/* Service Icon rendered via Google Material Symbols */}
                <text
                  x="14"
                  y="38"
                  style={{
                    fontFamily: "'Material Symbols Outlined'",
                    fontSize: '22px',
                    fill: status === 'cause' ? '#dc2626' : status === 'victim' ? '#d97706' : '#059669',
                    userSelect: 'none',
                  }}
                >
                  {icon}
                </text>

                {/* Service Name */}
                <text
                  x="42"
                  y="28"
                  fill="#1f2937"
                  fontSize="13"
                  fontWeight="700"
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {node}
                </text>

                {/* Telemetry subline: P99 & Error */}
                <text
                  x="42"
                  y="46"
                  fill="#4b5563"
                  fontSize="10"
                  fontWeight="600"
                  fontFamily="JetBrains Mono, monospace"
                >
                  P99: {telemetry.latency} • {telemetry.error} err
                </text>

                {/* Right Status Dot */}
                <circle cx={nodeWidth - 14} cy="28" r="4.5" fill={dotColor} stroke="#ffffff" strokeWidth="1.5" />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
