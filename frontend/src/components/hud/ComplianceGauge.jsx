/*
 * Compliance Gauge - Large circular compliance status gauge
 * Displays overall compliance percentage with segmented indicators
 */

import * as THREE from "three"

export const ComplianceGauge = ({ score }) => {
  // score is 0.0-1.0, convert to percentage
  const percentage = Math.round(score * 100)
  const compliantSegments = Math.round(percentage / 12.5)  // 8 segments for 100%
  const nonCompliantSegments = Math.round((100 - percentage) / 12.5)
  const reviewSegments = 8 - compliantSegments - nonCompliantSegments
  
  const colors = {
    compliant: "#0F9D8A",
    nonCompliant: "#FF5A3C",
    review: "#AABFBE",
  }
  
  const labels = {
    compliant: "COMPLIANT",
    nonCompliant: "NON-COMPLIANT",
    review: "REVIEW",
  }
  
  return (
    <group position={[0, 3, 0]}>        
      {/* Circular gauge base */}
      <group rotation={[-Math.PI / 2, 0, 0]}>        
        {/* Outer circle ring */}
        <torGeometry args={[12, 2, 32, 32]}/>
        <meshStandardMaterial
          color="#D3E8E7"
          opacity={0.3}
        />
      </group>
      
      {/* Compliance score percentage */}
      <meshText2d
        string={`${percentage}%`}
        font="Inter"
        size=24
        color={percentage >= 60 ? "#0F9D8A" : "#FF5A3C"}
        weight="bold"
        position={[0, 0, 0]}
      />
      
      {/* Status label */}
      <meshText2d
        string={percentage >= 60 ? "COMPLIANT" : "REVIEW NEEDED"}
        font="JetBrains Mono"
        size=10
        color={percentage >= 60 ? "#0F9D8A" : "#FF5A3C"}
        position={[0, -4, 0]}
      />
    </group>
  )
}