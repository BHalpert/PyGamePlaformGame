import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()  # initializes mixer
pygame.init()

# clock/timer
clock = pygame.time.Clock()
fps = 60

#  size of screen
screen_width = 1000
screen_height = 1000

#  creates screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

#define font
font = pygame.font.SysFont('Bauhaus 93', (screen_width//14))
font_score = pygame.font.SysFont('Bauhaus 93', (screen_width//30))
vfont = pygame.font.SysFont('Bauhaus 93', (screen_width//40))




scroll = [0, 0]

#  define game variables
tile_size = screen_width/20
game_over = 0 # -1 = lost, 0 = nothing, 1 = won
main_menu = True
level = 0
max_levels = 7
score = 0

#define colors
white = (255, 255, 255)
blue = (0, 0, 255)



#  load images
sun_img = pygame.image.load('Images/img/sun.png')
bg_img = pygame.image.load('Images/img/sky.png')
restart_img = pygame.image.load('Images/img/restart_btn.png')
start_img = pygame.image.load('Images/img/start_btn.png')
exit_img = pygame.image.load('Images/img/exit_btn.png')

# load sounds
pygame.mixer.music.load('Images/img/music.wav') # background music - always playing
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('Images/img/coin.wav')
coin_fx.set_volume(.5)
jump_fx = pygame.mixer.Sound('Images/img/jump.wav')
jump_fx.set_volume(.5)
game_over_fx = pygame.mixer.Sound('Images/img/game_over.wav')
game_over_fx.set_volume(.5)

#  draws a grid across the screen based on the tile size(for design and testing ONLY)
def draw_grid():
    for line in range(0,20):
        pygame.draw.line(screen, (255,255,255), (0, line * tile_size), (screen_width, line * tile_size))
        pygame.draw.line(screen, (255,255,255), (line * tile_size, 0), (line * tile_size, screen_height))

# draws introduction text to the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col) # turns text into picture
    screen.blit(img, (x,y))

# this function resets levels by emptying all sprite groups
def reset_level(Level):
    player.reset((tile_size*2), screen_height - (tile_size * 1.5))
    blob_group.empty()
    platform_group.empty()
    lava_group.empty()
    exit_group.empty()

    # load in level data and create world
    if path.exists(f'Levels/level{level}_data'):
        pickle_in = open(f'Levels/level{level}_data', 'rb')  # rb = read data(binary)
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False # tracks if mouse button is clicked

    # draws the buttons to the screen and returns whether the player has clicked the start button or not
    def draw(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos): # if the mouse is over the restart button
            # checks if button is clicked, [0] = left mouse button clicked
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        ## checks if left mouse button does not press button
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draws button
        screen.blit(self.image, self.rect)

        return action
class Player():
    def __init__(self, x, y):
        self.reset(x,y)

    # updates the position of the player based off of keystrokes and velocity variables
    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = (tile_size//2.5)

        ## if the game is not over get the key being pressed
        if game_over == 0:
            #  get keypresses
            key = pygame.key.get_pressed()
            # if the key being pressed is space of W or up and player is not already in the air, then set jumped to true
            if (key[pygame.K_SPACE] or key[pygame.K_w] or key[pygame.K_UP]) and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            # if space, w, or up is not being pressed then set jumped to false
            if (key[pygame.K_SPACE] or key[pygame.K_w] or key[pygame.K_UP]) == False:
                self.jumped = False
            # if left or a is being pressed, then set the dx to a negative tile size
            if key[pygame.K_LEFT] or key[pygame.K_a]:
                dx -= (tile_size//10)
                self.counter += 1
                self.direction = -1
            # if right or d is being pressed, then set the dx to a positive tile size
            if key[pygame.K_RIGHT] or key[pygame.K_d]:
                dx += (tile_size//10)
                self.counter += 1
                self.direction = 1
            # if left, right, a, or d is not being pressed then counter and index to 0
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False and key[pygame.K_a] == False and key[pygame.K_d] == False:
                self.counter = 0
                self.index = 0
                #  keeps player facing the correct direction when stopped
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #if the number of pixels the player is moving for is greater than the walk cooldown
            # then cycle through the animation iamges
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                # if index is greater than number of images then reset the index to 0
                if self.index >= len(self.images_right):
                    self.index = 0
                # if direction is one then cycle through right images
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                # if direction is -1 then cycle through left images
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # gravity
            self.vel_y += 1  # positive = falling, negative = jumping(moving up)
            # if velocity in y direction is greater than tile size divided by five, then set the velocity to its max
            if self.vel_y > (tile_size//5):
                self.vel_y = (tile_size//5)
            dy += self.vel_y

            # Checking for collisions(blocks/world)
            self.in_air = True
            # traverses through the number of tiles in tile list
            for tile in world.tile_list:
                # check for collision in x direction with tile 1
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # check for collision in y direction with tile 1
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if below the ground(jumping)
                    # if the velocity in y direction is less than 0 set vel y to 0, the dy is the change
                    # from the top of the player to bottom of the block (hitting head while jumping)
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # check if the player is above the ground(falling/gravity)
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # check for collision with enemies(game over)
            if pygame.sprite.spritecollide(self, blob_group, False): #  check player against blob groups
                game_over = -1
                game_over_fx.play()
            # check for collision with lava(game over)
            if pygame.sprite.spritecollide(self, lava_group, False): #  check player against lava groups
                game_over = -1
                game_over_fx.play()
            # check collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False): #  check player against lava groups
                game_over = 1

            #collision with moving platforms
            for platform in platform_group:
                #collision in x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #collision in y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    #check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    #move sideways with platform when changing from vertical to horizontal platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            # Update Player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('Game Over!', font, blue, (screen_width // 2) - (tile_size*2.75), screen_height // 2)
            if self.rect.y > tile_size:
                self.rect.y -= 5

        #  draw player onto screen(updating image)
        screen.blit(self.image, (self.rect.x - scroll[0] , self.rect.y - scroll[1]))
        #pygame.draw.rect(screen, (255,255,255), self.rect, 2) # player rect visualized

        return game_over

    def reset(self, x, y): # resets player
        # images and animation
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'Images/img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, ((tile_size//1.25), (tile_size//.625)))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('Images/img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        #  Coordinates and Movement
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []

        #  load images
        dirt_img = pygame.image.load('Images/img/dirt.png')
        grass_img = pygame.image.load('Images/img/grass.png')

        #  any place in the array with a 1 will be dirt
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                ##adds dirt to tile list
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                ##adds grass to tile list
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + tile_size/3)
                    blob_group.add(blob)
                if tile == 4: # horizontal platform
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5: # vertical platform
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size//2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1
    def draw(self):  #  draws the tile_list from above(World constructor)
        for tile in self.tile_list:
            screen.blit(tile[0] , (tile[1].x - scroll[0], tile[1].y - scroll[1]))

            #pygame.draw.rect(screen, (255,255,255), tile[1], 2) # tile rect visualized

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('Images/img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > tile_size:
            self.move_direction *= -1
            self.move_counter *= -1
        screen.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('Images/img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > tile_size:
            self.move_direction *= -1
            self.move_counter *= -1
        screen.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('Images/img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    def update(self):
        screen.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('Images/img/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
    def update(self):
        screen.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('Images/img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    def update(self):
        screen.blit(self.image, (self.rect.x - scroll[0], self.rect.y - scroll[1]))

#instances
player = Player(100, screen_height - 130)

#groups
blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()

# load in level data and create world
if path.exists(f'Levels/level{level}_data'):
    pickle_in = open(f'Levels/level{level}_data', 'rb') #  rb = read data(binary)
    world_data = pickle.load(pickle_in)
world = World(world_data)

#create buttons
restart_button = Button(screen_width // 2 - tile_size, screen_height // 2 - (tile_size-2), restart_img)
start_button = Button(screen_width // 2 - (tile_size*7), screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + (tile_size*3), screen_height // 2, exit_img)



#tutorial text
move1 = vfont.render('1. awd or arrow keys to move', True, white)
move2 = vfont.render('and space to jump', True, white)
danger = vfont.render('2. Dont touch the Lava or Slimes!', True, white)
coin = vfont.render('3. Get all the coins', True, white)
fun = vfont.render('4. Have fun! :)', True, white)

RM1 = move1.get_rect()
RM2 = move2.get_rect()
RD = danger.get_rect()
RC = coin.get_rect()
RF = fun.get_rect()

RM1.center = (1225 // 2, 850 // 2)
RM2.center = (1225 // 2, 950 // 2)
RD.center = (1225 // 2, 1050 // 2)
RC.center = (1225 // 2, 1150 // 2)
RF.center = (1225 // 2, 1250 // 2)




# main game loop
run = True
while run:

    clock.tick(fps)
    screen.blit(bg_img, (0, 0))  # sky background

    screen.blit(sun_img, (100, 100))


    if (level == 0) and main_menu == False:
        screen.blit(move1, RM1)
        screen.blit(move2, RM2)
        screen.blit(danger, RD)
        screen.blit(coin, RC)
        screen.blit(fun, RF)

    scroll[0] += (player.rect.x - scroll[0] - 500) / 15
    scroll[1] += (player.rect.y - scroll[1] - 620) / 15

    if main_menu == True:
        if exit_button.draw() == True: # if exit clicked
            run = False
        if start_button.draw() == True: # if start clicked
            main_menu = False
    else: #  main_menu == False
        world.draw() # adds world on top of background and sun

        if game_over == 0: # prevents the blobs from moving when game is over(game_over = -1)
            blob_group.update()  # updates ALL "blob" (enemies)(in blob group)
            platform_group.update()
            lava_group.update()
            coin_group.update()
            exit_group.update()
            #  update score - check if a coin has been collected
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text('Score: ' + str(score), font_score, white, tile_size - (tile_size//3), (tile_size//3))

        #blob_group.draw(screen)
        #platform_group.draw(screen)
        #lava_group.draw(screen)
        #coin_group.draw(screen)
        #exit_group.draw(screen)

        game_over = player.update(game_over)

        #draw_grid()

        # If player has died
        if game_over == -1:
            if restart_button.draw():
                world_data = []  # clearing current world data
                world = reset_level(level)  # deletes past level and creates new level then new world
                game_over = 0
                score = 0
        # if player has completed level
        if game_over == 1:
            #reset game and go to next level
            level += 1 # increase level by 1
            if level <= max_levels:
                #reset level
                world_data = [] # clearing current world data
                world = reset_level(level) # deletes past level and creates new level then new world
                game_over = 0
            else: # end of game
                draw_text('You Win!', font, blue, (screen_width // 2) - (tile_size*3), screen_height // 2)
                #restarts game
                if restart_button.draw():
                    level = 1
                    world_data = []  # clearing current world data
                    world = reset_level(level)  # deletes past level and creates new level then new world
                    game_over = 0
                    score = 0
    pygame.event.pump()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # quits game when close window button(X) is clicked
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # quits game when esc is pressed
                run = False
        elif event.type == VIDEORESIZE: # non fullscreen resizing
            screen.blit(pygame.transform.scale(bg_img, event.dict['size']), (0, 0))
        elif event.type == VIDEOEXPOSE: # handles window minimising/maximising
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(bg_img, screen.get_size()), (0, 0))
    pygame.display.update()

pygame.quit()