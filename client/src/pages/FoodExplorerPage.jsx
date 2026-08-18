import { useEffect, useState } from "react";
import { api } from "../api";

export default function FoodExplorerPage() {
  const [foods, setFoods] = useState([]);
  const [categories, setCategories] = useState([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");

  useEffect(() => {
    api.foodCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    api.foods({ q: query, category: category || undefined }).then(setFoods).catch(() => setFoods([]));
  }, [query, category]);

  return (
    <div>
      <h2>Food Explorer</h2>
      <div className="row">
        <input placeholder="Search foods" value={query} onChange={(e) => setQuery(e.target.value)} />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </div>
      <div className="food-grid">
        {foods.map((food) => (
          <div className="card" key={food._id || food.id}>
            <h4>
              {food.name} {food.name_hindi ? `(${food.name_hindi})` : ""}
            </h4>
            <p>{food.category}</p>
            <p>
              {food.calories} kcal | P {food.protein_g} | C {food.carbs_g} | F {food.fat_g}
            </p>
            <p>
              Rasa: {food.rasa || "-"} | Virya: {food.virya || "-"}
            </p>
            <p>
              V {food.vata_effect <= 0 ? "✓" : "✗"} P {food.pitta_effect <= 0 ? "✓" : "✗"} K{" "}
              {food.kapha_effect <= 0 ? "✓" : "✗"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

