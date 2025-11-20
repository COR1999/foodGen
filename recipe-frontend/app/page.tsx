// app/page.tsx
import RecipeSearch from './components/RecipeSearch';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 py-12 px-4">
      <div className="w-full max-w-5xl mx-auto">
        <RecipeSearch />
      </div>
    </main>
  );
}