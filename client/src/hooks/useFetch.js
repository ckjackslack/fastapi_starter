import { useState, useEffect } from "react";

const useFetch = (fetchData) => {
  const [state, setState] = useState();

  useEffect(() => {
    callFetch();
  }, []);

  const callFetch = async () => {
    for await (const item of fetchData) {
      const response = await item.method;
      setState({
        ...state,
        [item.state]: response.data,
      });
    }
  };

  return {
    state,
  };
};

export default useFetch;
