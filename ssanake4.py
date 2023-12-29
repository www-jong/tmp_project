import pygame
import sys
import random
import socket
from _thread import *
import datetime
import time

HOST = 'xxx.xxx.xxx.xxx' ## server에 출력되는 ip를 입력해주세요 ##
PORT = 9875

#데이터수신부
'''
def recv_data(client_socket):
    while True:
        data = client_socket.recv(1024)
        print("recive : ", repr(data.decode()))
'''
rankings_data=[]

global client_socket
connection_status = "idle"
def try_connect_to_server():
    global connection_status,client_socket
    try:
        connection_status = "connecting"
        update_ui_with_connection_status()  # UI 업데이트 함수 호출
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(3)  # 타임아웃 3초 설정
        client_socket.connect((HOST, PORT))
        start_new_thread(recv_data, (client_socket,))
        connection_status = "idle"
        print('연결성공')
        return True
    except socket.timeout:
        print("연결 시도 시간 초과")
        connection_status = "failed"
        update_ui_with_connection_status()  # UI 업데이트 함수 호출
        return False
    except Exception as e:
        print("연결 실패:", e)
        connection_status = "failed"
        update_ui_with_connection_status()  # UI 업데이트 함수 호출
        return False
    
# UI 업데이트 함수
def update_ui_with_connection_status():
    global connection_status
    font = pygame.font.SysFont("malgungothic", 15)
    if connection_status == "connecting":
        text1 = font.render("연결실패", True, (255, 255, 255))  # 공백으로 메시지 숨김
        screen.blit(text1, (160, 260))
        # "연결중..." 메시지 표시
        text1 = font.render("연결중...", True, (0, 0, 0))
        screen.blit(text1, (160, 260))
    elif connection_status == "failed":
        text1 = font.render("연결중...", True, (255, 255, 255))
        screen.blit(text1, (160, 260))
        # "연결 실패" 메시지 숨김
        text1 = font.render("연결실패", True, (0, 0, 0))  # 공백으로 메시지 숨김
        screen.blit(text1, (160, 260))
    pygame.display.flip()


def recv_data(client_socket):
    global rankings_data  # 전역 변수로 랭킹 데이터를 저장
    while True:
        try:
            data = client_socket.recv(1024)
            if data:
                decoded_data = data.decode()
                # 예를 들어, 서버 응답의 시작 부분에 'rankings:'이 포함되어 있다면
                if decoded_data.startswith('ranking'):
                    rankings_data = decoded_data[len('ranking'):]
        except socket.timeout:
            # 타임아웃 발생 시 처리
            print("서버로부터 응답 대기 중 타임아웃 발생")
            continue  # 루프를 계속 유지
        except Exception as e:
            print("recv_data 함수에서 예외 발생:", e)
            break  # 루프 종료 및 함수 종료

#랭킹 가져오기

def get_rankings_from_server():
    global rankings_data,client_socket  # 전역 변수 사용
    rankings_list = []
    try:
        print('서버에 요청 전송')
        client_socket.send("GET".encode())

        #서버응답 대기(3초)
        timeout = 3
        start_time = time.time()
        while not rankings_data and time.time() - start_time < timeout:
            time.sleep(0.1)  # 짧은 대기 시간
        
        # 전역 변수에서 랭킹 데이터를 사용
        if rankings_data:
            splited_rankings_data = rankings_data.split('\n')
            for rk in splited_rankings_data:
                rankings_list.append(rk.split('!'))
    except Exception as e:
        print("에러 발생:", e)
        rankings_list = [['에러발생', '다시시도해주세요', '.']]

    print('랭킹데이터:', rankings_list)
    return rankings_list
