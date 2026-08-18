export default function FoodSearchDropdown({ foods, value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {foods.map((food) => {
        const foodId = food._id || food.id;
        return (
          <option key={foodId} value={foodId}>
            {food.name} ({food.category})
          </option>
        );
      })}
    </select>
  );
}

