import React from 'react';

export default function DependencyGraph({ graph, anomalousServices = {}, selectedService, onSelectService }) {
  // Service icons mapping
  const serviceIcons = {
    frontend: '💻',
    checkout: '🛒',
    payment: '🗄️',
    cart: '🛒',
    user: '👤',
    db: '💾',
    catalogue: '📦',
    orders: '📋',
  };

  // Fixed visual layout positions for standard topologies, or fallback to auto
  const fixedPositions = {
    frontend: { x: 230, y: 30 },
    checkout: { x: 230, y: 110 },
    payment: { x: 130, y: 200 },
    cart: { x: 330, y: 200 },
    user: { x: 230, y: 280 },
    db: { x: 230, y: 280 },
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
    // Defaults if mock scenario
    if (node === 'payment') return 'cause';
    if (node === 'checkout' || node === 'frontend') return 'victim';
    return 'healthy';
  };

  // Node dimension
  const nodeWidth = 140;
  const nodeHeight = 54;

  return (
    <div className="topology-graph-card">
      {/* Header */}
      <div className="topology-header-row">
        <div className="topology-title-wrap">
          <div className="graph-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="18" cy="5" r="3"></circle>
              <circle cx="6" cy="12" r="3"></circle>
              <circle cx="18" cy="19" r="3"></circle>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
          </div>
          <div>
            <h3 className="topology-title">Service Dependency Topology</h3>
            <p className="topology-subtitle">
              Causal propagation graph. Red indicates root cause, amber indicates cascade victims. Click a service to filter timeline.
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="topology-legend">
          <div className="legend-item">
            <span className="legend-dot dot-cause"></span>
            <span>Root Cause</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-victim"></span>
            <span>Cascade Victim</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-healthy"></span>
            <span>Healthy</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="topology-canvas-container">
        <svg className="topology-svg" viewBox="0 0 580 360" width="100%" height="360">
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
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#9c9285" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map(([fromNode, toNode], idx) => {
            const pFrom = fixedPositions[fromNode] || { x: 100 + idx * 60, y: 50 };
            const pTo = fixedPositions[toNode] || { x: 150 + idx * 60, y: 220 };

            const startX = pFrom.x + nodeWidth / 2;
            const startY = pFrom.y + nodeHeight;
            const endX = pTo.x + nodeWidth / 2;
            const endY = pTo.y;

            return (
              <g key={`edge-${fromNode}-${toNode}-${idx}`}>
                <path
                  d={`M ${startX} ${startY} C ${startX} ${startY + 25}, ${endX} ${endY - 25}, ${endX} ${endY}`}
                  fill="none"
                  stroke="#b4a99a"
                  strokeWidth="1.8"
                  markerEnd="url(#topo-arrow)"
                />
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = fixedPositions[node] || { x: 150, y: 150 };
            const status = getNodeStatus(node);
            const isSelected = selectedService === node;
            const icon = serviceIcons[node] || '🖥️';

            // Status styling
            let borderColor = '#9ae6b4';
            let bgColor = '#f0fff4';
            let badgeText = 'HEALTHY';
            let badgeBg = '#22a06b';
            let dotColor = '#22a06b';

            if (status === 'cause') {
              borderColor = '#feb2b2';
              bgColor = '#fff5f5';
              badgeText = 'CAUSE';
              badgeBg = '#e04848';
              dotColor = '#e04848';
            } else if (status === 'victim') {
              borderColor = '#fbd38d';
              bgColor = '#fffaf0';
              badgeText = 'VICTIM';
              badgeBg = '#d9822b';
              dotColor = '#d9822b';
            }

            return (
              <g
                key={`node-${node}`}
                className="topo-node-group"
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelectService && onSelectService(selectedService === node ? null : node)}
                style={{ cursor: 'pointer' }}
              >
                {/* Node Box */}
                <rect
                  x="0"
                  y="0"
                  width={nodeWidth}
                  height={nodeHeight}
                  rx="10"
                  fill={bgColor}
                  stroke={isSelected ? '#3182ce' : borderColor}
                  strokeWidth={isSelected ? '2.5' : '1.6'}
                  filter="drop-shadow(0px 2px 4px rgba(0,0,0,0.03))"
                />

                {/* Top Status Tag */}
                <g transform="translate(10, -9)">
                  <rect
                    x="0"
                    y="0"
                    width={badgeText.length * 7 + 12}
                    height="18"
                    rx="4"
                    fill={badgeBg}
                  />
                  <text
                    x={badgeText.length * 3.5 + 6}
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

                {/* Service Icon */}
                <text x="16" y="34" fontSize="18">
                  {icon}
                </text>

                {/* Service Name */}
                <text
                  x="44"
                  y="33"
                  fill="#2d2823"
                  fontSize="13"
                  fontWeight="600"
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {node}
                </text>

                {/* Right Status Dot */}
                <circle cx={nodeWidth - 18} cy="27" r="4.5" fill={dotColor} />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
