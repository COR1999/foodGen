// app/components/RecipeForm.tsx
'use client';

import { useState } from 'react';

// Define the structure of the form data
interface FormData {
  ingredients: string; // We'll use a single string for comma-separated ingredients
  cuisine: string;
  cook_time: string;
}

// Define the props the component will accept
interface RecipeFormProps {
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

export default function RecipeForm({ onSubmit, isLoading }: RecipeFormProps) {
  const [formData, setFormData] = useState<FormData>({
    ingredients: '',
    cuisine: '',
    cook_time: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Split the ingredients string into an array, trimming whitespace
    const ingredientsArray = formData.ingredients.split(',').map(item => item.trim());
    
    // Call the parent component's submit handler
    onSubmit({
      ...formData,
      ingredients: ingredientsArray,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-lg bg-white p-8 rounded-lg shadow-md">
      <div className="mb-4">
        <label htmlFor="ingredients" className="block text-gray-700 text-sm font-bold mb-2">
          Ingredients (comma-separated)
        </label>
        <input
          type="text"
          name="ingredients"
          id="ingredients"
          value={formData.ingredients}
          onChange={handleChange}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="e.g., chicken, garlic, tomato"
          required
        />
      </div>
      <div className="mb-4">
        <label htmlFor="cuisine" className="block text-gray-700 text-sm font-bold mb-2">
          Cuisine (optional)
        </label>
        <input
          type="text"
          name="cuisine"
          id="cuisine"
          value={formData.cuisine}
          onChange={handleChange}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="e.g., Italian, Mexican"
        />
      </div>
      <div className="mb-6">
        <label htmlFor="cook_time" className="block text-gray-700 text-sm font-bold mb-2">
          Cook Time (optional)
        </label>
        <input
          type="text"
          name="cook_time"
          id="cook_time"
          value={formData.cook_time}
          onChange={handleChange}
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          placeholder="e.g., under 30 minutes"
        />
      </div>
      <div className="flex items-center justify-between">
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:bg-blue-300 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Generating...' : 'Generate Recipe'}
        </button>
      </div>
    </form>
  );
}