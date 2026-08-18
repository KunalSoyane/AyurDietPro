import { useEffect, useState } from "react";
import ConflictBadge from "./ConflictBadge";

export default function MealCard({ item, onPortionChange, actions }) {
  const [portionDraft, setPortionDraft] = useState(item.portion_g);

  useEffect(() => {
    setPortionDraft(item.portion_g);
  }, [item.portion_g]);

  const commitPortion = () => {
    const parsed = Number(portionDraft);
    if (portionDraft !== "" && Number.isFinite(parsed) && parsed > 0 && parsed !== item.portion_g) {
      onPortionChange(parsed);
    } else {
      setPortionDraft(item.portion_g);
    }
  };

  const getDoshaIcon = (effect) => {
    if (effect > 0) return "⬆️";
    if (effect < 0) return "⬇️";
    return "•";
  };

  return (
    <div className="meal-row card" style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr 1fr" }}>
      <div>
        <strong style={{ color: "var(--accent)" }}>{item.meal_slot}</strong>
        <div style={{ fontSize: "1.1rem", fontWeight: "600" }}>{item.food.name}</div>
        <div className="row" style={{ marginTop: "0.5rem" }}>
          {item.food.rasa && <span className="dosha-tag">👅 {item.food.rasa}</span>}
          {item.food.virya && <span className="dosha-tag">🌡️ {item.food.virya}</span>}
          {item.food.vipaka && <span className="dosha-tag">♻️ {item.food.vipaka}</span>}
        </div>
      </div>

      <div className="form-group">
        <label>Portion (g)</label>
        <input
          type="number"
          value={portionDraft}
          onChange={(e) => setPortionDraft(e.target.value)}
          onBlur={commitPortion}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              commitPortion();
            }
          }}
          style={{ width: "80px" }}
        />
      </div>

      <div>
        <div className="muted" style={{ fontSize: "0.7rem" }}>DOSHA EFFECT</div>
        <div style={{ fontSize: "0.8rem" }}>
          V: {getDoshaIcon(item.food.vata_effect)} | 
          P: {getDoshaIcon(item.food.pitta_effect)} | 
          K: {getDoshaIcon(item.food.kapha_effect)}
        </div>
      </div>

      <div>
        <div className="muted" style={{ fontSize: "0.7rem" }}>REASONING</div>
        {item.is_conflict ? <ConflictBadge reason={item.reasoning} /> : <span className="success" style={{ fontSize: "0.8rem" }}>Compatible</span>}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {actions}
      </div>
    </div>
  );
}

