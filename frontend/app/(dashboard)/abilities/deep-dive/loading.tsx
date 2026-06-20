export default function AbilitiesDeepDiveLoading() {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="h-5 w-60 rounded-full bg-white/10 animate-pulse" />
      <div className="glass-panel h-48 w-full animate-pulse" />
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="glass-panel h-64 animate-pulse" />
        <div className="glass-panel h-64 animate-pulse" />
      </div>
      <div className="glass-panel h-56 animate-pulse" />
    </main>
  );
}
