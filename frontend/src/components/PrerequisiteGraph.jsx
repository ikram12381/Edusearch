import { useMemo, useState } from "react";

// Visualisation interactive (SVG, sans dépendance externe) de la chaîne de
// prérequis d'un cours. Remplace l'ancien rendu textuel (<ul><li>...) par un
// graphe orienté animé : le cours recherché en haut, puis chaque niveau de
// prérequis en dessous, relié par des arêtes courbes. Quand un niveau propose
// plusieurs alternatives ("ou"), elles sont affichées côte à côte ; seule la
// première est développée au niveau suivant (c'est la branche que
// backend/services/graph_service.get_prerequisite_chain() choisit de suivre).
// Cliquer sur un nœud relance une recherche sur ce cours : la navigation dans
// le graphe devient elle-même une nouvelle requête hybride.

const NODE_W = 172;
const NODE_H = 60;
const V_GAP = 88;
const H_GAP = 26;
const PAD = 36;

export default function PrerequisiteGraph({ rootTitle, chain, onSelectCourse }) {
  const layout = useMemo(() => buildLayout(rootTitle, chain), [rootTitle, chain]);
  const [hovered, setHovered] = useState(null);

  if (!chain || chain.length === 0) {
    return (
      <div className="prereq-empty">
        <span className="prereq-empty-dot" />
        Aucun prérequis identifié dans le graphe — ce cours est directement accessible.
      </div>
    );
  }

  return (
    <div className="prereq-graph-wrap">
      <svg
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        className="prereq-graph"
        role="img"
        aria-label={`Chaîne de prérequis pour ${rootTitle}`}
      >
        <defs>
          <filter id="nodeGlow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {layout.edges.map((e, i) => (
          <g
            key={i}
            className={
              "prereq-edge" +
              (hovered && (hovered === e.from || hovered === e.to) ? " active" : "")
            }
          >
            <path d={edgePath(e)} className="prereq-edge-path" />
            <path d={edgePath(e)} className="prereq-edge-flow" />
            {e.label && (
              <text x={(e.x1 + e.x2) / 2} y={(e.y1 + e.y2) / 2 - 6} className="prereq-edge-label">
                {e.label}
              </text>
            )}
          </g>
        ))}

        {layout.nodes.map((n, i) => (
          <g
            key={n.id}
            transform={`translate(${n.x}, ${n.y})`}
            className={
              "prereq-node " +
              n.type +
              (hovered === n.id ? " hovered" : "") +
              (n.docId ? " clickable" : "")
            }
            style={{ animationDelay: `${i * 60}ms` }}
            onMouseEnter={() => setHovered(n.id)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => n.docId && onSelectCourse && onSelectCourse(n.docId, n.label)}
          >
            <rect
              width={NODE_W}
              height={NODE_H}
              rx={14}
              className="prereq-node-rect"
              filter={n.type === "root" ? "url(#nodeGlow)" : undefined}
            />
            <text x={NODE_W / 2} y={NODE_H / 2 - 5} className="prereq-node-title">
              {truncate(n.label, 24)}
            </text>
            <text x={NODE_W / 2} y={NODE_H / 2 + 15} className="prereq-node-sub">
              {n.type === "root" ? "cours recherché" : n.alt ? "alternative" : "prérequis"}
            </text>
          </g>
        ))}
      </svg>
      <p className="prereq-hint">
        Survolez pour suivre une branche, cliquez sur un prérequis pour l'explorer à son tour.
      </p>
    </div>
  );
}

function truncate(s, n) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function buildLayout(rootTitle, chain) {
  const maxCols = Math.max(1, ...chain.map((lvl) => lvl.length));
  const width = Math.max(340, maxCols * (NODE_W + H_GAP) + PAD * 2 - H_GAP);
  const rows = chain.length + 1;
  const height = rows * (NODE_H + V_GAP) - V_GAP + PAD * 2;

  const nodes = [];
  const edges = [];

  const rootX = width / 2 - NODE_W / 2;
  const rootY = PAD;
  nodes.push({ id: "root", label: rootTitle, x: rootX, y: rootY, type: "root" });

  let prevId = "root";
  let prevX = rootX + NODE_W / 2;
  let prevY = rootY + NODE_H;

  chain.forEach((level, levelIdx) => {
    const rowY = PAD + (levelIdx + 1) * (NODE_H + V_GAP);
    const rowWidth = level.length * NODE_W + (level.length - 1) * H_GAP;
    const startX = width / 2 - rowWidth / 2;

    level.forEach((step, colIdx) => {
      const x = startX + colIdx * (NODE_W + H_GAP);
      const id = `${levelIdx}-${colIdx}-${step.doc_id}`;
      nodes.push({
        id,
        docId: step.doc_id,
        label: step.titre,
        x,
        y: rowY,
        type: "prereq",
        alt: colIdx > 0,
      });
      edges.push({
        from: prevId,
        to: id,
        x1: prevX,
        y1: prevY,
        x2: x + NODE_W / 2,
        y2: rowY,
        label: colIdx > 0 ? "ou" : undefined,
      });
    });

    const current = level[0];
    prevId = `${levelIdx}-0-${current.doc_id}`;
    prevX = startX + NODE_W / 2;
    prevY = rowY + NODE_H;
  });

  return { nodes, edges, width, height };
}

function edgePath({ x1, y1, x2, y2 }) {
  const midY = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
}
