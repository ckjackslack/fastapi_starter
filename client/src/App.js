import React, { useEffect } from "react";
import { useSelector, useDispatch } from 'react-redux';
import { getAll } from "./store/actions";
import Api from "./api";

const App = () => {
  const dispatch = useDispatch();
  const pizzas = useSelector((state) => state.pizzas)
  useEffect(() => {
    getPizzas();
  }, []);

  const getPizzas = async () => {
    try {
      const response =  await Api.getAll();
      dispatch(getAll(response.data));
    } catch (err) {
      console.log(err);
    }
  }

  return (
    pizzas && pizzas.map(item => <h3 key={item.id}>{item.name}</h3>)
  );
}

export default App;
