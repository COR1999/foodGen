# modal_app/main.py - Complete single file version
import modal
import os
import json
import re
import boto3
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==================== DATA MODELS ====================


class RecipeRequest(BaseModel):
    ingredients: List[str]
    cuisine: Optional[str] = None
    cook_time: Optional[str] = None
    cooking_style: Optional[str] = None
    dietary_restrictions: List[str] = []
    skill_level: Optional[str] = None
    meal_type: Optional[str] = None
    spice_level: Optional[str] = None


class StructuredRecipe(BaseModel):
    title: str
    description: str
    ingredients: list[str]
    instructions: list[str]
    cook_time: str
    cuisine: str
    cooking_style: Optional[str] = None  # NEW


class RecipeResponse(BaseModel):
    recipe: StructuredRecipe
    source: str
    match_score: Optional[float] = None


# ==================== CONFIGURATION ====================


class Config:
    MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
    CACHE_PATH = "/model-cache"
    MIN_MATCH_SCORE = 0.6
    COOK_TIME_WEIGHT = 0.9
    CHEF_SYSTEM_PROMPT = """You are a meticulous Executive Chef.
PRIMARY OBJECTIVE: Output ONLY valid JSON per the schema. No markdown, no headings, no emojis, no extra text.

CRITICAL RULES:

Ingredient–Instruction Consistency (both directions):

Every edible item used in instructions MUST first appear in ingredients.
Every ingredient must be used in at least one instruction.
Generic-to-specific allowed (e.g., "heat the oil" matches "Vegetable Oil" or "Sesame Oil").
Formatting:

US customary units only (tsp, tbsp, cup, oz, lb, °F). Never metric (ml, g, kg, °C).
Ingredient line format: "[quantity] [unit] [Name] [optional (note)]".
Do NOT list cookware/tools in ingredients.
Quantity realism (think like a chef):

Default servings to 4 unless otherwise implied by user input.
Typical baselines per 4 servings:
• Protein: 1 to 1.5 lb total
• Rice (uncooked): 1 to 2 cups; water 1.75–2x rice volume
• Oil for sautéing: 1–3 tbsp total (not more than 1/4 cup)
• Butter for finishing: 1–3 tbsp
• Salt: 1 to 2 tsp total unless brines/rubs justify more
• Black Pepper: 1/2 to 1 tsp
• Aromatics: 1–4 cloves garlic, 1 small onion/shallot
Alcohol policy:
• Never specify “bottle”, “750 ml”, or similar.
• For deglazing/pan sauces, use 1/4–1/2 cup wine; never exceed 1 cup total.
• Respect cuisine: in Japanese cuisine, wine is atypical—use very sparingly (1/4 cup max) or offer rice vinegar/mirin substitution.
Cuisine authenticity:

Match flavor anchors to cuisine. For Japanese, consider combinations of: Soy Sauce, Mirin, Sake (optional), Rice Vinegar, Miso, Ginger, Garlic, Scallions, Sesame Oil, Shichimi Togarashi/Chili Flakes. Avoid overly Western anchors unless user forces them.
If the user provides an atypical ingredient (e.g., white wine), integrate modestly or offer a substitution in parentheses.
Spice level mapping:

mild: 1/4–1/2 tsp chili flakes
medium: 1/2–1 tsp chili flakes or 1–2 small chiles
spicy/hot: 1–2 tsp chili flakes or 2–4 small chiles
Sanity check BEFORE finalizing:

No “bottle/carton/bag/box” quantities.
No metric units.
Check alcohol against policy; cap at 1/2 cup for non-braises (max 1 cup).
Ensure oil, salt, pepper, and any stated anchors are present and within ranges.
JSON SCHEMA:
{
"title": "string",
"description": "string (1–2 sentences)",
"ingredients": ["string"],
"instructions": ["string"],
"cook_time": "string",
"cuisine": "string",
"cooking_style": "string (the method used: fried, baked, grilled, etc.)",
"servings": integer
}
"""


# ==================== S3 MANAGER ====================


