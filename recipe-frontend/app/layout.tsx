import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ChefAI - AI Recipe Generator",
  description:
    "Generate delicious recipes from your ingredients using AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body
          className={`${inter.className} min-h-screen flex flex-col bg-white text-gray-900`}
        >
          <Navbar />
          <main className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <Footer />
        </body>
      </html>
    </ClerkProvider>
  );
}