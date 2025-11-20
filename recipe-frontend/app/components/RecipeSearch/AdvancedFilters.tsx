'use client';

import { useState } from 'react';
import Select from '../ui/Select';

export interface AdvancedFilterState {
  dietaryRestrictions: string[];
  skillLevel: string;
  cookTime: string;
  mealType: string;
  spiceLevel: string;
}

interface AdvancedFiltersProps {
  filters: AdvancedFilterState;
  onChange: (filters: AdvancedFilterState) => void;
}

const DIETARY_OPTIONS = [
  'Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', 'Paleo', 'Dairy-Free', 'Nut-Free'
];

const SKILL_LEVELS = [
  { value: '', label: 'Any Level' },
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
];

const COOK_TIMES = [
  { value: '', label: 'Any Time' },
  { value: '15', label: 'Under 15 min' },
  { value: '30', label: 'Under 30 min' },
  { value: '45', label: 'Under 45 min' },
  { value: '60', label: 'Under 1 hour' },
  { value: '90', label: 'Under 90 min' },
];

const MEAL_TYPES = [
  { value: '', label: 'Any Meal' },
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snack', label: 'Snack' },
  { value: 'dessert', label: 'Dessert' },
];

const SPICE_LEVELS = [
  { value: '', label: 'Any Spice Level' },
  { value: 'mild', label: 'Mild' },
  { value: 'medium', label: 'Medium' },
  { value: 'spicy', label: 'Spicy' },
];

export default function AdvancedFilters({ filters, onChange }: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleDietaryRestriction = (restriction: string) => {
    const current = filters.dietaryRestrictions || [];
    const updated = current.includes(restriction)
      ? current.filter((r: string) => r !== restriction)
      : [...current, restriction];
    
    onChange({ ...filters, dietaryRestrictions: updated });
  };

  return (
    <div className="border-2 border-gray-200 rounded-lg overflow-hidden bg-white">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left font-semibold text-gray-700 hover:bg-gray-50"
      >
        <span>Advanced Filters</span>
        <span className={`transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="p-4 pt-0 space-y-4 border-t border-gray-200 mt-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dietary Restrictions
            </label>
            <div className="flex flex-wrap gap-2">
              {DIETARY_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => toggleDietaryRestriction(option)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    filters.dietaryRestrictions?.includes(option)
                      ? 'bg-orange-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <Select
              label="Skill Level"
              options={SKILL_LEVELS}
              value={filters.skillLevel}
              onChange={(e) => onChange({ ...filters, skillLevel: e.target.value })}
            />
            <Select
              label="Cook Time"
              options={COOK_TIMES}
              value={filters.cookTime}
              onChange={(e) => onChange({ ...filters, cookTime: e.target.value })}
            />
            <Select
              label="Meal Type"
              options={MEAL_TYPES}
              value={filters.mealType}
              onChange={(e) => onChange({ ...filters, mealType: e.target.value })}
            />
            <Select
              label="Spice Level"
              options={SPICE_LEVELS}
              value={filters.spiceLevel}
              onChange={(e) => onChange({ ...filters, spiceLevel: e.target.value })}
            />
          </div>
        </div>
      )}
    </div>
  );
}