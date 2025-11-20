"use client";

import { useState } from "react";
import {
  ChefHat,
  Clock,
  Globe,
  Download,
  Share2,
  Database,
  Sparkles,
  Trophy,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { Recipe } from "../types/recipe";

interface RecipeDisplayProps {
  recipe: Recipe | null;
  source?: "s3" | "generated";
  matchScore?: number;
}

export default function RecipeDisplay({
  recipe,
  source = "generated",
  matchScore,
}: RecipeDisplayProps) {
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  if (!recipe) {
    return null;
  }

  const toggleStep = (index: number) => {
    setCompletedSteps((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const downloadRecipe = () => {
    const dataStr = JSON.stringify(recipe, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${recipe.title.replace(/\s+/g, "-").toLowerCase()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareRecipe = async () => {
    const shareData = {
      title: recipe.title,
      text: `${recipe.description}\n\nCuisine: ${recipe.cuisine}\nCook Time: ${recipe.cook_time}`,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log("Share failed:", err);
      }
    } else {
      navigator.clipboard.writeText(
        `${recipe.title}\n\n${recipe.description}\n\nCuisine: ${recipe.cuisine}\nCook Time: ${recipe.cook_time}`
      );
      alert("Recipe copied to clipboard!");
    }
  };

  // Calculate Progress
  const progressPercentage = recipe.instructions.length 
    ? Math.round((completedSteps.length / recipe.instructions.length) * 100)
    : 0;

  return (
    <article className="w-full max-w-5xl mx-auto mt-8 pb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* --- STATUS BANNERS --- */}
      {source === "s3" && matchScore !== undefined && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4 shadow-sm">
          <div className="p-2 bg-blue-100 rounded-full">
            <Trophy className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1 text-center sm:text-left">
            <p className="font-bold text-blue-900">Found in Recipe Archive</p>
            <p className="text-sm text-blue-700">
              This recipe matches {Math.round(matchScore)}% of your ingredients.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-blue-100 shadow-sm">
            <Database className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-bold text-blue-600">INSTANT LOAD</span>
          </div>
        </div>
      )}

      {source === "generated" && (
        <div className="mb-6 bg-purple-50 border border-purple-200 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4 shadow-sm">
          <div className="p-2 bg-purple-100 rounded-full">
            <Sparkles className="w-6 h-6 text-purple-600" />
          </div>
          <div className="flex-1 text-center sm:text-left">
            <p className="font-bold text-purple-900">Freshly Created by AI</p>
            <p className="text-sm text-purple-700">
              A unique recipe generated just for you based on your inputs.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-purple-100 shadow-sm">
            <ChefHat className="w-4 h-4 text-purple-500" />
            <span className="text-xs font-bold text-purple-600">NEW RECIPE</span>
          </div>
        </div>
      )}

      {/* --- RECIPE CARD --- */}
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
        
        {/* Header Section */}
        <div className="relative bg-orange-50/50 p-8 md:p-10 border-b border-orange-100">
          <div className="flex justify-between items-start gap-4">
            <div className="space-y-4 flex-1">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 font-serif tracking-tight">
                {recipe.title}
              </h1>
              <p className="text-lg text-gray-600 italic max-w-2xl leading-relaxed">
                {recipe.description}
              </p>
            </div>
            
            {/* Action Buttons (Desktop) */}
            <div className="hidden md:flex gap-2">
              <button onClick={downloadRecipe} className="p-2 hover:bg-white rounded-full text-gray-500 hover:text-orange-600 transition-colors border border-transparent hover:border-gray-200" title="Download JSON">
                <Download className="w-5 h-5" />
              </button>
              <button onClick={shareRecipe} className="p-2 hover:bg-white rounded-full text-gray-500 hover:text-orange-600 transition-colors border border-transparent hover:border-gray-200" title="Share">
                <Share2 className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Meta Tags */}
          <div className="flex flex-wrap gap-3 mt-8">
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm text-sm font-medium text-gray-700">
              <Globe className="w-4 h-4 text-orange-500" />
              {recipe.cuisine}
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm text-sm font-medium text-gray-700">
              <Clock className="w-4 h-4 text-orange-500" />
              {recipe.cook_time}
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm text-sm font-medium text-gray-700">
              <ChefHat className="w-4 h-4 text-orange-500" />
              {recipe.ingredients.length} Ingredients
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid md:grid-cols-12 gap-0">
          
          {/* Left Column: Ingredients (Sticky Sidebar) */}
          <div className="md:col-span-4 bg-orange-50/30 p-8 border-r border-gray-100">
            <div className="sticky top-8">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-sm">🥕</span>
                Ingredients
              </h3>
              
              <div className="space-y-3">
                {recipe.ingredients.map((item, index) => (
                  <div 
                    key={index} 
                    className="group flex items-start gap-3 p-3 rounded-lg bg-white border border-orange-100 shadow-sm hover:shadow-md hover:border-orange-300 transition-all"
                  >
                    <div className="mt-1 w-5 h-5 rounded-full border-2 border-orange-200 flex-shrink-0 group-hover:bg-orange-50"></div>
                    <span className="text-gray-700 font-medium leading-snug">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Instructions */}
          <div className="md:col-span-8 p-8 md:p-10 bg-white">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <span className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-sm">👨‍🍳</span>
                Instructions
              </h3>
              
              <span className="text-xs font-bold px-3 py-1 bg-gray-100 rounded-full text-gray-600">
                {completedSteps.length} / {recipe.instructions.length} Done
              </span>
            </div>

            <div className="space-y-6">
              {recipe.instructions.map((step, index) => {
                const isCompleted = completedSteps.includes(index);
                const cleanStep = step.replace(/^\d+\.\s*/, '');

                return (
                  <div
                    key={index}
                    onClick={() => toggleStep(index)}
                    className={`group relative flex gap-5 cursor-pointer transition-all duration-300 rounded-xl p-4 -mx-4 hover:bg-gray-50 ${
                      isCompleted ? "opacity-50" : ""
                    }`}
                  >
                    <div className="flex-shrink-0 mt-1">
                      {isCompleted ? (
                        <CheckCircle2 className="w-8 h-8 text-green-500 fill-green-50" />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gray-900 text-white flex items-center justify-center font-bold text-sm shadow-md group-hover:scale-110 transition-transform">
                          {index + 1}
                        </div>
                      )}
                    </div>

                    <div className="flex-1 pt-0.5">
                      <p className={`text-lg leading-relaxed transition-all ${
                        isCompleted ? "text-gray-400 line-through" : "text-gray-800"
                      }`}>
                        {cleanStep}
                      </p>
                    </div>

                    {!isCompleted && (
                      <div className="absolute right-4 top-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Circle className="w-5 h-5 text-gray-300" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {progressPercentage === 100 && (
              <div className="mt-12 p-8 bg-green-50 rounded-2xl border border-green-100 text-center animate-in zoom-in duration-300">
                <div className="inline-flex p-3 bg-white rounded-full shadow-sm mb-3">
                  <ChefHat className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="text-2xl font-bold text-green-800 mb-2">Bon Appétit!</h4>
                <p className="text-green-700">
                  You've completed this recipe. Time to dig in!
                </p>
              </div>
            )}
          </div>
        </div>

        {/* --- Sticky Bottom Progress & Action Bar --- */}
        <div className="bg-gray-50 border-t border-gray-200 px-4 sm:px-8 py-4 sticky bottom-0">
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline-block text-sm font-medium text-gray-500 w-20">
              Progress
            </span>
            <div className="flex-1 h-2.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-500 to-red-500 transition-all duration-500 ease-out"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-orange-700 w-12 text-right">
              {progressPercentage}%
            </span>

            {/* Action Buttons (Mobile) */}
            <div className="flex md:hidden gap-1">
              <button onClick={downloadRecipe} className="p-2 rounded-full text-gray-500 hover:text-orange-600 hover:bg-white" title="Download JSON">
                <Download className="w-5 h-5" />
              </button>
              <button onClick={shareRecipe} className="p-2 rounded-full text-gray-500 hover:text-orange-600 hover:bg-white" title="Share">
                <Share2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
        
      </div>
    </article>
  );
}