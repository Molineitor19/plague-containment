import pygame
import pygame.gfxdraw
import json
import os
import sys
import math
import random
import subprocess
import threading
from pathlib import Path


# paths to the json files we share with the other modules
BASE_DIR      = Path(__file__).parent
STATE_PATH    = BASE_DIR / "state.json"
RESULT_PATH   = BASE_DIR / "result.json"
ACTION_PATH   = BASE_DIR / "action.json"
ALGORITHM_DIR = BASE_DIR


# window and grid size settings
WINDOW_W   = 1100
WINDOW_H   = 720
GRID_COLS  = 8
GRID_ROWS  = 8
CELL_SIZE  = 72        # size of each cell in pixels
CELL_GAP   = 4         # gap between cells
GRID_X     = 30        # left margin of the grid
GRID_Y     = 90        # top margin of the grid
PANEL_X    = GRID_X + GRID_COLS * (CELL_SIZE + CELL_GAP) + 20

FPS = 60


# colors for each district state and UI elements
C_BG          = (245, 245, 245)   # fondo blanco
C_GRID_BG     = (220, 220, 220)
C_HEALTHY     = (255, 255, 255)   # sano — blanco
C_HEALTHY_HI  = (230, 230, 230)
C_INFECTED    = (200,  30,  30)   # infectado — rojo
C_INFECTED_HI = (240,  60,  60)
C_VACCINATED  = ( 40, 160,  70)   # vacunado — verde
C_VACCINATED_HI=(70, 200, 100)
C_QUARANTINE  = (200, 170,   0)   # cuarentena — amarillo
C_QUARANTINE_HI=(240, 210,  20)
C_GREEDY_RING = ( 30, 100, 200)   # sugerencia greedy — azul
C_BT_RING     = (200, 130,   0)   # sugerencia backtracking — naranja
C_SELECTED    = ( 50,  50,  50)
C_TEXT        = ( 30,  30,  30)   # texto oscuro sobre fondo claro
C_TEXT_DIM    = (120, 120, 120)
C_PANEL_BG    = (235, 235, 240)
C_PANEL_BORDER= (180, 180, 200)
C_WIN         = ( 30, 150,  60)
C_LOSE        = (200,  30,  30)
C_BTN_VACC    = ( 40, 140,  70)
C_BTN_QUAR    = (180, 150,   0)
C_BTN_SKIP    = (140, 140, 150)
C_BTN_HOVER   = ( 60, 180,  90)
C_BTN_HOVER   = (80, 160, 255)

# maps each state string to its color
STATE_COLORS = {
    "healthy":     C_HEALTHY,
    "infected":    C_INFECTED,
    "vaccinated":  C_VACCINATED,
    "quarantined": C_QUARANTINE,
}
STATE_COLORS_HI = {
    "healthy":     C_HEALTHY_HI,
    "infected":    C_INFECTED_HI,
    "vaccinated":  C_VACCINATED_HI,
    "quarantined": C_QUARANTINE_HI,
}
STATE_LABELS = {
    "healthy":     "HEALTHY",
    "infected":    "INFECTED",
    "vaccinated":  "VACCINATED",
    "quarantined": "QUARANTINE",
}


# small particles that appear when a district changes state
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        # random direction and speed
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.07)
        self.size = random.randint(3, 7)
        self.color = color

    def update(self):
        # move and fade the particle each frame
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08   # soft gravity
        self.life -= self.decay
        return self.life > 0

    def draw(self, surf):
        # draw with transparency based on remaining life
        alpha = int(self.life * 220)
        r, g, b = self.color
        pygame.gfxdraw.filled_circle(
            surf, int(self.x), int(self.y), self.size,
            (r, g, b, alpha)
        )


# holds the current game state loaded from state.json
class GameState:
    def __init__(self):
        self.districts  = {}   # key is (row, col), value is district dict
        self.stats      = {"total_healthy":0,"total_infected":0,
                           "total_vaccinated":0,"total_quarantined":0}
        self.turn       = 0
        self.grid_size  = 8
        self.status     = "ongoing"   # can be ongoing, win or lose

    def load(self, path):
        # read state.json and fill the districts dict
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.districts = {}
            for d in data.get("districts", []):
                self.districts[(d["row"], d["col"])] = d
            self.stats     = data.get("stats", self.stats)
            self.turn      = data.get("turn", self.turn)
            self.grid_size = data.get("grid_size", 8)
            # check if the game is over
            if self.stats.get("total_infected", 1) == 0:
                self.status = "win"
            elif self.stats.get("total_healthy", 1) == 0:
                self.status = "lose"
            else:
                self.status = "ongoing"
            return True
        except Exception as e:
            print(f"[UI] Error loading state.json: {e}")
            return False

    def get(self, row, col):
        # return district data or a default healthy district if not found
        return self.districts.get((row, col), {"row": row, "col": col,
                                               "risk": 0, "state": "healthy"})


