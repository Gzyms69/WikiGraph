import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Zap, Loader2, CheckCircle2, ChevronRight } from 'lucide-react';

interface InitializationScreenProps {
  isLoading: boolean;
  selectedLangs: string[];
  toggleLang: (lang: string) => void;
  startNebula: () => void;
}

const API_BASE = "http://localhost:8000";

// Reusing the hash color logic for consistency
const getLangColor = (lang: string) => {
  let hash = 0;
  for (let i = 0; i < lang.length; i++) {
    hash = lang.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash % 360);
  return `hsl(${h}, 70%, 50%)`;
};

const InitializationScreen: React.FC<InitializationScreenProps> = ({
  isLoading,
  selectedLangs,
  toggleLang,
  startNebula,
}) => {
  const [availableLangs, setAvailableLangs] = useState<string[]>([]);
  const [isFetchingLangs, setIsFetchingLangs] = useState(true);

  useEffect(() => {
    const fetchLangs = async () => {
      try {
        const res = await axios.get(`${API_BASE}/graph/languages`);
        setAvailableLangs(res.data.languages || []);
      } catch (e) {
        console.error("Failed to fetch languages", e);
        // Fallback to empty if API fails, preventing hardcoded assumptions
        setAvailableLangs([]);
      } finally {
        setIsFetchingLangs(false);
      }
    };
    fetchLangs();
  }, []);

  // Browser-native language name formatter
  const langName = new Intl.DisplayNames(['en'], { type: 'language' });

  return (
    <div className="absolute inset-0 z-50 bg-[#050505] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-3xl shadow-2xl">
        <div className="flex items-center gap-4 mb-8">
          <div className="p-3 bg-blue-600 rounded-2xl shadow-xl shadow-blue-600/20">
            <Zap className="text-white" size={32} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-white tracking-tight italic uppercase">
              WikiGraph <span className="text-blue-500">Lab</span>
            </h2>
            <p className="text-white/20 text-[9px] font-bold uppercase tracking-[0.3em] mt-2">
              Initialization Protocol
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-white/30 text-[10px] font-bold uppercase tracking-widest ml-1">
              Detected Knowledge Clusters
            </label>
            
            {isFetchingLangs ? (
               <div className="flex justify-center p-4">
                 <Loader2 className="animate-spin text-white/20" size={24} />
               </div>
            ) : availableLangs.length === 0 ? (
               <div className="p-4 text-center text-white/40 text-xs border border-dashed border-white/10 rounded-2xl">
                 No languages found in the graph.
               </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
                {availableLangs.map((l) => (
                  <button
                    key={l}
                    onClick={() => toggleLang(l)}
                    className={`flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 ${
                      selectedLangs.includes(l)
                        ? 'bg-white/10 border-blue-500/50 scale-[1.02]'
                        : 'bg-white/5 border-white/5 hover:bg-white/10'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full shadow-lg"
                        style={{ backgroundColor: getLangColor(l) }}
                      />
                      <span className="text-white font-bold uppercase tracking-tighter text-xs truncate">
                        {/* Try to format name, fallback to code if fails */}
                        {(() => {
                          try { return langName.of(l); } 
                          catch { return l; }
                        })()}
                      </span>
                    </div>
                    {selectedLangs.includes(l) && (
                      <CheckCircle2 className="text-blue-500" size={16} />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            disabled={selectedLangs.length === 0 || isLoading}
            onClick={startNebula}
            className="w-full py-5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/20 flex items-center justify-center gap-3 group"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                SYNTHESIZE NEBULA
                <ChevronRight
                  className="group-hover:translate-x-1 transition-transform"
                  size={20}
                />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InitializationScreen;
