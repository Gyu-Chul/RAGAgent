#Github test
import pygame
import random

pygame.init()
clock = pygame.time.Clock()

# 창 크기 지정
background = pygame.display.set_mode((480, 360))
pygame.display.set_caption('Moving Game')

# 게임 물체 설정
player = pygame.image.load("Player.png")
player = pygame.transform.scale(player, (20, 50))
player_rect = player.get_rect()

player_x_p = background.get_size()[0] // 2 - 10
player_y_p = background.get_size()[1] - 50

to_x = 0 # 좌표 누적값 초기화
to_y = 0 # 좌표 누적값 초기화


# 장애물 돌 설정
stone_img = pygame.image.load("Stone.png").convert_alpha() # convert_alpha는 투명도와 관련, 누끼따서 차이 X
stone_img = pygame.transform.scale(stone_img, (40, 60))
stone_speed = 5
stone_frequency = 25
stones = [] # 돌의 "좌표"를 집어넣을거임!!

def draw_stones(stones):
    for x, y in stones:
        background.blit(stone_img, (x, y))

# 점수판
font = pygame.font.Font(None, 36)
score = 0

def display_score(score):
    score_text = font.render("Score: " + str(score), True, (255, 255, 255))
    background.blit(score_text, (10, 10))


### Main Game Loop ###
play = True
while play:
    df = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            play = False

        # 키보드 조작 설정
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                to_y = -10
            elif event.key == pygame.K_DOWN:
                to_y = 10
            elif event.key == pygame.K_RIGHT:
                to_x = 10
            elif event.key == pygame.K_LEFT:
                to_x = -10

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                to_y = 0
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                to_x = 0

    # 키보드 조작으로 변한 물체 위치 누적 좌표 적용
    player_x_p += to_x
    player_y_p += to_y

    # 누적 좌표로 물체 이동
    player_rect.topleft = (player_x_p, player_y_p)

    if random.randrange(stone_frequency) == 0: # 장애물 내려오는 속도 랜덤, frequency로 난이도 조절 가능
        stone_x_p = random.randint(0, background.get_size()[0] - stone_img.get_width())
        stone_y_p = -stone_img.get_height()
        stones.append((stone_x_p, stone_y_p)) # 좌표를 튜플로 리스트에 추가

    for i, (x, y) in enumerate(stones): # enumerate메서드 : 인덱스와 요소를 함께 추출하는 메서드
        y += stone_speed
        stones[i] = (x, y)
        if y > background.get_size()[1]:
            stones.pop(i) # pop메서드 : 리스트에서 특정 인덱스를 삭제하고 해당 요소를 반환한다!
                          # 해당 요소만 삭제한 채로 리스트는 return하고, 자기 자신이 그 해당 요소로 변신
                          # 지금은 변신한 값은 의미가 없으므로 그냥 삭제만 해주는 역할
            score += 1

    stone_speed += 0.01 # 점점 빨라져서 난이도 상승

    for x, y in stones: # 물체와 돌의 사각형이 겹치면 게임 끝
        stone_rect = pygame.Rect(x, y, stone_img.get_width(), stone_img.get_height())
        if player_rect.colliderect(stone_rect):
            print("{}점 입니다.".format(score))
            play = False

    background.fill((0, 0, 0))
    background.blit(player, (player_x_p, player_y_p))
    draw_stones(stones)
    display_score(score)
    pygame.display.update()

pygame.quit()