class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        self.bucket_name = os.environ.get("S3_BUCKET_NAME")

    def upload_to_s3(self, content: str, folder: str = "responses") -> str:
        """Upload content to S3 and return the object key"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            object_key = f"model_responses/{folder}/{timestamp}.json"

            self.s3_client.put_object(
                Body=content.encode('utf-8'),
                Bucket=self.bucket_name,
                Key=object_key,
                ContentType='application/json'
            )

            print(f"✅ Uploaded to s3://{self.bucket_name}/{object_key}")
            return object_key
        except Exception as e:
            print(f"⚠️ S3 upload failed: {e}")
            return ""

    def get_all_recipes(self) -> List[Dict]:
        """Get all recipes from S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="model_responses/generated_recipes/"
            )

            recipes = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        file_obj = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        recipe_data = json.loads(
                            file_obj['Body'].read().decode('utf-8'))
                        recipes.append(recipe_data)
                    except Exception as e:
                        print(f"Error loading recipe {obj['Key']}: {e}")
                        continue

            return recipes
        except Exception as e:
            print(f"Error fetching recipes from S3: {e}")
            return []

    def get_recipe(self, filename: str) -> Dict:
        """Get a specific recipe from S3"""
        try:
            object_key = f"model_responses/generated_recipes/{filename}"
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"Error fetching recipe: {e}")
            return {}

    def list_recipe_files(self) -> List[Dict]:
        """List all recipe files metadata"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="model_responses/generated_recipes/"
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'filename': obj['Key'].split('/')[-1]
                    })

            return files
        except Exception as e:
            print(f"Error listing recipes: {e}")
            return []

# ==================== RECIPE MATCHER ====================


class RecipeMatcher:
    """Handles recipe matching logic"""

    @staticmethod
    def calculate_ingredient_match(user_ingredients: List[str], recipe_ingredients: List[str]) -> float:
        user_ing_normalized = [ing.lower().strip() for ing in user_ingredients]
        recipe_ing_combined = " ".join(recipe_ingredients).lower()

        match_count = 0
        for user_ing in user_ing_normalized:
            # \b ensures "ice" matches "ice" but not "rice" or "spiced"
            # escape the user input to handle characters like parens ()
            pattern = r'\b' + re.escape(user_ing) + r'\b'
            if re.search(pattern, recipe_ing_combined):
                match_count += 1

        return match_count / len(user_ing_normalized) if user_ing_normalized else 0

    @staticmethod
    def matches_criteria(recipe_data: Dict, request: RecipeRequest, min_match_score: float = None) -> Tuple[bool, float]:
        """
        Check if a recipe matches the user's criteria
        Returns (matches: bool, score: float)
        """
        if min_match_score is None:
            min_match_score = Config.MIN_MATCH_SCORE

        recipe_ingredients = recipe_data.get('ingredients', [])
        match_score = RecipeMatcher.calculate_ingredient_match(
            request.ingredients, recipe_ingredients)

        if match_score < min_match_score:
            return False, match_score

        # Check cuisine if specified
        if request.cuisine:
            recipe_cuisine = recipe_data.get('cuisine', '').lower()
            if request.cuisine.lower() not in recipe_cuisine:
                return False, match_score

        # Check cooking style if specified (NEW)
        if request.cooking_style:
            recipe_instructions = " ".join(
                recipe_data.get('instructions', [])).lower()
            cooking_style_lower = request.cooking_style.lower()

            # Map cooking styles to expected instruction keywords
            style_keywords = {
                "fried": ["fry", "frying", "fried", "pan-fry", "deep-fry"],
                "baked": ["bake", "baking", "baked", "oven"],
                "grilled": ["grill", "grilling", "grilled", "barbecue", "bbq"],
                "steamed": ["steam", "steaming", "steamed"],
                "roasted": ["roast", "roasting", "roasted"],
                "sauteed": ["sauté", "sautéed", "sauteed", "pan"],
                "boiled": ["boil", "boiling", "boiled"],
                "slow cooked": ["slow cook", "crockpot", "slow cooker", "braise"]
            }

            keywords = style_keywords.get(
                cooking_style_lower, [cooking_style_lower])

            # If none of the keywords appear in instructions, penalize heavily
            if not any(kw in recipe_instructions for kw in keywords):
                match_score *= 0.3  # Heavy penalty for mismatched cooking style
                if match_score < min_match_score:
                    return False, match_score

        # Check cook time if specified (optional)
        if request.cook_time:
            recipe_cook_time = recipe_data.get('cook_time', '').lower()
            if request.cook_time.lower() not in recipe_cook_time:
                match_score *= Config.COOK_TIME_WEIGHT

        return True, match_score

    @staticmethod
    def find_best_match(recipes: List[Dict], request: RecipeRequest) -> Optional[Tuple[StructuredRecipe, float]]:
        """
        Find the best matching recipe from a list of recipes
        Returns (recipe, match_score) if found, None otherwise
        """
        best_match = None
        best_score = 0.0

        for recipe_data in recipes:
            try:
                matches, score = RecipeMatcher.matches_criteria(
                    recipe_data, request)

                if matches and score > best_score:
                    best_score = score
                    recipe_clean = {
                        'title': recipe_data.get('title'),
                        'description': recipe_data.get('description'),
                        'ingredients': recipe_data.get('ingredients'),
                        'instructions': recipe_data.get('instructions'),
                        'cook_time': recipe_data.get('cook_time'),
                        'cuisine': recipe_data.get('cuisine')
                    }
                    best_match = StructuredRecipe(**recipe_clean)
                    print(
                        f"✅ Found matching recipe: {best_match.title} (score: {best_score:.2f})")

            except Exception as e:
                print(f"Error processing recipe: {e}")
                continue

        if best_match:
            print(f"🎯 Best match found with score: {best_score:.2f}")
            return best_match, best_score

        return None

# ==================== RECIPE MODEL ====================


class RecipeModel:
    """Main AI recipe generation model"""

    def __init__(self, cache_path: str):
        # Import torch/transformers here to avoid loading until needed
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        print(f"Loading model from cache path: {cache_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            Config.MODEL_NAME,
            cache_dir=cache_path
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_NAME,
            device_map="auto",
            quantization_config=quantization_config,
            cache_dir=cache_path
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Initialize managers
        self.s3_manager = S3Manager()

        print("✅ Model loaded successfully.")

    def _clean_json_response(self, response_text: str) -> str:
        """Clean common JSON formatting issues from LLM responses"""
        response_text = re.sub(
            r'^```json\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(
            r'^```\s*$', '', response_text, flags=re.MULTILINE)
        response_text = response_text.strip()
        response_text = re.sub(r'\.\s*(\}|\])', r'\1', response_text)
        response_text = re.sub(r',\s*(\}|\])', r'\1', response_text)

        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            response_text = match.group(0)

        return response_text

    def _repair_and_parse_json(self, json_str: str) -> Dict:
        """Attempts to fix common LLM JSON errors before parsing"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fix 1: Remove trailing commas in arrays/objects
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            # Fix 2: Handle unescaped newlines
            json_str = json_str.replace('\n', ' ')
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"❌ CRITICAL JSON FAILURE: {json_str[:50]}...")
                raise

    def _validate_consistency(self, recipe_data: Dict) -> Dict:
        """
        Ensures basic staples are present if referenced in instructions.
        Adds minimal, sane quantities with notes when missing.
        """
        instructions_text = " ".join(
            recipe_data.get('instructions', [])).lower()
        ingredients_blob = " ".join(recipe_data.get('ingredients', [])).lower()

        # Common staples that LLMs often forget to list, mapped to a Formal Name
        staples = {
            "salt": "1 tsp Kosher Salt (or to taste)",
            "pepper": "1/2 tsp Black Pepper",
            "oil": "1 tbsp Vegetable Oil (for sautéing)",
            "butter": "1 tbsp Unsalted Butter",
            "water": "1 cup Water"
        }

        for key, line in staples.items():
            if key in instructions_text and key not in ingredients_blob:
                print(f"🔧 Auto-Fix: Adding missing '{line}' to ingredients.")
                recipe_data.setdefault("ingredients", []).append(line)

        return recipe_data

    def _apply_quantity_sanity_caps(self, data: Dict) -> Dict:
        """
        Clamp unrealistic quantities, avoid container units, prefer US customary units,
        and enforce light-touch Japanese anchors if cuisine is Japanese.
        """
        if "ingredients" not in data or not isinstance(data["ingredients"], list):
            return data

    def search_s3_recipes(self, request: RecipeRequest) -> Optional[Tuple[StructuredRecipe, float]]:
        """
        Search S3 for existing recipes that match the request
        Returns (recipe, match_score) if found, None otherwise
        """
        print(f"🔍 Searching S3 for recipes matching: {request.ingredients}")

        recipes = self.s3_manager.get_all_recipes()
        if not recipes:
            print("No recipes found in S3")
            return None

        print(
            f"Found {len(recipes)} recipes in S3, searching for best match...")
        return RecipeMatcher.find_best_match(recipes, request)

    def _build_chef_prompt(self, request: RecipeRequest) -> str:
        """Build context-aware chef prompt"""

        # Get the right chef
        persona = ChefPersonaBuilder.build_persona(request.cuisine)

        # Analyze ingredients
        analysis = IngredientAnalyzer.detect_conflicts(
            request.ingredients,
            request.cuisine
        )

        # Build the prompt dynamically
        prompt_parts = [
            f"You are {persona['name']}, {persona['background']}.",
            f"\nA customer brings you these ingredients: {', '.join(request.ingredients)}."
        ]

        if request.cuisine:
            prompt_parts.append(f"\nThey want {request.cuisine} cuisine.")

        # Handle conflicts intelligently
        if analysis["has_conflict"]:
            conflict_text = []
            for c in analysis["conflicts"]:
                conflict_text.append(
                    f"• {c['ingredient']} is {c['suggestion']}")

            prompt_parts.append(
                f"\n\n⚠️ NOTE: You notice some ingredients are atypical:\n" +
                "\n".join(conflict_text) +
                f"\n\nAs a professional, you will either:"
                f"\n1. Use them VERY sparingly (e.g., 2-3 tbsp max if liquid)"
                f"\n2. Explain why you're adapting the dish in chef_notes"
                f"\n3. Substitute with traditional ingredients from your kitchen: {', '.join(analysis['staples'][:5])}"
            )

        # Add kitchen context
        prompt_parts.append(
            f"\n\n🍳 YOUR KITCHEN IS FULLY STOCKED WITH:"
            f"\n- Essential staples: {', '.join(analysis['staples'][:8])}"
            f"\n- Typical cooking fat: {analysis['typical_fats']}"
            f"\n- Standard proteins, vegetables, herbs, and spices"
        )

        
        
        # MEAL TYPE APPROPRIATENESS (if specified)
        if request.meal_type:
            meal_lower = request.meal_type.lower()
            
            meal_guidelines = {
                "breakfast": {
                    "appropriate": [
                        "eggs (scrambled, fried, poached, omelettes)",
                        "pancakes, waffles, french toast",
                        "breakfast meats (bacon, sausage, ham)",
                        "oatmeal, granola, cereal",
                        "breakfast sandwiches (egg-based)",
                        "smoothies, yogurt bowls",
                        "breakfast burritos/tacos (egg-based)",
                        "muffins, scones, pastries"
                    ],
                    "inappropriate": [
                        "burgers, cheeseburgers",
                        "heavy pasta dishes",
                        "steaks, roasts",
                        "fried chicken (dinner-style)",
                        "tacos/burritos without eggs",
                        "pizza",
                        "casseroles (unless breakfast casserole)"
                    ],
                    "guidance": "Focus on lighter, morning-appropriate dishes. If user's ingredients suggest a lunch/dinner dish (like beef → burgers), TRANSFORM it into a breakfast version (like beef breakfast hash or steak and eggs)."
                },
                "lunch": {
                    "appropriate": [
                        "sandwiches, wraps",
                        "salads with protein",
                        "soups, light stews",
                        "pasta dishes (lighter portions)",
                        "tacos, burritos",
                        "grain bowls",
                        "lighter meat dishes"
                    ],
                    "inappropriate": [
                        "pancakes, waffles",
                        "heavy roasts (save for dinner)",
                        "breakfast cereals"
                    ],
                    "guidance": "Create satisfying but not overly heavy dishes. Portions should be moderate."
                },
                "dinner": {
                    "appropriate": [
                        "steaks, roasts, braised meats",
                        "pasta dishes (hearty)",
                        "casseroles",
                        "grilled meats and fish",
                        "curries, stews",
                        "pizza",
                        "burgers (dinner-appropriate)"
                    ],
                    "inappropriate": [
                        "pancakes, waffles",
                        "breakfast cereals",
                        "muffins, scones"
                    ],
                    "guidance": "Create hearty, satisfying dishes. This is the main meal of the day."
                },
                "snack": {
                    "appropriate": [
                        "dips and spreads",
                        "finger foods",
                        "small bites, appetizers",
                        "chips, crackers with toppings",
                        "vegetable sticks with dip",
                        "small portions"
                    ],
                    "inappropriate": [
                        "full meals",
                        "large portions",
                        "multi-course dishes"
                    ],
                    "guidance": "Keep it small, portable, and easy to eat with hands or minimal utensils."
                },
                "dessert": {
                    "appropriate": [
                        "cakes, pies, cookies",
                        "ice cream dishes",
                        "puddings, custards",
                        "fruit-based sweets",
                        "chocolate dishes"
                    ],
                    "inappropriate": [
                        "savory main dishes",
                        "breakfast items (unless dessert-style)"
                    ],
                    "guidance": "Focus on sweet endings to meals. Transform savory ingredients creatively if needed."
                }
            }
            
            guidelines = meal_guidelines.get(meal_lower, {
                "guidance": f"Create an appropriate {request.meal_type} dish."
            })
            
            prompt_parts.append(
                f"\n\n🍽️ MEAL TYPE: {request.meal_type.upper()}"
            )
            
            if "appropriate" in guidelines:
                prompt_parts.append(
                    f"\n✅ APPROPRIATE for {request.meal_type}:\n   " + 
                    "\n   ".join(f"• {item}" for item in guidelines["appropriate"][:6])
                )
            
            if "inappropriate" in guidelines:
                prompt_parts.append(
                    f"\n❌ INAPPROPRIATE for {request.meal_type}:\n   " + 
                    "\n   ".join(f"• {item}" for item in guidelines["inappropriate"][:6])
                )
            
            prompt_parts.append(
                f"\n📋 GUIDANCE: {guidelines['guidance']}"
            )
            
            # Special transformation logic for common conflicts
            if meal_lower == "breakfast":
                prompt_parts.append(
                    f"\n\n💡 TRANSFORMATION EXAMPLES:"
                    f"\n   • User has beef → Make 'Beef Breakfast Hash' or 'Steak and Eggs', NOT burgers"
                    f"\n   • User has chicken → Make 'Chicken Breakfast Sausage Patties', NOT fried chicken"
                    f"\n   • User has pasta → Make 'Breakfast Pasta Frittata', NOT spaghetti"
                    f"\n   • User has rice → Make 'Savory Breakfast Rice Bowl with Egg', NOT fried rice"
                )
        
        # COOKING STYLE ENFORCEMENT (Strong)
        if request.cooking_style:
            style_lower = request.cooking_style.lower()

            # Specific instructions per cooking method
            style_guidance = {
                "fried": {
                    "method": "pan-fry or deep-fry",
                    "requirements": "Heat oil (2-4 tbsp for pan-fry, 2-4 cups for deep-fry) to 350-375°F. Fry until golden and crispy. Do NOT bake, braise, or boil.",
                    "title_must_include": "Fried, Pan-Fried, or Crispy"
                },
                "baked": {
                    "method": "bake in oven",
                    "requirements": "Preheat oven to specific temperature (325-425°F). Bake for specified time. Do NOT pan-fry, boil, or grill.",
                    "title_must_include": "Baked or Oven-"
                },
                "grilled": {
                    "method": "grill over direct heat",
                    "requirements": "Preheat grill to medium-high heat. Grill with lid closed, flipping once. Do NOT bake or fry in a pan.",
                    "title_must_include": "Grilled"
                },
                "steamed": {
                    "method": "steam",
                    "requirements": "Set up steamer basket over boiling water. Steam until cooked through. Do NOT fry or bake.",
                    "title_must_include": "Steamed"
                },
                "roasted": {
                    "method": "roast in oven at high heat",
                    "requirements": "Preheat oven to 400-450°F. Roast until caramelized and tender. Do NOT boil or steam.",
                    "title_must_include": "Roasted"
                },
                "sauteed": {
                    "method": "sauté in a pan",
                    "requirements": "Heat 1-3 tbsp oil or butter in pan over medium-high heat. Sauté, stirring frequently, until cooked through. Do NOT bake or steam.",
                    "title_must_include": "Sautéed or Pan-"
                },
                "boiled": {
                    "method": "boil in liquid",
                    "requirements": "Bring water or broth to a rolling boil. Add ingredients and boil until tender. Do NOT fry or bake.",
                    "title_must_include": "Boiled"
                },
                "slow cooked": {
                    "method": "slow cook or braise",
                    "requirements": "Cook low and slow (slow cooker, dutch oven, or oven at 250-300°F for 2+ hours). Do NOT pan-fry or quick-cook.",
                    "title_must_include": "Braised, Slow-Cooked, or Stewed"
                },
                "braised": {
                    "method": "braise",
                    "requirements": "Sear first, then cook covered in liquid in oven or stovetop at low heat (300°F or low simmer) for 1.5+ hours. Do NOT fry or grill.",
                    "title_must_include": "Braised"
                }
            }

            guidance = style_guidance.get(style_lower, {
                "method": request.cooking_style,
                "requirements": f"Use {request.cooking_style} cooking method throughout.",
                "title_must_include": request.cooking_style.title()
            })

            prompt_parts.append(
                f"\n\n🔥 COOKING METHOD REQUIREMENT (MANDATORY - NON-NEGOTIABLE):"
                f"\nMethod: You MUST {guidance['method']} this dish."
                f"\nRequirements: {guidance['requirements']}"
                f"\nTitle MUST include: '{guidance['title_must_include']}'"
                f"\n\n❌ FORBIDDEN: Any cooking method other than {request.cooking_style} is INCORRECT and UNACCEPTABLE."
                f"\n✅ CORRECT: Every instruction step must support the {request.cooking_style} method."
            )

        # Spice level
        spice_map = {
            "mild": "very gentle heat (1/4 tsp chili or red pepper flakes)",
            "medium": "moderate heat (1/2-1 tsp chili or 1-2 small chiles)",
            "spicy": "bold heat (1-2 tsp chili or 2-3 fresh chilis)",
            "hot": "intense heat (2+ tsp chili or 4+ fresh chilis)"
        }
        if request.spice_level:
            prompt_parts.append(
                f"\n\n🌶️ SPICE LEVEL: {request.spice_level.upper()} ({spice_map.get(request.spice_level.lower(), 'moderate')})"
            )

        # Chef thinking framework
        prompt_parts.append("""

    YOUR TASK:
    1. Decide what dish to make (consider the customer's ingredients + your expertise + COOKING METHOD)
    2. Gather ALL needed ingredients from your kitchen (remember: customers have ONLY what they listed)
    3. Write the complete recipe using the REQUIRED cooking method

    PORTION SIZES (default to 4 servings):
    - Protein: 1-1.5 lb total
    - Rice/grains: 1-2 cups uncooked
    - Liquids for cooking: measured in tbsp or cups, NEVER "bottles", "cartons", or "containers"
    - Oil for cooking: 1-3 tbsp for sautéing; 2-4 cups for deep-frying
    - Alcohol (if used): 1/4 to 1/2 cup MAX for deglazing; 1 cup MAX for braises

    CRITICAL RULES:
    1. Every ingredient used in instructions MUST be listed in ingredients first
    2. Every ingredient listed MUST be used in at least one instruction
    3. Use US customary units ONLY (tsp, tbsp, cup, oz, lb, °F) - NO metric (ml, g, kg, °C)
    4. The cooking method dictates the ENTIRE recipe - if user said "fried", you CANNOT braise or bake

    OUTPUT FORMAT: Valid JSON only, no markdown, no code blocks, no extra text.
    {
    "chef_notes": "1 brief sentence about your dish decision and cooking method choice",
    "title": "string (MUST reflect the cooking method)",
    "description": "string (1-2 sentences)",
    "ingredients": ["qty unit Name (optional note)"],
    "instructions": ["step-by-step using the required cooking method"],
    "cook_time": "X minutes",
    "cuisine": "string",
    "cooking_style": "string (echo back the exact method: fried, baked, grilled, etc.)"
    }""")

        return "\n".join(prompt_parts)

    def generate_new_recipe(self, request: RecipeRequest) -> StructuredRecipe:
        """Generate recipe with dynamic chef persona"""

        # Build smart, context-aware prompt
        chef_prompt = self._build_chef_prompt(request)

        chat = [{"role": "user", "content": chef_prompt}]

        formatted_prompt = self.tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(
            formatted_prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1200,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.65,  # Balanced
            top_p=0.92,
            repetition_penalty=1.15
        )

        response_text = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[-1]:],
            skip_special_tokens=True
        )

        # Clean and parse
        cleaned = self._clean_json_response(response_text)

        try:
            data = self._repair_and_parse_json(cleaned)
            # Validate meal type appropriateness
            if not self._validate_meal_type_appropriateness(data, request):
                print("🔄 Recipe doesn't match meal type, will regenerate...")
                # You could either:
                # Option A: Raise an error to trigger regeneration
                raise ValueError(f"Generated recipe not appropriate for {request.meal_type}")
            
        except Exception as e:
            print(f"❌ Parse failed: {e}")
            print(f"Raw output: {response_text[:300]}")
            raise

        # Light validation (just ensure required fields exist)
        required = ["title", "description", "ingredients", "instructions", "cook_time", "cuisine"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        # FIX INGREDIENTS - Add this order:
        data = self._normalize_ingredients(data)        # NEW - normalize arrays to strings
        data = self._apply_light_quantity_fixes(data)   # existing - fix ml/g/bottles

        # Build recipe
        recipe = StructuredRecipe(
            title=data["title"],
            description=data["description"],
            ingredients=data["ingredients"],
            instructions=data["instructions"],
            cook_time=data["cook_time"],
            cuisine=data["cuisine"],
            cooking_style=data.get("cooking_style", request.cooking_style)
        )

        # Cache to S3
        try:
            self.s3_manager.upload_to_s3(
                json.dumps(recipe.model_dump(), ensure_ascii=False),
                folder="generated_recipes"
            )
        except Exception as e:
            print(f"⚠️ S3 upload failed: {e}")

        return recipe

    def _apply_light_quantity_fixes(self, data: Dict) -> Dict:
        """Fix only the most obvious quantity mistakes"""
        
        if "ingredients" not in data or not isinstance(data["ingredients"], list):
            return data
        
        fixed_ingredients = []
        
        for line in data.get("ingredients", []):
            # Ensure line is a string
            if not isinstance(line, str):
                fixed_ingredients.append(str(line))
                continue
                
            lower = line.lower()
            
            # Fix: "1 bottle" → "1/2 cup"
            if "bottle" in lower:
                line = re.sub(r'\d+\s*bottle[s]?\s+', '1/2 cup ', line, flags=re.IGNORECASE)
            
            # Fix: "400ml" → "~1.5 cups" (rough)
            if "ml" in lower:
                line = re.sub(r'(\d+)\s*ml', lambda m: f"{int(m.group(1))//240 or 1} cup", line)
            
            # Fix: "600g" → "~1.3 lb" (rough)
            if " g " in lower or lower.endswith("g"):
                line = re.sub(r'(\d+)\s*g\b', lambda m: f"{round(int(m.group(1))*0.0022, 1)} lb", line)
            
            fixed_ingredients.append(line)
        
        data["ingredients"] = fixed_ingredients
        return data
    
    def _normalize_ingredients(self, data: Dict) -> Dict:
        """Convert nested arrays or malformed ingredients into proper string format"""
        
        if "ingredients" not in data or not isinstance(data["ingredients"], list):
            return data
        
        normalized = []
        
        for item in data["ingredients"]:
            # Case 1: Already a proper string
            if isinstance(item, str):
                normalized.append(item)
            
            # Case 2: Nested array like ["1.5 lb", "beef", "cut into strips"]
            elif isinstance(item, list):
                # Join with spaces and capitalize first letter of ingredient name
                parts = [str(p).strip() for p in item if p]
                if len(parts) >= 2:
                    # Format: "qty unit Name, notes"
                    qty_unit = " ".join(parts[:2])
                    rest = ", ".join(parts[2:]) if len(parts) > 2 else ""
                    ingredient_name = parts[1] if len(parts) > 1 else parts[0]
                    
                    # Capitalize ingredient name (skip if it's a unit like 'tbsp')
                    units = ['tsp', 'tbsp', 'cup', 'oz', 'lb', 'g', 'ml', 'kg']
                    if ingredient_name.lower() not in units:
                        ingredient_name = ingredient_name.capitalize()
                    
                    if rest:
                        normalized.append(f"{parts[0]} {ingredient_name}, {rest}")
                    else:
                        normalized.append(f"{parts[0]} {ingredient_name}")
                else:
                    # Fallback: just join everything
                    normalized.append(" ".join(parts))
            
            # Case 3: Something else (dict, number, etc.) - convert to string
            else:
                normalized.append(str(item))
        
        data["ingredients"] = normalized
        return data
    
    def _validate_meal_type_appropriateness(self, data: Dict, request: RecipeRequest) -> bool:
        """Check if generated recipe is appropriate for requested meal type"""
        
        if not request.meal_type:
            return True  # No meal type specified, so anything goes
        
        meal_lower = request.meal_type.lower()
        title_lower = data.get("title", "").lower()
        desc_lower = data.get("description", "").lower()
        
        # Breakfast red flags
        if meal_lower == "breakfast":
            breakfast_violations = ["burger", "cheeseburger", "pizza", "spaghetti", "lasagna"]
            for violation in breakfast_violations:
                if violation in title_lower:
                    print(f"⚠️ Meal type violation: '{violation}' in title for breakfast")
                    return False
        
        # Dinner served as breakfast
        if meal_lower == "breakfast":
            if any(word in title_lower for word in ["roast", "braised", "grilled chicken dinner"]):
                if "breakfast" not in title_lower and "egg" not in title_lower:
                    print(f"⚠️ Dinner-style dish proposed for breakfast")
                    return False
        
        return True

    def get_or_generate_recipe(self, request: RecipeRequest) -> RecipeResponse:
        """
        First search S3 for matching recipes, if not found or match is too low, generate a new one
        """
        search_result = self.search_s3_recipes(request)

        if search_result:
            recipe, match_score = search_result

            # Check if match score is good enough (51% or higher)
            if match_score >= 0.51:
                print(
                    f"✨ Returning existing recipe from S3: {recipe.title} (match: {match_score*100:.1f}%)")
                return RecipeResponse(
                    recipe=recipe,
                    source="s3",
                    match_score=match_score
                )
            else:
                print(
                    f"⚠️ Match score too low ({match_score*100:.1f}%), generating new recipe instead")

        print("🤖 Generating new recipe with AI")
        recipe = self.generate_new_recipe(request)
        return RecipeResponse(
            recipe=recipe,
            source="generated",
            match_score=None
        )


class ChefPersonaBuilder:
    """Builds appropriate chef persona based on request"""

    CUISINE_EXPERTS: Dict[str, Dict[str, Any]] = {
        "italian": {
            "name": "Chef Marco",
            "background": "20 years in Tuscany, trained in traditional Italian cooking",
            "staples": ["olive oil", "garlic", "tomatoes", "parmesan", "basil", "oregano", "pasta", "balsamic vinegar"],
            "typical_fats": "olive oil",
            "avoid": ["soy sauce", "fish sauce", "miso", "gochujang"]
        },
        "chinese": {
            "name": "Chef Wei",
            "background": "Szechuan and Cantonese master from Chengdu",
            "staples": ["soy sauce", "rice vinegar", "ginger", "garlic", "scallions", "sesame oil", "shaoxing wine", "oyster sauce", "white pepper"],
            "typical_fats": "vegetable oil or peanut oil",
            "avoid": ["butter", "cream", "olive oil", "parmesan"]
        },
        "mexican": {
            "name": "Chef Rosa",
            "background": "Oaxaca family recipes, expert in mole and traditional techniques",
            "staples": ["cumin", "chili powder", "cilantro", "lime", "garlic", "tomatoes", "onions", "jalapeños", "coriander", "oregano"],
            "typical_fats": "vegetable oil, lard, or avocado oil",
            "avoid": ["soy sauce", "mirin", "fish sauce", "curry powder"]
        },
        "indian": {
            "name": "Chef Anjali",
            "background": "Kerala spice expert with North and South Indian expertise",
            "staples": ["cumin", "coriander", "turmeric", "garam masala", "ginger", "garlic", "ghee", "cardamom", "curry leaves", "yogurt"],
            "typical_fats": "ghee or vegetable oil",
            "avoid": ["soy sauce", "mirin", "fish sauce"]
        },
        "japanese": {
            "name": "Chef Takashi",
            "background": "Kyoto-trained kaiseki specialist with 15 years experience",
            "staples": ["soy sauce", "mirin", "sake", "dashi", "ginger", "rice vinegar", "sesame oil", "miso", "nori", "wasabi"],
            "typical_fats": "sesame oil or vegetable oil",
            "avoid": ["heavy cream", "butter", "olive oil", "wine"]
        },
        "thai": {
            "name": "Chef Somchai",
            "background": "Bangkok street food master specializing in balance of flavors",
            "staples": ["fish sauce", "lime juice", "palm sugar", "thai basil", "lemongrass", "galangal", "thai chilies", "cilantro", "coconut milk"],
            "typical_fats": "vegetable oil or coconut oil",
            "avoid": ["soy sauce", "butter", "heavy cream"]
        },
        "french": {
            "name": "Chef Dubois",
            "background": "Trained at Le Cordon Bleu, classically educated in French technique",
            "staples": ["butter", "cream", "white wine", "shallots", "thyme", "tarragon", "dijon mustard", "garlic", "bay leaf"],
            "typical_fats": "butter or olive oil",
            "avoid": ["fish sauce", "soy sauce", "mirin", "gochujang"]
        },
        "mediterranean": {
            "name": "Chef Dimitris",
            "background": "Coastal Mediterranean specialist from Greece and Southern Italy",
            "staples": ["olive oil", "lemon", "garlic", "oregano", "basil", "tomatoes", "olives", "feta cheese", "capers", "parsley"],
            "typical_fats": "olive oil",
            "avoid": ["soy sauce", "fish sauce", "heavy cream", "butter"]
        },
        "american": {
            "name": "Chef Jake",
            "background": "Modern American cuisine with Southern and BBQ influences",
            "staples": ["butter", "garlic powder", "onion powder", "paprika", "black pepper", "worcestershire sauce", "mustard", "brown sugar", "hot sauce"],
            "typical_fats": "butter, vegetable oil, or bacon fat",
            "avoid": ["fish sauce", "mirin"]
        },
        "korean": {
            "name": "Chef Min-ju",
            "background": "Seoul-trained in traditional and modern Korean cooking",
            "staples": ["gochujang", "gochugaru", "soy sauce", "sesame oil", "garlic", "ginger", "scallions", "doenjang", "rice vinegar", "perilla oil"],
            "typical_fats": "sesame oil or vegetable oil",
            "avoid": ["butter", "cream", "olive oil", "fish sauce"]
        },
        "greek": {
            "name": "Chef Yiannis",
            "background": "Athens-trained in traditional Greek taverna cooking",
            "staples": ["olive oil", "lemon", "oregano", "garlic", "feta cheese", "olives", "tomatoes", "dill", "mint", "yogurt"],
            "typical_fats": "olive oil",
            "avoid": ["soy sauce", "fish sauce", "butter", "heavy cream"]
        },
        "spanish": {
            "name": "Chef Carmen",
            "background": "Barcelona-trained in tapas and paella traditions",
            "staples": ["olive oil", "garlic", "paprika", "saffron", "tomatoes", "parsley", "almonds", "sherry vinegar", "chorizo", "manchego cheese"],
            "typical_fats": "olive oil",
            "avoid": ["soy sauce", "fish sauce", "butter", "asian spices"]
        }
    }

    @staticmethod
    def build_persona(cuisine: Optional[str]) -> Dict[str, Any]:
        """Return the matching persona dict or a generalist if none specified."""
        if not cuisine:
            return {
                "name": "Chef Alex",
                "background": "Culinary Institute graduate with global fusion experience",
                "approach": "I adapt any ingredient to create balanced, delicious dishes",
                "staples": ["salt", "pepper", "garlic", "onions", "olive oil", "butter", "herbs", "spices"],
                "typical_fats": "olive oil or butter",
                "avoid": []
            }

        key = cuisine.lower().strip()
        return ChefPersonaBuilder.CUISINE_EXPERTS.get(key, {
            "name": "Chef Alex",
            "background": f"{cuisine.title()} cuisine specialist with international training",
            "approach": f"I create authentic {cuisine.title()} dishes while respecting ingredient availability",
            "staples": ["salt", "pepper", "garlic", "onions", "oil", "herbs", "spices"],
            "typical_fats": "oil or butter",
            "avoid": []
        })


class IngredientAnalyzer:
    """Analyzes user ingredients for cuisine conflicts"""

    @staticmethod
    def detect_conflicts(user_ingredients: List[str], cuisine: Optional[str]) -> Dict:
        """Detect if user ingredients conflict with requested cuisine"""
        if not cuisine:
            return {
                "has_conflict": False,
                "conflicts": [],
                "staples": ["salt", "pepper", "garlic", "onions", "oil"],
                "typical_fats": "oil or butter"
            }

        persona = ChefPersonaBuilder.build_persona(cuisine)

        # avoid is already a list, not a string
        avoid_list = persona.get("avoid", [])

        conflicts = []
        for ing in user_ingredients:
            ing_lower = ing.lower()
            for avoid_item in avoid_list:
                avoid_lower = avoid_item.lower()
                if avoid_lower in ing_lower:
                    conflicts.append({
                        "ingredient": ing,
                        "issue": avoid_item,
                        "suggestion": f"atypical for {cuisine}"
                    })

        return {
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts,
            "staples": persona.get("staples", []),
            "typical_fats": persona.get("typical_fats", "oil")
        }


# ==================== MODAL SETUP ====================
app = modal.App("recipe-generator-final-test")
model_cache_volume = modal.Volume.from_name(
    "recipe-cache-final-test",
    create_if_missing=True
)
CACHE_PATH = "/model-cache"

# Define the image
image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "bitsandbytes>=0.41.0",
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "boto3>=1.28.0",
        "sentencepiece>=0.1.99",
        "protobuf>=3.20.0"
    )
)


