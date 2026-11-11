/*
 * RAG Machine - Procedural 3D Visualization
 * Built entirely with custom Three.js geometries, shaders, and materials
 * No external GLTF/OBJ files - all visuals generated programmatically
 */

import React, { useRef, useState } from "react"
import { useFrame, useThree } from "@react-three/fiber"
import { Text } from "@react-three/drei"
import * as THREE from "three"

// ============================================================
// HELPER: Create Instanced Mesh for many similar objects
// ============================================================
export const createInstanced = (Geometry, Count = 50, params = {}) => {
  const countVal = Math.max(1, Count)
  const geometry = new Geometry()

  const material = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uColor1: { value: new THREE.Color(params.color1 || "#0F9D8A") },
      uColor2: { value: new THREE.Color(params.color2 || "#46C9BF") },
    },
    vertexShader: `
      attribute float offset;
      varying float vOffset;
      uniform float uTime;
      
      void main() {
        vOffset = offset;
        vec3 pos = position;
        pos.y += sin(offset * 0.5 + uTime * 0.2) * 0.5;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `,
    fragmentShader: `
      varying float vOffset;
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      
      void main() {
        float t = vOffset;
        vec3 color = mix(uColor1, uColor2, t);
        gl_FragColor = vec4(color, 1.0);
      }
    `,
    transparent: true,
    depthWrite: false,
  })

  const mesh = new THREE.InstancedMesh(geometry, material, countVal)
  mesh.count = countVal

  const dummy = new THREE.Object3D()
  const positions = new Float32Array(countVal * 3)
  const offsets = new Float32Array(countVal)

  for (let i = 0; i < countVal; i++) {
    const theta = Math.random() * Math.PI * 2
    const radius = 2 + Math.random() * 3
    const y = (Math.random() - 0.5) * 4

    dummy.position.set(
      Math.cos(theta) * radius,
      y,
      Math.sin(theta) * radius
    )
    dummy.updateMatrix()
    dummy.matrix.toArray(positions, i * 3)
    offsets[i] = Math.random()
    mesh.setMatrixAt(i, dummy.matrix)
  }

  mesh.instanceMatrix.needsUpdate = true
  return { mesh, material, positions, offsets }
}

