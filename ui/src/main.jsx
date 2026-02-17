import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AppRouter } from "./routes/AppRouter";
import { ApiConfigProvider } from "./state/ApiConfigContext";
import "@xyflow/react/dist/style.css";
import "./styles/base.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ApiConfigProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </ApiConfigProvider>
  </React.StrictMode>
);
