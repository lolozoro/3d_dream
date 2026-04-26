import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, Stars } from "@react-three/drei";
import * as THREE from "three";
import type { MindMap } from "./types";
import { computeLayout } from "./layout";

interface Props {
  mindmap: MindMap;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  autoRotate: boolean;
}

function Node({
  position,
  label,
  color,
  selected,
  onClick,
}: {
  position: [number, number, number];
  label: string;
  color: string;
  selected: boolean;
  onClick: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    if (meshRef.current) {
      const t = state.clock.getElapsedTime();
      meshRef.current.scale.setScalar(
        selected ? 1.15 + Math.sin(t * 3) * 0.05 : 1,
      );
    }
  });

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
      >
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 1.2 : 0.5}
          metalness={0.3}
          roughness={0.25}
        />
      </mesh>
      {/* Halo */}
      <mesh>
        <sphereGeometry args={[0.75, 24, 24]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={selected ? 0.18 : 0.08}
        />
      </mesh>
      <Html
        center
        distanceFactor={10}
        position={[0, 1.1, 0]}
        style={{ pointerEvents: "none" }}
      >
        <div
          className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap backdrop-blur-md border ${
            selected
              ? "bg-primary/90 text-primary-foreground border-primary shadow-glow"
              : "bg-card/80 text-foreground border-border/60"
          }`}
        >
          {label}
        </div>
      </Html>
    </group>
  );
}

function Edge({
  from,
  to,
  highlighted,
}: {
  from: [number, number, number];
  to: [number, number, number];
  highlighted: boolean;
}) {
  const points = useMemo(
    () => [new THREE.Vector3(...from), new THREE.Vector3(...to)],
    [from, to],
  );
  const geometry = useMemo(
    () => new THREE.BufferGeometry().setFromPoints(points),
    [points],
  );
  return (
    <line>
      <primitive object={geometry} attach="geometry" />
      <lineBasicMaterial
        color={highlighted ? "#22d3ee" : "#64748b"}
        transparent
        opacity={highlighted ? 0.95 : 0.45}
        linewidth={1}
      />
    </line>
  );
}

function Scene({ mindmap, selectedId, onSelect, autoRotate }: Props) {
  const positions = useMemo(() => {
    const computed = computeLayout(mindmap);
    // Allow node-supplied positions to override
    mindmap.nodes.forEach((n) => {
      if (n.position) computed[n.id] = n.position;
    });
    return computed;
  }, [mindmap]);

  const palette = ["#22d3ee", "#a855f7", "#f472b6", "#fbbf24", "#34d399", "#60a5fa"];

  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#22d3ee" />
      <pointLight position={[-10, -10, -10]} intensity={0.6} color="#a855f7" />
      <Stars radius={80} depth={50} count={2000} factor={3} fade speed={1} />

      {mindmap.edges.map((e, i) => {
        const f = positions[e.from];
        const t = positions[e.to];
        if (!f || !t) return null;
        return (
          <Edge
            key={`${e.from}-${e.to}-${i}`}
            from={f}
            to={t}
            highlighted={selectedId === e.from || selectedId === e.to}
          />
        );
      })}

      {mindmap.nodes.map((n, i) => {
        const pos = positions[n.id];
        if (!pos) return null;
        return (
          <Node
            key={n.id}
            position={pos}
            label={n.label}
            color={n.color || palette[i % palette.length]}
            selected={selectedId === n.id}
            onClick={() => onSelect(n.id)}
          />
        );
      })}

      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        autoRotate={autoRotate}
        autoRotateSpeed={0.6}
        minDistance={4}
        maxDistance={60}
      />
    </>
  );
}

export default function MindMap3D(props: Props) {
  return (
    <Canvas
      camera={{ position: [10, 6, 14], fov: 55 }}
      onPointerMissed={() => props.onSelect(null)}
      gl={{ antialias: true, alpha: true }}
    >
      <color attach="background" args={["#0a0e1a"]} />
      <fog attach="fog" args={["#0a0e1a", 25, 70]} />
      <Scene {...props} />
    </Canvas>
  );
}