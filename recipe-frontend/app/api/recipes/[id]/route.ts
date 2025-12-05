// app/api/recipes/[id]/route.ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const MODAL_URL =
  process.env.MODAL_ENDPOINT_URL ||
  "https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run";

type Params = Promise<{ id: string }>;

// GET a specific recipe
export async function GET(
  request: NextRequest,
  segmentData: { params: Params }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const params = await segmentData.params;
    const id = params.id;

    if (!id) {
      return NextResponse.json({ error: "Recipe ID required" }, { status: 400 });
    }

    const filename = id.endsWith(".json") ? id : `${id}.json`;

    const res = await fetch(
      `${MODAL_URL}/user/${userId}/recipes/${filename}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!res.ok) {
      return NextResponse.json({ error: "Recipe not found" }, { status: 404 });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching recipe:", error);
    return NextResponse.json(
      { error: "Failed to fetch recipe" },
      { status: 500 }
    );
  }
}

// DELETE a recipe
export async function DELETE(
  request: NextRequest,
  segmentData: { params: Params }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    const params = await segmentData.params;
    const id = params.id;

    console.log(`🗑️ User ${userId} deleting recipe: ${id}`);

    if (!id) {
      return NextResponse.json(
        { success: false, error: "Recipe ID required" },
        { status: 400 }
      );
    }

    const filename = id.endsWith(".json") ? id : `${id}.json`;

    const res = await fetch(
      `${MODAL_URL}/user/${userId}/recipes/${filename}`,
      {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!res.ok) {
      let errorMessage = "Failed to delete recipe";
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Ignore JSON parse errors
      }

      return NextResponse.json(
        { success: false, error: errorMessage },
        { status: res.status }
      );
    }

    const data = await res.json();

    return NextResponse.json({
      success: true,
      message: data.message || "Recipe deleted successfully",
    });
  } catch (error) {
    console.error("❌ Error deleting recipe:", error);
    return NextResponse.json(
      { success: false, error: "Failed to delete recipe" },
      { status: 500 }
    );
  }
}