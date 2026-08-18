import React, { useState, useEffect } from "react";
import { api } from "./api";

export default function GenerateDietPlan() {
  const [patients, setPatients] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [patientsData, templatesData] = await Promise.all([
          api.patients(),
          api.templates(),
        ]);
        setPatients(patientsData);
        setTemplates(templatesData);
      } catch (err) {
        setError("Failed to load patients or templates.");
      }
    }
    loadData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Prevent submitting null/empty IDs to FastAPI
    if (!selectedPatientId || !selectedTemplateId) {
      setError("Please select both a patient and a template.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        patient_id: String(selectedPatientId),
        template_id: String(selectedTemplateId),
      };

      const result = await api.generatePlan(payload);
      alert("Diet Plan generated successfully!");
      console.log("Generated Plan:", result);
    } catch (err) {
      setError(err.message || "Failed to generate diet plan.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-lg mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Generate Ayurvedic Diet Plan</h2>

      {error && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Select Patient</label>
          <select
            className="w-full p-2 border rounded mt-1"
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
          >
            <option value="">-- Choose Patient --</option>
            {patients.map((p) => (
              <option key={p._id || p.id} value={p._id || p.id}>
                {p.name} ({p.prakriti || "General"})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium">Select Diet Template</label>
          <select
            className="w-full p-2 border rounded mt-1"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            <option value="">-- Choose Template --</option>
            {templates.map((t) => (
              <option key={t._id || t.id} value={t._id || t.id}>
                {t.title || t.name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate Diet Plan"}
        </button>
      </form>
    </div>
  );
}