import pygame
import os
import sys
import argparse
import pymorphy2 as pm


morph = pm.MorphAnalyzer()
step_word = morph.parse('ход')[0]

parser = argparse.ArgumentParser()
parser.add_argument('map', type=str, nargs='?', default='map.map')
args = parser.parse_args()
map_file = args.map


def load_image(name, color_key=None):
    fullname = os.path.join('img', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key is -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


pygame.init()
pygame.mixer.init()
sound_step = pygame.mixer.Sound('sound/step.wav')
sound_push = pygame.mixer.Sound('sound/push1.wav')
sound_hand_clap = pygame.mixer.Sound('sound/hand_clap.wav')
screen_size = (800, 700)
screen = pygame.display.set_mode(screen_size)
FPS = 50


tile_images = {
    'wall': load_image('grass.png'),
    'empty': load_image('empty.png'),
    'place': load_image('place.png')
}
player_image = load_image('mar.png')
box_image = load_image('box.png')

tile_width = tile_height = 50


class SpriteGroup(pygame.sprite.Group):

    def __init__(self):
        super().__init__()

    def get_event(self, event):
        for sprite in self:
            sprite.get_event(event)


class Sprite(pygame.sprite.Sprite):

    def __init__(self, group):
        super().__init__(group)
        self.rect = None

    def get_event(self, event):
        pass


class Tile(Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(sprite_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.mask = pygame.mask.from_surface(self.image)


class Player(Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(hero_group)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 15, tile_height * pos_y + 5)
        self.pos = (pos_x, pos_y)
        self.mask = pygame.mask.from_surface(self.image)

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0] + 15, tile_height * self.pos[1] + 5)


class Box(Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(box_group)
        self.image = box_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)
        self.mask = pygame.mask.from_surface(self.image)

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0], tile_height * self.pos[1])


player = None
running = True
clock = pygame.time.Clock()
sprite_group = SpriteGroup()
hero_group = SpriteGroup()
box_group = SpriteGroup()


def terminate():
    pygame.quit()
    sys.exit


def show_screen(text, fon_file):

    fon = pygame.transform.scale(load_image(fon_file), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in text:
        string_rendered = font.render(line, True, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


def load_level(level_map):
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '#')), level_map))


def load_levels(filename):
    filename = 'data/' + filename
    with open(filename, 'r') as mapFile:
        lines = [line.strip() for line in mapFile]
    levels = []
    level = []
    #  pprint(lines)
    for i in range(len(lines)):
        #  pprint(lines[i])
        if lines[i].strip() != '':
            level += [lines[i]]
        else:
            #  pprint(level)
            levels += [level]
            level = []
    return levels


def generate_level(level):
    new_player, x, y = None, None, None
    sprite_group.empty()
    box_group.empty()
    hero_group.empty()
    box_dict = {}
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == 'P':
                Tile('place', x, y)
            elif level[y][x] == 'B':
                Tile('empty', x, y)
                box_dict[Box(x, y)] = x, y
                level[y][x] = '.'
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
                level[y][x] = '.'
    #  print(box_dict)
    return new_player, box_dict, x, y


def check_win(level_map, box_dict):
    return all([level_map[y][x] == 'P' for x, y in box_dict.values()])


