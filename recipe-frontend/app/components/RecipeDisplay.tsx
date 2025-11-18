// app/components/RecipeDisplay.tsx

// Define the structure of a recipe
interface Recipe {
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  cook_time: string;
  cuisine: string;
}

interface RecipeDisplayProps {
  recipe: Recipe | null;
}

export default function RecipeDisplay({ recipe }: RecipeDisplayProps) {
  if (!recipe) {
    return null;
  }

  return (
    <div className="w-full max-w-lg bg-white p-8 rounded-lg shadow-md mt-8 animate-fade-in">
      <h2 className="text-2xl font-bold mb-2 text-gray-800">{recipe.title}</h2>
      <p className="text-gray-600 mb-1"><strong>Cuisine:</strong> {recipe.cuisine}</p>
      <p className="text-gray-600 mb-4"><strong>Cook Time:</strong> {recipe.cook_time}</p>
      <p className="text-gray-700 mb-6">{recipe.description}</p>

      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-2 text-gray-800">Ingredients</h3>
        <ul className="list-disc list-inside text-gray-700">
          {recipe.ingredients.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="text-xl font-semibold mb-2 text-gray-800">Instructions</h3>
        <ol className="list-decimal list-inside text-gray-700 space-y-2">
          {recipe.instructions.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
      </div>
    </div>
  );
}