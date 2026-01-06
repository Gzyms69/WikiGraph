import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WikiGraph Lab",
  description: "High-performance 3D Wikipedia Knowledge Graph Visualizer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
