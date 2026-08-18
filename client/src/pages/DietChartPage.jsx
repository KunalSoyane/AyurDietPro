import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import FoodSearchDropdown from "../components/FoodSearchDropdown";
import MealCard from "../components/MealCard";
import NutritionBar from "../components/NutritionBar";
import ReasoningModal from "../components/ReasoningModal";
import { exportDietPlanPdf } from "../utils/pdfExport";

function TargetCaloriesInput({ value, onCommit }) {
  const [draft, setDraft] = useState(value ?? "");

  useEffect(() => {
    setDraft(value ?? "");
  }, [value]);

  const commit = () => {
    const parsed = Number(draft);
    if (draft !== "" && Number.isFinite(parsed) && parsed > 0 && parsed !== value) {
      onCommit(parsed);
    } else {
      setDraft(value ?? "");
    }
  };

  return (
    <input
      type="number"
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          commit();
        }
      }}
      style={{ width: "100px", padding: "4px 8px" }}
    />
  );
}

export default function DietChartPage() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [templateId, setTemplateId] = useState("");
  const [plan, setPlan] = useState(null);
  const [foods, setFoods] = useState([]);
  const [selectedDay, setSelectedDay] = useState(1);
  const [openReasoning, setOpenReasoning] = useState(false);

  useEffect(() => {
    if (!id || id === "undefined") return;

    api.patient(id).then(setPatient).catch(console.error);
    
    api.templates().then((t) => {
      setTemplates(t || []);
      if (t && t.length > 0) {
        const firstId = t[0]._id || t[0].id;
        setTemplateId(String(firstId));
      }
    }).catch(console.error);

    api.foods().then(setFoods).catch(console.error);
    
    api.patientPlans(id).then((plans) => {
      if (plans && plans.length > 0) {
        setPlan(plans[0]); // Load the most recent plan
      }
    }).catch(console.error);
  }, [id]);

  if (!id || id === "undefined") {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
          <h2>Invalid Patient Selected</h2>
          <p className="muted" style={{ margin: "1rem 0" }}>Please select a valid patient from the patients directory.</p>
          <Link to="/patients" className="primary-btn">
            Back to Patients
          </Link>
        </div>
      </div>
    );
  }

  const updateItem = async (item, foodId, portionG) => {
    const planId = plan?._id || plan?.id;
    const itemId = item?._id || item?.id;
    if (!planId || itemId === undefined || itemId === null) return;

    try {
      const updated = await api.updatePlan(planId, {
        items: [{ id: String(itemId), food_id: String(foodId || item.food_id), portion_g: portionG || item.portion_g }],
      });
      setPlan(updated);
    } catch (err) {
      console.error("Failed to update meal item", err);
    }
  };

  const updateTargets = async (targets) => {
    const planId = plan?._id || plan?.id;
    if (!planId) return;

    try {
      const updated = await api.updatePlan(planId, targets);
      setPlan(updated);
    } catch (err) {
      console.error("Failed to update targets", err);
    }
  };

  const generate = async () => {
    if (!id || !templateId) return;

    try {
      const generated = await api.generatePlan({
        patient_id: String(id),
        template_id: String(templateId),
      });
      setPlan(generated);
    } catch (err) {
      console.error("Failed to generate plan", err);
    }
  };

  const dayItems = useMemo(() => {
    if (!plan || !plan.items) return [];
    return plan.items.filter((i) => i.day_of_week === selectedDay);
  }, [plan, selectedDay]);

  const currentPlanId = plan?._id || plan?.id;

  return (
    <div className="container">
      <div className="card">
        <div className="spread">
          <div>
            <h1>Diet Chart Builder</h1>
            <p className="muted">Craft a balanced, clinical-grade plan for {patient?.name || "Patient"}.</p>
          </div>
          <div className="row">
            {plan && patient && (
              <button className="primary-btn" onClick={() => exportDietPlanPdf(patient, plan)}>
                PDF Export
              </button>
            )}
            {plan && (
              <button className="ghost-btn" onClick={() => setOpenReasoning(true)}>
                Ayur-Logic Reasoning
              </button>
            )}
          </div>
        </div>

        <div className="row" style={{ marginTop: "1rem" }}>
          <select value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
            {templates.map((template) => {
              const tId = template._id || template.id;
              return (
                <option key={tId} value={tId}>
                  Template: {template.name || template.title}
                </option>
              );
            })}
          </select>
          <button className="primary-btn" onClick={generate} disabled={!templateId}>
            {plan ? "Re-Generate Plan" : "Generate Initial Plan"}
          </button>
        </div>
      </div>

      {plan && (
        <>
          <div className="day-switcher">
            {[1, 2, 3, 4, 5, 6, 7].map((day) => (
              <button
                key={day}
                className={`day-btn ${selectedDay === day ? "active" : ""}`}
                onClick={() => setSelectedDay(day)}
              >
                Day {day}
              </button>
            ))}
          </div>

          <NutritionBar plan={plan} />

          <div className="card">
            <div className="spread" style={{ marginBottom: "1rem" }}>
              <h2>Meals - Day {selectedDay}</h2>
              <div className="row">
                <div className="form-group">
                  <label style={{ fontSize: "0.7rem" }}>TARGET CALORIES</label>
                  <TargetCaloriesInput
                    value={plan.target_calories}
                    onCommit={(n) => updateTargets({ target_calories: n })}
                  />
                </div>
              </div>
            </div>

            {dayItems.length === 0 && (
              <div className="muted" style={{ padding: "2rem", textAlign: "center" }}>
                No items generated for this day. Use a weekly template or add items manually.
              </div>
            )}

            <div className="form-grid">
              {dayItems.map((item) => {
                const itemId = item._id || item.id;
                return (
                  <MealCard
                    key={itemId}
                    item={item}
                    onPortionChange={(newPortion) => updateItem(item, null, newPortion)}
                    actions={
                      <FoodSearchDropdown
                        foods={foods}
                        value={item.food_id}
                        onChange={(foodId) => updateItem(item, foodId, null)}
                      />
                    }
                  />
                );
              })}
            </div>
          </div>

          <div style={{ marginTop: "2rem", display: "flex", justifyContent: "center" }}>
            <Link className="primary-btn" to={`/plan/${currentPlanId}/view`} style={{ padding: "12px 32px" }}>
              Launch Interactive Patient View
            </Link>
          </div>
        </>
      )}
      <ReasoningModal open={openReasoning} onClose={() => setOpenReasoning(false)} items={plan?.items || []} />
    </div>
  );
}