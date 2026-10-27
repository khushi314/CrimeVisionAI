import React, {useEffect, useRef, useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {Grid3X3, RotateCcw, Eye, ChevronDown, ChevronUp} from 'lucide-react';
import {Object3DNode, Scene3DData} from '../types/forensic';

interface Scene3DReconstructionProps {
  scene3d: Scene3DData;
  selectedId: string | null;
  onSelectNode: (node: Object3DNode | null) => void;
}

function createEvidenceBadgeTexture(markerNumber: number, category: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d')!;

  const bg =
    category === 'weapon' ? '#ef4444' : category === 'person' ? '#38bdf8' : '#facc15';
  const fg = category === 'object' ? '#0f172a' : '#ffffff';

  ctx.fillStyle = bg;
  ctx.beginPath();
  ctx.arc(64, 64, 52, 0, Math.PI * 2);
  ctx.fill();

  ctx.lineWidth = 6;
  ctx.strokeStyle = '#0f172a';
  ctx.stroke();

  ctx.fillStyle = fg;
  ctx.font = '700 54px "IBM Plex Mono", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(markerNumber), 64, 67);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function buildProceduralObjectGroup(node: Object3DNode, isSelected: boolean): THREE.Group {
  const group = new THREE.Group();
  const label = node.label.toLowerCase();
  const [nx1, ny1, nx2, ny2] = node.bbox;
  const isHorizontal = nx2 - nx1 > (ny2 - ny1) * 1.18;

  const highlightEmissive = isSelected ? new THREE.Color('#38bdf8') : new THREE.Color('#000000');
  const emissiveIntensity = isSelected ? 0.35 : 0;

  if (node.category === 'person') {
    const suitMat = new THREE.MeshStandardMaterial({
      color: '#64748b',
      roughness: 0.45,
      metalness: 0.15,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const figure = new THREE.Group();

    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.55, 8, 16), suitMat);
    torso.position.y = 0.92;
    figure.add(torso);

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), suitMat);
    head.position.y = 1.48;
    figure.add(head);

    const legGeo = new THREE.CylinderGeometry(0.07, 0.06, 0.56, 10);
    const leftLeg = new THREE.Mesh(legGeo, suitMat);
    leftLeg.position.set(-0.1, 0.28, 0);
    const rightLeg = new THREE.Mesh(legGeo, suitMat);
    rightLeg.position.set(0.1, 0.28, 0);
    figure.add(leftLeg, rightLeg);

    if (isHorizontal) {
      figure.rotation.z = Math.PI / 2;
      figure.position.set(-0.75, 0.22, 0);
    }
    group.add(figure);
  } else if (node.category === 'weapon') {
    const bladeMat = new THREE.MeshStandardMaterial({
      color: '#e2e8f0',
      roughness: 0.2,
      metalness: 0.85,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const gripMat = new THREE.MeshStandardMaterial({color: '#1e293b', roughness: 0.7});
    const blade = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.02, 0.07), bladeMat);
    blade.position.set(-0.1, 0.04, 0);
    const grip = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.04, 0.08), gripMat);
    grip.position.set(0.2, 0.04, 0);

    const ringGeo = new THREE.RingGeometry(0.38, 0.44, 32);
    ringGeo.rotateX(-Math.PI / 2);
    const ringMat = new THREE.MeshBasicMaterial({
      color: '#ef4444',
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.75,
    });
    const alertRing = new THREE.Mesh(ringGeo, ringMat);
    alertRing.position.y = 0.01;
    group.add(blade, grip, alertRing);
  } else if (label.includes('desk') || label.includes('table')) {
    const woodMat = new THREE.MeshStandardMaterial({
      color: '#6b4c38',
      roughness: 0.6,
      metalness: 0.1,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const top = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.07, 0.8), woodMat);
    top.position.y = 0.74;
    group.add(top);
    const legGeo = new THREE.BoxGeometry(0.06, 0.72, 0.06);
    for (const [lx, lz] of [
      [-0.68, -0.34],
      [0.68, -0.34],
      [-0.68, 0.34],
      [0.68, 0.34],
    ]) {
      const leg = new THREE.Mesh(legGeo, woodMat);
      leg.position.set(lx, 0.36, lz);
      group.add(leg);
    }
  } else if (label.includes('display') || label.includes('counter')) {
    const baseMat = new THREE.MeshStandardMaterial({
      color: '#1e3a5f',
      roughness: 0.4,
      metalness: 0.3,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: '#7dd3fc',
      transparent: true,
      opacity: 0.38,
      roughness: 0.1,
      metalness: 0.1,
    });
    const base = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.62, 0.72), baseMat);
    base.position.y = 0.31;
    const hood = new THREE.Mesh(new THREE.BoxGeometry(1.66, 0.38, 0.68), glassMat);
    hood.position.y = 0.81;
    group.add(base, hood);
  } else if (label.includes('chair')) {
    const chairMat = new THREE.MeshStandardMaterial({
      color: '#334155',
      roughness: 0.55,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const chairGroup = new THREE.Group();
    const seat = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.06, 0.52), chairMat);
    seat.position.y = 0.44;
    const back = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 0.06), chairMat);
    back.position.set(0, 0.72, -0.23);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.42, 10), chairMat);
    post.position.y = 0.21;
    chairGroup.add(seat, back, post);
    chairGroup.rotation.z = 0.45;
    group.add(chairGroup);
  } else if (label.includes('laptop')) {
    const alumMat = new THREE.MeshStandardMaterial({
      color: '#cbd5e1',
      roughness: 0.28,
      metalness: 0.75,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const screenMat = new THREE.MeshStandardMaterial({
      color: '#0ea5e9',
      emissive: new THREE.Color('#0284c7'),
      emissiveIntensity: 0.55,
    });
    const base = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.02, 0.3), alumMat);
    base.position.y = 0.79;
    const lid = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.28, 0.02), screenMat);
    lid.position.set(0, 0.93, -0.14);
    lid.rotation.x = -0.2;
    group.add(base, lid);
  } else {
    const propMat = new THREE.MeshStandardMaterial({
      color: '#f59e0b',
      roughness: 0.4,
      metalness: 0.35,
      emissive: highlightEmissive,
      emissiveIntensity,
    });
    const prop = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.28, 0.26), propMat);
    prop.position.y = 0.14;
    group.add(prop);
  }

  // Yellow pyramidal forensic marker cone beside every cataloged item
  const coneMat = new THREE.MeshStandardMaterial({
    color: '#facc15',
    roughness: 0.35,
    metalness: 0.1,
  });
  const cone = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.26, 4), coneMat);
  cone.position.set(0.32, 0.13, 0.24);
  group.add(cone);

  // Numbered billboard sprite above object
  const badgeTex = createEvidenceBadgeTexture(node.marker_number, node.category);
  const spriteMat = new THREE.SpriteMaterial({map: badgeTex, depthTest: false});
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(0.38, 0.38, 1);
  sprite.position.set(0, node.category === 'person' && !isHorizontal ? 1.85 : 1.15, 0);
  group.add(sprite);

  group.position.set(node.position.x, node.position.y, node.position.z);
  group.userData = {forensicNode: node};
  return group;
}

