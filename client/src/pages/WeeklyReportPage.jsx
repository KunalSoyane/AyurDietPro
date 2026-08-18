import { useEffect, useState } from "react";
import { api } from "../api";

export default function WeeklyReportPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getWeeklyReport();
        setData(res);
      } catch (e) {
        console.error("Failed to load report", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="container">Loading report...</div>;
  if (!data) return <div className="container">Error loading report.</div>;

  return (
    <div className="container">
      <header style={{ marginBottom: "2rem" }}>
        <h1>Weekly Insights</h1>
        <p className="muted">Performance summary for the last 7 days.</p>
      </header>

      <div className="grid3" style={{ marginBottom: "2rem" }}>
        <div className="stat-card">
          <span className="stat-label">New Patients</span>
          <span className="stat-value">{data.stats.new_patients}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Plans Generated</span>
          <span className="stat-value">{data.stats.new_plans}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Top Vikriti</span>
          <span className="stat-value" style={{ fontSize: "1.5rem" }}>
            {Object.keys(data.stats.vikriti_breakdown).length > 0
              ? Object.entries(data.stats.vikriti_breakdown).sort((a, b) => b[1] - a[1])[0][0]
              : "N/A"}
          </span>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: "1rem" }}>Recent Patients</h2>
        <ul className="glass-list">
          {data.recent_patients.length === 0 && <p className="muted">No recent activity.</p>}
          {data.recent_patients.map((p) => (
            <li key={p.id} className="glass-item">
              <div>
                <strong>{p.name}</strong>
                <div className="muted" style={{ fontSize: "0.8rem" }}>
                  Added on {p.created_at ? new Date(p.created_at).toLocaleDateString() : "—"}
                </div>
              </div>
              <span className={`pill ${(p.vikriti || "vata").toLowerCase()}`}>{p.vikriti || "Unknown"}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: "1rem" }}>Vikriti Distribution</h2>
        <div className="form-grid">
          {Object.entries(data.stats.vikriti_breakdown).map(([v, count]) => (
            <div key={v} className="spread line">
              <span>{v}</span>
              <span className="pill" style={{ background: "rgba(255,255,255,0.1)" }}>
                {count} patients
              </span>
            </div>
          ))}
          {Object.keys(data.stats.vikriti_breakdown).length === 0 && (
            <p className="muted">No data available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
