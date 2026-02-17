import { useState } from "react";
import { Outlet } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBars, faXmark } from "@fortawesome/free-solid-svg-icons";
import { Heartbeat } from "../components/Heartbeat";
import { NavBar } from "../components/NavBar";

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(true);

  return (
    <div className="app-shell">
      <button
        type="button"
        className={`menu-toggle${menuOpen ? " open" : ""}`}
        onClick={() => setMenuOpen((prev) => !prev)}
        aria-expanded={menuOpen}
        aria-controls="reach-side-menu"
      >
        <FontAwesomeIcon icon={menuOpen ? faXmark : faBars} />
      </button>
      <NavBar isOpen={menuOpen} onNavigate={() => setMenuOpen(false)} />
      <div className="content-shell">
        <main className="page-content">
          <Outlet />
        </main>
      </div>
      <Heartbeat />
    </div>
  );
}
