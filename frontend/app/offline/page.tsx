export default function OfflinePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-6 text-center">
      <div className="glass-panel w-full p-10">
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Offline mode</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">You are currently offline</h1>
        <p className="mt-4 text-white/70">
          KASH could not reach the network. Please check your connection and retry. Previously cached pages remain
          available.
        </p>
      </div>
    </main>
  );
}
