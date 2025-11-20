'use client';

import { useState } from 'react';
import SearchForm from './SearchForm';
import ErrorDisplay from './ErrorDisplay';
import LoadingState from './LoadingState';
// Assuming RecipeDisplay is one folder up in components/
import RecipeDisplay from '../RecipeDisplay'; 
import { Recipe, ApiResponse, SearchFilters } from '@/app/types/recipe';

export default function RecipeSearch() {
  // Application State
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [source, setSource] = useState<'s3' | 'generated'>('generated');
  const [matchScore, setMatchScore] = useState<number | undefined>();
  
  // UI State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (filters: SearchFilters) => {
    setLoading(true);
    setError(null);
    setRecipe(null); // Clear previous results while searching

    try {
      console.log('Sending request to API:', filters);

      const response = await fetch('/api/recipes/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      
      // Validate we actually got a recipe back
      if (!data.recipe) {
        throw new Error('No recipe data received from server');
      }

      setRecipe(data.recipe);
      setSource(data.source);
      setMatchScore(data.matchScore);

    } catch (err) {
      console.error('Search failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate recipe. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      
      {/* 1. The Search Form */}
      <div className="mb-8">
        <SearchForm onSearch={handleSearch} isLoading={loading} />
      </div>

      {/* 2. Error Message (if any) */}
      {error && (
        <ErrorDisplay 
          message={error} 
          onDismiss={() => setError(null)} 
        />
      )}

      {/* 3. Loading State */}
      {loading && <LoadingState />}

      {/* 4. Result Display */}
      {!loading && recipe && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <RecipeDisplay 
            recipe={recipe} 
            source={source}
            matchScore={matchScore}
          />
          
          {/* Optional: 'Search Again' helper text */}
          <div className="text-center mt-8 pb-8">
            <p className="text-gray-500 text-sm">
              Not what you wanted? Adjust the filters above and try again!
            </p>
          </div>
        </div>
      )}
    </div>
  );
}