import { GET_PIZZAS, SET_MESSAGE } from "../types";

const initialStat = {
  pizzas: [],
  message: null
}

const rootReducer = function (state = initialStat, action) {
  switch (action.type) {
    case GET_PIZZAS:
      return {
        ...state,
        pizzas: action.payload
      };
    case SET_MESSAGE:
      return {
        ...state,
        message: action.payload
      }
    default:
      return state;
  }
};

export default rootReducer;
