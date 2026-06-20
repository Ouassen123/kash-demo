import type { Metadata } from 'next';
import { Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import QueryProvider from '../providers/query-provider';
import { ServiceWorkerRegister } from '../components/performance/service-worker-register';
import { AuthProvider } from '../lib/auth-context';
import { TopNav } from '../components/layout/top-nav';
import { AssistantPopup } from '../components/onboarding/assistant-popup';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-sans' });
const jetBrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

export const metadata: Metadata = {
  title: 'KASH Intelligence Platform',
  description: 'Career intelligence scoring and insights across Knowledge, Abilities, Skills, and Holistic Intelligence.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${jetBrains.variable}`}>
      <body className="bg-midnight text-white antialiased">
        <QueryProvider>
          <AuthProvider>
            <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(91,129,255,0.25),_rgba(4,8,20,0.9))]">
              <TopNav />
              {children}
              <AssistantPopup />
            </div>
          </AuthProvider>
        </QueryProvider>
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