#랭킹화면 표시
def show_ranking_screen(rankings,close_rank_button):
    ranking_surface_width=250
    ranking_surface = pygame.Surface((ranking_surface_width, 300))
    ranking_surface.fill((192,192,192))

    scroll_y = 0
    ranking_running = True
    font = pygame.font.SysFont("malgungothic", 15)

    # "랭킹" 텍스트 렌더링 위치 조정
    text_title = font.render("랭킹(상위 30)", True, BLACK)
    title_pos_x = ranking_surface_width // 2 - text_title.get_width() // 2  # 랭킹 창 중앙
    title_pos_y = 10  # 상단에서 조금 떨어진 위치
    

    # 창닫기 버튼 렌더링하기
    button_text = "창닫기"
    close_rank_button.color = (255, 0, 0)  # 빨간색
    close_rank_button.draw(screen)
    text = font.render(button_text, True, (255, 255, 255))
    screen.blit(text, (close_rank_button.rect.x + 10, close_rank_button.rect.y + 10))
    while ranking_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ranking_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if close_rank_button.rect.collidepoint(event.pos):
                    # "창닫기" 버튼 클릭 시 함수 탈출
                    ranking_surface=None
                    ranking_running = False
                    break
                if event.button == 4: scroll_y = min(scroll_y + 15, 0)
                if event.button == 5: scroll_y = max(scroll_y - 15, -len(rankings) * 20 + 100)
        if ranking_surface:
            ranking_surface.fill((192, 192, 192))
            ranking_surface.blit(text_title, (title_pos_x, title_pos_y))

            for i, (player, score, _) in enumerate(rankings):
                text = font.render(f"{i + 1}. {player} {score}", True, BLACK)
                ranking_surface.blit(text, (20, 40 + i * 20 + scroll_y))  # 스크롤 위치 조정

            screen.blit(ranking_surface, (WIDTH // 2 - ranking_surface_width // 2, HEIGHT // 2 - 150))
            pygame.display.flip()
            pygame.time.wait(10)
    return

# 서버에 데이터 전송
def work(nickname='None', score=0,type="send"):
    if type == "send":
        print('>> Connect Server')
        print('score:', score)
        current_datetime = datetime.datetime.now()

        year = current_datetime.year
        month = current_datetime.month
        day = current_datetime.day
        hour = current_datetime.hour
        minute = current_datetime.minute
        second = current_datetime.second

        formatted_datetime = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
        print('send!', nickname, score, formatted_datetime)
        message = str(nickname) + '!' + str(score) + '!' + formatted_datetime
        try:
            client_socket.send(message.encode())
            print('전송성공')
            return 1
        except Exception as e:
            print("에러 발생:", e)
            print('전송실패')
            return 0
    elif type=="get":
        try:
            rankings=get_rankings_from_server()
            
            print('받기성공')
            return 1
        except:
            print('전송실패')
            return 0

pygame.init()
# Constants
WIDTH, HEIGHT = 400, 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
WHITE = (255, 255, 255)
HEAD_COLOR = (51,255,255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

#버튼
class Button:
    def __init__(self, x, y, width, height, color, inactive_color=(128, 128, 128)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.inactive_color = inactive_color  # 비활성화 색상
        self.visible = True
        self.enabled = True  # 버튼 활성화 상태

    def draw(self, screen):
        if self.visible:
            if self.enabled:
                pygame.draw.rect(screen, self.color, self.rect)
            else:
                pygame.draw.rect(screen, self.inactive_color, self.rect)  # 비활성화 상태일 때 색상

    def hide(self):
        self.visible = False

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def isenable(self):
        return self.enabled

# 버튼요소 
check_rank_button = Button(150, 350, 100, 40, (0, 128, 255))
close_rank_button = Button(150, 350, 100, 40, (0, 128, 255))
button = Button(150, 220, 100, 40, (0, 128, 255))
# 방향
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# 서버연결
connect_info=1
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
    print('서버연결성공')
    start_new_thread(recv_data, (client_socket,))
except:
    connect_info=0


# 화면생성
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

# 게임 루프
clock = pygame.time.Clock()
score = 0
game_running=True
is_ranking_shown = False
game_over_screen = False
# 한게임 데이터
done = False
nickname='None'
while game_running:
    snake = [(5, 5)]
    snake_sets=set((5,5))
    snake_dir = RIGHT
    food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))

    # Game loop
    clock = pygame.time.Clock()
    score = 0
    pygame.display.set_caption("싸네이크")
    font = pygame.font.Font(None, 36)
    text = ""
    input_box = pygame.Rect(100, 150, 400, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                client_socket.close()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.rect.collidepoint(event.pos):
                    button.hide()
                    nickname=text
                    print('게임시작',nickname)
                    done = True
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        # 여기서 닉네임을 처리하고 원하는 작업을 수행하세요.
                        nickname=text
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += str(event.unicode)


        screen.fill((30, 30, 30))
        font = pygame.font.SysFont("malgungothic", 30)
        text1 = font.render(f"Enter nickname", True, (255, 255, 255))
        screen.blit(text1, (100, 90))
        font = pygame.font.SysFont("malgungothic", 12)
        text2 = font.render(f"only english and number", True, (255, 255, 255))
        screen.blit(text2, (133, 130))
        font = pygame.font.SysFont("malgungothic", 30)
        text3 = font.render(f"", True, (255, 255, 255))
        screen.blit(text3, (100, 120))
        print('text',text)
        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 7))
        button.draw(screen)
        text1 = font.render(f"start", True, (255, 255, 255))
        screen.blit(text1, (160, 220))

        font = pygame.font.SysFont("malgungothic", 20)
        text1 = font.render(f"서버 : ", True, (255, 255, 255))
        screen.blit(text1, (110, 270))
        if connect_info:
            text1 = font.render(f"Online", True, (0, 0, 255))
        else:
            text1 = font.render(f"Offline", True, (255, 0, 0))

        screen.blit(text1, (170, 270))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()

    print('nickname',nickname)
    # 인게임부
    while True:
        game_over_screen=False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and snake_dir != DOWN:
                    snake_dir = UP
                elif event.key == pygame.K_DOWN and snake_dir != UP:
                    snake_dir = DOWN
                elif event.key == pygame.K_LEFT and snake_dir != RIGHT:
                    snake_dir = LEFT
                elif event.key == pygame.K_RIGHT and snake_dir != LEFT:
                    snake_dir = RIGHT

        # Move the Snake
        new_head = (snake[0][0] + snake_dir[0], snake[0][1] + snake_dir[1])
        snake.insert(0, new_head)
        snake_sets.add(new_head)

        # Check for collision with food
        if snake[0] == food:
            score += 1
            while True:
                tmp= (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                if tmp not in snake_sets:
                    food = tmp
                    game_over_screen=True
                    break
        else:
            snake_sets.discard(snake.pop())
            

        # Check for collision with walls
        if (
            snake[0][0] < 0
            or snake[0][0] >= GRID_WIDTH
            or snake[0][1] < 0
            or snake[0][1] >= GRID_HEIGHT
        ):
            game_over_screen=True
            break
        # Check for collision with itself
        if snake[0] in snake[1:]:
            game_over_screen=True
            break
        # Clear the screen
        screen.fill(BLACK)
        # Draw Snake

        pygame.draw.rect(screen, HEAD_COLOR, (snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        for segment in snake[1:]:
            pygame.draw.rect(screen, GREEN, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

        # Draw Food
        pygame.draw.rect(screen, RED, (food[0] * GRID_SIZE, food[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        font = pygame.font.Font(None, 30)
        text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
        clock.tick(5+score*15//75)  # Adjust the speed of the game

    game_data_send_check=False

    while game_over_screen:
        #게임오버부
        screen.fill(WHITE)
        font = pygame.font.SysFont("malgungothic", 38)
        text_game_over = font.render(f"Game Over : {score}", True, (0, 0, 0))
        try:
            if not game_data_send_check:
                res_cended=work(nickname=nickname,score=score)
        except:
            try:
                client_socket.connect((HOST, PORT))
                print('서버연결성공')
                start_new_thread(recv_data, (client_socket,))
                if not game_data_send_check:
                    res_cended=work(nickname=nickname,score=score)
            except:
                print('연결실패')
                pass
        if res_cended:
            font = pygame.font.SysFont("malgungothic", 15)
            text1 = font.render(f"데이터 전송성공", True, (0, 0, 0))
            screen.blit(text1, (140, 220))
            game_data_send_check=True
            check_rank_button.enable()
            button_text = "등수확인"
            check_rank_button.color = (0, 128, 255)  # 원래 색상
            check_rank_button.draw(screen)
            text = font.render(button_text, True, (255, 255, 255))
            screen.blit(text, (check_rank_button.rect.x + 10, check_rank_button.rect.y + 10))
        else:
            check_rank_button.disable()
            print('버튼 비활성화')
            font = pygame.font.SysFont("malgungothic", 10)
            button = Button(150, 220, 100, 40, (0, 128, 255))
            button.draw(screen)
            text1 = font.render(f"데이터 전송에러;", True, (255, 255, 255))
            screen.blit(text1, (160, 220))
            text1 = font.render(f"눌러서 재전송;", True, (255, 255, 255))
            screen.blit(text1, (160, 235))
            res_check=0
        screen.blit(text_game_over, (100,80))
        
        font = pygame.font.SysFont("malgungothic", 20)

        text_nickname = font.render(f"nickname: {nickname}", True, (0, 0, 0))
        screen.blit(text_nickname, (140,135))
        font = pygame.font.SysFont("malgungothic", 20)
        text = font.render(f"   Regame(R)", True, (0, 0, 0))
        screen.blit(text,(120,160))
        text = font.render(f"   Quit(Q)", True, (0, 0, 0))
        screen.blit(text,(120,185))
        while True:
            pygame.display.flip()
            check=0
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        check=1
                        game_over_screen=False
                        break
                    elif event.key == pygame.K_q:
                        check=2
                        game_over_screen=False
                        break
                if event.type == pygame.QUIT:
                    pygame.quit()
                    client_socket.close()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button.rect.collidepoint(event.pos): #재연결부분
                        button.hide()
                        if try_connect_to_server():
                            res_check=work(nickname=nickname,score=score)
                            if res_check:
                                print('연결서서성공')
                                check = 1
                                game_data_send_check=True
                                res_cended=True

                                #game_over_screan = False
                                break
                        else:
                            update_ui_with_connection_status()  # UI 업데이트 함수 호출
                    if check_rank_button.rect.collidepoint(event.pos) and check_rank_button.isenable():
                            print('랭킹조회')
                            pygame.time.wait(100)
                            rankings = get_rankings_from_server()
                            show_ranking_screen(rankings,close_rank_button)
                            print('창닫음')
                            check=1
                            break
            if check:
                break
        if not game_over_screen:
            pygame.display.update()
        if check==2:
            pygame.quit()
            client_socket.close()
            sys.exit()