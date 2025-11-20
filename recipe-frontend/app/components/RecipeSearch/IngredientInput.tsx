'use client';

import { useState } from 'react';

interface IngredientInputProps {
  ingredients: string[];
  onChange: (ingredients: string[]) => void;
  error?: string;
}

export default function IngredientInput({ ingredients, onChange, error }: IngredientInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addIngredient = () => {
    const trimmed = inputValue.trim().toLowerCase();
    if (trimmed && !ingredients.includes(trimmed)) {
      onChange([...ingredients, trimmed]);
      setInputValue('');
    }
  };

  const removeIngredient = (index: number) => {
    onChange(ingredients.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addIngredient();
    } else if (e.key === 'Backspace' && inputValue === '' && ingredients.length > 0) {
      onChange(ingredients.slice(0, -1));
    }
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Ingredients <span className="text-red-500">*</span>
      </label>
      
      <div className={`min-h-[50px] p-3 border-2 rounded-lg bg-white transition-colors flex flex-wrap gap-2 items-center ${
        error ? 'border-red-300' : 'border-gray-300 focus-within:border-orange-500'
      }`}>
        {ingredients.map((ingredient, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium"
          >
            {ingredient}
            <button
              type="button"
              onClick={() => removeIngredient(index)}
              className="hover:text-orange-900 font-bold text-lg leading-none ml-1"
            >
              ×
            </button>
          </span>
        ))}
        
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={addIngredient}
          placeholder={ingredients.length === 0 ? "e.g. chicken, garlic, tomato" : "Add another..."}
          className="flex-1 min-w-[120px] outline-none bg-transparent py-1"
        />
      </div>
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}