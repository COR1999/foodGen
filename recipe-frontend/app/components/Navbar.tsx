"use client";

import { useState } from "react";
import Link from "next/link";
import {
  useUser,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import { Menu, X, ChefHat } from "lucide-react";

interface NavLink {
  name: string;
  href: string;
  requiresAuth: boolean;
}

const Navbar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const { isSignedIn, isLoaded } = useUser();

  const navLinks: NavLink[] = [
    { name: "Home", href: "/", requiresAuth: false },
    { name: "Generate", href: "/generate", requiresAuth: true },
    { name: "My Recipes", href: "/saved", requiresAuth: true },
  ];

  // Filter links based on auth status
  const visibleLinks = navLinks.filter(
    (link) => !link.requiresAuth || isSignedIn
  );

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2">
              <ChefHat className="h-8 w-8 text-orange-500" />
              <span className="font-bold text-xl text-gray-900">ChefAI</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {visibleLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="text-gray-600 hover:text-orange-500 font-medium transition-colors"
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Auth Buttons (Desktop) */}
          <div className="hidden md:flex items-center space-x-4">
            {!isLoaded ? (
              // Loading state
              <div className="h-8 w-20 bg-gray-200 animate-pulse rounded-lg" />
            ) : isSignedIn ? (
              // Signed in - show user button
              <UserButton
                afterSignOutUrl="/"
                appearance={{
                  elements: {
                    avatarBox: "w-10 h-10",
                  },
                }}
              />
            ) : (
              // Not signed in - show sign in/up buttons
              <>
                <SignInButton mode="modal">
                  <button className="text-gray-600 hover:text-gray-900 font-medium">
                    Log in
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                    Sign up
                  </button>
                </SignUpButton>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-600 hover:text-gray-900"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-gray-200">
          <div className="px-4 pt-2 pb-4 space-y-2">
            {visibleLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-50"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {link.name}
              </Link>
            ))}

            {!isLoaded ? (
              <div className="pt-4 border-t border-gray-200">
                <div className="h-10 bg-gray-200 animate-pulse rounded-lg" />
              </div>
            ) : !isSignedIn ? (
              <div className="pt-4 border-t border-gray-200 space-y-2">
                <SignInButton mode="modal">
                  <button
                    className="w-full px-4 py-2 text-gray-600 font-medium rounded-lg hover:bg-gray-50"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Log in
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button
                    className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Sign up
                  </button>
                </SignUpButton>
              </div>
            ) : (
              <div className="pt-4 border-t border-gray-200 flex justify-center">
                <UserButton afterSignOutUrl="/" />
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;