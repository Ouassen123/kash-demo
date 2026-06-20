import Link from 'next/link';

import { KashJourneyRunner } from '@/components/kash/kash-journey-runner';

export default function KashStartPage() {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
      </div>

      <KashJourneyRunner />
    </main>
  );
}
