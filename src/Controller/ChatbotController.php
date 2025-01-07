<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Contracts\HttpClient\HttpClientInterface;
use App\Repository\RecipeRepository;
use Doctrine\ORM\EntityManagerInterface;
use App\Form\IngredientSelectionType;
use App\Entity\Ingredient;
use Symfony\Component\HttpClient\HttpClient;

class ChatbotController extends AbstractController
{
    private $httpClient;
    private $ingredientsMap = [
        'tomates' => ['emoji' => '🍅', 'en' => 'tomatoes'],
        'oignons' => ['emoji' => '🧅', 'en' => 'onions'],
        'ail' => ['emoji' => '🧄', 'en' => 'garlic'],
        'carottes' => ['emoji' => '🥕', 'en' => 'carrots'],
        'pomme de terre' => ['emoji' => '🥔', 'en' => 'potatoes'],
        'poivron' => ['emoji' => '🫑', 'en' => 'bell pepper'],
        'champignon' => ['emoji' => '🍄', 'en' => 'mushroom'],
        'tomate' => ['emoji' => '🍅', 'en' => 'tomato'],
        'oignon' => ['emoji' => '🧅', 'en' => 'onion'],
        'carotte' => ['emoji' => '🥕', 'en' => 'carrot'],
        'oignon rouge' => ['emoji' => '🧅', 'en' => 'red onion']
    ];

    public function __construct(HttpClientInterface $httpClient, RecipeRepository $recipeRepository, EntityManagerInterface $entityManager)
    {
        $this->httpClient = $httpClient;
        $this->recipeRepository = $recipeRepository;
        $this->entityManager = $entityManager;
    }

    #[Route('/', name: 'recipe_home')]
    public function index(): Response
    {
        return $this->render('recipe/index.html.twig');
    }

    private function translateText($text, $targetLang = 'fr', $sourceLang = 'en')
    {
        // Simulation de traduction
        return $text;
    }

    private function translateToEnglish($ingredients)
    {
        $translatedIngredients = [];
        foreach ($ingredients as $ingredient) {
            $ingredientLower = strtolower($ingredient);
            $translatedIngredients[] = $this->ingredientsMap[$ingredientLower]['en'] ?? $ingredient;
        }
        return $translatedIngredients;
    }

    private function translateRecipeData(array $recipe)
    {
        return $recipe;
    }

    /**
     * Recherche de recettes par ingrédients
     */
    #[Route('/recipes/by-ingredients', name: 'recipes_by_ingredients', methods: ['GET'])]
    public function searchRecipesByIngredients(Request $request): JsonResponse
    {
        $ingredientsParam = $request->query->get('ingredients', '');
        $ingredients = explode(',', $ingredientsParam);
        
        if (empty($ingredients)) {
            return $this->json([
                'success' => false,
                'message' => 'Aucun ingrédient fourni'
            ], 400);
        }

        // Traduire les ingrédients en anglais
        $translatedIngredients = $this->translateIngredients($ingredients);

        try {
            // Utiliser l'API Spoonacular pour trouver des recettes
            $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/recipes/findByIngredients', [
                'query' => [
                    'apiKey' => $this->getParameter('app.spoonacular_api_key'),
                    'ingredients' => implode(',+', $translatedIngredients), // Utiliser '+' pour l'API Spoonacular
                    'number' => 12, // Augmenter le nombre de recettes
                    'ranking' => 1, // Maximiser les ingrédients utilisés
                    'ignorePantry' => true // Ignorer les ingrédients de base
                ]
            ]);

            $recipes = $response->toArray();

