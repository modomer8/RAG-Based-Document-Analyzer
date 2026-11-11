/*
 * Quick Actions Controls - Labels/Exploded/View toggles
 * Bottom-left controls for the 3D interactive experience
 */

import * as THREE from "three"

export const QuickActions = ({ labelsOn, exploded, onToggleLabels, onToggleExplode }) => {
  return (
    <group position={[-20, -8, 0]}>        
      {/* Labels toggle button */}
      <group onClick={onToggleLabels} style={{ cursor: "pointer" }}>
        <boxGeometry args={[2.5, 0.8, 0.3]}/>
        <meshStandardMaterial 
          color={labelsOn ? "#0F9D8A" : "#5D8284"} 
          opacity={0.8}
        />
        <meshText2d
          string={`Labels: ${labelsOn ? "ON" : "OFF"}`
          } font="JetBrains Mono" size=8 color="#FFFFFF"
        />
      </group>
      
      {/* Exploded view toggle */}
      <group position={[4, 0, 0]} onClick={onToggleExplode} style={{ cursor: "pointer" }}>
        <boxGeometry args=[2.5, 0.8, 0.3]/>
        <meshStandardMaterial 
          color={exploded ? "#FF5A3C" : "#5D8284"} 
          opacity={0.8}
        />
        <meshText2d
          string={`Exploded: ${exploded ? "ON" : "OFF"}`
          } font="JetBrains Mono" size=8 color="#FFFFFF"
        />
      </group>
      
      {/* Rotate toggle */}
      <group position={[8, 0, 0]} onClick={() => alert("Rotate toggled")} style={{ cursor: "pointer" }}>
        <boxGeometry args=[2.5, 0.8, 0.3]/>
        <meshStandardMaterial color="#AABFBE" opacity={0.8} />
        <meshText2d string="Rotate: ON" font="JetBrains Mono" size=8 color="#FFFFFF" />
      </group>
    </group>
  )
}