// ============================================================
// RAG MACHINE COMPONENT
// ============================================================
export const RAGMachine = ({
  isPlaying = false,
  progress = 0,
  labelsOn = true,
  exploded = false,
  onPlayPause,
  onToggleLabels,
  onToggleExplode,
}) => {
  const machineRef = useRef()
  const [time, setTime] = useState(0)

  useFrame((state, delta) => {
    const elapsed = state.clock.elapsedTime
    setTime(elapsed)

    if (!machineRef.current) return
    const machine = machineRef.current

    if (!exploded) {
      machine.rotation.y += 0.005 * (isPlaying ? 1 : 0.5)
      machine.rotation.x += 0.002
    }
  })

  return (
    <group ref={machineRef} position={[-0.5, 0, 0]} scale={0.8}>
      {/* ====================================================== */}
      {/* DOCUMENT INGESTION WING (Left) - Floating ceramic sheets */}
      {/* ====================================================== */}
      <group position={[-22, 8, 0]} rotation={[0, 0, 0.1]}>
        {["PDF1", "PDF2", "PDF3"].map((label, i) => (
          <group
            key={label}
            position={[-3 + i * 2, Math.sin(time + i) * 2 + 8, 0]}
            rotation={[0, 0, Math.sin(time * 0.3 + i) * 0.3]}
          >
            <mesh>
              <planeGeometry args={[2, 1]} />
              <meshStandardMaterial
                color="#D3E8E7"
                opacity={0.8}
                transparent
                side={THREE.DoubleSide}
              />
            </mesh>
            {/* PDF marker */}
            <mesh position={[0, 0.8, 0.05]}>
              <sphereGeometry args={[0.15, 16, 16]} />
              <meshStandardMaterial color="#0E3A3D" />
            </mesh>
          </group>
        ))}
      </group>

      {/* ====================================================== */}
      {/* SEMANTIC CHUNKING ZONE - Sheets dividing into fragments */}
      {/* ====================================================== */}
      <group position={[-22, 0, 0]} rotation={[0, 0.1, 0]}>
        {exploded ? (
          Array.from({ length: 20 }, (_, i) => (
            <group
              key={i}
              position={[
                (Math.sin(i * 1.7) * 7.5),
                (Math.cos(i * 1.3) * 5),
                (Math.sin(i * 2.1) * 7.5),
              ]}
            >
              <mesh>
                <boxGeometry args={[0.5, 0.3, 0.2]} />
                <meshStandardMaterial color="#0F9D8A" opacity={0.6} transparent />
              </mesh>
            </group>
          ))
        ) : (
          Array.from({ length: 8 }, (_, i) => (
            <group
              key={i}
              position={[-3 + i * 2, 2, 0]}
              rotation={[0, 0, Math.sin(time * 0.5 + i) * 0.2]}
            >
              <mesh>
                <boxGeometry args={[1.5, 0.5, 0.1]} />
                <meshStandardMaterial
                  color="#0F9D8A"
                  opacity={0.4 + Math.sin(time * 2 + i) * 0.2}
                  transparent
                />
              </mesh>
            </group>
          ))
        )}
      </group>

      {/* ====================================================== */}
      {/* VECTOR EMBEDDING CORE - Cylindrical metallic hub + cloud */}
      {/* ====================================================== */}
      <group position={[0, 0, 0]}>
        <mesh>
          <cylinderGeometry
            args={[0.5, 3, 8, 32, 1, false]}
          />
          <meshStandardMaterial
            color="#10211F"
            metalness={0.8}
            roughness={0.3}
          />
        </mesh>

        {/* Rotating point cloud of embeddings */}
        <group>
          {Array.from({ length: 64 }, (_, i) => (
            <mesh
              key={i}
              position={[
                Math.cos(time * 0.5 + i) * 4,
                Math.sin(time * 0.3 + i) * 3,
                Math.cos(time * 0.7 + i) * 4,
              ]}
            >
              <sphereGeometry args={[0.2, 16, 16]} />
              <meshStandardMaterial
                color="#46C9BF"
                emissive="#46C9BF"
                emissiveIntensity={0.5 + Math.sin(time * 2 + i) * 0.2}
                opacity={0.8}
                transparent
              />
            </mesh>
          ))}
        </group>
      </group>

      {/* ====================================================== */}
      {/* DUAL HYBRID RETRIEVAL BEAMS - BM25 & DENSE */}
      {/* ====================================================== */}
      <group position={[22, 8, 0]} rotation={[0, 0, -0.1]}>
        {/* BM25 Beam */}
        <mesh position={[0, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.3, 0.3, 8, 16]} />
          <meshStandardMaterial
            color="#FF5A3C"
            opacity={0.6}
            transparent
            metalness={0.3}
            roughness={0.6}
          />
        </mesh>

        {/* Dense Search Beam */}
        <mesh position={[0, 6, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.3, 0.3, 8, 16]} />
          <meshStandardMaterial
            color="#46C9BF"
            opacity={0.6}
            transparent
            metalness={0.3}
            roughness={0.6}
          />
        </mesh>

        {/* Converging center gate */}
        <mesh position={[0, 2, 0]} rotation={[Math.sin(time * 0.3) * 0.3, 0, 0]}>
          <torusGeometry args={[1, 0.3, 16, 24]} />
          <meshStandardMaterial color="#46C9BF" opacity={0.5} transparent />
        </mesh>
      </group>

      {/* ====================================================== */}
      {/* CROSS-ENCODER RERANKING GATE */}
      {/* ====================================================== */}
      <group position={[22, 0, 0]} rotation={[0, 0.1, 0]}>
        {exploded ? (
          Array.from({ length: 6 }, (_, i) => (
            <mesh
              key={i}
              position={[
                (Math.sin(i) * 4),
                (Math.cos(i) * 3),
                (Math.sin(i * 2) * 4),
              ]}
            >
              <boxGeometry args={[1.2, 0.8, 0.4]} />
              <meshStandardMaterial
                color="#FF5A3C"
                opacity={0.7 + i * 0.05}
                transparent
              />
            </mesh>
          ))
        ) : (
          <group>
            {/* Top 4 selected results moving forward */}
            {Array.from({ length: 4 }, (_, i) => (
              <mesh
                key={i}
                position={[-2 + i * 0.8, Math.sin(time * 1.2 + i) * 1.5, 0]}
                rotation={[0, 0, Math.cos(time * 0.5 + i) * 0.2]}
              >
                <boxGeometry args={[1.5, 0.6, 0.3]} />
                <meshStandardMaterial
                  color="#FF5A3C"
                  opacity={0.8 - i * 0.15}
                  transparent
                />
              </mesh>
            ))}

            {/* Irrelevant chunks going into wireframe depth */}
            {Array.from({ length: 4 }, (_, i) => (
              <mesh
                key={i + 4}
                position={[
                  -2 + (4 - i) * 0.8,
                  -Math.sin(time * 1.2 + i) * 1.5,
                  -(i * 2 + 5),
                ]}
                rotation={[0, 0, Math.sin(time * 0.5 + i) * 0.3]}
              >
                <boxGeometry args={[1.2, 0.5, 0.2]} />
                <meshBasicMaterial
                  color="#5D8284"
                  opacity={0.3}
                  wireframe
                  transparent
                />
              </mesh>
            ))}
          </group>
        )}
      </group>

      {/* ====================================================== */}
      {/* LLM PROCESSING REACTOR */}
      {/* ====================================================== */}
      <group position={[-22, -8, 0]}>
        <mesh>
          <cylinderGeometry args={[1, 2, 10, 32]} />
          <meshStandardMaterial
            color="#10211F"
            metalness={0.9}
            roughness={0.1}
            emissive="#10211F"
            emissiveIntensity={0.2}
          />
        </mesh>

        {/* Pulsing light rings */}
        <group rotation={[0, time * 0.8, 0]}>
          {Array.from({ length: 4 }, (_, i) => (
            <mesh
              key={i}
              position={[0, 3 + Math.cos(time * 1.5 + i) * 1, 0]}
            >
              <torusGeometry args={[1.5, 0.4, 16, 32]} />
              <meshStandardMaterial
                color={i % 2 === 0 ? "#46C9BF" : "#FF5A3C"}
                emissive={i % 2 === 0 ? "#46C9BF" : "#FF5A3C"}
                emissiveIntensity={0.3 + Math.sin(time * 2 + i) * 0.1}
                opacity={0.5}
                transparent
              />
            </mesh>
          ))}
        </group>
      </group>

      {/* ====================================================== */}
      {/* AUDIT OUTPUT STATION */}
      {/* ====================================================== */}
      <group position={[22, -8, 0]}>
        {Array.from({ length: 3 }, (_, i) => (
          <mesh key={i} position={[(i - 1) * 3, 3, 0]}>
            <boxGeometry args={[2, 0.5, 0.3]} />
            <meshStandardMaterial
              color={i === 0 ? "#0F9D8A" : i === 1 ? "#FF5A3C" : "#AABFBE"}
              opacity={0.9}
              transparent
            />
          </mesh>
        ))}

        {labelsOn && (
          <group position={[0, -4, 0]}>
            <Text
              fontSize={1.2}
              color="#0F9D8A"
              anchorX="center"
              anchorY="middle"
            >
              86%
            </Text>
            <Text
              position={[0, -1.2, 0]}
              fontSize={0.8}
              color="#0F9D8A"
              anchorX="center"
              anchorY="middle"
            >
              COMPLIANT
            </Text>
          </group>
        )}
      </group>
    </group>
  )
}

export default RAGMachine