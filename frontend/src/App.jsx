import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

// This is the "shape" of a new, empty form -- matches SalesInput in main.py
// exactly, field for field.
const initialForm = {
  order_date: "",
  ship_date: "",
  ship_mode: "Second Class",
  segment: "Consumer",
  country: "United States",
  state: "",
  postal_code: "",
  region: "South",
  category: "Furniture",
  sub_category: "Bookcases",
  quantity: 1,
  discount: 0,
};

function App() {
  // useState gives us: [currentValue, functionToChangeIt]
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Called every time any input changes -- updates just that one field,
  // keeping everything else in "form" exactly as it was.
  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault(); // stops the browser's default full-page-reload form submit
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          quantity: Number(form.quantity),
          discount: Number(form.discount),
          postal_code: Number(form.postal_code),
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail?.[0]?.msg || "Prediction failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Estimate expected order value before finalizing a sale</h1>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label>
          Order date
          <input type="date" name="order_date" value={form.order_date} onChange={handleChange} required />
        </label>

        <label>
          Ship date
          <input type="date" name="ship_date" value={form.ship_date} onChange={handleChange} required />
        </label>

        <label>
          Ship mode
          <select name="ship_mode" value={form.ship_mode} onChange={handleChange}>
            <option>First Class</option>
            <option>Second Class</option>
            <option>Standard Class</option>
            <option>Same Day</option>
          </select>
        </label>

        <label>
          Segment
          <select name="segment" value={form.segment} onChange={handleChange}>
            <option>Consumer</option>
            <option>Corporate</option>
            <option>Home Office</option>
          </select>
        </label>

        <label>
          State
          <input type="text" name="state" value={form.state} onChange={handleChange} placeholder="e.g. Kentucky" required />
        </label>

        <label>
          Postal code
          <input type="number" name="postal_code" value={form.postal_code} onChange={handleChange} required />
        </label>

        <label>
          Region
          <select name="region" value={form.region} onChange={handleChange}>
            <option>South</option>
            <option>West</option>
            <option>East</option>
            <option>Central</option>
          </select>
        </label>

        <label>
          Category
          <select name="category" value={form.category} onChange={handleChange}>
            <option>Furniture</option>
            <option>Technology</option>
            <option>Office Supplies</option>
          </select>
        </label>

        <label>
          Sub-category
          <input type="text" name="sub_category" value={form.sub_category} onChange={handleChange} placeholder="e.g. Bookcases" required />
        </label>

        <label>
          Quantity
          <input type="number" name="quantity" min="1" value={form.quantity} onChange={handleChange} required />
        </label>

        <label>
          Discount (0 to 1)
          <input type="number" name="discount" min="0" max="1" step="0.1" value={form.discount} onChange={handleChange} required />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Predict sales"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: 20, padding: 16, background: "#e6f4ea", borderRadius: 8 }}>
          <strong>Predicted sales: ${result.predicted_sales}</strong>
          <div style={{ fontSize: 13, color: "#555" }}>Prediction ID: {result.prediction_id}</div>
        </div>
      )}

      {error && (
        <div style={{ marginTop: 20, padding: 16, background: "#fdecea", borderRadius: 8, color: "#a33" }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default App;