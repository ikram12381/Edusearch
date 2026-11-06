import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { Search, Database, Brain, Share2, ArrowRight } from "lucide-react";

const EXAMPLE_CONCEPTS = ["Computer Vision", "CNN", "Deep Learning", "Neural Networks"];

export default function Home() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  function handleSearch(e) {
    e.preventDefault();
    navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`);
  }

  return (
    <div className="fade-in">
      <section className="hero">
        <span className="hero-eyebrow"><Search size={13} /> Elasticsearch · Semantic Embeddings · Knowledge Graph</span>
        <h1>Learn smarter.<br /><span className="accent">Search beyond keywords.</span></h1>
        <p className="sub">
          Discover courses using an intelligent search engine powered by Elasticsearch, Semantic Embeddings
          and Knowledge Graphs — not just keyword matching.
        </p>
        <form className="hero-search" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="What do you want to learn?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">Search with AI <ArrowRight size={15} /></button>
        </form>
      </section>

      <h2 style={{ fontSize: 20, marginBottom: 4 }}>How it works</h2>
      <p style={{ color: "var(--text-muted)", fontSize: 13.5 }}>Three signals, fused into one ranked list.</p>

      <div className="how-it-works">
        <div className="how-card">
          <div className="how-card-num">01</div>
          <div className="how-card-icon" style={{ background: "var(--lexical-soft)", color: "var(--lexical)" }}><Database size={18} /></div>
          <h3>Lexical Search</h3>
          <p>Finds exact keyword matches efficiently, using BM25 on Elasticsearch.</p>
          <p className="powered">Powered by Elasticsearch</p>
        </div>
        <div className="how-card">
          <div className="how-card-num">02</div>
          <div className="how-card-icon" style={{ background: "var(--semantic-soft)", color: "var(--semantic)" }}><Brain size={18} /></div>
          <h3>Semantic Search</h3>
          <p>Understands the meaning behind your query, even without shared keywords.</p>
          <p className="powered">Powered by Embeddings</p>
        </div>
        <div className="how-card">
          <div className="how-card-num">03</div>
          <div className="how-card-icon" style={{ background: "var(--graph-soft)", color: "var(--graph)" }}><Share2 size={18} /></div>
          <h3>Knowledge Graph</h3>
          <p>Connects concepts, courses, skills and prerequisites for contextual results.</p>
          <p className="powered">Powered by RDF/OWL</p>
        </div>
      </div>

      <div className="demo-example fade-in-up">
        <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text-muted)", marginBottom: 12 }}>Example search</p>
        <p className="demo-example-query">"I want to learn how computers recognize images"</p>
        <p style={{ fontSize: 12.5, color: "var(--text-muted)", marginBottom: 10 }}>Detected concepts:</p>
        <div className="concept-chips">
          {EXAMPLE_CONCEPTS.map((c) => <span key={c} className="badge badge-primary">{c}</span>)}
        </div>
      </div>
    </div>
  );
}
