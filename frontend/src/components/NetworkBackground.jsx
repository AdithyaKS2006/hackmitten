import React, { useEffect, useRef } from 'react';

/**
 * Super Creative Network & Server Mesh Background Canvas
 * Renders an animated constellation of server nodes, network buses, and flowing telemetry packets.
 * Ultra-lightweight, 60fps native Canvas 2D with subtle interactive cursor physics.
 */
export default function NetworkBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Mouse tracking for subtle interactive network pull
    const mouse = { x: -1000, y: -1000, radius: 140 };
    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    const handleMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    // Create 50 network server nodes
    const nodeCount = Math.floor(Math.min(width, 1400) / 24);
    const nodes = [];
    const colors = ['#b47836', '#22a06b', '#d9822b', '#92531a', '#3b82f6'];

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: Math.random() * 2.5 + 1.8,
        color: colors[i % colors.length],
        pulse: Math.random() * Math.PI,
        serverType: i % 4 === 0 ? 'gateway' : i % 4 === 1 ? 'core' : 'worker',
      });
    }

    // Flowing telemetry data packets traveling across network lines
    const packets = [];
    const packetCount = 14;

    function render() {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw subtle circuit grid lines in background
      ctx.strokeStyle = 'rgba(180, 120, 54, 0.04)';
      ctx.lineWidth = 1;
      const gridSize = 48;
      const startX = 0;
      const startY = 0;

      ctx.beginPath();
      for (let x = startX; x < width; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
      }
      for (let y = startY; y < height; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();

      // 2. Update and draw nodes
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Move node
        node.x += node.vx;
        node.y += node.vy;

        // Bounce on boundaries
        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        // Subtle mouse repulsion/pull
        const dx = mouse.x - node.x;
        const dy = mouse.y - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          const force = (mouse.radius - dist) / mouse.radius;
          node.x -= (dx / dist) * force * 1.5;
          node.y -= (dy / dist) * force * 1.5;
        }

        // Pulse effect
        node.pulse += 0.03;
        const currentRadius = node.radius + Math.sin(node.pulse) * 0.8;

        // Draw node glow halo
        ctx.beginPath();
        ctx.arc(node.x, node.y, currentRadius * 2.4, 0, Math.PI * 2);
        ctx.fillStyle = `${node.color}14`; // 8% opacity
        ctx.fill();

        // Draw node core
        ctx.beginPath();
        ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.fill();

        // 3. Connect nearby nodes with network bus lines
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeB = nodes[j];
          const distNodes = Math.hypot(node.x - nodeB.x, node.y - nodeB.y);
          const maxConnectDist = 135;

          if (distNodes < maxConnectDist) {
            const alpha = (1 - distNodes / maxConnectDist) * 0.28;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(nodeB.x, nodeB.y);
            ctx.strokeStyle = `rgba(180, 120, 54, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Spawn telemetry packets on lines occasionally
            if (packets.length < packetCount && Math.random() < 0.003) {
              packets.push({
                from: node,
                to: nodeB,
                progress: 0,
                speed: Math.random() * 0.012 + 0.008,
                color: node.color,
              });
            }
          }
        }
      }

      // 4. Update and draw flowing telemetry packets
      for (let p = packets.length - 1; p >= 0; p--) {
        const pkt = packets[p];
        pkt.progress += pkt.speed;

        if (pkt.progress >= 1) {
          packets.splice(p, 1);
          continue;
        }

        const px = pkt.from.x + (pkt.to.x - pkt.from.x) * pkt.progress;
        const py = pkt.from.y + (pkt.to.y - pkt.from.y) * pkt.progress;

        // Glowing packet dot
        ctx.beginPath();
        ctx.arc(px, py, 3.2, 0, Math.PI * 2);
        ctx.fillStyle = pkt.color;
        ctx.shadowColor = pkt.color;
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      }

      animationFrameId = requestAnimationFrame(render);
    }

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div className="network-background-viewport-container">
      <canvas ref={canvasRef} className="network-interactive-canvas" />
      <div className="network-ambient-radial-glow glow-top-left" />
      <div className="network-ambient-radial-glow glow-bottom-right" />
    </div>
  );
}
