import React, { useEffect } from "react";
import { useSelector } from 'react-redux';
import { getAll } from "./actions";

const App = () => {
  const pizzas = useSelector((state) => state.pizzas)
  useEffect(() => {
    getAll();
  }, []);
  return (
    pizzas.map(item => <h3 key={item.id}>{item.name}</h3>)
  );
}

export default App;
