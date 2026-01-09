import React from 'react';
import { Pause, Play, RotateCcw, Settings, Camera, Layers, Globe } from 'lucide-react';

interface ControlDeckProps {
  isPhysicsPaused: boolean;
  setIsPhysicsPaused: (paused: boolean) => void;
  autoRotate: boolean;
  setAutoRotate: (rotate: boolean) => void;
  colorByCommunity: boolean;
  setColorByCommunity: (val: boolean) => void;
  onResetCamera: () => void;
  onOpenSettings: () => void;
}

const ControlDeck: React.FC<ControlDeckProps> = ({
  isPhysicsPaused,
  setIsPhysicsPaused,
  autoRotate,
  setAutoRotate,
  colorByCommunity,
  setColorByCommunity,
  onResetCamera,
  onOpenSettings,
}) => {
  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 pointer-events-auto">
      <div className="flex items-center gap-2 p-2 bg-black/60 border border-white/10 rounded-2xl backdrop-blur-xl shadow-2xl">
        <button 
          onClick={() => setIsPhysicsPaused(!isPhysicsPaused)}
          className={`p-3 rounded-xl transition-all ${
            isPhysicsPaused 
            ? 'bg-amber-500/20 text-amber-500 shadow-inner' 
            : 'hover:bg-white/10 text-white/60 hover:text-white'
          }`}
          title={isPhysicsPaused ? "Resume Physics" : "Pause Physics"}
        >
          {isPhysicsPaused ? <Play size={20} fill="currentColor" /> : <Pause size={20} fill="currentColor" />}
        </button>
        
        <div className="w-px h-8 bg-white/10 mx-1" />
        
        <button 
          onClick={() => setAutoRotate(!autoRotate)}
          className={`p-3 rounded-xl transition-all ${
            autoRotate 
            ? 'bg-blue-500/20 text-blue-400 shadow-inner' 
            : 'hover:bg-white/10 text-white/60 hover:text-white'
          }`}
          title="Toggle Auto-Rotation"
        >
          <RotateCcw size={20} className={autoRotate ? "animate-spin-slow" : ""} />
        </button>

        <button 
          onClick={onResetCamera}
          className="p-3 rounded-xl hover:bg-white/10 text-white/60 hover:text-white transition-all"
          title="Reset Camera View"
        >
          <Camera size={20} />
        </button>
        
        <div className="w-px h-8 bg-white/10 mx-1" />

        <button 
          onClick={() => setColorByCommunity(!colorByCommunity)}
          className={`p-3 rounded-xl transition-all flex items-center gap-2 ${
            colorByCommunity 
            ? 'bg-purple-500/20 text-purple-400 shadow-inner' 
            : 'hover:bg-white/10 text-white/60 hover:text-white'
          }`}
          title={colorByCommunity ? "Color by Language" : "Color by Cluster"}
        >
          {colorByCommunity ? <Layers size={20} /> : <Globe size={20} />}
          <span className="text-[10px] font-black uppercase tracking-tighter">
            {colorByCommunity ? "Cluster" : "Lang"}
          </span>
        </button>

        <div className="w-px h-8 bg-white/10 mx-1" />

        <button 
          onClick={onOpenSettings}
          className="p-3 rounded-xl hover:bg-white/10 text-white/60 hover:text-white transition-all"
          title="System Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </div>
  );
};

export default ControlDeck;