@app.function(
    image=image,
    gpu="A10G",
    volumes={CACHE_PATH: model_cache_volume},
    secrets=[modal.Secret.from_name("food-gen-secret")],
    scaledown_window=300,
    timeout=600
)
@modal.asgi_app()
def fastapi_app():
    web_app = FastAPI(
        title="Recipe Generator API",
        description="AI-powered recipe generator with S3 caching",
        version="1.0.0"
    )

    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize model once per container
    recipe_model = RecipeModel(cache_path=CACHE_PATH)

    @web_app.post("/", tags=["Recipes"])
    def generate_recipe(request: RecipeRequest):
        """
        🔍 Search for existing recipe in S3, or generate new one if not found
        """
        result = recipe_model.get_or_generate_recipe(request)

        # Add debug logging
        print("=" * 50)
        print("📤 SENDING RESPONSE TO FRONTEND:")
        print(f"Recipe title: {result.recipe.title}")
        print(f"Ingredients count: {len(result.recipe.ingredients)}")
        print(f"Instructions count: {len(result.recipe.instructions)}")
        print(f"Source: {result.source}")
        print("=" * 50)

        # Return the recipe model directly, not from model_dump
        return {
            "recipe": {
                "title": result.recipe.title,
                "description": result.recipe.description,
                "ingredients": result.recipe.ingredients,
                "instructions": result.recipe.instructions,
                "cook_time": result.recipe.cook_time,
                "cuisine": result.recipe.cuisine,
            },
            "source": result.source,
            "match_score": result.match_score
        }

    @web_app.post("/generate-new", tags=["Recipes"])
    def force_generate_recipe(request: RecipeRequest):
        """
        🤖 Force generation of a new recipe (skip S3 search)

        Use this when you want a completely new recipe regardless of what's cached.
        """
        print("🚀 Forcing new recipe generation (skipping S3 search)")
        recipe = recipe_model.generate_new_recipe(request)
        return {
            "recipe": recipe.model_dump(),
            "source": "generated",
            "match_score": None
        }

    @web_app.post("/search", tags=["Search"])
    def search_recipes(request: RecipeRequest):
        """
        🔎 Search S3 for matching recipes without generating a new one

        Returns the best matching recipe from S3 or a message if none found.
        """
        search_result = recipe_model.search_s3_recipes(request)
        if search_result:
            recipe, match_score = search_result
            return {
                "found": True,
                "recipe": recipe.model_dump(),
                "match_score": match_score,
                "match_percentage": f"{match_score * 100:.1f}%"
            }
        return {
            "found": False,
            "message": "No matching recipes found in S3. Try /generate-new to create one!"
        }

    @web_app.get("/recipes", tags=["Browse"])
    def list_recipes():
        """
        📋 List all generated recipes from S3

        Returns metadata for all cached recipes.
        """
        files = recipe_model.s3_manager.list_recipe_files()
        return {
            "recipes": files,
            "count": len(files),
            "message": f"Found {len(files)} recipe(s) in cache"
        }

    @web_app.get("/recipe/{filename}", tags=["Browse"])
    def get_recipe(filename: str):
        """
        📖 Get a specific recipe from S3 by filename

        Example: /recipe/20240115_123456_789012.json
        """
        recipe = recipe_model.s3_manager.get_recipe(filename)
        if recipe:
            return recipe
        return {
            "error": "Recipe not found",
            "message": f"No recipe found with filename: {filename}"
        }

    @web_app.get("/health", tags=["System"])
    def health_check():
        """
        ✅ Health check endpoint

        Returns system status and S3 connection info.
        """
        try:
            recipes_count = len(recipe_model.s3_manager.list_recipe_files())
        except Exception as e:
            print(f"Error getting recipe count: {e}")
            recipes_count = 0

        return {
            "status": "healthy",
            "model": "loaded",
            "s3_connected": recipe_model.s3_manager.bucket_name is not None,
            "bucket_name": recipe_model.s3_manager.bucket_name,
            "cached_recipes": recipes_count,
            "cache_path": CACHE_PATH
        }

    @web_app.get("/stats", tags=["System"])
    def get_stats():
        """
        📊 Get statistics about cached recipes

        Returns counts by cuisine, ingredient usage, etc.
        """
        try:
            recipes = recipe_model.s3_manager.get_all_recipes()

            cuisines = {}
            total_recipes = len(recipes)

            for recipe in recipes:
                cuisine = recipe.get('cuisine', 'Unknown')
                cuisines[cuisine] = cuisines.get(cuisine, 0) + 1

            most_popular = None
            if cuisines:
                most_popular = max(cuisines.items(), key=lambda x: x[1])[0]

            return {
                "total_recipes": total_recipes,
                "cuisines": cuisines,
                "most_popular_cuisine": most_popular
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "error": str(e),
                "total_recipes": 0,
                "cuisines": {}
            }

    @web_app.get("/", tags=["System"])
    def root():
        """
        👋 Welcome endpoint
        """
        return {
            "message": "Welcome to Recipe Generator API",
            "version": "1.0.0",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "stats": "/stats",
                "generate": "POST /",
                "force_new": "POST /generate-new",
                "search": "POST /search",
                "list": "GET /recipes"
            }
        }

    return web_app
