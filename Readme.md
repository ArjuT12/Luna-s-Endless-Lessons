luna_game/
│
├── main.py
├── config.py
│
├── assets/
│   ├── images/
│   │   ├── player/
│   │   ├── enemies/
│   │   ├── items/
│   │   ├── backgrounds/
│   │   ├── ui/
│   │   └── effects/
│   │
│   ├── sounds/
│   │   ├── bgm/
│   │   ├── sfx/
│   │   └── voices/
│   │
│   └── fonts/
│
├── core/
│   ├── game.py          # Game loop and main orchestration
│   ├── scene.py         # Base Scene class & scene management
│   ├── background.py    # Background and weather system
│   ├── camera.py        # Camera logic
│   ├── ui.py            # UI manager & HUD
│   └── emotion.py       # Emotion system
│
├── entities/
│   ├── player.py
│   ├── enemy.py
│   ├── item.py
│   ├── companion.py
│   └── ability.py
│
├── levels/
│   ├── level_data.py
│   ├── level_1.json     # If using tilemap data or Tiled exports
│   ├── level_2.json
│   └── ...
│
├── utils/
│   ├── helpers.py       # Utility functions (e.g., collision checks)
│   ├── particles.py     # Particle effects
│   └── constants.py     # Global constants and colors
│
└── README.md