def move(hero, movement):
    x, y = hero.pos
    free_tile = ['.', 'P']

    if movement == 'up':
        if y > 0 and level_map[y - 1][x] in free_tile and (x, y - 1) not in box_dict.values():
            hero.move(x, y - 1)
            sound_step.play()
        elif y > 0 and level_map[y - 1][x] in free_tile and (x, y - 1) in box_dict.values():
            if level_map[y - 2][x] in free_tile and (x, y - 2) not in box_dict.values():
                for box, pos in box_dict.items():
                    if pos == (x, y - 1):
                        box.move(x, y - 2)
                        box_dict[box] = x, y - 2
                        sound_push.play()
                        break
                hero.move(x, y - 1)

    elif movement == 'down':
        if y < max_y - 1 and level_map[y + 1][x] in free_tile and (x, y + 1) not in box_dict.values():
            hero.move(x, y + 1)
            sound_step.play()
        elif y < max_y - 1 and level_map[y + 1][x] in free_tile and (x, y + 1) in box_dict.values():
            if level_map[y + 2][x] in free_tile and (x, y + 2) not in box_dict.values():
                for box, pos in box_dict.items():
                    if pos == (x, y + 1):
                        box.move(x, y + 2)
                        box_dict[box] = x, y + 2
                        sound_push.play()
                        break
                hero.move(x, y + 1)

    elif movement == 'left':
        if x > 0 and level_map[y][x - 1] in free_tile and (x - 1, y) not in box_dict.values():
            hero.move(x - 1, y)
            sound_step.play()
        elif x > 0 and level_map[y][x - 1] in free_tile and (x - 1, y) in box_dict.values():
            if level_map[y][x - 2] in free_tile and (x - 2, y) not in box_dict.values():
                for box, pos in box_dict.items():
                    if pos == (x - 1, y):
                        box.move(x - 2, y)
                        box_dict[box] = x - 2, y
                        sound_push.play()
                        break
                hero.move(x - 1, y)

    elif movement == 'right':
        if x < max_x - 1 and level_map[y][x + 1] in free_tile and (x + 1, y) not in box_dict.values():
            hero.move(x + 1, y)
            sound_step.play()
        elif x < max_x - 1 and (x + 1, y) and (x + 1, y) in box_dict.values():
            if level_map[y][x + 2] in free_tile and (x + 2, y) not in box_dict.values():
                for box, pos in box_dict.items():
                    if pos == (x + 1, y):
                        box.move(x + 2, y)
                        box_dict[box] = x + 2, y
                        sound_push.play()
                        break
                hero.move(x + 1, y)


intro_text = ['Sokoban', 'Игроку необходимо расставить ящики по обозначенным местам лабиринта.',
              'одновременно можно двигать только один ящик, толкая его вперёд.',
              'r - сброс текущего уровня',
              'n - следующий уровень']

show_screen(intro_text, 'fon.jpg')
levels = load_levels(map_file)
for level in range(len(levels)):
    sound_hand_clap.stop()
    steps = 0
    level_map = load_level(levels[level])
    hero, box_dict, max_x, max_y = generate_level(level_map)
    win = False
    pygame.display.set_caption(f'Sokoban уровень {level + 1},  {steps} {step_word.make_agree_with_number(steps).word}')
    while running and not win:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    move(hero, 'up')
                    steps += 1
                elif event.key == pygame.K_DOWN:
                    move(hero, 'down')
                    steps += 1
                elif event.key == pygame.K_LEFT:
                    move(hero, 'left')
                    steps += 1
                elif event.key == pygame.K_RIGHT:
                    move(hero, 'right')
                    steps += 1
                elif event.key == pygame.K_r:
                    hero, box_dict, max_x, max_y = generate_level(load_level(levels[level]))
                elif event.key == pygame.K_n:
                    win = True
                pm_steps = f'{steps} {step_word.make_agree_with_number(steps).word}'
                if check_win(level_map, box_dict):
                    sound_hand_clap.play()
                    win_text = [
                        'Ура !',
                        f'Уровень {level + 1} пройден за {pm_steps}!',
                        'для продолжения нажмите любую клавишу',
                    ]
                    pygame.display.set_caption(f'Sokoban уровень {level + 1}, {pm_steps}')
                    show_screen(win_text, 'fon.jpg')
                    win = True
                pygame.display.set_caption(f'Sokoban уровень {level + 1}, {pm_steps}')

        screen.fill(pygame.Color('black'))
        sprite_group.draw(screen)
        box_group.draw(screen)
        hero_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()

pygame.quit()
