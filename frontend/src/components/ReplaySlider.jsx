import React, { useState, useEffect, useRef } from 'react';

export default function ReplaySlider({ meta, currentAsOf, onAsOfChange, loading }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [sliderVal, setSliderVal] = useState(100); // 0 to 100 percentage
  const playTimerRef = useRef(null);

  const timeRange = meta?.time_range || [];
  const startIso = timeRange[0] || '2026-10-28T13:30:00Z';
  const endIso = timeRange[1] || '2026-10-28T14:30:00Z';
  const incidentStartIso = meta?.incident_start || startIso;

  const startMs = new Date(startIso).getTime();
  const endMs = new Date(endIso).getTime();
  const incidentStartMs = new Date(incidentStartIso).getTime();
  const totalDurationMs = Math.max(1000, endMs - startMs);

  // Position of incident start marker
  const incidentPercent = Math.min(
    100,
    Math.max(0, ((incidentStartMs - startMs) / totalDurationMs) * 100)
  );

  // Calculate current timestamp from sliderVal
  const currentTsMs = startMs + (sliderVal / 100) * totalDurationMs;
  const currentIso = new Date(currentTsMs).toISOString();

  // Elapsed offset since incident start
  const elapsedSec = Math.round((currentTsMs - incidentStartMs) / 1000);
  const isBeforeIncident = elapsedSec < 0;
  const absSec = Math.abs(elapsedSec);
  const mins = Math.floor(absSec / 60);
  const secs = absSec % 60;
  const elapsedLabel = `${isBeforeIncident ? '-' : '+'}${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  // Formatted clock time
  const clockTimeStr = new Date(currentTsMs).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'UTC',
  }) + ' UTC';

  // Debounced update to parent
  useEffect(() => {
    const timer = setTimeout(() => {
      if (sliderVal >= 99) {
        onAsOfChange(null); // Full telemetry
      } else {
        onAsOfChange(currentIso);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [sliderVal]);

  // Handle Play/Pause simulation
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setSliderVal((prev) => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return Math.min(100, prev + 2);
        });
      }, 500);
    } else {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying]);

  const handleReset = () => {
    setIsPlaying(false);
    setSliderVal(100);
    onAsOfChange(null);
  };

  const jumpToIncident = () => {
    setIsPlaying(false);
    setSliderVal(incidentPercent);
  };

  // Generate 48 graphical telemetry density waveform bars
  const waveBars = Array.from({ length: 48 }, (_, i) => {
    const barPercent = (i / 48) * 100;
    let height = 6;
    let color = '#d6c9ba';

    if (barPercent < incidentPercent - 5) {
      // Baseline normal traffic
      height = 5 + (i % 3) * 3;
      color = '#b7cfbd';
    } else if (barPercent >= incidentPercent - 5 && barPercent <= incidentPercent + 15) {
      // Anomaly onset spike
      height = 20 + ((i * 7) % 14);
      color = '#e05252';
    } else {
      // Cascade elevated state
      height = 12 + ((i * 5) % 10);
      color = '#e2993a';
    }

    return { height, color, isPassed: barPercent <= sliderVal };
  });

  return (
    <div className="replay-scrubber-card">
      {/* Card Header */}
      <div className="scrubber-header-row">
        <div className="scrubber-title-group">
          <div className="waveform-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#b47836" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 12h3l2-6 4 12 3-9 2 5 2-2h4"></path>
            </svg>
          </div>
          <div>
            <h3 className="scrubber-title">Incident Replay & Causal Scrubber</h3>
            <p className="scrubber-subtitle">Simulate real-time causal attribution as telemetry streams in.</p>
          </div>
        </div>

        <div className="scrubber-timing-badges">
          <div className="timing-pill">
            <span className="timing-label">Offset</span>
            <span className="timing-value">{elapsedLabel}</span>
          </div>
          <div className="timing-pill clock-pill">
            <span className="clock-icon">🕒</span>
            <span className="timing-clock">{clockTimeStr}</span>
          </div>
        </div>
      </div>

      {/* Graphical Waveform Spectrum of Telemetry Activity */}
      <div className="scrubber-waveform-container" title="Telemetry Ingestion Volume & Anomaly Density">
        <div className="waveform-label-top">
          <span>Normal Baseline Traffic</span>
          <span className="onset-text">Onset Peak Spikes</span>
          <span>Sustained Cascade</span>
        </div>
        <div className="waveform-bars-track">
          {waveBars.map((bar, idx) => (
            <div
              key={idx}
              className={`wave-bar-col ${bar.isPassed ? 'active-passed' : 'dimmed'}`}
              style={{
                height: `${bar.height}px`,
                backgroundColor: bar.isPassed ? bar.color : '#e2d7cb',
              }}
            ></div>
          ))}
        </div>
      </div>

      {/* Slider Track with Incident Marker */}
      <div className="scrubber-track-container">
        <input
          type="range"
          min="0"
          max="100"
          step="1"
          value={sliderVal}
          onChange={(e) => setSliderVal(Number(e.target.value))}
          className="scrubber-range-input"
        />

        {/* Incident Start Marker Flag */}
        <div
          className="incident-start-marker"
          style={{ left: `${incidentPercent}%` }}
        >
          <div className="marker-flag">Incident Start</div>
          <div className="marker-pin"></div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="scrubber-actions-row">
        <div className="scrubber-btn-group">
          <button
            type="button"
            className={`btn-play-stream ${isPlaying ? 'playing' : ''}`}
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? '⏸ Pause Stream' : '▶ Play Stream'}
          </button>

          <button type="button" className="btn-replay-pill" onClick={jumpToIncident}>
            ⚡ Jump to Onset
          </button>

          <button type="button" className="btn-replay-pill" onClick={handleReset}>
            🔄 Full Incident
          </button>
        </div>

        <button type="button" className="link-telemetry-window" onClick={handleReset}>
          Complete Telemetry Window →
        </button>
      </div>
    </div>
  );
}
