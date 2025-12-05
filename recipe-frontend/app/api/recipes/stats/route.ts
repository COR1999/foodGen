// app/api/recipes/stats/route.ts
import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const MODAL_URL =
  process.env.MODAL_ENDPOINT_URL ||
  "https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run";

export async function GET() {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const res = await fetch(`${MODAL_URL}/user/${userId}/stats`, {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error("Failed to fetch stats");
    }

    const data = await res.json();

    return NextResponse.json({
      totalRecipes: data.total_recipes,
      cuisines: data.cuisines,
      mostPopularCuisine: data.most_popular_cuisine,
    });
  } catch (error) {
    console.error("Stats API error:", error);
    return NextResponse.json({
      totalRecipes: 0,
      cuisines: {},
      mostPopularCuisine: null,
    });
  }
}