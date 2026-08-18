export default function ReasoningModal({ open, onClose, items }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Why This Diet?</h3>
        <ul className="reason-list">
          {items.map((item, idx) => (
            <li key={item.id || idx}>
              <strong>{item.food.name}</strong>: {item.reasoning || "No explanation."}
            </li>
          ))}
        </ul>
        <button className="primary-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