            // Formater les recettes avec des informations détaillées
            $formattedRecipes = array_map(function($recipe) {
                // Récupérer les détails complets de la recette
                try {
                    $recipeDetails = $this->httpClient->request('GET', "https://api.spoonacular.com/recipes/{$recipe['id']}/information", [
                        'query' => [
                            'apiKey' => $this->getParameter('app.spoonacular_api_key'),
                            'includeNutrition' => false
                        ]
                    ])->toArray();

                    return [
                        'id' => $recipe['id'],
                        'title' => $recipe['title'],
                        'image' => $recipe['image'],
                        'usedIngredientCount' => $recipe['usedIngredientCount'],
                        'missedIngredientCount' => $recipe['missedIngredientCount'],
                        'usedIngredients' => array_map(function($ing) {
                            return $ing['name'];
                        }, $recipe['usedIngredients']),
                        'missedIngredients' => array_map(function($ing) {
                            return $ing['name'];
                        }, $recipe['missedIngredients']),
                        // Informations supplémentaires
                        'readyInMinutes' => $recipeDetails['readyInMinutes'] ?? null,
                        'servings' => $recipeDetails['servings'] ?? null,
                        'sourceUrl' => $recipeDetails['sourceUrl'] ?? null,
                        'summary' => strip_tags($recipeDetails['summary'] ?? ''), // Enlever les balises HTML
                        'instructions' => $recipeDetails['instructions'] ?? null
                    ];
                } catch (\Exception $e) {
                    // En cas d'erreur lors de la récupération des détails, retourner les informations de base
                    return [
                        'id' => $recipe['id'],
                        'title' => $recipe['title'],
                        'image' => $recipe['image'],
                        'usedIngredientCount' => $recipe['usedIngredientCount'],
                        'missedIngredientCount' => $recipe['missedIngredientCount'],
                        'usedIngredients' => array_map(function($ing) {
                            return $ing['name'];
                        }, $recipe['usedIngredients']),
                        'missedIngredients' => array_map(function($ing) {
                            return $ing['name'];
                        }, $recipe['missedIngredients'])
                    ];
                }
            }, $recipes);

