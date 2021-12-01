import { GET_PIZZAS } from "../types";

const getAll = (payload) => {
  return {
    type: GET_PIZZAS,
    payload,
  };
};

export { getAll };
