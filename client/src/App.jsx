import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";

function useAsync(loader) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const reload = useCallback(() => {
    setState((s) => ({ ...s, loading: true }));
    loader()
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }));
  }, [loader]);
  useEffect(reload, [reload]);
  return { ...state, reload };
}

function NewPizzaForm({ toppings, onCreated }) {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState([]);
  const [error, setError] = useState(null);

  const toggle = (topping) =>
    setSelected((s) => (s.includes(topping) ? s.filter((t) => t !== topping) : [...s, topping]));

  async function submit(event) {
    event.preventDefault();
    try {
      await api.createPizza({ name, toppings: selected });
      setName("");
      setSelected([]);
      setError(null);
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>New pizza</h2>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" required />
      <div className="chips">
        {toppings.map((t) => (
          <label key={t.id} className={selected.includes(t.name) ? "chip on" : "chip"}>
            <input type="checkbox" checked={selected.includes(t.name)} onChange={() => toggle(t.name)} />
            {t.name}
          </label>
        ))}
      </div>
      <button type="submit">Create</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function BakeButton({ pizza }) {
  const [status, setStatus] = useState(null);

  async function bake() {
    setStatus("baking…");
    const { task_id } = await api.bakePizza(pizza.id, 2);
    const poll = async () => {
      const task = await api.taskStatus(task_id);
      if (task.status === "pending") setTimeout(poll, 500);
      else setStatus(task.status === "success" ? task.result : `failed: ${task.error}`);
    };
    poll();
  }

  return (
    <span>
      <button onClick={bake} disabled={status === "baking…"}>
        Bake
      </button>{" "}
      {status && <small>{status}</small>}
    </span>
  );
}

export default function App() {
  const pizzas = useAsync(api.listPizzas);
  const toppings = useAsync(api.listToppings);

  async function remove(id) {
    await api.deletePizza(id);
    pizzas.reload();
  }

  return (
    <main>
      <h1>Pizzas</h1>
      {pizzas.loading && <p>Loading…</p>}
      {pizzas.error && <p className="error">Could not reach the API: {pizzas.error.message}</p>}
      {pizzas.data && (
        <ul className="pizzas">
          {pizzas.data.items.map((p) => (
            <li key={p.id} className="card">
              <strong>{p.name}</strong>
              {p.chef && <span className="muted"> by {p.chef.name}</span>}
              <div className="muted">{p.toppings.map((t) => t.name).join(", ") || "no toppings"}</div>
              <BakeButton pizza={p} />{" "}
              <button className="danger" onClick={() => remove(p.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
      {toppings.data && <NewPizzaForm toppings={toppings.data} onCreated={pizzas.reload} />}
    </main>
  );
}
