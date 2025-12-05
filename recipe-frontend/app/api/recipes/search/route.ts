// app/api/recipes/search/route.ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const MODAL_URL =
  process.env.MODAL_ENDPOINT_URL ||
  "https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run";

interface SearchRequest {
  ingredients: string[];
  cuisine?: string;
  cookingStyle?: string;
  cookTime?: string;
  dietaryRestrictions?: string[];
  skillLevel?: string;
  mealType?: string;
  spiceLevel?: string;
}

export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body: SearchRequest = await request.json();

    // Basic Validation
    if (!body.ingredients || body.ingredients.length === 0) {
      return NextResponse.json(
        { error: "Ingredients are required" },
        { status: 400 }
      );
    }

    console.log(`🍳 Generating recipe for user: ${userId}`);

    // Construct payload with user_id
    const modalPayload = {
      ingredients: body.ingredients,
      cuisine: body.cuisine || null,
      cook_time: body.cookTime || null,
      cooking_style: body.cookingStyle || null,
      dietary_restrictions: body.dietaryRestrictions || [],
      skill_level: body.skillLevel || null,
      meal_type: body.mealType || null,
      spice_level: body.spiceLevel || null,
      user_id: userId, // Include user ID so recipe is saved to their folder
    };

    console.log("📤 Sending to Modal:", JSON.stringify(modalPayload, null, 2));

    // Use the user-specific endpoint
    const response = await fetch(`${MODAL_URL}/user/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(modalPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Modal error response:", errorText);
      throw new Error(
        `Modal request failed: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();

    console.log("✅ Recipe generated successfully");

    return NextResponse.json({
      recipe: data.recipe,
      source: data.source,
      matchScore: data.match_score || data.matchScore,
    });
  } catch (error) {
    console.error("Recipe API error:", error);
    return NextResponse.json(
      {
        error: "Failed to generate recipe",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}