import pygame
import asyncio
import os
from solver import Solver

pygame.init()


class Game:
    def __init__(self, board, screenSize):
        self.images = None
        self.screen = None
        self.board = board
        self.screenSize = screenSize
        self.pieceSize = (
            self.screenSize[0] // self.board.getSize()[1],
            self.screenSize[1] // self.board.getSize()[0],
        )

        self.font = pygame.font.Font(None, 36)
        self.loadImages()
        self.bombsLeft = self.board.getMinesNum()

    def displayGameOverMenu(self, won):
        # Display game over screen with restart options
        overlay = pygame.Surface(self.screenSize)
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Game over message
        font_large = pygame.font.Font(None, 74)
        font_medium = pygame.font.Font(None, 50)
        font_small = pygame.font.Font(None, 36)

        if won:
            main_text = font_large.render("You Won!", True, (0, 255, 0))
        else:
            main_text = font_large.render("Game Over!", True, (255, 0, 0))

        main_rect = main_text.get_rect(center=(self.screenSize[0] // 2, self.screenSize[1] // 2 - 100))
        self.screen.blit(main_text, main_rect)

        # Options
        restart_text = font_medium.render("Press R to Restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(self.screenSize[0] // 2, self.screenSize[1] // 2 - 20))
        self.screen.blit(restart_text, restart_rect)

        menu_text = font_medium.render("Press M for Main Menu", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=(self.screenSize[0] // 2, self.screenSize[1] // 2 + 30))
        self.screen.blit(menu_text, menu_rect)

        quit_text = font_medium.render("Press Q to Quit", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=(self.screenSize[0] // 2, self.screenSize[1] // 2 + 80))
        self.screen.blit(quit_text, quit_rect)

    async def run(self, use_solver=False, solver_delay=0.5):
        self.screen = pygame.display.set_mode(self.screenSize)
        pygame.display.set_caption("Minesweeper")
        running = True
        solver = Solver(self.board) if use_solver else None
        game_over = False

        clock = pygame.time.Clock()
        last_solver_time = 0

        while running:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'

                # Input handling when game is OVER
                if game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return 'restart'
                    elif event.key == pygame.K_m:
                        return 'menu'
                    elif event.key == pygame.K_q:
                        return 'quit'

                # Input handling when game is RUNNING
                if not game_over and event.type == pygame.MOUSEBUTTONDOWN and not use_solver:
                    pos = pygame.mouse.get_pos()
                    rightClick = pygame.mouse.get_pressed()[2]
                    self.handleClick(pos, rightClick)
                elif not game_over and event.type == pygame.MOUSEBUTTONDOWN and use_solver and self.board.first:
                    # User needs to make the first click for AI
                    pos = pygame.mouse.get_pos()
                    rightClick = pygame.mouse.get_pressed()[2]
                    self.handleClick(pos, rightClick)

            # --- Game Logic ---
            if not game_over:
                # AI solver with timing
                if (use_solver and solver and not self.board.first and
                        current_time - last_solver_time > solver_delay * 1000):

                    moves_made = solver.move()
                    if moves_made:
                        last_solver_time = current_time

                # Check for game end conditions
                if self.board.getLost() or self.board.getWon():
                    game_over = True
                    if self.board.getLost():
                        self.playLoseSound()
                    else:
                        self.playWinSound()

            # --- Drawing ---
            # 1. Always draw the board
            self.draw(self.board.getLost())
            self.drawUI()

            # 2. If game over, draw the overlay on top
            if game_over:
                self.displayGameOverMenu(self.board.getWon())

            # 3. Flip the display (Essential to prevent freezing)
            pygame.display.flip()

            clock.tick(60)
            await asyncio.sleep(0)

        return 'quit'

    def draw(self, lost):
        self.screen.fill((192, 192, 192))
        topLeft = (0, 0)
        for row in range(self.board.getSize()[0]):
            for col in range(self.board.getSize()[1]):
                piece = self.board.getPiece((row, col))
                image = self.getImage(piece, lost)
                self.screen.blit(image, topLeft)
                topLeft = topLeft[0] + self.pieceSize[0], topLeft[1]
            topLeft = 0, topLeft[1] + self.pieceSize[1]

    def drawUI(self):
        bombs_text = self.font.render(f"Bombs: {self.board.getMinesNum()}", True, (0, 0, 0))
        self.screen.blit(bombs_text, (10, 10))

    def loadImages(self):
        self.images = {}
        for fileName in os.listdir("images"):
            if not fileName.endswith(".png"):
                continue
            image = pygame.image.load(r"images/" + fileName)
            image = pygame.transform.scale(image, self.pieceSize)
            self.images[fileName.split(".")[0]] = image

    def getImage(self, piece, lost):
        if piece.getClicked():
            string = "bomb-at-clicked-block" if piece.getHasBomb() else str(piece.getNumAround())
        elif piece.getFlagged() and not lost:
            string = "flag"
        else:
            if piece.getFlagged() and not piece.getHasBomb():
                string = "wrong-flag"
            elif lost and piece.getHasBomb():
                string = "unclicked-bomb"
            else:
                string = "empty-block"

        return self.images[string]

    def handleClick(self, pos, rightClick):
        if pos[1] < 0 or pos[0] < 0:
            return

        row = pos[1] // self.pieceSize[1]
        col = pos[0] // self.pieceSize[0]

        if row >= self.board.getSize()[0] or col >= self.board.getSize()[1]:
            return

        piece = self.board.getPiece((row, col))
        self.board.handleClick(piece, rightClick)

    def playWinSound(self):
        try:
            sound = pygame.mixer.Sound("sounds/win.wav")
            sound.play()
        except:
            pass

    def playLoseSound(self):
        try:
            sound = pygame.mixer.Sound("sounds/lose.wav")
            sound.play()
        except:
            pass