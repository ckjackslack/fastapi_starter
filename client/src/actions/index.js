import Api from "../api";
import { GET_PIZZAS } from "../store/types";
import store from "../store";

const getAll = async () => {
  await Api.getAll()
    .then(response => {
      store.dispatch({
        type: GET_PIZZAS,
        payload: response.data
      });
    })
    .catch(error => {
      console.log(error)
      store.dispatch({
        type: GET_PIZZAS,
        payload: "error"
      });
    });
}

export {
  getAll
};
