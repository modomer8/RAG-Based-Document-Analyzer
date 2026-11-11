/*
 * Stage Meter - Dynamic processing activity meter visualizer
 * 50-cell progress bar showing pipeline activity percentage
 */

import * as THREE from "three"

export const StageMeter = ({ progress, isPlaying }) => {
  // progress is 0-25, convert to 0-50 cell level
  const activityLevel = Math.min(Math.round(progress / 25 * 50), 50)
  const filledCells = activityLevel
  const emptyCells = 50 - filledCells
  
  return (
    <group position={[0, 2, 0]}>        
      {/* Meter background - 50 cells */}
      {Array.from({ length: 50 }, (_, i) => (
        <group
          key={i}
          position={[(i % 50) * 0.4 - 9.8, (Math.floor(i / 50) - 1) * 0.3 + 2, 0]}
        >
          <boxGeometry args={[0.35, 0.3, 0.1]}/>
          <meshStandardMaterial 
            color="#D3E8E7" 
            opacity={filledCells > i ? 0.2 : 0.8}
          />
        </group>
      ))}
      
      {/* Filled progress cells */}
      {Array.from({ length: filledCells }, (_, i) => (
        <group
          key={i}
          position={[(i % 50) * 0.4 - 9.8, (Math.floor(i / 50) - 1) * 0.3 + 2, 0]}
        >
          <boxGeometry args={[0.35, 0.3, 0.1]}/>
          <meshStandardMaterial color="#0F9D8A" opacity={0.9} />
        </group>
      ))}
    </group>
  )
}