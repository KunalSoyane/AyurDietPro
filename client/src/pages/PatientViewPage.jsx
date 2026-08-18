import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BASE_URL } from "../api";

export default function PatientViewPage() {
  const { id } = useParams();
  const [plan, setPlan] = useState(null);
  const [failed, setFailed] = useState(false);
  const [selectedDay, setSelectedDay] = useState(1);

  useEffect(() => {
    let cancelled = false;

    fetch(`${BASE_URL}/public/plan/${id}`)
      .then((res) => (res.ok ? res.text() : Promise.reject()))
      .then((text) => (text.trim() ? JSON.parse(text) : null))
      .then((data) => {
        if (cancelled) return;
        setPlan(data);
        setFailed(!data);
      })
      .catch(() => {
        if (cancelled) return;
        setPlan(null);
        setFailed(true);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const days = useMemo(() => {
    if (!plan || !Array.isArray(plan.items)) return [];
    return [...new Set(plan.items.map((item) => item.day_of_week))].sort((a, b) => a - b);
  }, [plan]);

  const dayItems = useMemo(() => {
    if (!plan || !Array.isArray(plan.items)) return [];
    return plan.items.filter((item) => item.day_of_week === selectedDay);
  }, [plan, selectedDay]);

  if (failed) {
    return (
      <div className="container card" style={{ textAlign: "center", padding: "2rem" }}>
        <h2>Plan Not Available</h2>
        <p className="muted">This diet plan could not be found. It may have been removed.</p>
      </div>
    );
  }

  if (!plan) {
    return <div className="container card">Loading plan...</div>;
  }

  return (
    <div className="container card">
      <h2>Daily Diet Schedule</h2>

      {days.length > 1 && (
        <div className="day-switcher">
          {days.map((day) => (
            <button
              key={day}
              className={`day-btn ${selectedDay === day ? "active" : ""}`}
              onClick={() => setSelectedDay(day)}
            >
              Day {day}
            </button>
          ))}
        </div>
      )}

      {dayItems.map((item, idx) => (
        <div key={item._id || item.id || idx} className="line">
          <strong>{item.meal_slot}</strong>: {item.food?.name || "Unknown food"} - {item.portion_g} g
        </div>
      ))}
      {dayItems.length === 0 && <p className="muted">No meals recorded for this day.</p>}

      <p className="muted">
        Total: {plan.total_calories} kcal | P {plan.total_protein} | C {plan.total_carbs} | F {plan.total_fat}
      </p>
    </div>
  );
}
