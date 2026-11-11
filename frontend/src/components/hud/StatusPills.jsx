/*
 * Status Pills - Three pills showing COMPLIANT, NON-COMPLIANT, REQUIRES REVIEW
 * Glassmorphic design matching the RCI visual identity
 */

import * as THREE from "three"

export const StatusPills = ({ compliant, nonCompliant, review }) => {
  const pillColors = {
    compliant: "#0F9D8A",
    nonCompliant: "#FF5A3C",
    requiresReview: "#AABFBE",
  }
  
  const labels = {
    compliant: "COMPLIANT",
    nonCompliant: "NON-COMPLIANT",
    requiresReview: "REQUIRES REVIEW",
  }
  
  return (
    <group position={[0, 2, 0]}>        
      {["compliant", "nonCompliant", "review"].map((key, i) => (
        <group
          key={i}
          position={[(i - 1) * 4, 0, 0]}
        >
          <boxGeometry args={[3.5, 0.8, 0.4]}/>
          <meshStandardMaterial
            color={pillColors[key]}
            opacity={0.9}
          />
          <meshText2d
            string={labels[key]}
            font="JetBrains Mono"
            size=9
            color="#FFFFFF"
            weight="bold"
          />
        </group>
      ))}
    </group>
  )
}