export const Scene3DReconstruction: React.FC<Scene3DReconstructionProps> = ({
  scene3d,
  selectedId,
  onSelectNode,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);

  const [showGrid, setShowGrid] = useState(true);
  const [dockCollapsed, setDockCollapsed] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 640;
    const height = container.clientHeight || 420;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0d131f');

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(5.8, 4.8, 6.4);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({antialias: true, powerPreference: 'high-performance'});
    const gl = renderer.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    const gpuStr = dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : '';
    const isSoftwareGl = /SwiftShader|llvmpipe|Software/i.test(gpuStr);

    renderer.setPixelRatio(isSoftwareGl ? 1 : Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const pmrem = new THREE.PMREMGenerator(renderer);
    const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = envTex;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI / 2 - 0.03;
    controls.minDistance = 2.5;
    controls.maxDistance = 16;
    controls.target.set(0, 0.6, 0);
    controlsRef.current = controls;

    // Room floor & walls
    const roomW = scene3d.dimensions?.width || 9.0;
    const roomD = scene3d.dimensions?.depth || 7.0;
    const roomH = scene3d.dimensions?.height || 3.2;

    const floorMat = new THREE.MeshStandardMaterial({
      color: '#172030',
      roughness: 0.85,
      metalness: 0.08,
    });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(roomW, roomD), floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const grid = new THREE.GridHelper(roomW, 18, '#38bdf8', '#243247');
    grid.position.y = 0.005;
    grid.visible = showGrid;
    gridRef.current = grid;
    scene.add(grid);

    const wallMat = new THREE.MeshStandardMaterial({
      color: '#1e293b',
      roughness: 0.9,
      transparent: true,
      opacity: 0.45,
      side: THREE.DoubleSide,
    });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(roomW, roomH), wallMat);
    backWall.position.set(0, roomH / 2, -roomD / 2);
    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(roomD, roomH), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-roomW / 2, roomH / 2, 0);
    scene.add(backWall, leftWall);

    // Key + Rim lights
    const keyLight = new THREE.DirectionalLight('#f8fafc', 1.35);
    keyLight.position.set(4, 7, 5);
    const rimLight = new THREE.DirectionalLight('#38bdf8', 0.45);
    rimLight.position.set(-5, 4, -4);
    scene.add(keyLight, rimLight);

    // Populate cataloged 3D forensic objects
    const interactiveGroups: THREE.Object3D[] = [];
    for (const node of scene3d.objects || []) {
      const grp = buildProceduralObjectGroup(node, node.id === selectedId);
      scene.add(grp);
      interactiveGroups.push(grp);
    }

    // Raycaster click selection
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    const handlePointerDown = (ev: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(interactiveGroups, true);
      if (hits.length > 0) {
        let cur: THREE.Object3D | null = hits[0].object;
        while (cur && !cur.userData?.forensicNode) {
          cur = cur.parent;
        }
        if (cur?.userData?.forensicNode) {
          onSelectNode(cur.userData.forensicNode as Object3DNode);
          return;
        }
      }
    };

    renderer.domElement.addEventListener('pointerdown', handlePointerDown);

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        const h = entry.contentRect.height;
        if (w > 0 && h > 0) {
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        }
      }
    });
    resizeObserver.observe(container);

    let rafId = 0;
    const animate = () => {
      rafId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('pointerdown', handlePointerDown);
      controls.dispose();
      envTex.dispose();
      pmrem.dispose();
      renderer.dispose();
    };
  }, [scene3d, selectedId]);

  useEffect(() => {
    if (gridRef.current) {
      gridRef.current.visible = showGrid;
    }
  }, [showGrid]);

  const setCameraPreset = (preset: 'iso' | 'top' | 'front') => {
    const cam = cameraRef.current;
    const ctrl = controlsRef.current;
    if (!cam || !ctrl) return;
    ctrl.target.set(0, 0.5, 0);
    if (preset === 'iso') {
      cam.position.set(5.8, 4.8, 6.4);
    } else if (preset === 'top') {
      cam.position.set(0, 9.2, 0.01);
    } else {
      cam.position.set(0, 2.2, 7.6);
    }
    ctrl.update();
  };

  const selectedNode = scene3d.objects.find((o) => o.id === selectedId) || null;

  return (
    <div className="relative h-[420px] w-full overflow-hidden rounded-lg border border-slate-800 bg-[#0d131f]">
      <div ref={containerRef} className="h-full w-full cursor-grab active:cursor-grabbing" />

      {/* Top-left spatial context readout */}
      <div className="pointer-events-none absolute top-3 left-3 rounded border border-slate-800/90 bg-slate-950/85 px-3 py-1.5 backdrop-blur-sm">
        <div className="text-xs font-medium text-slate-200 capitalize">
          Simulated 3D Floor Projection · {scene3d.room_type}
        </div>
        <div className="font-mono text-[11px] text-slate-400 tabular-nums">
          {scene3d.dimensions.width}m × {scene3d.dimensions.depth}m · {scene3d.objects.length} estimated{' '}
          {scene3d.objects.length === 1 ? 'marker' : 'markers'}
        </div>
      </div>

      {scene3d.objects.length === 0 && (
        <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 px-6 text-center">
          <span className="inline-block rounded border border-slate-800 bg-slate-950/90 px-3 py-1.5 font-mono text-xs text-slate-400">
            No localized foreground markers to project into 3D space
          </span>
        </div>
      )}

      {/* Selected 3D marker coordinate card */}
      {selectedNode && (
        <div className="absolute top-3 right-3 max-w-[240px] rounded border border-sky-500/40 bg-slate-950/90 px-3 py-2 text-xs backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono font-semibold text-amber-400 tabular-nums">
              Marker #{selectedNode.marker_number}
            </span>
            <button
              type="button"
              onClick={() => onSelectNode(null)}
              className="text-[11px] text-slate-400 hover:text-slate-200"
            >
              Clear
            </button>
          </div>
          <div className="mt-0.5 font-medium text-slate-100 capitalize">{selectedNode.label}</div>
          <div className="mt-1 font-mono text-[11px] text-slate-400 tabular-nums">
            {selectedNode.confidence !== null
              ? `Est. ${(selectedNode.confidence * 100).toFixed(0)}%`
              : 'Score N/A'}{' '}
            · Sim X {selectedNode.position.x}m · Z {selectedNode.position.z}m
          </div>
        </div>
      )}

      {/* Collapsible bottom camera preset dock */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2">
        <div className="flex items-center gap-1 rounded border border-slate-800 bg-slate-950/90 px-2 py-1 backdrop-blur-md">
          {!dockCollapsed && (
            <>
              <button
                type="button"
                onClick={() => setCameraPreset('iso')}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                <RotateCcw className="h-3.5 w-3.5 text-sky-400" />
                Isometric
              </button>
              <button
                type="button"
                onClick={() => setCameraPreset('top')}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                <Eye className="h-3.5 w-3.5 text-sky-400" />
                Plan View
              </button>
              <button
                type="button"
                onClick={() => setCameraPreset('front')}
                className="rounded px-2 py-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                Front
              </button>
              <button
                type="button"
                onClick={() => setShowGrid((v) => !v)}
                className={`flex items-center gap-1 rounded px-2 py-1 text-xs ${
                  showGrid ? 'bg-sky-500/15 text-sky-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Grid3X3 className="h-3.5 w-3.5" />
                Grid
              </button>
            </>
          )}
          <button
            type="button"
            onClick={() => setDockCollapsed((v) => !v)}
            title={dockCollapsed ? 'Expand 3D controls' : 'Collapse 3D controls'}
            className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            {dockCollapsed ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
};
