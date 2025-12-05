// types/recipe.ts

export interface Recipe {
  id?: string;
  filename?: string;
  last_modified?: string;
  created_at?: string;
  user_id?: string; // NEW: For user-based storage
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  cook_time: string;
  cuisine: string;
  cooking_style: string;
  servings: number;
}

export interface ApiResponse {
  recipe: Recipe;
  source: "s3" | "generated";
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

// NEW: Response types
export interface RecipeListResponse {
  recipes: Recipe[];
  count: number;
}

export interface RecipeStats {
  totalRecipes: number;
  cuisines: Record<string, number>;
  mostPopularCuisine: string | null;
}

export interface DeleteResponse {
  success: boolean;
  message?: string;
  error?: string;
}