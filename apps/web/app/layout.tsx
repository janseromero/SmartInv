import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

import './globals.css';

export const metadata: Metadata = {
  title: 'SmartInv — AI-Powered MRO Inventory Intelligence',
  description:
    'A trusted intelligence layer for MRO inventory decisions: explainable AI, governed agents, and executive-grade narratives.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
