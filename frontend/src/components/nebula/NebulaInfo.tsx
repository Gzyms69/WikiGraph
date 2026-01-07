import React from 'react';
import { Zap, Activity } from 'lucide-react';

interface NebulaInfoProps {
  selectedLangs: string[];
  activeNodeCount: number;
}

const NebulaInfo: React.FC<NebulaInfoProps> = ({ selectedLangs, activeNodeCount }) => {
  return (
    <>
      <div className="absolute top-8 left-8 z-20 pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500 rounded-lg shadow-lg shadow-blue-500/20">
            <Zap className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-white italic leading-none">
              WIKIGRAPH <span className="text-blue-400">LAB</span>
            </h1>
            <div className="flex gap-2 items-center mt-2">
              {selectedLangs.map((l) => (
                <span
                  key={l}
                  className="flex items-center gap-1 px-2 py-0.5 bg-white/5 rounded border border-white/10 text-[8px] font-black text-white/40 uppercase tracking-widest"
                >
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      l === 'pl' ? 'bg-[#dc143c]' : 'bg-[#ffce00]'
                    }`}
                  />
                  {l}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="absolute bottom-8 left-8 flex gap-4 pointer-events-none">
        <div className="px-4 py-2 bg-black/40 border border-white/10 rounded-full backdrop-blur-md flex items-center gap-2 shadow-2xl shadow-black">
          <Activity className="text-green-500" size={14} />
          <span className="text-[9px] text-white/60 font-bold uppercase tracking-widest">
            Active Nodes: {activeNodeCount.toLocaleString()}
          </span>
        </div>
      </div>
    </>
  );
};

export default NebulaInfo;
