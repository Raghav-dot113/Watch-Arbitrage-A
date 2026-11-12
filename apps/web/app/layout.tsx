import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import Providers from "./Providers";
import { AuthProvider } from "./AuthProvider";
import "./globals.css";
import "@bryntum/core-business/fontawesome/css/fontawesome.css";
import "@bryntum/core-business/fontawesome/css/solid.css";
import "@bryntum/grid-business/grid.css";
import "@bryntum/grid-business/svalbard-dark.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ChronoArb",
  description: "B2B dealer acquisition intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <AppRouterCacheProvider options={{ enableCssLayer: true }}>
          <Providers>
            <AuthProvider>
              <main>{children}</main>
            </AuthProvider>
          </Providers>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
