// app/api/recipes/search/route.ts
import { NextRequest, NextResponse } from 'next/server';

// Define what the UI sends to this endpoint
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
    const body: SearchRequest = await request.json();
    
    // Basic Validation
    if (!body.ingredients || body.ingredients.length === 0) {
      return NextResponse.json(
        { error: 'Ingredients are required' },
        { status: 400 }
      );
    }

    // Define your Modal endpoint
    const modalEndpoint = process.env.MODAL_ENDPOINT_URL || 
      'https://cor1999--recipe-generator-final-test-fastapi-app-dev.modal.run'; // Update with your actual live URL
    
    console.log('Processing request for Modal:', modalEndpoint);

    // Construct the payload for Modal (converting camelCase UI props to snake_case for Python)
    const modalPayload = {
      ingredients: body.ingredients,
      cuisine: body.cuisine || null,
      cook_time: body.cookTime || null,          // UI sends 'cookTime', Python likely wants 'cook_time'
      cooking_style: body.cookingStyle || null,  // UI sends 'cookingStyle'
      dietary_restrictions: body.dietaryRestrictions || [],
      skill_level: body.skillLevel || null,
      meal_type: body.mealType || null,
      spice_level: body.spiceLevel || null,
    };

    console.log('Sending payload to Modal:', JSON.stringify(modalPayload, null, 2));
    
    // Call the Modal Backend
    const response = await fetch(`${modalEndpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(modalPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Modal error response:', errorText);
      throw new Error(`Modal request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Return the data to the UI matching our ApiResponse interface
    return NextResponse.json({
      recipe: data.recipe,
      source: data.source,
      // Handle case where Modal returns snake_case 'match_score' but UI expects camelCase 'matchScore'
      matchScore: data.match_score || data.matchScore, 
    });

  } catch (error) {
    console.error('Recipe API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to generate recipe',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}