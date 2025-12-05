"use client";

import { useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { Search, Loader2, FolderOpen, Plus, RefreshCw, LogIn } from "lucide-react";
import Link from "next/link";
import RecipeCard from "../components/RecipeCard";
import { Recipe } from "@/types/recipe";

export default function SavedRecipesPage() {
  const { isSignedIn, isLoaded } = useUser();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch recipes
  const loadRecipes = async () => {
    if (!isSignedIn) return;

    setIsLoading(true);
    try {
      const res = await fetch("/api/recipes");
      const data = await res.json();

      if (data.error === "Unauthorized") {
        console.error("Unauthorized - user needs to sign in");
        setRecipes([]);
        return;
      }

      setRecipes(data.recipes || []);
    } catch (error) {
      console.error("Failed to load recipes:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete recipe
  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/recipes/${id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (data.success) {
        setRecipes((prev) => prev.filter((r) => r.id !== id));
      } else {
        alert(data.error || "Failed to delete recipe");
      }
    } catch (error) {
      console.error("Delete error:", error);
      alert("Failed to delete recipe. Please try again.");
    }
  };

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadRecipes();
    } else if (isLoaded && !isSignedIn) {
      setIsLoading(false);
    }
  }, [isLoaded, isSignedIn]);

  // Filter recipes by search
  const filteredRecipes = recipes.filter((recipe) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      recipe.title.toLowerCase().includes(query) ||
      recipe.cuisine.toLowerCase().includes(query) ||
      recipe.description.toLowerCase().includes(query)
    );
  });

  // Show loading while Clerk loads
  if (!isLoaded) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-10 h-10 text-orange-500 animate-spin mb-4" />
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  // Show sign in prompt if not signed in
  if (!isSignedIn) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-20 h-20 bg-orange-50 rounded-full flex items-center justify-center mb-4">
          <LogIn className="w-10 h-10 text-orange-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Sign in to view your recipes
        </h2>
        <p className="text-gray-600 mb-6 max-w-md">
          Create an account or sign in to save and manage your generated recipes.
        </p>
        <Link
          href="/sign-in"
          className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors flex items-center gap-2"
        >
          <LogIn className="w-5 h-5" />
          Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Recipes</h1>
          <p className="text-gray-600 mt-1">
            {recipes.length} saved {recipes.length === 1 ? "recipe" : "recipes"}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={loadRecipes}
            disabled={isLoading}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
          <Link
            href="/generate"
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Recipe
          </Link>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, cuisine, or description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-orange-500 animate-spin mb-4" />
          <p className="text-gray-600">Loading your recipes...</p>
        </div>
      )}

      {/* Empty State - No Recipes */}
      {!isLoading && recipes.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 bg-orange-50 rounded-full flex items-center justify-center mb-4">
            <FolderOpen className="w-10 h-10 text-orange-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            No recipes yet
          </h2>
          <p className="text-gray-600 mb-6 max-w-md">
            You haven't generated any recipes yet. Create your first one!
          </p>
          <Link
            href="/generate"
            className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Generate Your First Recipe
          </Link>
        </div>
      )}

      {/* Empty State - No Search Results */}
      {!isLoading && recipes.length > 0 && filteredRecipes.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search className="w-12 h-12 text-gray-300 mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            No matches found
          </h2>
          <p className="text-gray-600 mb-4">No recipes match "{searchQuery}"</p>
          <button
            onClick={() => setSearchQuery("")}
            className="text-orange-500 hover:text-orange-600 font-medium"
          >
            Clear search
          </button>
        </div>
      )}

      {/* Recipe Grid */}
      {!isLoading && filteredRecipes.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRecipes.map((recipe) => (
            <RecipeCard
              key={recipe.id || recipe.title}
              recipe={recipe}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}