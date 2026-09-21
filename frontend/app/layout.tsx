import type { ReactNode } from "react";

export const metadata = {
  title: "Revenue Leakage Investigator",
  description: "AI-assisted revenue assurance and leakage investigation for B2B SaaS",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
