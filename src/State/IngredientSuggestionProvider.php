<?php

namespace App\State;

use ApiPlatform\Metadata\Operation;
use ApiPlatform\State\ProviderInterface;
use App\Entity\Ingredient;
use Symfony\Contracts\HttpClient\HttpClientInterface;
use Symfony\Component\DependencyInjection\ParameterBag\ParameterBagInterface;

class IngredientSuggestionProvider implements ProviderInterface
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private ParameterBagInterface $params
    ) {}

    public function provide(Operation $operation, array $uriVariables = [], array $context = []): array
    {
        $query = $context['filters']['q'] ?? '';
        
        if (empty($query)) {
            return [];
        }

        try {
            $response = $this->httpClient->request('GET', 'https://api.spoonacular.com/food/ingredients/autocomplete', [
                'query' => [
                    'apiKey' => $this->params->get('app.spoonacular_api_key'),
                    'query' => $query,
                    'number' => 5,
                    'metaInformation' => false
                ]
            ]);

            $data = $response->toArray();
            
            return array_map(function($item) {
                $ingredient = new Ingredient();
                $ingredient->setName($item['name']);
                return $ingredient;
            }, $data);
        } catch (\Exception $e) {
            return [];
        }
    }
}
