// Tiny fetch wrapper around the FastAPI backend (replaces axios).
async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

export const api = {
  listPizzas: () => request("/pizzas"),
  listToppings: () => request("/toppings"),
  createPizza: (pizza) => request("/pizzas", { method: "POST", body: JSON.stringify(pizza) }),
  deletePizza: (id) => request(`/pizzas/${id}`, { method: "DELETE" }),
  bakePizza: (id, seconds = 2) =>
    request(`/pizzas/${id}/bake`, { method: "POST", body: JSON.stringify({ seconds }) }),
  taskStatus: (taskId) => request(`/tasks/${taskId}`),
};
