from settings import *
from generator import *
from collisions import *

"""
GLOBALS
"""

pygame.init()
settings = get_settings()
agent = None

display = pygame.display.set_mode((settings['display_width'], settings['display_height']))
pygame.display.set_caption('Snake')

action_space = [
    pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP})    ,
    pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}) ,
    pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN})  ,
    pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})  ,
]

default_font = settings['default_font']
title_font = settings['title_font']
score_font = settings['score_font']
SEG_DIM = settings['block_dim']

snake_head_img = None
snake_body_img = None
hor = None
ver = None
apple_img = None
star_img = None
wall_img = None
hole_img = None

head = None
tail = []
tail_rotations = []
facing = None
opposite = None
direction = None

apple = None
walls = []
tunnels = []
stars = []

total_score = 0
apples_ate = 0
tunnels_burrowed = 0
stars_collected = 0

state = pygame.surfarray.array3d(display)
action = None
reward = 0
next_state = None
done = False


"""
GAME SETUP
"""

def init_gfx():
    global snake_head_img, snake_body_img, hor, ver, apple_img, star_img, wall_img, hole_img
    snake_head_img = pygame.image.load("snake head.png")
    snake_head_img = pygame.transform.scale(snake_head_img, (SEG_DIM, SEG_DIM))

    snake_body_img = pygame.image.load("snake body.png")
    snake_body_img = pygame.transform.scale(snake_body_img, (SEG_DIM, SEG_DIM))
    hor = snake_body_img
    ver = pygame.transform.rotate(snake_body_img, 90)

    apple_img = pygame.image.load("apple.png")
    apple_img = pygame.transform.scale(apple_img, (SEG_DIM, SEG_DIM))

    star_img = pygame.image.load("star.png")
    star_img = pygame.transform.scale(star_img, (SEG_DIM, SEG_DIM))

    wall_img = pygame.image.load("wall.png")
    wall_img = pygame.transform.scale(wall_img, (SEG_DIM, SEG_DIM))

    hole_img = pygame.image.load("hole.png")
    hole_img = pygame.transform.scale(hole_img, (SEG_DIM, SEG_DIM))


def init_env():
    global facing, direction, opposite, apple
    facing = settings['starting_direction']
    direction = settings['starting_direction']
    opposite = Directions.get_opposite(facing)
    if settings['autostart']:
        direction = facing

    if settings['walls_on']:
        generate_walls(walls, tunnels, settings['display_width'], settings['display_width'], settings['display_height'], settings['wall_max_w'], settings['wall_max_h'])

    if settings['tunnels_on']:
        generate_tunnels(tunnels, walls, settings['tunnel_count'], settings['display_width'], settings['display_height'], SEG_DIM)

    collided = True
    while collided:
        apple = spawn_apple(settings['display_width'], settings['display_height'], SEG_DIM)
        collided = False
        if any_collisions(apple, walls, tunnels, tail, head, [i['star_rect'] for i in stars]):
            collided = True


def init_snake():
    global head, orient_points, tail, tail_rotations, direction, facing
    head = spawn_snake_seg(settings['starting_x'], settings['starting_y'], SEG_DIM, SEG_DIM)
    direction = settings['starting_direction']
    facing = settings['starting_direction']
    tail = []
    tail_rotations = []

    for _ in range(settings['starting_tail']):

        move_head(facing)
        tail.append(spawn_snake_seg())


def init_agents():
    global agent, state, next_state
    if settings['agent_hook']:
        if settings['agent_class']:

            if settings['agent_hook']:
                next_state = pygame.surfarray.array3d(display)
                if settings['state_info']['positions']:
                    next_state = [head, apple, settings['block_dim'], facing, tail]

                agent = settings['agent_class'](action_space, state)

def reset_scores():
    global total_score, apples_ate, tunnels_burrowed, stars_collected
    total_score = 0
    apples_ate = 0
    tunnels_burrowed = 0
    stars_collected = 0

def create_game():
    init_gfx()
    init_env()
    init_snake()
    init_agents()

def reset_game():
    init_gfx()
    init_env()
    init_snake()
    reset_scores()


"""
GAME MECHANICS
"""

