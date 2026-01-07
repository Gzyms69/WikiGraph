import React from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchOverlayProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchResults: any[];
  isSearching: boolean;
  focusOnNode: (qid: string, title: string, lang: string) => void;
}

const SearchOverlay: React.FC<SearchOverlayProps> = ({
  searchQuery,
  setSearchQuery,
  searchResults,
  isSearching,
  focusOnNode,
}) => {
  return (
    <div className="absolute top-8 right-8 z-30 w-80">
      <div className="relative group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          {isSearching ? (
            <Loader2 className="text-blue-400 animate-spin" size={18} />
          ) : (
            <Search className="text-white/30" size={18} />
          )}
        </div>
        <input
          type="text"
          className="w-full bg-black/40 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:bg-white/10 transition-all backdrop-blur-xl"
          placeholder="Search the nebula..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        {searchResults.length > 0 && (
          <div className="absolute top-full mt-2 w-full bg-black/90 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-2xl shadow-2xl animate-in zoom-in-95 duration-200">
            {searchResults.map((res, i) => (
              <button
                key={i}
                onClick={() => focusOnNode(res.qid, res.title, res.lang)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors border-b border-white/5 last:border-0 group/item"
              >
                <div>
                  <span className="text-white/90 font-bold block group-hover/item:text-blue-400 transition-colors text-sm">
                    {res.title}
                  </span>
                  <span className="text-white/20 text-[9px] uppercase font-mono tracking-tighter">
                    {res.qid}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-lg border border-white/5">
                  <div
                    className={`w-2 h-2 rounded-sm ${
                      res.lang === 'pl' ? 'bg-[#dc143c]' : 'bg-[#ffce00]'
                    }`}
                  />
                  <span className="text-[9px] text-white/50 font-black uppercase tracking-tighter">
                    {res.lang}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchOverlay;
