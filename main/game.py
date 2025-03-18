import pygame
import random
import time
import math

# Initialize Pygame
pygame.init()

# Screen Dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎨 Shape Drawing Art Game")

# Colors
BACKGROUND = (240, 240, 240)
TEXT_COLOR = (0, 0, 0)
SHAPE_COLORS = {
    "circle": (255, 100, 100),
    "square": (100, 255, 100),
    "triangle": (100, 100, 255),
    "star": (255, 215, 0),
}

# Load Sound Effects
pygame.mixer.init()
success_sound = pygame.mixer.Sound("success.wav")
fail_sound = pygame.mixer.Sound("fail.wav")
pygame.mixer.music.load("background.mp3")  # Background music

# Font
font = pygame.font.Font(None, 36)

# Shape-Object Mapping
shape_object_map = {
    "circle": ("Soccer Ball", "⚽"),
    "square": ("TV", "📺"),
    "triangle": ("Pizza Slice", "🍕"),
    "star": ("Starfish", "🌟"),
}

# Shape Detection Function
def detect_shape(points):
    """Detect drawn shape based on pattern."""
    if len(points) < 10:
        return None

    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    width, height = max_x - min_x, max_y - min_y
    aspect_ratio = width / max(height, 1)

    center_x, center_y = (min_x + max_x) // 2, (min_y + max_y) // 2
    distances = [math.dist((center_x, center_y), p) for p in points]
    avg_distance = sum(distances) / len(distances)
    variation = sum((d - avg_distance) ** 2 for d in distances) / len(distances)

    if variation < 800:
        return "circle"
    if 0.85 < aspect_ratio < 1.15:
        return "square"
    if len(points) < 50:
        return "triangle"
    if len(points) > 100:
        return "star"
    return None

# 🎮 Main Game Function
def play_game():
    """Game loop with replay functionality."""
    pygame.mixer.music.set_volume(0.3)  # 🔊 Reduce music volume (30%)
    pygame.mixer.music.play(-1)  # Play background music on loop

    while True:
        drawing, drawn_points = False, []
        target_shape = random.choice(list(shape_object_map.keys()))
        game_time, start_time = 30, time.time()
        game_active = True

        while game_active:
            screen.fill(BACKGROUND)

            # Handle Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    drawing, drawn_points = True, []  
                elif event.type == pygame.MOUSEBUTTONUP:
                    drawing = False
                elif event.type == pygame.MOUSEMOTION and drawing:
                    drawn_points.append(event.pos)

            # Draw Shape Path
            for point in drawn_points:
                pygame.draw.circle(screen, SHAPE_COLORS[target_shape], point, 3)

            # Display Timer & Instructions
            elapsed_time = int(time.time() - start_time)
            remaining_time = max(0, game_time - elapsed_time)

            timer_text = font.render(f"Time Left: {remaining_time}s", True, TEXT_COLOR)
            shape_text = font.render(f"Draw a {target_shape.upper()}!", True, TEXT_COLOR)
            screen.blit(timer_text, (10, 10))
            screen.blit(shape_text, (WIDTH // 2 - 100, 50))

            pygame.display.flip()

            # Time's Up - Check Shape
            if remaining_time <= 0:
                recognized_shape = detect_shape(drawn_points)
                screen.fill((0, 0, 0))  # Results screen

                if recognized_shape == target_shape:
                    object_name, object_emoji = shape_object_map[target_shape]
                    success_sound.play()
                    result_text = font.render(f"✅ You drew a {object_name}!", True, (255, 255, 255))
                    emoji_text = font.render(object_emoji, True, (255, 255, 255))
                else:
                    fail_sound.play()
                    result_text = font.render(f"❌ That wasn't a {target_shape}.", True, (255, 255, 255))
                    emoji_text = font.render("😞", True, (255, 255, 255))

                screen.blit(result_text, (WIDTH // 4, HEIGHT // 2 - 50))
                screen.blit(emoji_text, (WIDTH // 2, HEIGHT // 2 + 20))
                pygame.display.flip()
                pygame.time.delay(3000)
                game_active = False

        # Replay or Quit
        screen.fill(BACKGROUND)
        replay_text = font.render("Press 'R' to Replay or 'Q' to Quit", True, TEXT_COLOR)
        screen.blit(replay_text, (WIDTH // 3, HEIGHT // 2))
        pygame.display.flip()

        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  
                        waiting_for_input = False  # Restart game
                    elif event.key == pygame.K_q:  
                        pygame.quit()
                        return

# 🚀 Run the Game
play_game()