def move_head(direction):
    global head, tail, head_x, head_y, facing, opposite, snake_head_img

    if direction == opposite:
        direction = facing

    if facing != direction:
        orientate_head(direction)

    if direction == Directions.UP:
        head.top -= SEG_DIM
        facing = Directions.UP
        opposite = Directions.get_opposite(direction)

    elif direction == Directions.RIGHT:
        head.left += SEG_DIM
        facing = Directions.RIGHT
        opposite = Directions.get_opposite(direction)

    elif direction == Directions.DOWN:
        head.top += SEG_DIM
        facing = Directions.DOWN
        opposite = Directions.get_opposite(direction)

    elif direction == Directions.LEFT:
        head.left -= SEG_DIM
        facing = Directions.LEFT
        opposite = Directions.get_opposite(direction)


def orientate_head(direction):
    global snake_head_img
    rotation = facing.value - direction.value
    snake_head_img = pygame.transform.rotate(snake_head_img, rotation)


def move_tail(prev_head, prev_direction):
    global tail, snake_body_img, tail_rotations
    if tail:
        new_tail = tail[1:]
        new_tail.append(prev_head)
        tail = new_tail

        new_rotations = tail_rotations[1:]
        if prev_direction == Directions.UP or prev_direction == Directions.DOWN:
            new_rot = ver
        else:
            new_rot = hor
        new_rotations.append(new_rot)
        tail_rotations = new_rotations


def grow(prev_head, last_direction):
    global head, tail, snake_body_img, tail_rotations
    new_segment = prev_head.copy()
    tail.append(new_segment)

    if last_direction == Directions.RIGHT or last_direction == Directions.LEFT:
        tail_rotations.append(hor)
    else:
        tail_rotations.append(ver)


def burrow_tunnel(tunnel_ind):
    global head, tunnels_burrowed
    emerging_tunnel = tunnel_ind
    while emerging_tunnel == tunnel_ind:
        emerging_tunnel = random.randrange(len(tunnels))

    tunnels_burrowed += 1
    head = tunnels[emerging_tunnel].copy()


def spawn_stars():
    global stars
    collided = True
    while collided:
        star = spawn_star(settings['star_prob'], settings['display_width'], settings['display_height'], SEG_DIM)
        if not star:
            break

        collided = False
        if any_collisions(star, head, tail, apple, walls, tunnels):
            collided = True
        stars.append({'star_rect': star, 'countdown': settings['star_countdown']})


def fade_stars():
    for star in stars:
        star['countdown'] -= 1
        if star['countdown'] == 0:
            stars.remove(star)


def get_text_object(text, color, large_font=False):
    if large_font:
        text_surf = title_font.render(text, True, color)
    else:
        text_surf = default_font.render(text, True, color)
    return text_surf, text_surf.get_rect()


"""
DISPLAY CONTROL
"""
def display_message(message, color, large_font=False, y_displace=0):
    text_surf, text_rect = get_text_object(message, color, large_font)
    text_rect.center = (settings['display_width'] / 2, settings['display_height'] / 2 + y_displace)
    display.blit(text_surf, text_rect)


def render_score():
    text = score_font.render("Score: " + str(total_score) +
                        "     Stars collected: " + str(stars_collected) +
                        "     Apples ate: " + str(apples_ate) +
                        "     Tunnels burrowed: " + str(tunnels_burrowed), True, pygame.Color('green'))
    display.blit(text, [0, 0])


def render_env():
    global head, tail, display, wall_img, walls, snake_head_img

    display.fill(settings['background_color'])
    display.blit(snake_head_img, head)

    display.blit(apple_img, apple)

    for rotation, seg in enumerate(tail):
        display.blit(tail_rotations[rotation], seg)

    for wall in walls:
        start_x = wall.left
        start_y = wall.top
        end_x = wall.left + wall.width
        end_y = wall.top + wall.height

        for i in range(start_x, end_x, SEG_DIM):
            for j in range(start_y, end_y, SEG_DIM):
                block = pygame.Rect(i, j, SEG_DIM, SEG_DIM)
                display.blit(wall_img, block)

    for tunnel in tunnels:
        display.blit(hole_img, tunnel)

    for star in stars:
        display.blit(star_img, star['star_rect'])

    render_score()
    pygame.display.update()


