import Link from "next/link";
import {
  ChefHat,
  Sparkles,
  Clock,
  Utensils,
  ArrowRight,
  Zap,
  BookOpen,
  Salad,
  ChevronRight,
} from "lucide-react";

export default function Landing() {
  return (
    <div className="flex flex-col">
      {/* ===== HERO SECTION ===== */}
      <section className="relative overflow-hidden bg-gradient-to-br from-orange-50 via-white to-amber-50">
        {/* Background Decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-orange-200 rounded-full opacity-20 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-amber-200 rounded-full opacity-20 blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32 lg:py-40">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-white border border-orange-200 rounded-full px-4 py-2 mb-8 shadow-sm">
              <Sparkles className="w-4 h-4 text-orange-500" />
              <span className="text-sm font-medium text-gray-700">
                Powered by Advanced AI
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 tracking-tight mb-6">
              Turn Your{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-500">
                Ingredients
              </span>{" "}
              Into Delicious Meals
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              Stop staring at your fridge. Tell us what you have, and our AI
              chef will create personalized recipes in seconds.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/generate"
                className="group inline-flex items-center gap-2 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-semibold px-8 py-4 rounded-xl shadow-lg shadow-orange-500/25 hover:shadow-xl hover:shadow-orange-500/30 transition-all duration-300"
              >
                <ChefHat className="w-5 h-5" />
                Start Cooking
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/saved"
                className="inline-flex items-center gap-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold px-8 py-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <BookOpen className="w-5 h-5" />
                View My Recipes
              </Link>
            </div>

            {/* Social Proof */}
            <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-red-400 border-2 border-white"
                    />
                  ))}
                </div>
                <span>1,000+ happy cooks</span>
              </div>
              <div className="hidden sm:block w-1 h-1 bg-gray-300 rounded-full" />
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <span key={i} className="text-yellow-400">
                    ★
                  </span>
                ))}
                <span className="ml-1">4.9/5 rating</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS SECTION ===== */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From fridge to feast in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
            {/* Step 1 */}
            <div className="relative group">
              <div className="bg-orange-50 rounded-2xl p-8 h-full border border-orange-100 hover:border-orange-200 hover:shadow-lg transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center text-white font-bold text-xl mb-6 shadow-lg shadow-orange-500/25">
                  1
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  Enter Your Ingredients
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Type in whatever you have in your kitchen—vegetables, proteins,
                  spices, or pantry staples. No judgment here!
                </p>
              </div>
              {/* Connector Arrow (Desktop) */}
              <div className="hidden md:block absolute top-1/2 -right-6 transform -translate-y-1/2 z-10">
                <ChevronRight className="w-8 h-8 text-orange-300" />
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative group">
              <div className="bg-orange-50 rounded-2xl p-8 h-full border border-orange-100 hover:border-orange-200 hover:shadow-lg transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center text-white font-bold text-xl mb-6 shadow-lg shadow-orange-500/25">
                  2
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  AI Creates Your Recipe
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Our advanced AI analyzes your ingredients and generates a
                  personalized, delicious recipe tailored just for you.
                </p>
              </div>
              {/* Connector Arrow (Desktop) */}
              <div className="hidden md:block absolute top-1/2 -right-6 transform -translate-y-1/2 z-10">
                <ChevronRight className="w-8 h-8 text-orange-300" />
              </div>
            </div>

            {/* Step 3 */}
            <div className="group">
              <div className="bg-orange-50 rounded-2xl p-8 h-full border border-orange-100 hover:border-orange-200 hover:shadow-lg transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center text-white font-bold text-xl mb-6 shadow-lg shadow-orange-500/25">
                  3
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  Cook & Enjoy
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Follow the step-by-step instructions, check off each step as
                  you go, and enjoy your homemade meal!
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section className="py-24 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose ChefAI?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              More than just a recipe generator—it's your personal kitchen assistant
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:border-orange-200 transition-all duration-300">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Lightning Fast</h3>
              <p className="text-gray-600 text-sm">
                Get complete recipes generated in under 10 seconds.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:border-orange-200 transition-all duration-300">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Salad className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Zero Food Waste</h3>
              <p className="text-gray-600 text-sm">
                Use what you already have instead of buying more groceries.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:border-orange-200 transition-all duration-300">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Save Time</h3>
              <p className="text-gray-600 text-sm">
                No more endless scrolling through recipe blogs for ideas.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:border-orange-200 transition-all duration-300">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <Utensils className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Any Cuisine</h3>
              <p className="text-gray-600 text-sm">
                Italian, Asian, Mexican, or fusion—AI adapts to your taste.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA SECTION ===== */}
      <section className="py-24 bg-gradient-to-r from-orange-500 to-red-500">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Cooking?
          </h2>
          <p className="text-xl text-orange-100 mb-10 max-w-2xl mx-auto">
            Join thousands of home cooks who are already creating amazing meals
            with AI. It's free to get started!
          </p>
          <Link
            href="/generate"
            className="inline-flex items-center gap-2 bg-white hover:bg-gray-100 text-orange-600 font-bold px-10 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <ChefHat className="w-5 h-5" />
            Generate Your First Recipe
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}