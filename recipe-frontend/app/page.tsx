// app/page.tsx
import RecipeSearch from './components/RecipeSearch';

import Landing from './components/Landing';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 py-12 px-4">
      <Landing />
      {/* <div className="w-full max-w-5xl mx-auto">
        <RecipeSearch />
      </div> */}
    </main>
  );
}