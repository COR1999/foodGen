'use client';

import { useState } from 'react';
import IngredientInput from './IngredientInput';
import CuisineSelect from './CuisineSelect';
import CookingStyleSelect from './CookingStyleSelect';
import AdvancedFilters from './AdvancedFilters';
import Button from '../ui/Button';
import { SearchFilters } from '@/app/types/recipe';

interface SearchFormProps {
  onSearch: (filters: SearchFilters) => void;
  isLoading: boolean;
}

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  // State for all inputs
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [cuisine, setCuisine] = useState('');
  const [cookingStyle, setCookingStyle] = useState('');
  const [advancedFilters, setAdvancedFilters] = useState({
    dietaryRestrictions: [] as string[],
    skillLevel: '',
    cookTime: '',
    mealType: '',
    spiceLevel: '',
  });
  
  // Validation state
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 1. Validation
    if (ingredients.length === 0) {
      setValidationError('Please add at least one ingredient');
      return;
    }
    setValidationError('');

    // 2. Construct the filters object
    // We only send fields that have values to keep the payload clean
    const filters: SearchFilters = {
      ingredients,
      ...(cuisine && { cuisine }),
      ...(cookingStyle && { cookingStyle }),
      ...(advancedFilters.cookTime && { cookTime: advancedFilters.cookTime }),
      ...(advancedFilters.skillLevel && { skillLevel: advancedFilters.skillLevel }),
      ...(advancedFilters.mealType && { mealType: advancedFilters.mealType }),
      ...(advancedFilters.spiceLevel && { spiceLevel: advancedFilters.spiceLevel }),
      ...(advancedFilters.dietaryRestrictions.length > 0 && { 
        dietaryRestrictions: advancedFilters.dietaryRestrictions 
      }),
    };

    onSearch(filters);
  };

  const handleReset = () => {
    setIngredients([]);
    setCuisine('');
    setCookingStyle('');
    setAdvancedFilters({
      dietaryRestrictions: [],
      skillLevel: '',
      cookTime: '',
      mealType: '',
      spiceLevel: '',
    });
    setValidationError('');
  };

  // Check if any filter is active to enable/disable Reset button
  const hasFilters = 
    ingredients.length > 0 ||
    cuisine ||
    cookingStyle ||
    Object.values(advancedFilters).some(val => val.length > 0);

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
      
      {/* Top Section: Ingredients */}
      <IngredientInput
        ingredients={ingredients}
        onChange={setIngredients}
        error={validationError}
      />

      {/* Middle Section: Basic Filters */}
      <div className="grid md:grid-cols-2 gap-4">
        <CuisineSelect value={cuisine} onChange={setCuisine} />
        <CookingStyleSelect value={cookingStyle} onChange={setCookingStyle} />
      </div>

      {/* Bottom Section: Advanced Filters */}
      <AdvancedFilters
        filters={advancedFilters}
        onChange={setAdvancedFilters}
      />

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          fullWidth
          className="sm:flex-1"
        >
          {isLoading ? 'Chef is thinking...' : 'Find Recipe'}
        </Button>
        
        <Button
          type="button"
          variant="outline"
          onClick={handleReset}
          disabled={isLoading || !hasFilters}
          className="sm:w-auto px-8"
        >
          Reset
        </Button>
      </div>
    </form>
  );
}