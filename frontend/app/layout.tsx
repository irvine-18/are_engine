import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "SCR Asset Market Risk",
  description: "Solvency II SCR asset market risk — economic scenarios, asset pricing and SCR reporting.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
