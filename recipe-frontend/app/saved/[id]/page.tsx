"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { ArrowLeft, Loader2, LogIn } from "lucide-react";
import Link from "next/link";
import RecipeDisplay from "../../components/RecipeDisplay";
import { Recipe } from "@/types/recipe";

export default function RecipeDetailPage() {
  const params = useParams();
  const { isSignedIn, isLoaded } = useUser();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRecipe = async () => {
      if (!isSignedIn) {
        setIsLoading(false);
        return;
      }

      try {
        const res = await fetch(`/api/recipes/${params.id}`);

        if (!res.ok) {
          if (res.status === 401) {
            setError("Please sign in to view this recipe");
          } else if (res.status === 404) {
            setError("Recipe not found");
          } else {
            setError("Failed to load recipe");
          }
          return;
        }

        const data = await res.json();

        if (data.error) {
          setError(data.error);
          return;
        }

        setRecipe(data);
      } catch (err) {
        console.error("Failed to load recipe:", err);
        setError("Failed to load recipe");
      } finally {
        setIsLoading(false);
      }
    };

    if (isLoaded && params.id) {
      loadRecipe();
    }
  }, [params.id, isLoaded, isSignedIn]);

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
          Sign in to view this recipe
        </h2>
        <p className="text-gray-600 mb-6">
          You need to be signed in to view your saved recipes.
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

  // Loading recipe
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-10 h-10 text-orange-500 animate-spin mb-4" />
        <p className="text-gray-600">Loading recipe...</p>
      </div>
    );
  }

  // Error state
  if (error || !recipe) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          {error || "Recipe Not Found"}
        </h1>
        <p className="text-gray-600 mb-6">
          This recipe doesn't exist or you don't have access to it.
        </p>
        <Link
          href="/saved"
          className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
        >
          Back to My Recipes
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Back Button */}
      <Link
        href="/saved"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-orange-500 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to My Recipes
      </Link>

      {/* Recipe Display */}
      <RecipeDisplay recipe={recipe} source="s3" />
    </div>
  );
}