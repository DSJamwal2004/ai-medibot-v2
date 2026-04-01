export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-slate-500 dot-1" />
        <span className="w-2 h-2 rounded-full bg-slate-500 dot-2" />
        <span className="w-2 h-2 rounded-full bg-slate-500 dot-3" />
      </div>
      <span className="text-xs text-slate-500 ml-1">Analysing…</span>
    </div>
  );
}
