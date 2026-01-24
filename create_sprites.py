#!/usr/bin/env python
"""
Sprite Generator - Creates placeholder sprites for the game
"""

from PIL import Image, ImageDraw
import os
import random

# Colors
COLORS = {
    'player': {
        'body': (0.2, 0.8, 1.0),  # Light blue
        'head': (1.0, 0.9, 0.7),  # Skin
        'outline': (0, 0, 0),      # Black
    },
    'father': {
        'body': (0.6, 0.4, 0.2),  # Brown
        'head': (1.0, 0.9, 0.7),  # Skin
        'outline': (0, 0, 0),
    },
    'mother': {
        'body': (1.0, 0.6, 0.8),  # Pink
        'head': (1.0, 0.9, 0.7),  # Skin
        'outline': (0, 0, 0),
    },
    'monkey': {
        'body': (0.6, 0.4, 0.2),  # Brown
        'head': (0.8, 0.6, 0.4),  # Lighter brown
        'outline': (0, 0, 0),
    },
}

def rgb_to_int(color):
    """Convert 0-1 float color to 0-255 int"""
    return tuple(int(c * 255) for c in color)

def create_player_idle():
    """Create player idle sprite (facing down) - карапуз (little child)"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = COLORS['player']
    colors = {k: rgb_to_int(v) for k, v in colors.items()}
    
    # Bigger head (childlike proportions)
    draw.ellipse([9, 0, 23, 16], fill=colors['head'], outline=colors['outline'], width=2)
    # Smaller body (child proportions)
    draw.rectangle([10, 16, 22, 26], fill=colors['body'], outline=colors['outline'], width=2)
    # Short legs
    draw.rectangle([11, 26, 14, 30], fill=colors['body'], outline=colors['outline'], width=1)
    draw.rectangle([18, 26, 21, 30], fill=colors['body'], outline=colors['outline'], width=1)
    # Small arms
    draw.ellipse([6, 18, 10, 22], fill=colors['head'], outline=colors['outline'], width=1)
    draw.ellipse([22, 18, 26, 22], fill=colors['head'], outline=colors['outline'], width=1)
    
    return img

def create_player_walk_direction(direction):
    """Create player walk sprite for direction - карапуз walking"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = COLORS['player']
    colors = {k: rgb_to_int(v) for k, v in colors.items()}
    
    # Bigger head (childlike)
    draw.ellipse([9, 0, 23, 16], fill=colors['head'], outline=colors['outline'], width=2)
    
    # Body and walking animation
    if direction == 'left':
        draw.rectangle([8, 16, 22, 26], fill=colors['body'], outline=colors['outline'], width=2)
        # Legs (walking - one up, one down)
        draw.rectangle([9, 26, 13, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.rectangle([19, 26, 23, 28], fill=colors['body'], outline=colors['outline'], width=1)
        # Arms swinging
        draw.ellipse([4, 18, 8, 22], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([24, 20, 28, 24], fill=colors['head'], outline=colors['outline'], width=1)
    elif direction == 'right':
        draw.rectangle([10, 16, 24, 26], fill=colors['body'], outline=colors['outline'], width=2)
        draw.rectangle([9, 26, 13, 28], fill=colors['body'], outline=colors['outline'], width=1)
        draw.rectangle([19, 26, 23, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.ellipse([4, 20, 8, 24], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([24, 18, 28, 22], fill=colors['head'], outline=colors['outline'], width=1)
    elif direction == 'up':
        draw.rectangle([10, 16, 22, 26], fill=colors['body'], outline=colors['outline'], width=2)
        draw.rectangle([11, 26, 14, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.rectangle([18, 24, 21, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.ellipse([6, 18, 10, 22], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([22, 18, 26, 22], fill=colors['head'], outline=colors['outline'], width=1)
    else:  # down
        draw.rectangle([10, 16, 22, 26], fill=colors['body'], outline=colors['outline'], width=2)
        draw.rectangle([11, 24, 14, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.rectangle([18, 26, 21, 30], fill=colors['body'], outline=colors['outline'], width=1)
        draw.ellipse([6, 18, 10, 22], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([22, 18, 26, 22], fill=colors['head'], outline=colors['outline'], width=1)
    
    return img

def create_father():
    """Create father static sprite"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = COLORS['father']
    colors = {k: rgb_to_int(v) for k, v in colors.items()}
    
    # Head
    draw.ellipse([8, 0, 24, 16], fill=colors['head'], outline=colors['outline'], width=2)
    # Body (bigger)
    draw.rectangle([6, 16, 26, 30], fill=colors['body'], outline=colors['outline'], width=2)
    # Beard
    draw.ellipse([10, 8, 22, 16], fill=(100, 100, 100, 255), outline=colors['outline'], width=1)
    
    return img

def create_mother_cooking_frame(frame=0):
    """Create mother cooking animation sprite (multiple frames)
    
    Args:
        frame: 0 or 1 for animation frames
    """
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = COLORS['mother']
    colors = {k: rgb_to_int(v) for k, v in colors.items()}
    
    # Head
    draw.ellipse([8, 0, 24, 16], fill=colors['head'], outline=colors['outline'], width=2)
    # Body (apron for cooking)
    draw.rectangle([6, 16, 26, 30], fill=colors['body'], outline=colors['outline'], width=2)
    draw.rectangle([8, 18, 24, 26], fill=(255, 255, 255, 255), outline=colors['outline'], width=1)  # Apron
    # Hair
    draw.ellipse([6, 2, 26, 12], fill=(200, 150, 100, 255), outline=colors['outline'], width=1)
    
    # Cooking animation - arms move
    if frame == 0:
        # Frame 1: arms up (stirring)
        draw.ellipse([2, 12, 8, 20], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([24, 12, 30, 20], fill=colors['head'], outline=colors['outline'], width=1)
        # Spoon in right hand
        draw.line([26, 14, 28, 18], fill=(139, 90, 43, 255), width=2)
    else:
        # Frame 2: arms down (preparing)
        draw.ellipse([0, 18, 8, 26], fill=colors['head'], outline=colors['outline'], width=1)
        draw.ellipse([24, 18, 32, 26], fill=colors['head'], outline=colors['outline'], width=1)
    
    return img

def create_monkey(age):
    """Create monkey sprite for specific age"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = COLORS['monkey']
    colors = {k: rgb_to_int(v) for k, v in colors.items()}
    
    # Size based on age (1-4)
    size_factor = 0.5 + (age * 0.15)
    width = int(16 * size_factor)
    height = int(20 * size_factor)
    x_offset = (32 - width) // 2
    y_offset = 32 - height - 2
    
    # Head
    head_size = int(12 * size_factor)
    head_x = x_offset + (width - head_size) // 2
    draw.ellipse([head_x, y_offset - head_size + 4, head_x + head_size, y_offset + 4], 
                 fill=colors['head'], outline=colors['outline'], width=2)
    # Body
    draw.ellipse([x_offset, y_offset, x_offset + width, y_offset + height], 
                 fill=colors['body'], outline=colors['outline'], width=2)
    # Ears
    ear_size = int(4 * size_factor)
    draw.ellipse([head_x - 2, y_offset - head_size + 6, head_x + ear_size, y_offset - head_size + 6 + ear_size], 
                 fill=colors['head'], outline=colors['outline'], width=1)
    draw.ellipse([head_x + head_size - ear_size, y_offset - head_size + 6, head_x + head_size + 2, y_offset - head_size + 6 + ear_size], 
                 fill=colors['head'], outline=colors['outline'], width=1)
    
    return img

def create_tile_floor():
    """Create floor tile"""
    img = Image.new('RGBA', (32, 32), rgb_to_int((0.4, 0.3, 0.2)))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 32, 32], outline=(0, 0, 0), width=1)
    return img

def create_tile_wall():
    """Create wall tile"""
    img = Image.new('RGBA', (32, 32), rgb_to_int((0.5, 0.4, 0.3)))
    draw = ImageDraw.Draw(img)
    # Brick pattern
    for y in range(0, 32, 8):
        for x in range(0, 32, 16):
            offset = 8 if (y // 8) % 2 == 1 else 0
            draw.rectangle([x + offset, y, x + offset + 16, y + 8], outline=(0, 0, 0), width=1)
    return img

def create_cave_floor():
    """Create cave floor tile"""
    import random
    img = Image.new('RGBA', (32, 32), rgb_to_int((0.3, 0.2, 0.15)))  # Brown cave color
    draw = ImageDraw.Draw(img)
    # Rock pattern with some texture
    for y in range(0, 32, 4):
        for x in range(0, 32, 4):
            offset = random.randint(-3, 3)
            color_var = random.randint(-15, 15)
            color = (max(0, min(255, 77 + color_var)), max(0, min(255, 51 + color_var)), max(0, min(255, 38 + color_var)))
            draw.rectangle([x + offset, y, x + 4 + offset, y + 4], fill=color, outline=(0, 0, 0), width=1)
    # Add some pebbles/stones
    for _ in range(5):
        x = random.randint(2, 30)
        y = random.randint(2, 30)
        size = random.randint(1, 2)
        draw.ellipse([x, y, x + size, y + size], fill=(60, 40, 30, 255))
    return img

def create_cave_wall():
    """Create cave wall tile - darker with distinct vertical stone pattern"""
    import random
    img = Image.new('RGBA', (32, 32), rgb_to_int((0.15, 0.12, 0.08)))  # Much darker brown
    draw = ImageDraw.Draw(img)
    # Vertical stone blocks pattern to clearly distinguish from floor
    block_width = 4
    for x in range(0, 32, block_width):
        block_base_color = random.randint(30, 50)  # Dark gray-brown base
        for y in range(0, 32, 8):
            block_height = random.randint(6, 10)
            # Each stone block
            block_color = (max(0, block_base_color + random.randint(-5, 5)), 
                          max(0, block_base_color + random.randint(-5, 5) - 5), 
                          max(0, block_base_color + random.randint(-5, 5) - 10))
            draw.rectangle([x, y, min(32, x + block_width), min(32, y + block_height)], 
                          fill=block_color, outline=(0, 0, 0), width=1)
            # Add mortar lines between blocks
            if y > 0:
                draw.line([x, y, min(32, x + block_width), y], fill=(10, 8, 5, 255), width=1)
        # Vertical separator lines between columns
        if x > 0:
            draw.line([x, 0, x, 32], fill=(10, 8, 5, 255), width=1)
    # Add some darker vertical shadows
    for x in range(2, 32, 8):
        draw.line([x, 0, x, 32], fill=(8, 6, 4, 150), width=1)
    return img

def create_cave_exit():
    """Create cave exit (to outside/minigame)"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Dark cave opening
    draw.ellipse([4, 8, 28, 28], fill=(20, 20, 30, 255), outline=(10, 10, 15, 255), width=2)
    # Light coming from outside
    draw.ellipse([8, 12, 24, 24], fill=(100, 120, 150, 200), outline=(150, 170, 200, 255), width=1)
    # Some cave edges
    draw.arc([6, 10, 26, 26], start=0, end=180, fill=(30, 25, 20, 255), width=3)
    # Ground
    draw.rectangle([0, 28, 32, 32], fill=(40, 30, 20, 255), outline=(0, 0, 0), width=1)
    return img

def create_cave_door():
    """Create cave door/transition to another room (kitchen)"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Door frame (wooden)
    draw.rectangle([6, 4, 26, 30], fill=rgb_to_int((0.6, 0.4, 0.2)), outline=(0, 0, 0), width=2)
    # Door (wood planks)
    for y in range(8, 28, 4):
        draw.rectangle([8, y, 24, y + 3], fill=rgb_to_int((0.5, 0.35, 0.2)), outline=(0, 0, 0), width=1)
    # Door handle
    draw.ellipse([20, 16, 24, 18], fill=(150, 150, 150, 255), outline=(0, 0, 0), width=1)
    # Some details (wood grain)
    for y in range(10, 26, 6):
        draw.line([10, y, 22, y], fill=(70, 50, 30, 255), width=1)
    return img

def create_kitchen_decoration(name):
    """Create kitchen decoration - electronic appliances"""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if name == 'stove':
        # Stove (electric stove)
        draw.rectangle([2, 4, 30, 30], fill=(80, 80, 80, 255), outline=(0, 0, 0), width=2)
        # Stovetop
        draw.rectangle([4, 6, 28, 14], fill=(60, 60, 60, 255), outline=(0, 0, 0), width=1)
        # Burners
        draw.ellipse([8, 8, 16, 16], fill=(200, 150, 0, 255), outline=(0, 0, 0), width=1)  # On
        draw.ellipse([18, 8, 26, 16], fill=(100, 100, 100, 255), outline=(0, 0, 0), width=1)  # Off
        # Oven door
        draw.rectangle([8, 16, 24, 28], fill=(40, 40, 40, 255), outline=(0, 0, 0), width=1)
        draw.rectangle([14, 20, 18, 24], fill=(100, 100, 100, 255), outline=(0, 0, 0), width=1)  # Window
    elif name == 'counter':
        # Kitchen counter
        draw.rectangle([0, 20, 32, 32], fill=(139, 90, 43, 255), outline=(0, 0, 0), width=2)
        # Countertop edge
        draw.rectangle([0, 18, 32, 20], fill=(160, 120, 80, 255), outline=(0, 0, 0), width=1)
    elif name == 'sink':
        # Sink
        draw.rectangle([6, 14, 26, 30], fill=(180, 180, 180, 255), outline=(0, 0, 0), width=2)
        # Sink bowl
        draw.ellipse([10, 18, 22, 28], fill=(150, 200, 255, 255), outline=(0, 0, 0), width=1)
        # Faucet
        draw.rectangle([14, 8, 18, 18], fill=(200, 200, 200, 255), outline=(0, 0, 0), width=1)
    elif name == 'fridge':
        # Refrigerator
        draw.rectangle([2, 0, 30, 32], fill=(220, 220, 240, 255), outline=(0, 0, 0), width=2)
        # Door lines
        draw.line([16, 0, 16, 32], fill=(100, 100, 100, 255), width=1)
        # Handle
        draw.rectangle([18, 12, 22, 20], fill=(100, 100, 100, 255), outline=(0, 0, 0), width=1)
        # Freezer section
        draw.rectangle([4, 2, 14, 10], fill=(200, 200, 220, 255), outline=(0, 0, 0), width=1)
    elif name == 'microwave':
        # Microwave oven
        draw.rectangle([4, 8, 28, 26], fill=(120, 120, 120, 255), outline=(0, 0, 0), width=2)
        # Door
        draw.rectangle([6, 10, 26, 24], fill=(60, 60, 60, 255), outline=(0, 0, 0), width=1)
        # Window
        draw.rectangle([10, 12, 22, 20], fill=(200, 200, 200, 180), outline=(100, 100, 100, 255), width=1)
        # Control panel
        draw.rectangle([10, 6, 22, 10], fill=(80, 80, 80, 255), outline=(0, 0, 0), width=1)
        # Buttons
        draw.ellipse([12, 7, 14, 9], fill=(200, 0, 0, 255), outline=(0, 0, 0), width=1)
        draw.ellipse([18, 7, 20, 9], fill=(0, 200, 0, 255), outline=(0, 0, 0), width=1)
    
    return img

def main():
    """Generate all sprites"""
    base_dir = "assets/sprites"
    
    # Character sprites
    os.makedirs(f"{base_dir}/player", exist_ok=True)
    os.makedirs(f"{base_dir}/player/idle", exist_ok=True)
    os.makedirs(f"{base_dir}/player/walk", exist_ok=True)
    
    create_player_idle().save(f"{base_dir}/player/idle/down.png")
    for direction in ['up', 'down', 'left', 'right']:
        create_player_walk_direction(direction).save(f"{base_dir}/player/walk/{direction}.png")
    
    # NPC sprites
    os.makedirs(f"{base_dir}/npc", exist_ok=True)
    os.makedirs(f"{base_dir}/npc/portraits", exist_ok=True)
    
    create_father().save(f"{base_dir}/npc/father.png")
    create_father().resize((64, 64), Image.NEAREST).save(f"{base_dir}/npc/portraits/father.png")
    
    # Mother cooking sprites (frame 0 for default)
    create_mother_cooking_frame(0).save(f"{base_dir}/npc/mother.png")
    create_mother_cooking_frame(0).resize((64, 64), Image.NEAREST).save(f"{base_dir}/npc/portraits/mother.png")
    # Cooking animation frame 1
    create_mother_cooking_frame(1).save(f"{base_dir}/npc/mother_cook1.png")
    
    # Monkey sprites
    os.makedirs(f"{base_dir}/monkey", exist_ok=True)
    os.makedirs(f"{base_dir}/monkey/run", exist_ok=True)
    os.makedirs(f"{base_dir}/monkey/throw", exist_ok=True)
    
    for age in range(1, 5):
        create_monkey(age).save(f"{base_dir}/monkey/age{age}.png")
        # Run animation (just offset slightly)
        run_sprite = create_monkey(age)
        draw = ImageDraw.Draw(run_sprite)
        # Add motion lines
        draw.line([0, 28, 8, 28], fill=(200, 200, 200, 150), width=2)
        run_sprite.save(f"{base_dir}/monkey/run/age{age}.png")
        # Throw animation
        throw_sprite = create_monkey(age)
        draw = ImageDraw.Draw(throw_sprite)
        # Add throwing arm
        draw.ellipse([20, 8, 30, 18], fill=(139, 90, 43), outline=(0, 0, 0), width=1)
        throw_sprite.save(f"{base_dir}/monkey/throw/age{age}.png")
    
    # Environment tiles
    os.makedirs(f"{base_dir}/tiles", exist_ok=True)
    create_tile_floor().save(f"{base_dir}/tiles/floor.png")
    create_tile_wall().save(f"{base_dir}/tiles/wall.png")
    
    # Cave tiles and decorations
    os.makedirs(f"{base_dir}/cave", exist_ok=True)
    create_cave_floor().save(f"{base_dir}/cave/cave_floor.png")
    print(f"Created: {base_dir}/cave/cave_floor.png")
    
    create_cave_wall().save(f"{base_dir}/cave/cave_wall.png")
    print(f"Created: {base_dir}/cave/cave_wall.png")
    
    create_cave_exit().save(f"{base_dir}/cave/cave_exit.png")
    print(f"Created: {base_dir}/cave/cave_exit.png")
    
    create_cave_door().save(f"{base_dir}/cave/cave_door.png")
    print(f"Created: {base_dir}/cave/cave_door.png")
    
    # Kitchen decorations (electronic appliances)
    os.makedirs(f"{base_dir}/kitchen", exist_ok=True)
    create_kitchen_decoration('stove').save(f"{base_dir}/kitchen/stove.png")
    create_kitchen_decoration('counter').save(f"{base_dir}/kitchen/counter.png")
    create_kitchen_decoration('sink').save(f"{base_dir}/kitchen/sink.png")
    create_kitchen_decoration('fridge').save(f"{base_dir}/kitchen/fridge.png")
    create_kitchen_decoration('microwave').save(f"{base_dir}/kitchen/microwave.png")
    
    # Minigame elements
    os.makedirs(f"{base_dir}/minigame", exist_ok=True)
    # Poop projectile
    poop = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(poop)
    draw.ellipse([2, 2, 14, 14], fill=(101, 67, 33), outline=(0, 0, 0), width=1)
    poop.save(f"{base_dir}/minigame/poop.png")
    
    print("All sprites generated successfully!")
    print(f"Sprites saved to {base_dir}/")

if __name__ == "__main__":
    main()