            return $this->json([
                'success' => true,
                'recipes' => $formattedRecipes
            ]);
        } catch (\Exception $e) {
            // En cas d'erreur d'API (comme 402 Payment Required), utiliser les recettes mockées
            if (strpos($e->getMessage(), '402 Payment Required') !== false) {
                $mockRecipes = $this->generateMockRecipes($ingredients);
                
                return $this->json([
                    'success' => true,
                    'recipes' => $mockRecipes,
                    'message' => 'Utilisation de recettes mockées en raison de problèmes d\'API'
                ]);
            }

            // Autres types d'erreurs
            return $this->json([
                'success' => false,
                'message' => 'Erreur lors de la recherche de recettes : ' . $e->getMessage(),
                'error_details' => [
                    'code' => $e->getCode(),
                    'trace' => $e->getTraceAsString()
                ]
            ], 500);
        }
    }

    private function translateIngredients(array $ingredients): array
    {
        $translations = [
            // Fruits
            'Banane' => 'banana',
            'Pomme' => 'apple',
            'Poire' => 'pear',
            'Orange' => 'orange',
            'Fraise' => 'strawberry',
            'Framboise' => 'raspberry',
            
            // Légumes
            'Tomate' => 'tomato',
            'Carotte' => 'carrot',
            'Pomme de terre' => 'potato',
            'Oignon' => 'onion',
            'Ail' => 'garlic',
            'Champignon' => 'mushroom',
            'Poivron' => 'bell pepper',
            
            // Produits laitiers
            'Lait' => 'milk',
            'Crème' => 'cream',
            'Fromage' => 'cheese',
            'Beurre' => 'butter',
            'Yaourt' => 'yogurt',
            
            // Protéines
            'Œuf' => 'egg',
            'Poulet' => 'chicken',
            'Bœuf' => 'beef',
            'Poisson' => 'fish',
            'Thon' => 'tuna',
            
            // Herbes et épices
            'Basilic' => 'basil',
            'Persil' => 'parsley',
            'Thym' => 'thyme',
            'Romarin' => 'rosemary',
            
            // Autres
            'Sucre' => 'sugar',
            'Sel' => 'salt',
            'Poivre' => 'pepper',
            'Huile d\'olive' => 'olive oil',
            'Miel' => 'honey'
        ];

        return array_map(function($ingredient) use ($translations) {
            // Recherche de correspondance exacte
            $ingredient = trim($ingredient);
            if (isset($translations[$ingredient])) {
                return $translations[$ingredient];
            }

            // Recherche de correspondance partielle
            foreach ($translations as $french => $english) {
                if (stripos($ingredient, $french) !== false) {
                    return $english;
                }
            }

            // Si aucune correspondance, retourner l'ingrédient en minuscules
            return strtolower($ingredient);
        }, $ingredients);
    }

    private function generateMockRecipes(array $ingredients): array
    {
        $mockRecipes = [
            [
                'id' => 1,
                'title' => 'Salade de Tomates et Oignons',
                'image' => 'https://example.com/salade.jpg',
                'usedIngredientCount' => 2,
                'missedIngredientCount' => 0,
                'usedIngredients' => $ingredients,
                'missedIngredients' => [],
                'readyInMinutes' => 15,
                'servings' => 2,
                'instructions' => "1. Laver et couper les tomates en dés.\n2. Émincer finement les oignons.\n3. Mélanger les tomates et les oignons dans un bol.\n4. Assaisonner avec du sel, du poivre et un filet d'huile d'olive.\n5. Servir frais.",
                'summary' => 'Une salade fraîche et simple à base de tomates et d\'oignons.'
            ],
            [
                'id' => 2,
                'title' => 'Omelette aux Champignons',
                'image' => 'https://example.com/omelette.jpg',
                'usedIngredientCount' => 1,
                'missedIngredientCount' => 1,
                'usedIngredients' => ['Champignon'],
                'missedIngredients' => ['Œufs'],
                'readyInMinutes' => 20,
                'servings' => 1,
                'instructions' => "1. Nettoyer et couper les champignons en lamelles.\n2. Faire chauffer une poêle avec du beurre.\n3. Faire revenir les champignons jusqu'à ce qu'ils soient dorés.\n4. Battre les œufs et les verser dans la poêle.\n5. Cuire l'omelette des deux côtés.",
                'summary' => 'Une délicieuse omelette aux champignons, simple et rapide à préparer.'
            ]
        ];

        return $mockRecipes;
    }

    #[Route('/api/recipe/search', name: 'api_recipe_search', methods: ['POST'])]
    public function searchRecipes(Request $request): JsonResponse
    {
        try {
            $data = json_decode($request->getContent(), true);
            
            error_log('Données reçues : ' . print_r($data, true));

            if (!isset($data['ingredients'])) {
                return new JsonResponse([
                    'success' => false,
                    'message' => 'Le paramètre "ingredients" est manquant'
                ]);
            }

            $ingredients = explode(',', $data['ingredients']);
            $ingredientsSet = array_map('strtolower', $ingredients);

            if (empty($ingredients)) {
                return new JsonResponse([
                    'success' => false,
                    'message' => 'Veuillez fournir au moins un ingrédient'
                ]);
            }

            // Vérifier si nous sommes en mode démo
            if (!isset($_ENV['SPOONACULAR_API_KEY']) || empty($_ENV['SPOONACULAR_API_KEY'])) {
                // Retourner des données de démonstration
                return $this->getDemoRecipes($ingredients);
            }

            try {
                $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/recipes/findByIngredients', [
                    'query' => [
                        'apiKey' => $_ENV['SPOONACULAR_API_KEY'],
                        'ingredients' => implode(',', $ingredients),
                        'number' => 2, // Réduit à 2 pour économiser les points API
                        'ranking' => 2,
                        'ignorePantry' => true
                    ]
                ]);

                $statusCode = $response->getStatusCode();
                if ($statusCode === 402) {
                    return $this->getDemoRecipes($ingredients);
                }

                $recipes = json_decode($response->getContent(), true);

                if (empty($recipes)) {
                    return new JsonResponse([
                        'success' => false,
                        'message' => 'Aucune recette trouvée avec ces ingrédients'
                    ]);
                }

                $detailedRecipes = [];
                foreach ($recipes as $recipe) {
                    $detailsUrl = "https://api.spoonacular.com/recipes/{$recipe['id']}/information";
                    error_log('Récupération des détails de la recette : ' . $detailsUrl);

                    $detailsResponse = $this->httpClient->request('GET', $detailsUrl, [
                        'query' => [
                            'apiKey' => $_ENV['SPOONACULAR_API_KEY']
                        ]
                    ]);

                    $details = json_decode($detailsResponse->getContent(), true);
                    error_log('Détails de la recette : ' . print_r($details, true));

                    $translatedTitle = $this->translateText($details['title']);
                    $translatedInstructions = $details['instructions'] ? $this->translateText($details['instructions']) : 'Instructions non disponibles';

                    $availableIngredients = [];
                    $missingIngredients = [];

                    foreach ($details['extendedIngredients'] as $ingredient) {
                        $translatedName = $this->translateText($ingredient['original']);
                        $ingredientLower = strtolower($ingredient['name']);
                        
                        $amount = isset($ingredient['amount']) ? $ingredient['amount'] : '';
                        $unit = isset($ingredient['unit']) ? $ingredient['unit'] : '';
                        
                        if (in_array($ingredientLower, $ingredientsSet)) {
                            $availableIngredients[] = [
                                'name' => $translatedName,
                                'amount' => $amount,
                                'unit' => $unit
                            ];
                        } else {
                            $missingIngredients[] = [
                                'name' => $translatedName,
                                'amount' => $amount,
                                'unit' => $unit
                            ];
                        }
                    }

                    $detailedRecipes[] = [
                        'id' => $details['id'],
                        'title' => $translatedTitle,
                        'image' => $details['image'] ?? '',
                        'readyInMinutes' => $details['readyInMinutes'] ?? 0,
                        'servings' => $details['servings'] ?? 0,
                        'availableIngredients' => $availableIngredients,
                        'missingIngredients' => $missingIngredients,
                        'instructions' => $translatedInstructions,
                        'sourceUrl' => $details['sourceUrl'] ?? ''
                    ];
                }

                return new JsonResponse([
                    'success' => true,
                    'recipes' => $detailedRecipes
                ]);

            } catch (\Exception $e) {
                error_log('Erreur API Spoonacular : ' . $e->getMessage());
                return $this->getDemoRecipes($ingredients);
            }

        } catch (\Exception $e) {
            error_log('Erreur lors de la recherche de recettes : ' . $e->getMessage());
            return new JsonResponse([
                'success' => false,
                'message' => 'Une erreur est survenue lors de la recherche de recettes. Veuillez réessayer.'
            ]);
        }
    }

    #[Route('/api/ingredients/autocomplete', name: 'api_ingredients_autocomplete', methods: ['GET'])]
    public function autocomplete(Request $request): JsonResponse
    {
        $query = $request->query->get('query');
        
        if (empty($query)) {
            return new JsonResponse([]);
        }

        try {
            // Appel à l'API Spoonacular pour l'autocomplétion
            $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/food/ingredients/autocomplete', [
                'query' => [
                    'apiKey' => $_ENV['SPOONACULAR_API_KEY'],
                    'query' => $query,
                    'number' => 5,
                    'language' => 'fr', // Ajout de la langue française
                    'metaInformation' => true
                ]
            ]);

            $suggestions = json_decode($response->getContent(), true);
            
            // Log des suggestions reçues
            error_log('Suggestions reçues de Spoonacular: ' . print_r($suggestions, true));
            
            // Traduire les suggestions en français
            $translatedSuggestions = [];
            foreach ($suggestions as $suggestion) {
                $translatedName = $this->translateText($suggestion['name']);
                error_log("Traduction: {$suggestion['name']} -> {$translatedName}");
                
                $translatedSuggestions[] = [
                    'name' => $translatedName,
                    'image' => "https://spoonacular.com/cdn/ingredients_100x100/" . ($suggestion['image'] ?? ''),
                    'original' => $suggestion['name']
                ];
            }

            error_log('Suggestions traduites: ' . print_r($translatedSuggestions, true));
            return new JsonResponse($translatedSuggestions);
        } catch (\Exception $e) {
            error_log('Erreur autocomplete: ' . $e->getMessage());
            return new JsonResponse([]);
        }
    }

    #[Route('/api/ingredients/suggest', name: 'api_ingredients_suggest', methods: ['GET'])]
    public function suggestIngredients(Request $request): JsonResponse
    {
        $query = $request->query->get('q', '');
        
        if (strlen($query) < 1) {
            return new JsonResponse([]);
        }

        try {
            $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/food/ingredients/autocomplete', [
                'query' => [
                    'apiKey' => $this->getParameter('app.spoonacular_api_key'),
                    'query' => $query,
                    'number' => 5,
                    'metaInformation' => false
                ]
            ]);

            $suggestions = json_decode($response->getContent(), true);
            
            // Transformer les suggestions pour n'avoir que les noms
            $suggestions = array_map(function($item) {
                return $item['name'];
            }, $suggestions);

            return new JsonResponse($suggestions);
        } catch (\Exception $e) {
            return new JsonResponse([]);
        }
    }

    #[Route('/ingredients/select', name: 'ingredient_select', methods: ['GET', 'POST'])]
    public function selectIngredients(Request $request): Response
    {
        // Récupérer tous les ingrédients
        $ingredients = $this->entityManager->getRepository(Ingredient::class)->findAll();
        
        // Créer un formulaire pour chaque ingrédient
        $forms = [];
        foreach ($ingredients as $ingredient) {
            $form = $this->createForm(IngredientSelectionType::class, $ingredient);
            $form->handleRequest($request);
            
            if ($form->isSubmitted() && $form->isValid()) {
                $this->entityManager->persist($ingredient);
            }
            
            $forms[] = $form->createView();
        }
        
        // Si le formulaire est soumis, enregistrer les modifications
        if ($request->isMethod('POST')) {
            $this->entityManager->flush();
            return $this->redirectToRoute('ingredient_select');
        }
        
        return $this->render('ingredient/select.html.twig', [
            'ingredientForms' => $forms
        ]);
    }

    #[Route('/ingredients/selected', name: 'ingredient_selected')]
    public function getSelectedIngredients(): JsonResponse
    {
        $selectedIngredients = $this->entityManager->getRepository(Ingredient::class)->findBy(['selected' => true]);
        
        $ingredientNames = array_map(function($ingredient) {
            return $ingredient->getName();
        }, $selectedIngredients);
        
        return $this->json([
            'selectedIngredients' => $ingredientNames
        ]);
    }

    private function getDemoRecipes(array $ingredients): JsonResponse
    {
        $selectedIngredients = array_map('strtolower', $ingredients);

        $allRecipes = [
            [
                'id' => 1,
                'title' => 'Carottes rôties à l\'ail',
                'image' => 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
                'readyInMinutes' => 30,
                'servings' => 4,
                'availableIngredients' => [
                    ['name' => 'Carottes', 'amount' => 500, 'unit' => 'g'],
                    ['name' => 'Ail', 'amount' => 2, 'unit' => 'gousses']
                ],
                'missingIngredients' => [
                    ['name' => 'Huile d\'olive', 'amount' => 2, 'unit' => 'cuillères à soupe'],
                    ['name' => 'Thym', 'amount' => 1, 'unit' => 'branche']
                ],
                'instructions' => "1. Préchauffer le four à 200°C.\n2. Peler et couper les carottes en bâtonnets.\n3. Écraser l'ail.\n4. Mélanger les carottes avec l'huile d'olive et l'ail.\n5. Ajouter le thym.\n6. Cuire au four pendant 25-30 minutes.",
                'sourceUrl' => '#'
            ],
            [
                'id' => 2,
                'title' => 'Champignons farcis',
                'image' => 'https://images.unsplash.com/photo-1504544750208-dc0358e63f7f?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
                'readyInMinutes' => 35,
                'servings' => 2,
                'availableIngredients' => [
                    ['name' => 'Champignons', 'amount' => 200, 'unit' => 'g']
                ],
                'missingIngredients' => [
                    ['name' => 'Fromage', 'amount' => 50, 'unit' => 'g'],
                    ['name' => 'Persil', 'amount' => 1, 'unit' => 'bouquet']
                ],
                'instructions' => "1. Nettoyer et évider les champignons.\n2. Préparer la farce avec du fromage et du persil.\n3. Remplir les champignons.\n4. Faire cuire au four à 180°C pendant 20 minutes.",
                'sourceUrl' => '#'
            ]
        ];

        $filteredRecipes = array_filter($allRecipes, function($recipe) use ($selectedIngredients) {
            $availableIngredientNames = array_map('strtolower', array_column($recipe['availableIngredients'], 'name'));
            return count(array_intersect($selectedIngredients, $availableIngredientNames)) > 0;
        });

        return new JsonResponse([
            'success' => true,
            'recipes' => array_values($filteredRecipes)
        ]);
    }

    private function getIngredientCategory(string $ingredient)
    {
        return 'ingrédient similaire';
    }
}
