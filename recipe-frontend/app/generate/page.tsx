"use client";

import { useUser } from "@clerk/nextjs";
import { Loader2, LogIn, ChefHat } from "lucide-react";
import Link from "next/link";
import RecipeSearch from "../components/RecipeSearch";

export default function GeneratePage() {
  const { isSignedIn, isLoaded } = useUser();

  // Loading Clerk
  if (!isLoaded) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-10 h-10 text-orange-500 animate-spin mb-4" />
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  // Not signed in
  if (!isSignedIn) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-20 h-20 bg-orange-50 rounded-full flex items-center justify-center mb-4">
          <LogIn className="w-10 h-10 text-orange-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Sign in to generate recipes
        </h2>
        <p className="text-gray-600 mb-6 max-w-md">
          Create an account or sign in to start generating delicious recipes
          with AI.
        </p>
        <div className="flex gap-4">
          <Link
            href="/sign-in"
            className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors flex items-center gap-2"
          >
            <LogIn className="w-5 h-5" />
            Sign In
          </Link>
          <Link
            href="/sign-up"
            className="px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Create Account
          </Link>
        </div>
      </div>
    );
  }

  // Signed in - show the recipe generator
  return (
    <div className="py-8">
      {/* Page Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
          <ChefHat className="w-8 h-8 text-orange-600" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
          Generate a Recipe
        </h1>
        <p className="text-lg text-gray-600 max-w-xl mx-auto">
          Enter your available ingredients below and let AI create a delicious
          recipe just for you.
        </p>
      </div>

      {/* Recipe Search Component */}
      <RecipeSearch />
    </div>
  );
}