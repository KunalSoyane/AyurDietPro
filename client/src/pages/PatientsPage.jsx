import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.patients().then((data) => setPatients(data || [])).catch(console.error);
  }, []);

  const filtered = patients.filter((p) => p.name?.toLowerCase().includes(query.toLowerCase()));

  return (
    <div>
      <div className="row spread">
        <h2>Patients</h2>
        <Link to="/patients/new" className="primary-btn">
          Add Patient
        </Link>
      </div>
      <input placeholder="Search patient" value={query} onChange={(e) => setQuery(e.target.value)} />
      <div className="card">
        {filtered.map((patient) => {
          const patientId = patient._id || patient.id;

          return (
            <div key={patientId} className="row spread line">
              <span>
                {patient.name} | {patient.vikriti}
              </span>
              <span>
                <Link to={`/patients/${patientId}`}>View</Link> |{" "}
                <Link to={`/patients/${patientId}/edit`}>Edit</Link> |{" "}
                <Link to={`/patients/${patientId}/diet`}>Create Diet</Link> |{" "}
                <button
                  className="text-btn danger"
                  onClick={async () => {
                    if (window.confirm("Are you sure you want to delete this patient?")) {
                      try {
                        await api.deletePatient(patientId);
                        setPatients((prev) => prev.filter((p) => (p._id || p.id) !== patientId));
                      } catch (err) {
                        console.error("Failed to delete patient", err);
                      }
                    }
                  }}
                >
                  Delete
                </button>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}