import { NavLink } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faGauge,
  faPlug,
  faTerminal,
  faFlask,
  faWandMagicSparkles,
  faNetworkWired,
  faRoute,
  faList,
  faPlus
} from "@fortawesome/free-solid-svg-icons";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: faGauge },
  { to: "/plugins", label: "Plugins", icon: faPlug },
  { to: "/logs", label: "Logs", icon: faTerminal },
  { to: "/playground", label: "Playground", icon: faFlask },
  { to: "/rules", label: "Rules", icon: faWandMagicSparkles },
  { to: "/dns", label: "DNS", icon: faNetworkWired }
];

const routeSubmenu = [
  { to: "/routes", label: "List", icon: faList },
  { to: "/routes/new", label: "Add", icon: faPlus }
];

export function NavBar({ isOpen, onNavigate }) {
  return (
    <aside id="reach-side-menu" className={`site-nav${isOpen ? " open" : ""}`}>
      <h1>REACH UI</h1>
      <nav>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => (isActive ? "active" : "")}
            onClick={onNavigate}
          >
            <FontAwesomeIcon icon={link.icon} />
            <span>{link.label}</span>
          </NavLink>
        ))}

        <div className="submenu-group">
          <div className="submenu-title">
            <FontAwesomeIcon icon={faRoute} />
            <span>Routes</span>
          </div>
          <div className="submenu-links">
            {routeSubmenu.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => (isActive ? "active" : "")}
                onClick={onNavigate}
              >
                <FontAwesomeIcon icon={link.icon} />
                <span>{link.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
    </aside>
  );
}
