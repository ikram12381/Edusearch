import { useEffect, useState } from "react";

const STEPS = [
  "Understanding your query...",
  "Searching Elasticsearch (lexical)...",
  "Analyzing semantic similarity...",
  "Enriching with Knowledge Graph...",
  "Ranking results...",
];

// Avance automatiquement dans les étapes pendant que la vraie requête est en
// vol, sans jamais prétendre être terminé avant que `active` ne redevienne
// false (c'est le parent qui contrôle la fin réelle de la recherche).
export default function LoadingSteps({ active }) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!active) {
      setCurrent(0);
      return;
    }
    const interval = setInterval(() => {
      setCurrent((c) => Math.min(c + 1, STEPS.length - 1));
    }, 420);
    return () => clearInterval(interval);
  }, [active]);

  if (!active) return null;

  return (
    <div className="loading-steps fade-in">
      {STEPS.map((label, i) => (
        <div key={label} className={`loading-step ${i === current ? "active" : i < current ? "done" : ""}`}>
          <span className="step-dot" />
          {label}
        </div>
      ))}
    </div>
  );
}
