<?php

namespace App\Entity;

use ApiPlatform\Metadata\ApiProperty;
use ApiPlatform\Metadata\Get;
use ApiPlatform\Metadata\GetCollection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;
use App\State\IngredientSuggestionProvider;

#[ORM\Entity]
#[ApiResource(
    operations: [
        new Get(),
        new GetCollection(
            uriTemplate: '/ingredients/suggest',
            provider: IngredientSuggestionProvider::class,
            description: 'Suggest ingredients based on query',
            parameters: [
                [
                    'name' => 'q', 
                    'description' => 'Search query for ingredients',
                    'in' => 'query',
                    'required' => true,
                    'schema' => ['type' => 'string']
                ]
            ]
        )
    ]
)]
class Ingredient
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 255)]
    #[Assert\NotBlank(message: "Ingredient name cannot be blank")]
    #[Assert\Length(
        min: 2, 
        max: 255, 
        minMessage: "Ingredient name must be at least {{ limit }} characters long",
        maxMessage: "Ingredient name cannot be longer than {{ limit }} characters"
    )]
    private ?string $name = null;

    #[ORM\Column(type: "boolean", options: ["default" => false])]
    private bool $selected = false;

    public function __construct(?string $name = null)
    {
        $this->name = $name;
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getName(): ?string
    {
        return $this->name;
    }

    public function setName(string $name): static
    {
        $this->name = $name;
        return $this;
    }

    public function isSelected(): bool
    {
        return $this->selected;
    }

    public function setSelected(bool $selected): self
    {
        $this->selected = $selected;
        return $this;
    }

    public function toggleSelected(): self
    {
        $this->selected = !$this->selected;
        return $this;
    }
}
