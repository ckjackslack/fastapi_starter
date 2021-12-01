import axios from "axios";

const Api = {
  getAll: () => axios.get("pizzas"),
};

export default Api;
