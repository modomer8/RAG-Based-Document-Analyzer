/*
 * RCI - RAG Compliance Intelligence
 * Main Interactive 3D Landing Page
 * React + Three.js / React Three Fiber + Tailwind CSS
 */

import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";

import { RAGMachine } from "./components/three/RAGMachine";
import { PipelineHUD } from "./components/hud/PipelineHUD";

import "./index.css";

// --------------------------------------------------
// PIPELINE STAGE DEFINITIONS
// --------------------------------------------------

export const stages = [
  { id: 0, start: 0, end: 3, label: "INGESTION", desc: "Document ingestion and processing", pos: [-22, 10, 0] },
  { id: 1, start: 3, end: 6, label: "PARSING", desc: "Structural text extraction", pos: [-22, 5, 0] },
  { id: 2, start: 6, end: 9, label: "CHUNKING", desc: "Semantic chunking", pos: [-22, 0, 0] },
  { id: 3, start: 9, end: 12, label: "VECTOR", desc: "Vector embedding indexing", pos: [0, 5, 0] },
  { id: 4, start: 12, end: 16, label: "HYBRID", desc: "BM25 + Dense Search fusion", pos: [22, 10, 0] },
  { id: 5, start: 16, end: 19, label: "RERANK", desc: "Cross-Encoder re-ranking", pos: [22, 0, 0] },
  { id: 6, start: 19, end: 22, label: "LLM", desc: "LLM reasoning core", pos: [-22, -8, 0] },
  { id: 7, start: 22, end: 25, label: "OUTPUT", desc: "Compliance audit output", pos: [22, -8, 0] },
];

// --------------------------------------------------
// MAIN APPLICATION
// --------------------------------------------------

export function App() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(12);
  const [labelsOn, setLabelsOn] = useState(true);
  const [exploded, setExploded] = useState(false);

  // Keyboard navigation & spacebar controls
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.code === "Space") {
        event.preventDefault();
        setIsPlaying((prev) => !prev);
      }
      if (/^[0-7]$/.test(event.key)) {
        const stage = stages[Number(event.key)];
        if (stage) {
          setProgress(stage.start + (stage.end - stage.start) / 2);
          setIsPlaying(false);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Global window controls for testing via browser console
  useEffect(() => {
    window.jumpToStage = (stageId) => {
      const stage = stages[stageId];
      if (stage) {
        setProgress(stage.start + (stage.end - stage.start) / 2);
        setIsPlaying(false);
      }
    };
    window.togglePlayPause = () => setIsPlaying((p) => !p);
    window.toggleLabels = () => setLabelsOn((l) => !l);
    window.toggleExplode = () => setExploded((e) => !e);
  }, []);

  // Playback timer progression
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setProgress((prev) => (prev >= 25 ? 0 : prev + 0.1));
    }, 100);
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative", backgroundColor: "#0b1312" }}>
      <Canvas
        gl={{
          antialias: true,
          powerPreference: "high-performance",
        }}
        camera={{
          position: [0, 0, 45],
          fov: 55,
        }}
        style={{ width: "100%", height: "100%" }}
      >
        {/* Ambient & directional illumination */}
        <ambientLight intensity={1.2} />
        <directionalLight position={[15, 20, 15]} intensity={1.8} />
        <pointLight position={[-15, -10, -10]} intensity={0.8} />

        {/* Interactive camera controls */}
        <OrbitControls
          enableDamping={true}
          dampingFactor={0.05}
          enablePan={true}
          enableZoom={true}
          makeDefault
        />

        {/* RAG Pipeline 3D Machine */}
        <RAGMachine
          isPlaying={isPlaying}
          progress={progress}
          labelsOn={labelsOn}
          exploded={exploded}
          onPlayPause={() => setIsPlaying((p) => !p)}
          onToggleLabels={() => setLabelsOn((l) => !l)}
          onToggleExplode={() => setExploded((e) => !e)}
        />

        {/* Pipeline HUD */}
        <PipelineHUD isPlaying={isPlaying} progress={progress} />

        {/* Pipeline Stage 3D Badges */}
        {labelsOn &&
          stages.map((stage) => (
            <Html
              key={stage.id}
              position={stage.pos}
              center
              distanceFactor={35}
              style={{
                pointerEvents: "none",
                color: "#0E3A3D",
                fontFamily: "monospace",
                fontSize: "10px",
                fontWeight: "bold",
                textTransform: "uppercase",
                background: "rgba(255, 255, 255, 0.85)",
                padding: "2px 8px",
                borderRadius: "4px",
                boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
                whiteSpace: "nowrap",
                border: "1px solid rgba(14, 58, 61, 0.2)",
              }}
            >
              {stage.label}
            </Html>
          ))}
      </Canvas>
    </div>
  );
}

// Mount to standard Vite index.html root
const rootElement = document.getElementById("root");
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

export default App;