# holds the algorithm results loaded from result.json
class AlgoResult:
    def __init__(self):
        self.greedy_row    = None
        self.greedy_col    = None
        self.greedy_risk   = None
        self.quarantine    = []    # list of (row, col) to quarantine
        self.qt_found      = False

    def load(self, path):
        # read result.json written by algorithms.py
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            gr = data.get("greedy_recommendation")
            if gr:
                self.greedy_row  = gr["row"]
                self.greedy_col  = gr["col"]
                self.greedy_risk = gr["risk"]
            else:
                self.greedy_row = self.greedy_col = self.greedy_risk = None
            qp = data.get("quarantine_plan", {})
            self.qt_found   = qp.get("found", False)
            self.quarantine = [(d["row"], d["col"]) for d in qp.get("districts", [])]
            return True
        except:
            return False


# helper: returns the pixel rect for a grid cell
def cell_rect(row, col):
    x = GRID_X + col * (CELL_SIZE + CELL_GAP)
    y = GRID_Y + row * (CELL_SIZE + CELL_GAP)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


# helper: draws a rectangle with rounded corners and optional border
def draw_rounded_rect(surf, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, width=border, border_radius=radius)


# helper: linear interpolation between two colors
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# helper: draw text centered at (cx, cy)
def draw_text_center(surf, font, text, cx, cy, color):
    surf2 = font.render(text, True, color)
    surf.blit(surf2, (cx - surf2.get_width() // 2, cy - surf2.get_height() // 2))


# helper: draw text at position (x, y)
def draw_text(surf, font, text, x, y, color):
    surf.blit(font.render(text, True, color), (x, y))


# a clickable button with hover effect
class Button:
    def __init__(self, rect, label, color, action):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.color  = color
        self.action = action
        self.hovered = False

    def draw(self, surf, font):
        # lighten color a bit when mouse is over it
        c = lerp_color(self.color, (255,255,255), 0.18) if self.hovered else self.color
        draw_rounded_rect(surf, c, self.rect, radius=8)
        draw_text_center(surf, font, self.label,
                         self.rect.centerx, self.rect.centery, C_TEXT)

    def handle(self, event):
        # update hover state and return action string when clicked
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None


# short message that appears on screen and fades out
class Toast:
    def __init__(self, text, color=C_TEXT, duration=2.5):
        self.text     = text
        self.color    = color
        self.life     = duration
        self.duration = duration

    def update(self, dt):
        # count down and return False when expired
        self.life -= dt
        return self.life > 0

    def draw(self, surf, font, y):
        # fade in at start and fade out at end
        alpha = min(1.0, self.life / 0.4, (self.duration - self.life) / 0.3 + 0.1)
        alpha = max(0.0, alpha)
        s = font.render(self.text, True, self.color)
        x = WINDOW_W // 2 - s.get_width() // 2
        tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        tmp.blit(s, (0, 0))
        tmp.set_alpha(int(alpha * 255))
        surf.blit(tmp, (x, y))


# main class that runs the whole interface
class PlagueUI:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Plague Containment — Equipo 16")
        self.screen  = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.toggle_fullscreen()
        self.clock   = pygame.time.Clock()

        # fonts for different text sizes
        self.font_lg  = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_md  = pygame.font.SysFont("Consolas", 16)
        self.font_sm  = pygame.font.SysFont("Consolas", 13)
        self.font_xl  = pygame.font.SysFont("Consolas", 36, bold=True)

        # game state and algorithm results
        self.state    = GameState()
        self.result   = AlgoResult()
        self.selected = None          # currently selected cell (row, col)
        self.hover    = None          # cell the mouse is over
        self.particles= []
        self.toasts   = []
        self.tick     = 0.0           # time counter for animations
        self.algo_running = False     # True while algorithms.py is running
        self.prev_states  = {}        # used to detect state changes for particles
        self.action_taken = False     # player already acted this turn

        # action buttons shown when a district is selected
        bw, bh = 160, 42
        bx = PANEL_X + 10
        self.btn_vaccinate  = Button((bx, 580, bw, bh), "💉 VACCINATE",    C_BTN_VACC, "vaccinate")
        self.btn_quarantine = Button((bx, 630, bw, bh), "🚧 QUARANTINE", C_BTN_QUAR, "quarantine")
        self.btn_skip       = Button((bx, 680 - bh - 4, WINDOW_W - bx - 20, bh - 6),
                                     "⏭  SKIP TURN", C_BTN_SKIP, "skip")

        # load initial state, create demo if no file exists yet
        if not STATE_PATH.exists():
            self._create_demo_state()
        self.state.load(STATE_PATH)
        self.result.load(RESULT_PATH)
        self.prev_states = {k: v["state"] for k, v in self.state.districts.items()}

    def _create_demo_state(self):
        # creates a default state.json with one infected district at (3,4)
        RISK_MAP = [
            [3,5,2,7,4,6,1,3],
            [4,6,8,5,3,7,2,5],
            [2,4,6,8,9,7,3,4],
            [5,3,4,7,6,5,8,2],
            [6,7,8,9,10,1,2,3],
            [4,5,6,7,8,9,10,1],
            [2,3,4,5,6,7,8,9],
            [10,1,2,3,4,5,6,7],
        ]
        districts = []
        for r in range(8):
            for c in range(8):
                import random
                infected_r = random.randint(1, 6)
                infected_c = random.randint(1, 6)
                state = "infected" if (r == infected_r and c == infected_c) else "healthy"
                districts.append({"row": r, "col": c,
                                  "risk": RISK_MAP[r][c], "state": state})
        data = {
            "turn": 1,
            "grid_size": 8,
            "districts": districts,
            "infection_chain": [{"row": infected_r, "col": infected_c, "turn_infected": 1}],
            "stats": {
                "total_healthy": 63,
                "total_infected": 1,
                "total_vaccinated": 0,
                "total_quarantined": 0
            }
        }
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("[UI] demo state.json created")

    def _spawn_particles(self):
        # spawn particles on cells that changed state since last reload
        for (r, c), dist in self.state.districts.items():
            new_st = dist["state"]
            old_st = self.prev_states.get((r, c), new_st)
            if old_st != new_st:
                rect = cell_rect(r, c)
                cx, cy = rect.centerx, rect.centery
                color = STATE_COLORS.get(new_st, C_TEXT)
                for _ in range(22):
                    self.particles.append(Particle(cx, cy, color))
        self.prev_states = {k: v["state"] for k, v in self.state.districts.items()}

    def _run_algorithms(self):
        # run algorithms.py in a separate thread so the UI doesnt freeze
        def _task():
            self.algo_running = True
            try:
                subprocess.run(
                    [sys.executable, str(ALGORITHM_DIR / "algorithms.py")],
                    cwd=str(ALGORITHM_DIR),
                    capture_output=True, text=True, timeout=30
                )
                self.result.load(RESULT_PATH)
                self.toasts.append(Toast("Algorithms done", C_WIN))
            except Exception as e:
                self.toasts.append(Toast(f"Error algoritmos: {e}", C_LOSE))
            finally:
                self.algo_running = False
        threading.Thread(target=_task, daemon=True).start()

    def _write_action(self, action_type, row, col):
        # write the player action to action.json so the C++ engine can read it
        data = {
            "action_type": action_type,
            "target": {"row": row, "col": col},
            "turn": self.state.turn
        }
        with open(ACTION_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[UI] action.json -> {action_type} ({row},{col}) turn {self.state.turn}")

    def _reload(self):
        # reload state and results from disk
        ok = self.state.load(STATE_PATH)
        self.result.load(RESULT_PATH)
        if ok:
            self._spawn_particles()
            self.action_taken = False
            self.selected = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected = None
                if event.key == pygame.K_r:      # reload state manually
                    self._reload()
                    self.toasts.append(Toast("State reloaded"))
                if event.key == pygame.K_SPACE:  # skip turn
                    self._skip_turn()

            # track which cell the mouse is hovering over
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self.hover = None
                for r in range(GRID_ROWS):
                    for c in range(GRID_COLS):
                        if cell_rect(r, c).collidepoint(mx, my):
                            self.hover = (r, c)

            # select a healthy district when clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                clicked = False
                for r in range(GRID_ROWS):
                    for c in range(GRID_COLS):
                        if cell_rect(r, c).collidepoint(mx, my):
                            dist = self.state.get(r, c)
                            if dist["state"] in ("healthy",):
                                if self.selected == (r, c):
                                    self.selected = None
                                else:
                                    self.selected = (r, c)
                            clicked = True

            # handle vaccinate and quarantine buttons
            if self.selected and not self.action_taken:
                for btn in [self.btn_vaccinate, self.btn_quarantine]:
                    action = btn.handle(event)
                    if action:
                        r, c = self.selected
                        self._write_action(action, r, c)
                        label = "Vaccination" if action == "vaccinate" else "Quarantine"
                        self.toasts.append(
                            Toast(f"{label} applied on ({r},{c})", C_VACCINATED
                                  if action == "vaccinate" else C_QUARANTINE_HI)
                        )
                        self.action_taken = True
                        self.selected = None

            # handle skip button
            skip = self.btn_skip.handle(event)
            if skip:
                self._skip_turn()

            # update hover state on all buttons
            self.btn_vaccinate.handle(event)
            self.btn_quarantine.handle(event)
            self.btn_skip.handle(event)

        return True

    def _skip_turn(self):
        # skip turn and wait for C++ engine to write new state
        self.toasts.append(Toast("Turn skipped", C_TEXT_DIM))
        self.action_taken = False
        self.selected = None

    def draw(self):
        # draw everything each frame
        self.screen.fill(C_BG)
        self._draw_header()
        self._draw_grid()
        self._draw_suggestions()
        self._draw_panel()
        self._draw_particles()
        self._draw_toasts()
        if self.state.status != "ongoing":
            self._draw_endscreen()
        pygame.display.flip()

    def _draw_header(self):
        # draw title and keyboard shortcuts at the top
        title = f"PLAGUE CONTAINMENT  —  Turn {self.state.turn}"
        draw_text(self.screen, self.font_lg, title, GRID_X, 18, C_TEXT)
        sub = "R=reload  |  SPACE=skip turn  |  ESC=cancel selection"
        draw_text(self.screen, self.font_sm, sub, GRID_X, 46, C_TEXT_DIM)
        pygame.draw.line(self.screen, C_PANEL_BORDER,
                         (GRID_X, 72), (WINDOW_W - 20, 72), 1)

    def _draw_grid(self):
        # draw each district cell with its color and info
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                dist  = self.state.get(r, c)
                state = dist["state"]
                rect  = cell_rect(r, c)

                base_color = STATE_COLORS.get(state, C_HEALTHY)
                hi_color   = STATE_COLORS_HI.get(state, C_HEALTHY_HI)

                # infected cells pulse between dark and bright red
                if state == "infected":
                    t = (math.sin(self.tick * 3.0 + r * 0.7 + c * 0.5) + 1) / 2
                    color = lerp_color(base_color, hi_color, t)
                elif (r, c) == self.hover and state == "healthy":
                    color = hi_color
                else:
                    color = base_color

                draw_rounded_rect(self.screen, color, rect, radius=8)

                # white border when selected
                if (r, c) == self.selected:
                    pygame.draw.rect(self.screen, C_SELECTED, rect,
                                     width=3, border_radius=8)

                # show risk number
                risk_text = str(dist["risk"])
                draw_text_center(self.screen, self.font_md, risk_text,
                                 rect.centerx, rect.centery - 8, C_TEXT)

                # show icon for each state
                icons = {"healthy": "✓", "infected": "☣",
                         "vaccinated": "💉", "quarantined": "🚧"}
                icon = icons.get(state, "")
                draw_text_center(self.screen, self.font_sm, icon,
                                 rect.centerx, rect.centery + 12, C_TEXT)

    def _draw_suggestions(self):
        # draw suggestion rings from algorithm results on top of grid
        # yellow ring = greedy vaccination suggestion
        if self.result.greedy_row is not None:
            r, c = self.result.greedy_row, self.result.greedy_col
            rect = cell_rect(r, c)
            t    = (math.sin(self.tick * 4.0) + 1) / 2
            pass
            pygame.draw.rect(self.screen, C_GREEDY_RING, rect,
                             width=3, border_radius=8)
            draw_text_center(self.screen, self.font_sm, "VACCINATE",
                             rect.centerx, rect.top - 9, C_GREEDY_RING)

        # orange rings = backtracking quarantine plan
        for (r, c) in self.result.quarantine:
            rect = cell_rect(r, c)
            pygame.draw.rect(self.screen, C_BT_RING, rect,
                             width=3, border_radius=8)

    def _draw_panel(self):
        # draw the right side panel with stats, suggestions and buttons
        panel_rect = pygame.Rect(PANEL_X - 10, 80,
                                 WINDOW_W - PANEL_X + 5, WINDOW_H - 90)
        draw_rounded_rect(self.screen, C_PANEL_BG, panel_rect,
                          radius=12, border=1, border_color=C_PANEL_BORDER)

        px = PANEL_X + 8
        py = 95

        # stats section with progress bars
        draw_text(self.screen, self.font_lg, "STATS", px, py, C_TEXT); py += 32

        stats_info = [
            ("Healthy",       self.state.stats.get("total_healthy", 0),    C_HEALTHY_HI),
            ("Infected",  self.state.stats.get("total_infected", 0),   C_INFECTED_HI),
            ("Vaccinated",   self.state.stats.get("total_vaccinated", 0), C_VACCINATED_HI),
            ("Quarantine",  self.state.stats.get("total_quarantined", 0),C_QUARANTINE_HI),
        ]
        for label, val, color in stats_info:
            total = 64
            bar_w  = 160
            fill_w = int(bar_w * val / total)
            bar_rect = pygame.Rect(px, py + 16, bar_w, 8)
            pygame.draw.rect(self.screen, C_PANEL_BORDER, bar_rect, border_radius=4)
            if fill_w > 0:
                fill_rect = pygame.Rect(px, py + 16, fill_w, 8)
                pygame.draw.rect(self.screen, color, fill_rect, border_radius=4)
            draw_text(self.screen, self.font_md,
                      f"{label}: {val:>2}", px, py, color)
            py += 30

        py += 10
        pygame.draw.line(self.screen, C_PANEL_BORDER,
                         (px, py), (px + 180, py), 1); py += 12

        # greedy suggestion
        draw_text(self.screen, self.font_md, "GREEDY — Vaccination", px, py, C_GREEDY_RING); py += 22
        if self.result.greedy_row is not None:
            draw_text(self.screen, self.font_sm,
                      f"  Distrito ({self.result.greedy_row},{self.result.greedy_col})"
                      f"  riesgo={self.result.greedy_risk}",
                      px, py, C_TEXT); py += 18
        else:
            draw_text(self.screen, self.font_sm, "  No candidates", px, py, C_TEXT_DIM); py += 18

        py += 6
        # backtracking suggestion
        draw_text(self.screen, self.font_md, "BACKTRACKING — Quarantine", px, py, C_BT_RING); py += 22
        if self.result.qt_found:
            draw_text(self.screen, self.font_sm,
                      f"  Plan: {len(self.result.quarantine)} districts",
                      px, py, C_TEXT); py += 18
            coords_str = ", ".join(f"({r},{c})" for r, c in self.result.quarantine[:3])
            if len(self.result.quarantine) > 3:
                coords_str += "…"
            draw_text(self.screen, self.font_sm, "  " + coords_str, px, py, C_TEXT_DIM); py += 18
        else:
            draw_text(self.screen, self.font_sm,
                      "  No valid plan found", px, py, C_TEXT_DIM); py += 18

        py += 6
        pygame.draw.line(self.screen, C_PANEL_BORDER,
                         (px, py), (px + 180, py), 1); py += 12

        # show selected district info and action buttons
        if self.selected:
            r, c = self.selected
            dist = self.state.get(r, c)
            draw_text(self.screen, self.font_md,
                      f"Selected: ({r},{c})", px, py, C_TEXT); py += 20
            draw_text(self.screen, self.font_sm,
                      f"  State: {STATE_LABELS.get(dist['state'], dist['state'])}",
                      px, py, C_TEXT_DIM); py += 16
            draw_text(self.screen, self.font_sm,
                      f"  Risk: {dist['risk']}/10",
                      px, py, C_TEXT_DIM); py += 24

            if not self.action_taken:
                self.btn_vaccinate.rect.topleft  = (px, py);      py += 48
                self.btn_quarantine.rect.topleft = (px, py)
                self.btn_vaccinate.draw(self.screen, self.font_md)
                self.btn_quarantine.draw(self.screen, self.font_md)
        else:
            draw_text(self.screen, self.font_sm,
                      "Click on HEALTHY district", px, py, C_TEXT_DIM); py += 16
            draw_text(self.screen, self.font_sm,
                      "to select an action.", px, py, C_TEXT_DIM)

        # skip button always visible at the bottom
        self.btn_skip.rect = pygame.Rect(px, WINDOW_H - 60,
                                         WINDOW_W - px - 20, 38)
        self.btn_skip.draw(self.screen, self.font_md)

        # show loading dots while algorithms are running
        if self.algo_running:
            t = int(self.tick * 4) % 4
            dots = "." * (t + 1)
            draw_text(self.screen, self.font_sm,
                      f"Running algorithms{dots}", px, WINDOW_H - 85,
                      C_TEXT_DIM)

        # color legend at the bottom of the panel
        legend_y = WINDOW_H - 170
        draw_text(self.screen, self.font_sm, "LEGEND:", px, legend_y, C_TEXT_DIM); legend_y += 18
        for state, color in [("Healthy", C_HEALTHY_HI),("Infected", C_INFECTED_HI),
                              ("Vaccinated", C_VACCINATED_HI),("Quarantine", C_QUARANTINE_HI)]:
            pygame.draw.rect(self.screen, color,
                             pygame.Rect(px, legend_y + 2, 12, 12), border_radius=3)
            draw_text(self.screen, self.font_sm, state, px + 18, legend_y, C_TEXT_DIM)
            legend_y += 17
        pygame.draw.rect(self.screen, C_GREEDY_RING,
                         pygame.Rect(px, legend_y + 2, 12, 12), width=2, border_radius=3)
        draw_text(self.screen, self.font_sm, "Greedy (vaccinate)", px + 18, legend_y, C_TEXT_DIM); legend_y += 17
        pygame.draw.rect(self.screen, C_BT_RING,
                         pygame.Rect(px, legend_y + 2, 12, 12), width=2, border_radius=3)
        draw_text(self.screen, self.font_sm, "Backtracking (quarantine)", px + 18, legend_y, C_TEXT_DIM)

    def _draw_particles(self):
        # draw all active particles
        for p in self.particles:
            p.draw(self.screen)

    def _draw_toasts(self):
        # draw notification messages near the top of the grid
        y = GRID_Y - 30
        for toast in self.toasts:
            toast.draw(self.screen, self.font_md, y)
            y -= 22

    def _draw_endscreen(self):
        # draw win or lose overlay when the game ends
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        if self.state.status == "win":
            msg   = "PLAGUE CONTAINED!"
            color = C_WIN
            sub   = "The city is safe."
        else:
            msg   = "CITY INFECTED!"
            color = C_LOSE
            sub   = "The plague won. Game over."
        draw_text_center(self.screen, self.font_xl, msg,
                         WINDOW_W // 2, WINDOW_H // 2 - 30, color)
        draw_text_center(self.screen, self.font_lg, sub,
                         WINDOW_W // 2, WINDOW_H // 2 + 20, C_TEXT)
        draw_text_center(self.screen, self.font_md, "Press ESC to exit",
                         WINDOW_W // 2, WINDOW_H // 2 + 60, C_TEXT_DIM)

    def run(self):
        print("[UI] Starting Pygame interface...")
        print(f"[UI] state.json  -> {STATE_PATH}")
        print(f"[UI] result.json -> {RESULT_PATH}")
        print(f"[UI] action.json -> {ACTION_PATH}")

        self._run_algorithms()

        last_mtime = 0
        running = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.tick += dt

            try:
                mtime = os.path.getmtime(STATE_PATH)
                if mtime != last_mtime and (self.tick - getattr(self, '_last_reload_tick', 0)) > 0.5:
                    last_mtime = mtime
                    self._last_reload_tick = self.tick
                    self.state.load(STATE_PATH)
                    self._spawn_particles()
                    self._run_algorithms()
                    self.action_taken = False
            except:
                pass

            self.particles = [p for p in self.particles if p.update()]
            self.toasts = [t for t in self.toasts if t.update(dt)]

            running = self.handle_events()

            self.draw()

        pygame.quit()
        print("[UI] Interface closed.")


if __name__ == "__main__":
    app = PlagueUI()
    app.run()
