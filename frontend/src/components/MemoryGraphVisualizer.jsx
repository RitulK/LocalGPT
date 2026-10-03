import { useEffect, useRef, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Brain,
  Check,
  GitBranch,
  Layers,
  Link as LinkIcon,
  Maximize2,
  Minimize2,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

const NODE_COLORS = {
  message: {
    bg: '#0f2927',
    border: '#20dcca',
    glow: 'rgba(32, 220, 202, 0.4)',
    text: '#8ffcf0',
    label: 'Message'
  },
  thread_snapshot: {
    bg: '#09251e',
    border: '#10b981',
    glow: 'rgba(16, 185, 129, 0.4)',
    text: '#a7f3d0',
    label: 'Thread'
  },
  preference: {
    bg: '#211233',
    border: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.4)',
    text: '#e9d5ff',
    label: 'Preference'
  },
  default: {
    bg: '#182228',
    border: '#38bdf8',
    glow: 'rgba(56, 189, 248, 0.4)',
    text: '#bae6fd',
    label: 'Memory'
  }
};

export default function MemoryGraphVisualizer({ apiUrl, onRefreshCount }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [connectingSource, setConnectingSource] = useState(null);
  const [relationType, setRelationType] = useState('relates_to');
  const [toast, setToast] = useState(null);

  const canvasRef = useRef(null);
  const simNodesRef = useRef([]);
  const simEdgesRef = useRef([]);
  const transformRef = useRef({ x: 0, y: 0, scale: 1 });
  const isDraggingNodeRef = useRef(null);
  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0 });
  const animationFrameRef = useRef(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`${apiUrl}/memories/graph`);
      const data = await res.json();
      setGraphData(data);
      if (onRefreshCount) onRefreshCount(data.nodes?.length || 0);
    } catch (err) {
      showToast('Failed to load memory graph', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, onRefreshCount]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Synchronize simulation nodes & edges when graphData changes
  useEffect(() => {
    const existingPos = new Map();
    simNodesRef.current.forEach((n) => existingPos.set(n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy }));

    const canvas = canvasRef.current;
    const width = canvas ? canvas.width : 800;
    const height = canvas ? canvas.height : 600;

    const filteredNodes = graphData.nodes.filter((node) => {
      if (filterType !== 'all' && node.node_type !== filterType) return false;
      if (searchQuery && !node.title?.toLowerCase().includes(searchQuery.toLowerCase()) && !node.content?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    });

    const activeNodeIds = new Set(filteredNodes.map((n) => n.id));

    const nodes = filteredNodes.map((n, idx) => {
      const prev = existingPos.get(n.id);
      if (prev) {
        return { ...n, x: prev.x, y: prev.y, vx: prev.vx || 0, vy: prev.vy || 0, radius: 24 };
      }
      const angle = (idx / (filteredNodes.length || 1)) * 2 * Math.PI;
      const dist = 140 + Math.random() * 80;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * dist,
        y: height / 2 + Math.sin(angle) * dist,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        radius: 24
      };
    });

    const edges = graphData.edges
      .filter((e) => activeNodeIds.has(e.source_id) && activeNodeIds.has(e.target_id))
      .map((e) => ({ ...e }));

    simNodesRef.current = nodes;
    simEdgesRef.current = edges;
  }, [graphData, filterType, searchQuery]);

  // Force-directed simulation & canvas rendering loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const updatePhysics = () => {
      const nodes = simNodesRef.current;
      const edges = simEdgesRef.current;
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // 1. Repulsion between all pairs
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);
          if (dist < 400) {
            const force = 3200 / distSq;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            nodes[i].vx -= fx;
            nodes[i].vy -= fy;
            nodes[j].vx += fx;
            nodes[j].vy += fy;
          }
        }
      }

      // 2. Spring attraction along edges
      const nodeMap = new Map();
      nodes.forEach((n) => nodeMap.set(n.id, n));

      for (let i = 0; i < edges.length; i++) {
        const src = nodeMap.get(edges[i].source_id);
        const tgt = nodeMap.get(edges[i].target_id);
        if (src && tgt) {
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const targetDist = edges[i].relation === 'follows' ? 95 : 140;
          const force = (dist - targetDist) * 0.045;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          src.vx += fx;
          src.vy += fy;
          tgt.vx -= fx;
          tgt.vy -= fy;
        }
      }

      // 3. Gravity towards center and velocity damping
      nodes.forEach((n) => {
        if (isDraggingNodeRef.current && isDraggingNodeRef.current.id === n.id) {
          return;
        }
        n.vx += (centerX - n.x) * 0.003;
        n.vy += (centerY - n.y) * 0.003;
        n.vx *= 0.84;
        n.vy *= 0.84;
        n.x += n.vx;
        n.y += n.vy;
      });
    };

    const render = () => {
      updatePhysics();

      const { x: panX, y: panY, scale } = transformRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(panX, panY);
      ctx.scale(scale, scale);

      const nodes = simNodesRef.current;
      const edges = simEdgesRef.current;
      const nodeMap = new Map();
      nodes.forEach((n) => nodeMap.set(n.id, n));

      // Draw Edges
      edges.forEach((edge) => {
        const src = nodeMap.get(edge.source_id);
        const tgt = nodeMap.get(edge.target_id);
        if (!src || !tgt) return;

        ctx.save();
        const isFollows = edge.relation === 'follows';
        ctx.strokeStyle = isFollows ? 'rgba(32, 220, 202, 0.45)' : 'rgba(168, 85, 247, 0.6)';
        ctx.lineWidth = isFollows ? 1.5 : 2;

        if (isFollows) {
          ctx.setLineDash([4, 4]);
        }

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();

        // Arrow head for directed follows
        if (isFollows) {
          const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
          const arrowX = tgt.x - Math.cos(angle) * (tgt.radius + 6);
          const arrowY = tgt.y - Math.sin(angle) * (tgt.radius + 6);
          ctx.setLineDash([]);
          ctx.fillStyle = '#20dcca';
          ctx.beginPath();
          ctx.moveTo(arrowX, arrowY);
          ctx.lineTo(arrowX - 8 * Math.cos(angle - Math.PI / 6), arrowY - 8 * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(arrowX - 8 * Math.cos(angle + Math.PI / 6), arrowY - 8 * Math.sin(angle + Math.PI / 6));
          ctx.closePath();
          ctx.fill();
        }
        ctx.restore();
      });

      // Draw Connecting line if in connect mode
      if (connectingSource) {
        const src = nodeMap.get(connectingSource.id);
        if (src) {
          ctx.save();
          ctx.strokeStyle = '#20dcca';
          ctx.setLineDash([6, 6]);
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(canvas.width / 2, canvas.height / 2);
          ctx.stroke();
          ctx.restore();
        }
      }

      // Draw Nodes
      nodes.forEach((node) => {
        const isSelected = selectedNode && selectedNode.id === node.id;
        const isConnecting = connectingSource && connectingSource.id === node.id;
        const color = NODE_COLORS[node.node_type] || NODE_COLORS.default;

        ctx.save();

        // Outer Glow
        if (isSelected || isConnecting) {
          ctx.shadowColor = color.border;
          ctx.shadowBlur = 24;
        } else {
          ctx.shadowColor = color.glow;
          ctx.shadowBlur = 10;
        }

        // Circle Body
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = color.bg;
        ctx.fill();
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.strokeStyle = isSelected ? '#ffffff' : color.border;
        ctx.stroke();

        // Inner Icon / Initials
        ctx.fillStyle = color.text;
        ctx.font = '600 11px system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const typeInitial = node.node_type === 'thread_snapshot' ? 'T' : node.node_type === 'preference' ? 'P' : 'M';
        ctx.fillText(typeInitial, node.x, node.y);

        // Text Label below
        ctx.shadowBlur = 0;
        ctx.fillStyle = isSelected ? '#ffffff' : '#cbdad6';
        ctx.font = isSelected ? '600 12px system-ui, sans-serif' : '500 11px system-ui, sans-serif';
        const titleText = (node.title || node.id).slice(0, 24) + ((node.title || '').length > 24 ? '…' : '');
        ctx.fillText(titleText, node.x, node.y + node.radius + 15);

        ctx.restore();
      });

      ctx.restore();

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [connectingSource, selectedNode]);

  // Handle Resize
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      if (canvas && canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Coordinate conversion helper
  const getCanvasCoords = (clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const { x: panX, y: panY, scale } = transformRef.current;
    return {
      x: (clientX - rect.left - panX) / scale,
      y: (clientY - rect.top - panY) / scale
    };
  };

  const handlePointerDown = (e) => {
    const coords = getCanvasCoords(e.clientX, e.clientY);
    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - coords.x;
      const dy = n.y - coords.y;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 5;
    });

    if (clickedNode) {
      if (connectingSource) {
        if (connectingSource.id !== clickedNode.id) {
          handleCreateEdge(connectingSource.id, clickedNode.id);
        }
        setConnectingSource(null);
        return;
      }
      isDraggingNodeRef.current = clickedNode;
      setSelectedNode(clickedNode);
    } else {
      if (connectingSource) {
        setConnectingSource(null);
      }
      isPanningRef.current = true;
      panStartRef.current = { x: e.clientX - transformRef.current.x, y: e.clientY - transformRef.current.y };
    }
  };

  const handlePointerMove = (e) => {
    if (isDraggingNodeRef.current) {
      const coords = getCanvasCoords(e.clientX, e.clientY);
      isDraggingNodeRef.current.x = coords.x;
      isDraggingNodeRef.current.y = coords.y;
      isDraggingNodeRef.current.vx = 0;
      isDraggingNodeRef.current.vy = 0;
    } else if (isPanningRef.current) {
      transformRef.current.x = e.clientX - panStartRef.current.x;
      transformRef.current.y = e.clientY - panStartRef.current.y;
    }
  };

  const handlePointerUp = () => {
    isDraggingNodeRef.current = null;
    isPanningRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.min(Math.max(transformRef.current.scale * zoomFactor, 0.3), 3.0);
    transformRef.current.scale = newScale;
  };

  const handleZoom = (direction) => {
    const factor = direction === 'in' ? 1.25 : 0.8;
    transformRef.current.scale = Math.min(Math.max(transformRef.current.scale * factor, 0.3), 3.0);
  };

  const handleResetView = () => {
    transformRef.current = { x: 0, y: 0, scale: 1 };
  };

  const handleCreateEdge = async (sourceId, targetId) => {
    try {
      const res = await fetch(`${apiUrl}/memories/edges`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: sourceId,
          target_id: targetId,
          relation: relationType
        })
      });
      if (!res.ok) throw new Error('Failed to link nodes');
      showToast(`Linked: ${relationType}`, 'success');
      fetchGraph();
    } catch (err) {
      showToast('Could not link memory nodes', 'error');
    }
  };

  const handleDeleteNode = async (nodeId) => {
    try {
      const res = await fetch(`${apiUrl}/memories/${nodeId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete node');
      showToast('Memory node deleted', 'info');
      setSelectedNode(null);
      fetchGraph();
    } catch (err) {
      showToast('Delete failed', 'error');
    }
  };

  const handleDeleteEdge = async (edgeId) => {
    try {
      const res = await fetch(`${apiUrl}/memories/edges/${edgeId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete edge');
      showToast('Link removed', 'info');
      fetchGraph();
    } catch (err) {
      showToast('Delete edge failed', 'error');
    }
  };

  const connectedEdges = selectedNode
    ? graphData.edges.filter((e) => e.source_id === selectedNode.id || e.target_id === selectedNode.id)
    : [];

  return (
    <div className="relative flex h-full w-full overflow-hidden bg-[#040908]">
      {/* Visualizer Canvas Area */}
      <div className="relative flex-1 h-full overflow-hidden">
        {/* Top Control Bar */}
        <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          <div className="pointer-events-auto flex items-center gap-2 rounded-2xl border border-white/[0.08] bg-[#07100f]/85 p-1.5 backdrop-blur-xl shadow-xl">
            <button
              onClick={() => setFilterType('all')}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                filterType === 'all'
                  ? 'border border-[#28ead8]/30 bg-[#20dcca]/15 text-[#8ffcf0]'
                  : 'text-[#8da19c] hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              All ({graphData.nodes.length})
            </button>
            <button
              onClick={() => setFilterType('message')}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                filterType === 'message'
                  ? 'border border-[#28ead8]/30 bg-[#20dcca]/15 text-[#8ffcf0]'
                  : 'text-[#8da19c] hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              Notes
            </button>
            <button
              onClick={() => setFilterType('thread_snapshot')}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                filterType === 'thread_snapshot'
                  ? 'border border-emerald-400/30 bg-emerald-500/15 text-emerald-300'
                  : 'text-[#8da19c] hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              Threads
            </button>
            <button
              onClick={() => setFilterType('preference')}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                filterType === 'preference'
                  ? 'border border-purple-400/30 bg-purple-500/15 text-purple-300'
                  : 'text-[#8da19c] hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              Preferences
            </button>
          </div>

          <div className="pointer-events-auto flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-[#6b827d]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search graph..."
                className="h-9 w-44 rounded-xl border border-white/[0.08] bg-[#07100f]/85 pl-9 pr-3 text-xs text-white placeholder:text-[#6b827d] outline-none backdrop-blur-xl transition focus:w-60 focus:border-[#28ead8]/35"
              />
            </div>
            <button
              onClick={fetchGraph}
              disabled={isLoading}
              className="grid h-9 w-9 place-items-center rounded-xl border border-white/[0.08] bg-[#07100f]/85 text-[#8da19c] backdrop-blur-xl transition hover:border-[#28ead8]/30 hover:text-[#8ffcf0]"
              title="Refresh graph"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Floating Connect Prompt */}
        {connectingSource && (
          <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 flex items-center gap-3 rounded-2xl border border-[#28ead8]/30 bg-[#07100f]/95 px-4 py-2.5 shadow-2xl backdrop-blur-xl">
            <Sparkles className="h-4 w-4 text-[#8ffcf0] animate-pulse" />
            <span className="text-xs text-[#cbdad6]">
              Click a target node to connect with relation:
            </span>
            <select
              value={relationType}
              onChange={(e) => setRelationType(e.target.value)}
              className="rounded-lg border border-white/[0.1] bg-[#0b1716] px-2 py-1 text-xs text-[#8ffcf0] outline-none"
            >
              <option value="relates_to">relates_to</option>
              <option value="references">references</option>
              <option value="derived_from">derived_from</option>
              <option value="follows">follows</option>
            </select>
            <button
              onClick={() => setConnectingSource(null)}
              className="rounded-lg p-1 text-[#6b827d] hover:bg-white/[0.06] hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Canvas Element */}
        <canvas
          ref={canvasRef}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onWheel={handleWheel}
          className="h-full w-full cursor-grab active:cursor-grabbing"
        />

        {/* Empty State Banner */}
        {graphData.nodes.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none p-6 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-3xl border border-[#28ead8]/20 bg-[#20dcca]/10 text-[#71fff1] shadow-[0_0_50px_rgba(32,220,202,0.15)] mb-4">
              <Brain className="h-8 w-8" />
            </div>
            <h3 className="text-xl font-semibold text-white">Your Memory Graph is Empty</h3>
            <p className="mt-2 max-w-md text-sm text-[#819690] leading-6">
              Capture knowledge from your chats! Hover over any assistant message in Chat to save notes or thread snapshots into this interconnected graph.
            </p>
          </div>
        )}

        {/* Floating Zoom / Reset Controls */}
        <div className="absolute bottom-5 left-5 z-20 flex items-center gap-1.5 rounded-2xl border border-white/[0.08] bg-[#07100f]/85 p-1 backdrop-blur-xl shadow-xl">
          <button
            onClick={() => handleZoom('in')}
            className="grid h-8 w-8 place-items-center rounded-xl text-[#8da19c] transition hover:bg-white/[0.06] hover:text-white"
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleZoom('out')}
            className="grid h-8 w-8 place-items-center rounded-xl text-[#8da19c] transition hover:bg-white/[0.06] hover:text-white"
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <div className="h-4 w-px bg-white/[0.1] my-auto" />
          <button
            onClick={handleResetView}
            className="grid h-8 w-8 place-items-center rounded-xl text-[#8da19c] transition hover:bg-white/[0.06] hover:text-white"
            title="Reset layout view"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Inspector Side Drawer */}
      {selectedNode && (
        <aside className="relative z-30 flex h-full w-96 flex-col border-l border-white/[0.08] bg-[#07100f]/95 shadow-2xl backdrop-blur-2xl animate-in slide-in-from-right duration-300">
          <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4">
            <div className="flex items-center gap-2">
              <span className="rounded-lg border border-[#28ead8]/30 bg-[#20dcca]/10 px-2 py-0.5 text-[11px] font-semibold uppercase text-[#8ffcf0]">
                {selectedNode.node_type}
              </span>
              <span className="text-xs text-[#637a75] font-mono">{selectedNode.id.slice(0, 10)}</span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="rounded-lg p-1.5 text-[#6b827d] transition hover:bg-white/[0.06] hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            <div>
              <h2 className="text-base font-semibold text-white leading-6">
                {selectedNode.title || 'Untitled Memory'}
              </h2>
              <div className="mt-1 flex items-center gap-3 text-xs text-[#637a75]">
                <span>{new Date(selectedNode.created_at).toLocaleDateString()}</span>
                {selectedNode.source_conversation_id && (
                  <span>From Chat #{selectedNode.source_conversation_id}</span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setConnectingSource(selectedNode)}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-[#28ead8]/25 bg-[#20dcca]/10 px-3 py-2 text-xs font-semibold text-[#8ffcf0] transition hover:bg-[#20dcca]/20"
              >
                <LinkIcon className="h-3.5 w-3.5" />
                Connect to another node
              </button>
              <button
                onClick={() => handleDeleteNode(selectedNode.id)}
                className="grid h-8 w-8 place-items-center rounded-xl border border-rose-400/25 bg-rose-400/10 text-rose-300 transition hover:bg-rose-400/20"
                title="Delete node"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="rounded-2xl border border-white/[0.07] bg-[#0b1716] p-4">
              <div className="text-xs font-medium uppercase tracking-wider text-[#637a75] mb-2">Content</div>
              <div className="prose prose-invert prose-sm max-w-none text-[#d6e5e1] leading-6">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {selectedNode.content}
                </ReactMarkdown>
              </div>
            </div>

            {connectedEdges.length > 0 && (
              <div>
                <div className="text-xs font-medium uppercase tracking-wider text-[#637a75] mb-2">
                  Connected Relationships ({connectedEdges.length})
                </div>
                <div className="space-y-2">
                  {connectedEdges.map((edge) => {
                    const isOutgoing = edge.source_id === selectedNode.id;
                    const otherId = isOutgoing ? edge.target_id : edge.source_id;
                    const otherNode = graphData.nodes.find((n) => n.id === otherId);
                    return (
                      <div
                        key={edge.id}
                        className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-[#0b1716] p-2.5 text-xs text-[#b8ccc6]"
                      >
                        <div className="min-w-0 flex-1">
                          <span className="text-[#8ffcf0] font-mono text-[10px]">
                            {isOutgoing ? `→ ${edge.relation} →` : `← ${edge.relation} ←`}
                          </span>
                          <button
                            onClick={() => otherNode && setSelectedNode(otherNode)}
                            className="block truncate text-left font-medium text-white hover:underline mt-0.5"
                          >
                            {otherNode?.title || otherId}
                          </button>
                        </div>
                        <button
                          onClick={() => handleDeleteEdge(edge.id)}
                          className="rounded p-1 text-[#6b827d] transition hover:bg-rose-400/10 hover:text-rose-300"
                          title="Remove link"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* Floating Notification Toast */}
      {toast && (
        <div
          className={`absolute bottom-5 right-5 z-50 flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-xs shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-2 ${
            toast.type === 'error'
              ? 'border-rose-400/30 bg-rose-950/80 text-rose-200'
              : 'border-[#28ead8]/30 bg-[#071f1c]/90 text-[#8ffcf0]'
          }`}
        >
          <Check className="h-4 w-4" />
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}
