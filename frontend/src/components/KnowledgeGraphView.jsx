import { useEffect, useRef } from "react";
import * as d3 from "d3";

// Visualisation interactive du graphe de domaines : nœuds = domaines de
// l'ontologie (taille ~ nombre de cours), arêtes = relations :sousDomaineDe
// directes (telles que déclarées, cf. backend/routers/graph.py). Force-directed
// layout D3, avec zoom/pan, drag, et sélection d'un nœud (callback vers le
// panneau latéral de détail dans KnowledgeGraphPage).

export default function KnowledgeGraphView({ nodes, edges, selectedId, onSelect }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!nodes.length) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [0, 0, width, height]);
    svg.selectAll("*").remove();

    const rootGroup = svg.append("g");

    svg.call(
      d3.zoom()
        .scaleExtent([0.4, 2.5])
        .on("zoom", (event) => rootGroup.attr("transform", event.transform))
    );

    const nodesCopy = nodes.map((n) => ({ ...n }));
    const linksCopy = edges.map((e) => ({ source: e.source, target: e.target }));

    const radius = (d) => 16 + Math.min(20, Math.sqrt(d.nb_cours || 1) * 5);
    const colorScale = d3.scaleOrdinal(d3.schemeSet2);

    const simulation = d3.forceSimulation(nodesCopy)
      .force("link", d3.forceLink(linksCopy).id((d) => d.id).distance(90).strength(0.7))
      .force("charge", d3.forceManyBody().strength(-260))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius((d) => radius(d) + 14));

    const link = rootGroup.append("g")
      .selectAll("line")
      .data(linksCopy)
      .join("line")
      .attr("class", "domain-link");

    const node = rootGroup.append("g")
      .selectAll("g")
      .data(nodesCopy)
      .join("g")
      .attr("class", (d) => `domain-node ${d.id === selectedId ? "selected" : ""}`)
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.25).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
      )
      .on("click", (_, d) => onSelect?.(d.id));

    node.append("circle")
      .attr("r", radius)
      .attr("fill", (d) => colorScale(d.id));

    node.append("text")
      .attr("dy", (d) => radius(d) + 14)
      .text((d) => d.label);

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x}, ${d.y})`);
    });

    return () => simulation.stop();
  }, [nodes, edges, selectedId, onSelect]);

  return (
    <div className="domain-graph-wrap" ref={containerRef}>
      <svg ref={svgRef} />
      <span className="domain-graph-hint">Glissez pour déplacer un nœud · molette pour zoomer · cliquez pour explorer</span>
    </div>
  );
}
