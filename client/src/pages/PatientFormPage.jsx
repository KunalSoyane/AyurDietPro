import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

const initial = {
  name: "",
  phone: "",
  age: "",
  gender: "Female",
  weight_kg: "",
  height_cm: "",
  activity_level: "light",
  vikriti: "Vata",
  prakriti: "Vata",
  conditions: [],
  appetite: "",
  digestion_strength: "",
  food_preference: "veg",
};

export default function PatientFormPage() {
  const { id } = useParams();
  const [form, setForm] = useState(initial);
  const [conditionsText, setConditionsText] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const isEdit = !!id && id !== "undefined";

  useEffect(() => {
    if (isEdit) {
      setLoading(true);
      api
        .patient(id)
        .then((p) => {
          setForm(p);
          setConditionsText((p.conditions || []).join(", "));
        })
        .catch(() => {
          navigate("/patients");
        })
        .finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const set = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const submit = async (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      conditions: conditionsText
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
    };

    try {
      if (isEdit) {
        await api.updatePatient(id, payload);
        navigate(`/patients/${id}`);
      } else {
        const created = await api.createPatient(payload);
        const createdId = created?._id || created?.id;

        if (createdId) {
          navigate(`/patients/${createdId}/diet`);
        } else {
          console.error("Created patient missing ID:", created);
          navigate("/patients");
        }
      }
    } catch (err) {
      console.error("Failed to save patient", err);
    }
  };

  if (loading) return <div className="container">Loading patient data...</div>;

  return (
    <div className="container">
      <div className="card">
        <h1 style={{ marginBottom: "0.5rem" }}>{isEdit ? "Update Patient Profile" : "New Patient Intake"}</h1>
        <p className="muted" style={{ marginBottom: "2rem" }}>
          {isEdit ? "Refine clinical details and medical history." : "Establish clinical profile and Ayurvedic baseline."}
        </p>

        <form onSubmit={submit} className="form-grid">
          {/* Section 1: Personal Details */}
          <section className="form-section">
            <h3>👤 Personal Information</h3>
            <div className="input-row">
              <div className="form-group">
                <label>Full Name</label>
                <input placeholder="Name" value={form.name} onChange={(e) => set("name", e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Phone Number</label>
                <input placeholder="+91 00000 00000" value={form.phone || ""} onChange={(e) => set("phone", e.target.value)} />
              </div>
            </div>
            <div className="input-row">
              <div className="form-group">
                <label>Age</label>
                <input
                  type="number"
                  placeholder="Age"
                  value={form.age}
                  onChange={(e) => set("age", e.target.value === "" ? "" : Number(e.target.value))}
                  required
                />
              </div>
              <div className="form-group">
                <label>Gender</label>
                <select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other</option>
                </select>
              </div>
            </div>
          </section>

          {/* Section 2: Vitals & Body */}
          <section className="form-section">
            <h3>⚖️ Vitals & Physical Profile</h3>
            <div className="input-row">
              <div className="form-group">
                <label>Weight (kg)</label>
                <input
                  type="number"
                  placeholder="Weight"
                  value={form.weight_kg}
                  onChange={(e) => set("weight_kg", e.target.value === "" ? "" : Number(e.target.value))}
                  required
                />
              </div>
              <div className="form-group">
                <label>Height (cm)</label>
                <input
                  type="number"
                  placeholder="Height"
                  value={form.height_cm}
                  onChange={(e) => set("height_cm", e.target.value === "" ? "" : Number(e.target.value))}
                  required
                />
              </div>
              <div className="form-group">
                <label>Activity Level</label>
                <select value={form.activity_level} onChange={(e) => set("activity_level", e.target.value)}>
                  <option value="sedentary">Sedentary</option>
                  <option value="light">Light</option>
                  <option value="moderate">Moderate</option>
                  <option value="active">Active</option>
                  <option value="very_active">Very Active</option>
                </select>
              </div>
            </div>
          </section>

          {/* Section 3: Ayurvedic Profile */}
          <section className="form-section">
            <h3>🕉️ Ayurvedic Assessment</h3>
            <div className="input-row">
              <div className="form-group">
                <label>Vikriti (Current Imbalance)</label>
                <select value={form.vikriti} onChange={(e) => set("vikriti", e.target.value)}>
                  <option>Vata</option>
                  <option>Pitta</option>
                  <option>Kapha</option>
                </select>
              </div>
              <div className="form-group">
                <label>Prakriti (Birth Constitution)</label>
                <select value={form.prakriti} onChange={(e) => set("prakriti", e.target.value)}>
                  <option>Vata</option>
                  <option>Pitta</option>
                  <option>Kapha</option>
                  <option>Vata-Pitta</option>
                  <option>Pitta-Kapha</option>
                  <option>Kapha-Vata</option>
                  <option>Sama (Tridoshic)</option>
                </select>
              </div>
            </div>
            <div className="input-row">
              <div className="form-group">
                <label>Appetite</label>
                <select value={form.appetite} onChange={(e) => set("appetite", e.target.value)}>
                  <option value="">Select Appetite</option>
                  <option>Low</option>
                  <option>Normal</option>
                  <option>High</option>
                  <option>Variable</option>
                </select>
              </div>
              <div className="form-group">
                <label>Digestion Strength</label>
                <select value={form.digestion_strength} onChange={(e) => set("digestion_strength", e.target.value)}>
                  <option value="">Select Strength</option>
                  <option>Weak</option>
                  <option>Medium</option>
                  <option>Strong</option>
                </select>
              </div>
              <div className="form-group">
                <label>Food Preference</label>
                <select value={form.food_preference} onChange={(e) => set("food_preference", e.target.value)}>
                  <option value="veg">Vegetarian</option>
                  <option value="non-veg">Non-Veg</option>
                  <option value="vegan">Vegan</option>
                </select>
              </div>
            </div>
          </section>

          {/* Section 4: Medical Details */}
          <section className="form-section">
            <h3>🏥 Medical History</h3>
            <div className="form-group">
              <label>Conditions (Comma separated)</label>
              <textarea
                style={{ background: "#111827", color: "white", padding: "10px", borderRadius: "10px" }}
                value={conditionsText}
                onChange={(e) => setConditionsText(e.target.value)}
                placeholder="Diabetes, Hypertension, Bloating..."
                rows={3}
              />
            </div>
          </section>

          <button className="primary-btn" type="submit" style={{ padding: "1rem" }}>
            {isEdit ? "Update Patient Profile" : "Create Patient & Generate Diet Plan"}
          </button>
        </form>
      </div>
    </div>
  );
}