/**
 * Root layout component for the Next.js frontend app.
 * - Sets up HTML structure, global Tailwind styles, and metadata.
 * - Wraps all pages/components in the app directory.
 */

import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RAG Q&A Demo",
  description:
    "Retrieval-Augmented Generation Q&A assistant demo. Ask questions and get answers with source citations.",
  viewport: "width=device-width, initial-scale=1",
  icons: [
    { rel: "icon", url: "/favicon.ico" },
    { rel: "apple-touch-icon", url: "/apple-touch-icon.png" },
  ],
  openGraph: {
    title: "RAG Q&A Demo",
    description:
      "Retrieval-Augmented Generation Q&A assistant demo. Ask questions and get answers with source citations.",
    url: "https://your-demo-url.com",
    siteName: "RAG Q&A Demo",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "RAG Q&A Demo",
    description:
      "Retrieval-Augmented Generation Q&A assistant demo. Ask questions and get answers with source citations.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-gray-50">
      <head />
      <body className="min-h-screen font-sans antialiased bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  );
}
