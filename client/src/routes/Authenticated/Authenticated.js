import React from "react";
import { Route, Routes } from "react-router-dom";
import Home from "../../pages/Home";
import AuthLayout from "./AuthLayout";

const Authenticated = () => {
  return (
    <AuthLayout>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </AuthLayout>
  );
};

export default Authenticated;
