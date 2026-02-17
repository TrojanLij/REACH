import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section>
      <h2>Not Found</h2>
      <p>The page does not exist.</p>
      <Link to="/dashboard">Go back</Link>
    </section>
  );
}
