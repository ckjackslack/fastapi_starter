import axios from "axios";

const Api = {
  getAll: () => axios.get("pizza"),
};

export default Api;
