// app/types/recipe.ts
export interface Recipe {
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  cook_time: string;
  cuisine: string;
}

export interface ApiResponse {
  recipe: Recipe;
  source: 's3' | 'generated';
  matchScore?: number;
}

export interface SearchFilters {
  ingredients: string[];
  cuisine?: string;
  cookingStyle?: string;
  cookTime?: string;
  dietaryRestrictions?: string[];
  skillLevel?: string;
  mealType?: string;
  spiceLevel?: string;
}