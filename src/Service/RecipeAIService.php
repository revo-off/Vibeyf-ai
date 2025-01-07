<?php

namespace App\Service;

use Symfony\Contracts\HttpClient\HttpClientInterface;
use Symfony\Component\DependencyInjection\ParameterBag\ParameterBagInterface;

class RecipeAIService
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private ParameterBagInterface $params
    ) {}

    public function getRecipeSuggestions(array $ingredients): array
    {
        try {
            // Obtenir les recettes de base avec Spoonacular
            $baseRecipes = $this->getBaseRecipes($ingredients);
            
            // Pour chaque recette, obtenir des alternatives et substitutions
            $enrichedRecipes = [];
            foreach ($baseRecipes as $recipe) {
                $enrichedRecipe = $this->enrichRecipeWithAlternatives($recipe, $ingredients);
                $enrichedRecipes[] = $enrichedRecipe;
            }
            
            return $enrichedRecipes;
        } catch (\Exception $e) {
            return [];
        }
    }

    private function getBaseRecipes(array $ingredients): array
    {
        $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/recipes/findByIngredients', [
            'query' => [
                'apiKey' => $this->params->get('app.spoonacular_api_key'),
                'ingredients' => implode(',', $ingredients),
                'number' => 5,
                'ranking' => 2, // Maximiser l'utilisation des ingrédients disponibles
                'ignorePantry' => true
            ]
        ]);

        return $response->toArray();
    }

    private function enrichRecipeWithAlternatives(array $recipe, array $availableIngredients): array
    {
        // Obtenir les détails complets de la recette
        $recipeDetails = $this->getRecipeDetails($recipe['id']);
        
        // Trouver des substitutions pour les ingrédients manquants
        $substitutions = [];
        foreach ($recipe['missedIngredients'] as $missedIngredient) {
            $substitutions[$missedIngredient['id']] = $this->findIngredientSubstitutes($missedIngredient['id']);
        }

        // Obtenir des variantes de la recette
        $variations = $this->getSimilarRecipes($recipe['id']);

        return array_merge($recipe, [
            'instructions' => $recipeDetails['instructions'] ?? '',
            'substitutions' => $substitutions,
            'variations' => $variations,
            'tips' => $this->generateCookingTips($recipe, $availableIngredients)
        ]);
    }

    private function getRecipeDetails(int $recipeId): array
    {
        $response = $this->httpClient->request('GET', "https://api.spoonacular.com/recipes/{$recipeId}/information", [
            'query' => [
                'apiKey' => $this->params->get('app.spoonacular_api_key')
            ]
        ]);

        return $response->toArray();
    }

    private function findIngredientSubstitutes(int $ingredientId): array
    {
        $response = $this->httpClient->request('GET', "https://api.spoonacular.com/food/ingredients/{$ingredientId}/substitutes", [
            'query' => [
                'apiKey' => $this->params->get('app.spoonacular_api_key')
            ]
        ]);

        $data = $response->toArray();
        return $data['substitutes'] ?? [];
    }

    private function getSimilarRecipes(int $recipeId): array
    {
        $response = $this->httpClient->request('GET', "https://api.spoonacular.com/recipes/{$recipeId}/similar", [
            'query' => [
                'apiKey' => $this->params->get('app.spoonacular_api_key'),
                'number' => 3
            ]
        ]);

        return $response->toArray();
    }

    private function generateCookingTips(array $recipe, array $availableIngredients): array
    {
        $tips = [];

        // Astuces basées sur les ingrédients disponibles
        if (count($recipe['missedIngredients']) > 0) {
            $tips[] = "Vous pouvez adapter cette recette en utilisant les ingrédients que vous avez déjà !";
        }

        // Astuces de préparation
        if (isset($recipe['preparationMinutes']) && $recipe['preparationMinutes'] > 30) {
            $tips[] = "Pour gagner du temps, vous pouvez préparer certains ingrédients à l'avance.";
        }

        // Astuces de conservation
        if (count($recipe['usedIngredients']) > 3) {
            $tips[] = "Les restes de cette recette se conservent bien au réfrigérateur pendant 2-3 jours.";
        }

        return $tips;
    }
}