"""
GAME LOOP
"""
def intro_loop():
    global display, done
    intro = True

    while intro:
        display.fill(settings['background_color'])
        display_message("Welcome to Snake", pygame.Color('green'), large_font=True, y_displace=-150)
        display_message("- Use the arrow buttons to move", pygame.Color('blue'), y_displace=-60)
        display_message("- Eat the apples to grow!", pygame.Color('blue'), y_displace=-20)
        display_message("- Avoid walls, edges and yourself!", pygame.Color('blue'), y_displace=20)
        display_message("- Collect stars for points", pygame.Color('blue'), y_displace=60)
        display_message("- Burrow tunnels at your own risk!!!", pygame.Color('blue'), y_displace=100)
        display_message(" optional features: walls || tunnels || stars", pygame.Color('purple'), y_displace=170)
        display_message("- press ENTER to continue or SPACE to exit game", pygame.Color(random_color()), y_displace=200)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    done = False
                    return

                elif event.key == pygame.K_SPACE:
                    done = True
                    return


def game_loop():
    global done, apple, total_score, apples_ate, tunnels_burrowed, stars_collected, direction, facing, \
           state, action, reward, next_state

    game_over = False
    clock = pygame.time.Clock()
    render_env()
    render_score()

    if settings['agent_hook']:
        if settings['state_info']['pixels']:
            next_state = pygame.surfarray.array3d(display)
        elif settings['state_info']['positions']:
            next_state = [head, apple, settings['block_dim'], facing, tail]

    while not done:
        state = next_state

        if game_over:
            done = handle_game_over()

        if settings['agent_hook']:
            action = agent.act(state)
            pygame.event.post(action)

        update_action()
        prev_head = head.copy()
        prev_direction = direction
        move_head(direction)

        reward, game_over = handle_collisions(prev_head, prev_direction)

        spawn_stars()
        fade_stars()
        clock.tick(10)
        render_env()

        if settings['agent_hook']:
            if settings['state_info']['pixels']:
                next_state = pygame.surfarray.array3d(display)
            elif settings['state_info']['positions']:
                next_state = [head, apple, settings['block_dim'], facing, tail]

        if settings['agent_hook']:
            agent.store_memory(state, action, reward, next_state, game_over)
            agent.learn()


def update_action():
    global direction, done, action
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                direction = Directions.UP # key 273

            elif event.key == pygame.K_RIGHT:
                direction = Directions.RIGHT # key 275

            elif event.key == pygame.K_DOWN:
                direction = Directions.DOWN # key 274

            elif event.key == pygame.K_LEFT:
                direction = Directions.LEFT # key 276


def handle_game_over():
    game_over = True
    if settings['auto_reset']:
        reset_game()
        game_over = False
    while game_over:
        display.fill(settings['background_color'])
        display_message("GAME OVER", pygame.Color('red'), True, -60)
        display_message("Press ENTER to play again or SPACE to quit", pygame.Color('black'), False, 50)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    create_game()
                    game_over = False

                elif event.key == pygame.K_SPACE:
                    return True

"""
EVENT HANDLING
"""
def handle_collisions(prev_head, prev_direction):
    global total_score, stars_collected

    if has_self_collided(head, tail):
        return (settings['game_over_reward'], True)

    if has_wall_collided(head, walls):
        return (settings['game_over_reward'], True)

    if has_apple_collided(head, apple, total_score, settings['apple_reward'], apples_ate):
        handle_apple_collisions(prev_head, prev_direction)
        return (settings['apple_reward'], False)
    else:
        move_tail(prev_head, prev_direction)

    if settings['stars_on']:
        if has_star_collided(head, stars, total_score, settings['star_reward'], stars_collected):
            total_score += settings['star_reward']
            stars_collected += 1
            return (settings['star_reward'], False)

    if settings['tunnels_on']:
        handle_tunnel_collisions()

    if has_boundary_collided(head, settings['display_width'], settings['display_height'], settings['block_dim']):
        return (settings['game_over_reward'], True)
    return (2, False)


def handle_apple_collisions(prev_head, prev_direction):
    global total_score, apples_ate, apple
    total_score += settings['apple_reward']
    apples_ate += 1
    grow(prev_head, prev_direction)
    collided = True
    while collided:
        apple = spawn_apple(settings['display_width'], settings['display_height'], SEG_DIM)
        collided = False
        if any_collisions(apple, walls, tunnels, tail, head, [i['star_rect'] for i in stars]):
            collided = True


def handle_tunnel_collisions():
    global tunnels_burrowed
    tunnel_ind = has_tunnel_collided(head, tunnels)
    if tunnel_ind >= 0:
        burrow_tunnel(tunnel_ind)
        tunnels_burrowed += 1


if __name__ == "__main__":
    create_game()
    intro_loop()
    game_loop()
    pygame.quit()
    quit()
