/*
 * Pipeline HUD - Top bar with brand, activity meter, and metadata grid
 * Glassmorphic design matching the RCI visual identity
 */

import React from "react"
import { useThree, useFrame } from "@react-three/fiber"
import { Text, Html } from "@react-three/drei"
import * as THREE from "three"

// Helper component to render 3D text in place of custom meshText2d
const MeshText2D = ({
  string = "",
  size = 10,
  color = "#0E3A3D",
  position = [0, 0, 0],
  weight = "normal",
  anchorX = "left",
  anchorY = "middle",
  ...props
}) => {
  return (
    <Text
      position={position}
      fontSize={size * 0.08}
      color={color}
      anchorX={anchorX}
      anchorY={anchorY}
      fontWeight={weight}
      {...props}
    >
      {string}
    </Text>
  )
}

export const PipelineHUD = ({ progress = 0, isPlaying = false }) => {
  const { viewport } = useThree()

  // Determine current stage based on progress (0-25 seconds)
  const stages = [
    { id: 0, start: 0, end: 3, label: "INGESTION", desc: "Document ingestion and processing" },
    { id: 1, start: 3, end: 6, label: "PARSING", desc: "Structural text extraction" },
    { id: 2, start: 6, end: 9, label: "CHUNKING", desc: "Semantic chunking" },
    { id: 3, start: 9, end: 12, label: "VECTOR", desc: "Vector embedding indexing" },
    { id: 4, start: 12, end: 16, label: "HYBRID", desc: "BM25 + Dense Search fusion" },
    { id: 5, start: 16, end: 19, label: "RERANK", desc: "Cross-Encoder re-ranking" },
    { id: 6, start: 19, end: 22, label: "LLM", desc: "LLM reasoning core" },
    { id: 7, start: 22, end: 25, label: "OUTPUT", desc: "Compliance audit output" },
  ]

  let currentStage = "INGESTION"
  let stageProgress = 0

  for (const stage of stages) {
    if (progress >= stage.start && progress < stage.end) {
      currentStage = stage.label
      stageProgress = ((progress - stage.start) / (stage.end - stage.start)) * 100
      break
    } else if (progress >= stage.end) {
      currentStage = stage.label
      stageProgress = 100
    }
  }

  // Pipeline activity meter level (0-50%)
  const activityLevel = Math.min(Math.round((progress / 25) * 50), 50)

  // Metadata
  const metadata = {
    engine: "RCI-001",
    inference: "LOCAL LLM",
    vectorStore: "QDRANT",
    status: isPlaying ? "ACTIVE" : "PAUSED",
  }

  const currentStageObj = stages.find((s) => s.label === currentStage)

  // Timeline bar dimensions
  const timelineTotalWidth = 35
  const currentProgressRatio = Math.min(Math.max(progress / 25, 0), 1)
  const progressWidth = Math.max(0.01, currentProgressRatio * timelineTotalWidth)

  // Card styling for glassmorphic HTML overlays
  const glassCardStyle = {
    background: "rgba(255, 255, 255, 0.55)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    borderRadius: "10px",
    padding: "12px 14px",
    minWidth: "160px",
    marginBottom: "12px",
    border: "1px solid rgba(255, 255, 255, 0.4)",
    boxShadow: "0 4px 14px rgba(16, 33, 31, 0.08)",
    fontFamily: "monospace",
    textAlign: "left",
  }

  useFrame(() => {
    // Optional shader uniform hooks or live HUD animations
  })

  return (
    <group position={[0, 0, 0]}>
      {/* ====================================================== */}
      {/* TOP BAR                                                */}
      {/* ====================================================== */}
      <group position={[0, 18, 0]} scale={1.1}>
        {/* Left: Brand + Title */}
        <group position={[-22, 0, 0]}>
          <MeshText2D string="[RCI]" size={11} color="#0E3A3D" position={[0, 1.2, 0]} />
          <MeshText2D string="RCI" size={18} color="#0E3A3D" weight="bold" position={[0, 0, 0]} />
          <MeshText2D
            string="ENTERPRISE DOCUMENT INTELLIGENCE"
            size={7}
            color="#5D8284"
            position={[0, -1.1, 0]}
          />
        </group>

        {/* Center: Activity Meter */}
        <group position={[-6, 0, 0]}>
          <MeshText2D
            string={`PIPELINE ACTIVITY: ${activityLevel}%`}
            size={10}
            color="#0E3A3D"
            position={[0, 0, 0]}
          />
        </group>

        {/* Right: Metadata Grid */}
        <group position={[10, 0, 0]}>
          <MeshText2D string={`ENGINE: ${metadata.engine}`} size={8} color="#5D8284" position={[0, 1.2, 0]} />
          <MeshText2D string={`INFERENCE: ${metadata.inference}`} size={8} color="#5D8284" position={[0, 0.4, 0]} />
          <MeshText2D string={`VECTOR STORE: ${metadata.vectorStore}`} size={8} color="#5D8284" position={[0, -0.4, 0]} />
          <MeshText2D string={`STATUS: ${metadata.status}`} size={8} color="#5D8284" position={[0, -1.2, 0]} />
        </group>
      </group>

      {/* ====================================================== */}
      {/* LEFT COLUMN GLASSMORPHIC CARDS (01-03)                */}
      {/* ====================================================== */}
      <group position={[-24, -2, 0]}>
        <Html transform scale={0.75} position={[0, 0, 0]}>
          {/* Card 01 - DOCUMENT INGESTION */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>DOC INGESTION</div>
            <div style={{ fontSize: "11px", color: "#5D8284", marginTop: "4px" }}>128 documents processed</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>(86 PDF, 42 DOCX)</div>
          </div>

          {/* Card 02 - VECTOR INTELLIGENCE */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>VECTOR INTELLIGENCE</div>
            <div style={{ fontSize: "11px", color: "#5D8284", marginTop: "4px" }}>BGE-Small-EN-v1.5</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>384 dimensions</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>2,840 indexed chunks</div>
          </div>

          {/* Card 03 - RETRIEVAL ENGINE */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>RETRIEVAL ENGINE</div>
            <div style={{ fontSize: "11px", color: "#5D8284", marginTop: "4px" }}>Hybrid: BM25 + Dense</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>Reranking: Cross-Encoder</div>
          </div>
        </Html>
      </group>

      {/* ====================================================== */}
      {/* RIGHT COLUMN GLASSMORPHIC CARDS (04-07)               */}
      {/* ====================================================== */}
      <group position={[18, -2, 0]}>
        <Html transform scale={0.75} position={[0, 0, 0]}>
          {/* Card 04 - AUDIT OVERVIEW */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>AUDIT OVERVIEW</div>
            <div style={{ fontSize: "20px", fontWeight: "bold", color: "#0F9D8A", margin: "2px 0" }}>86%</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>COMPLIANCE</div>
          </div>

          {/* Card 05 - AUDIT CLASSIFICATION */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>AUDIT CLASSIFICATION</div>
            <div style={{ fontSize: "10px", color: "#0F9D8A", marginTop: "4px" }}>COMPLIANT: 05</div>
            <div style={{ fontSize: "10px", color: "#FF5A3C" }}>NON-COMPLIANT: 08</div>
            <div style={{ fontSize: "10px", color: "#AABFBE" }}>REVIEW: 12</div>
          </div>

          {/* Card 06 - EVIDENCE RETRIEVAL */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>EVIDENCE RETRIEVAL</div>
            <div style={{ fontSize: "10px", color: "#5D8284", marginTop: "4px" }}>Top 4 citations:</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>• Access Control p.12</div>
            <div style={{ fontSize: "10px", color: "#5D8284" }}>• Encryption p.8</div>
          </div>

          {/* Card 07 - SYSTEM MODULES */}
          <div style={glassCardStyle}>
            <div style={{ fontWeight: "bold", fontSize: "12px", color: "#0E3A3D" }}>SYSTEM MODULES</div>
            <div style={{ fontSize: "10px", color: "#0F9D8A", marginTop: "4px" }}>• Qdrant ✓</div>
            <div style={{ fontSize: "10px", color: "#0F9D8A" }}>• BM25 ✓</div>
            <div style={{ fontSize: "10px", color: "#0F9D8A" }}>• Cross-Encoder ✓</div>
          </div>
        </Html>
      </group>

      {/* ====================================================== */}
      {/* BOTTOM BAR                                             */}
      {/* ====================================================== */}
      <group position={[0, -20, 0]} scale={1.1}>
        {/* Stage indicator */}
        <group position={[-24, 0, 0]}>
          <MeshText2D
            string={`STAGE: ${currentStage}`}
            size={12}
            color="#FF5A3D"
            weight="bold"
            position={[0, 0.6, 0]}
          />
          <MeshText2D
            string={currentStageObj?.desc || ""}
            size={7}
            color="#5D8284"
            position={[0, -0.6, 0]}
          />
        </group>

        {/* Scrubbable timeline with stage track */}
        <group position={[0, 0, 0]}>
          {/* Timeline background track */}
          <mesh position={[0, 0, 0]}>
            <boxGeometry args={[timelineTotalWidth, 0.8, 0.3]} />
            <meshStandardMaterial color="#D3E8E7" opacity={0.25} transparent />
          </mesh>

          {/* Progress fill bar */}
          <mesh position={[-timelineTotalWidth / 2 + progressWidth / 2, 0, 0.05]}>
            <boxGeometry args={[progressWidth, 0.82, 0.35]} />
            <meshStandardMaterial color="#0F9D8A" />
          </mesh>
        </group>

        {/* Quick action controls */}
        <group position={[20, 0, 0]}>
          <MeshText2D string="Labels: ON" size={7} color="#0E3A3D" position={[0, 0.8, 0]} />
          <MeshText2D string="Exploded: OFF" size={7} color="#5D8284" position={[0, 0, 0]} />
          <MeshText2D string="Rotate: ON" size={7} color="#5D8284" position={[0, -0.8, 0]} />
        </group>
      </group>
    </group>
  )
}

export default PipelineHUD