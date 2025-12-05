"use client";

import { useState } from "react";
import Link from "next/link";
import { Clock, ChefHat, Calendar, Trash2, Loader2 } from "lucide-react";
import { Recipe } from "@/types/recipe";

interface RecipeCardProps {
  recipe: Recipe;
  onDelete?: (id: string) => void;
}

export default function RecipeCard({ recipe, onDelete }: RecipeCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return null;
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(true);
  };

  const handleConfirmDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!recipe.id || !onDelete) return;

    setIsDeleting(true);
    try {
      await onDelete(recipe.id);
    } finally {
      setIsDeleting(false);
      setShowConfirm(false);
    }
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(false);
  };

  return (
    <Link href={`/saved/${recipe.id}`}>
      <div className="group relative bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg hover:border-orange-300 transition-all h-full flex flex-col">
        {/* Delete Confirmation Overlay */}
        {showConfirm && (
          <div
            className="absolute inset-0 bg-black/60 z-10 flex flex-col items-center justify-center p-4 rounded-xl"
            onClick={(e) => e.preventDefault()}
          >
            <p className="text-white text-center font-medium mb-4">
              Delete this recipe?
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleCancelDelete}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="h-24 bg-gradient-to-r from-orange-400 to-red-400 flex items-center justify-center relative">
          <ChefHat className="w-10 h-10 text-white/80" />

          {/* Delete Button */}
          {onDelete && !showConfirm && (
            <button
              onClick={handleDeleteClick}
              className="absolute top-2 right-2 p-2 bg-white/20 hover:bg-white/40 rounded-full opacity-0 group-hover:opacity-100 transition-all"
              title="Delete recipe"
            >
              <Trash2 className="w-4 h-4 text-white" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-5 flex-1 flex flex-col">
          {/* Cuisine Badge */}
          <span className="self-start text-xs font-medium bg-orange-100 text-orange-700 px-2 py-1 rounded-full mb-3">
            {recipe.cuisine}
          </span>

          {/* Title */}
          <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
            {recipe.title}
          </h3>

          {/* Description */}
          <p className="text-gray-600 text-sm mb-4 line-clamp-2 flex-1">
            {recipe.description}
          </p>

          {/* Meta Info */}
          <div className="flex items-center justify-between text-sm text-gray-500 pt-3 border-t border-gray-100">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{recipe.cook_time}</span>
            </div>
            <span>{recipe.ingredients.length} ingredients</span>
          </div>

          {/* Date */}
          {recipe.last_modified && (
            <div className="flex items-center gap-1 text-xs text-gray-400 mt-2">
              <Calendar className="w-3 h-3" />
              <span>{formatDate(recipe.last_modified)}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}