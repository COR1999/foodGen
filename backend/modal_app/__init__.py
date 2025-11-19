# # modal_app/__init__.py
# """
# Recipe Generator API
# ====================

# An AI-powered recipe generator that uses S3 for caching and intelligent recipe matching.

# Main components:
# - RecipeModel: Handles AI generation and recipe management
# - S3Manager: Manages S3 operations and storage
# - RecipeMatcher: Implements recipe matching logic
# """

# from .models import RecipeRequest, StructuredRecipe, RecipeResponse
# from .recipe_model import RecipeModel
# from .s3_manager import S3Manager
# from .recipe_matcher import RecipeMatcher

# __version__ = "1.0.0"
# __all__ = [
#     "RecipeRequest",
#     "StructuredRecipe", 
#     "RecipeResponse",
#     "RecipeModel",
#     "S3Manager",
#     "RecipeMatcher"
# ]