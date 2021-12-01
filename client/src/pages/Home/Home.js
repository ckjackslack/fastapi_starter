import React from "react";
import { Spin } from "antd";
import { Skeleton } from "antd";
import Api from "../../api";
import useFetch from "../../hooks/useFetch";

const fetchData = [
  {
    method: Api.getAll(),
    state: "pizzas",
  },
];

const Home = () => {
  const { state } = useFetch(fetchData);

  return !state ? (
    <Spin size="large" />
  ) : (
    <>
      {state.pizzas ? (
        state.pizzas.map((item) => <h1 key={item.id}>{item.name}</h1>)
      ) : (
        <Skeleton />
      )}
    </>
  );
};

export default Home;
