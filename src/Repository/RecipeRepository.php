<?php

namespace App\Repository;

use App\Entity\Recipe;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;
use Doctrine\ORM\QueryBuilder;

class RecipeRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Recipe::class);
    }

    /**
     * Find recipes by ingredients
     * 
     * @param array $ingredients List of ingredient names
     * @return array
     */
    public function findRecipesByIngredients(array $ingredients): array
    {
        // This is a placeholder implementation
        // In a real-world scenario, you'd likely use an external API or complex database query
        $qb = $this->createQueryBuilder('r');
        
        // Example of a simple query (you'll need to adjust based on your actual data model)
        $qb->where($qb->expr()->orX(
            ...array_map(fn($ingredient) => $qb->expr()->like('r.title', ":ingredient_{$ingredient}"), $ingredients)
        ));

        foreach ($ingredients as $ingredient) {
            $qb->setParameter("ingredient_{$ingredient}", "%{$ingredient}%");
        }

        return $qb->getQuery()->getResult();
    }
}
