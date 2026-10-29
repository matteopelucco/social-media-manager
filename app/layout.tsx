import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sheepper",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="it" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
