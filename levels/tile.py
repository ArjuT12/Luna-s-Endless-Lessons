import pygame
from config import TILE_SIZE


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE)) 
        # Use a neutral gray color instead of config color
        self.image.fill((128, 128, 128))
        self.rect = self.image.get_rect(topleft=pos)