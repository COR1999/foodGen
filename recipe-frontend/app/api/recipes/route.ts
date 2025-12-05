// app/api/recipes/route.ts
import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const MODAL_URL =
  process.env.MODAL_ENDPOINT_URL ||
  "https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run";

// GET all user's recipes
export async function GET() {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized", recipes: [] },
        { status: 401 }
      );
    }

    console.log(`📂 Fetching recipes for user: ${userId}`);

    const res = await fetch(`${MODAL_URL}/user/${userId}/recipes`, {
      cache: "no-store",
    });

    if (!res.ok) {
      console.error(`Failed to fetch recipes: ${res.status}`);
      throw new Error("Failed to fetch recipes");
    }

    const data = await res.json();

    return NextResponse.json({
      recipes: data.recipes || [],
      count: data.count || 0,
    });
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json({ recipes: [], count: 0 });
  }
}