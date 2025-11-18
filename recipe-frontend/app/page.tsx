// app/page.tsx
'use client';

import { useState } from 'react';
import RecipeForm from './components/RecipeForm';
import RecipeDisplay from './components/RecipeDisplay';

// This should be the same structure as your Pydantic model in the backend
interface Recipe {
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  cook_time: string;
  cuisine: string;
}

export default function Home() {
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateRecipe = async (formData: any) => {
    setIsLoading(true);
    setError(null);
    setRecipe(null);

    // IMPORTANT: Replace this with your actual Modal web endpoint URL
    const API_URL = "https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run";

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data: Recipe = await response.json();
      setRecipe(data);

    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-50">
      <div className="z-10 w-full max-w-5xl items-center justify-center font-mono text-sm flex flex-col">
        <h1 className="text-4xl font-bold mb-8 text-gray-800">AI Recipe Generator</h1>
        <p className="mb-8 text-gray-600">Enter your ingredients and let the AI create a recipe for you!</p>
        
        <RecipeForm onSubmit={handleGenerateRecipe} isLoading={isLoading} />

        {isLoading && <p className="mt-8 text-blue-600">Generating your masterpiece...</p>}

        {error && <p className="mt-8 text-red-500 bg-red-100 p-4 rounded-md">Error: {error}</p>}

        {recipe && <RecipeDisplay recipe={recipe} />}
      </div>
    </main>
  );
}