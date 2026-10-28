import React, { useState, useEffect, useRef } from 'react';

/**
 * Interactive Incident Replay Slider / Time Scrubber
 * Allows scrubbing through time from incident_start to incident_end.
 * Debounces API analysis calls and shows real-time elapsed offset (mm:ss).
 */
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

  // Debounced update to parent
  useEffect(() => {
    const timer = setTimeout(() => {
      if (sliderVal === 100) {
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
      }, 600);
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

  return (
    <div className="replay-slider-card">
      <div className="replay-header">
        <div className="replay-title-wrap">
          <span className="replay-live-dot"></span>
          <div>
            <h4 className="replay-title">Incident Replay Scrubber</h4>
            <span className="replay-subtitle">
              Simulate real-time causal attribution as telemetry streams in
            </span>
          </div>
        </div>

        <div className="replay-meta-badges">
          <span className="replay-chip">
            Offset: <strong>{elapsedLabel}</strong>
          </span>
          <span className="replay-chip replay-time">
            {new Date(currentTsMs).toLocaleTimeString()} UTC
          </span>
          {sliderVal < 100 && (
            <span className="replay-badge-active">
              Replay Active (as_of)
            </span>
          )}
        </div>
      </div>

      <div className="slider-track-wrap">
        <input
          type="range"
          min="0"
          max="100"
          value={sliderVal}
          onChange={(e) => {
            setIsPlaying(false);
            setSliderVal(Number(e.target.value));
          }}
          className="time-range-slider"
          disabled={loading}
        />

        {/* Incident Start Marker */}
        <div
          className="incident-marker"
          style={{ left: `${incidentPercent}%` }}
          title={`Incident Injected at: ${incidentStartIso}`}
        >
          <div className="marker-pin"></div>
          <span className="marker-label">Incident Start</span>
        </div>
      </div>

      <div className="replay-controls">
        <div className="btn-group">
          <button
            className={`btn-control ${isPlaying ? 'active' : ''}`}
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause replay' : 'Play replay simulation'}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play Stream'}
          </button>
          <button
            className="btn-control"
            onClick={jumpToIncident}
            title="Jump to injected incident fault start"
          >
            ⚡ Jump to Onset
          </button>
          <button
            className="btn-control"
            onClick={handleReset}
            title="View full completed scenario telemetry"
          >
            ↺ Full Incident
          </button>
        </div>

        <div className="replay-status-indicator">
          {loading ? (
            <span className="loading-spinner-inline">Re-correlating causal graph...</span>
          ) : sliderVal === 100 ? (
            <span className="status-complete">Complete Telemetry Window</span>
          ) : (
            <span className="status-window">Partial Telemetry Window ({sliderVal}%)</span>
          )}
        </div>
      </div>
    </div>
  );
}
