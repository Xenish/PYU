import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Masper Konsolu",
  description: "Task pipeline işleri için operatör konsolu",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  );
}
