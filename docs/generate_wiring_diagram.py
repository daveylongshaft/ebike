#!/usr/bin/env python3
"""
eBike wiring diagram: Left-to-right flow showing components and conductors.
Scan horizontally to verify ampacity, wire sizing, and component ratings.
"""

import pygame
from typing import List, Tuple

WIDTH, HEIGHT = 1800, 1000
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (30, 30, 30)
COMP_BG = (240, 240, 240)
COMP_BORDER = (100, 100, 100)
PDB_BG = (255, 250, 200)
PDB_BORDER = (200, 80, 80)
CONDUCTOR_BG = (230, 245, 255)
CONDUCTOR_BORDER = (100, 150, 200)

class ComponentBox:
    """Component specification box."""
    def __init__(self, label: str, specs: List[str], x: int, y: int, w: int = 120, h: int = 100, is_pdb: bool = False):
        self.label = label
        self.specs = specs
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_pdb = is_pdb

    def draw(self, surface, label_font, spec_font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        bg = PDB_BG if self.is_pdb else COMP_BG
        border = PDB_BORDER if self.is_pdb else COMP_BORDER

        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, border, rect, width=2)

        # Label
        label_text = label_font.render(self.label, True, TEXT_COLOR)
        label_rect = label_text.get_rect(center=(self.x + self.w//2, self.y + 8))
        surface.blit(label_text, label_rect)

        # Specs
        y_offset = self.y + 24
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 4, y_offset))
            y_offset += 12

    def right(self) -> int:
        return self.x + self.w

    def center_y(self) -> int:
        return self.y + self.h // 2

class ConductorBox:
    """Conductor callout with rounded corners."""
    def __init__(self, specs: List[str], x: int, y: int, w: int = 110, h: int = 100):
        self.specs = specs
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, spec_font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.ellipse(surface, CONDUCTOR_BG, rect)
        pygame.draw.ellipse(surface, CONDUCTOR_BORDER, rect, width=2)

        y_offset = self.y + 6
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 6, y_offset))
            y_offset += 13

    def center(self) -> Tuple[int, int]:
        return (self.x + self.w//2, self.y + self.h//2)

def draw_connection_line(surface, x1: int, y1: int, x2: int, y2: int):
    """Draw line between component and conductor boxes."""
    pygame.draw.line(surface, LINE_COLOR, (x1, y1), (x2, y2), width=2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Power Distribution - Left-to-Right Flow")

    font_title = pygame.font.SysFont("arial", 20, bold=True)
    font_label = pygame.font.SysFont("arial", 11, bold=True)
    font_spec = pygame.font.SysFont("arial", 8)

    screen.fill(BG_COLOR)

    # Title
    title = font_title.render("eBike Dual-Motor Dual-Battery Power Distribution - Verification Flow", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))

    subtitle = font_spec.render("Scan left-to-right to verify ampacity, wire sizing, and component ratings across the circuit", True, (80, 80, 80))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 32))

    # ===== BATTERY A PATH (top) =====
    y_path_a = 60
    x_start = 30

    # Components and conductors
    comp_a = ComponentBox("Battery A", ["48V 20Ah", "LiFePO4", "SoC"], x_start, y_path_a, 110, 95)
    cond_a1 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 130, y_path_a, 105, 95)

    fuse_a = ComponentBox("Fuse A", ["80A ANL", "2 AWG", "Inline"], x_start + 260, y_path_a, 110, 95)
    cond_a2 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 390, y_path_a, 105, 95)

    pdb = ComponentBox("Power Distribution Board", [
        "Contactors A/B",
        "Bus 48V",
        "Buck Conv F/R"
    ], x_start + 520, y_path_a, 160, 95, is_pdb=True)
    cond_a3 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 710, y_path_a, 105, 95)

    motor_f = ComponentBox("Motor F", ["750W hub", "INA226", "Current sense"], x_start + 840, y_path_a, 110, 95)
    cond_a4 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "2x #24 shield", "data"], x_start + 970, y_path_a, 105, 95)

    ctrl = ComponentBox("Controller", ["Pico W", "WiFi", "Logic"], x_start + 1100, y_path_a, 110, 95)

    # Draw path A
    for comp in [comp_a, fuse_a, pdb, motor_f, ctrl]:
        comp.draw(screen, font_label, font_spec)
    for cond in [cond_a1, cond_a2, cond_a3, cond_a4]:
        cond.draw(screen, font_spec)

    # Connection lines
    draw_connection_line(screen, comp_a.right(), comp_a.center_y(), cond_a1.x, cond_a1.y + cond_a1.h//2)
    draw_connection_line(screen, cond_a1.x + cond_a1.w, cond_a1.y + cond_a1.h//2, fuse_a.x, fuse_a.center_y())
    draw_connection_line(screen, fuse_a.right(), fuse_a.center_y(), cond_a2.x, cond_a2.y + cond_a2.h//2)
    draw_connection_line(screen, cond_a2.x + cond_a2.w, cond_a2.y + cond_a2.h//2, pdb.x, pdb.center_y())
    draw_connection_line(screen, pdb.right(), pdb.center_y(), cond_a3.x, cond_a3.y + cond_a3.h//2)
    draw_connection_line(screen, cond_a3.x + cond_a3.w, cond_a3.y + cond_a3.h//2, motor_f.x, motor_f.center_y())
    draw_connection_line(screen, motor_f.right(), motor_f.center_y(), cond_a4.x, cond_a4.y + cond_a4.h//2)
    draw_connection_line(screen, cond_a4.x + cond_a4.w, cond_a4.y + cond_a4.h//2, ctrl.x, ctrl.center_y())

    # ===== BATTERY B PATH (bottom) =====
    y_path_b = 500

    comp_b = ComponentBox("Battery B", ["48V 20Ah", "LiFePO4", "SoC"], x_start, y_path_b, 110, 95)
    cond_b1 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 130, y_path_b, 105, 95)

    fuse_b = ComponentBox("Fuse B", ["80A ANL", "2 AWG", "Inline"], x_start + 260, y_path_b, 110, 95)
    cond_b2 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 390, y_path_b, 105, 95)

    pdb_b_label = ComponentBox("(PDB shared)", ["Common", "Bus & Bucks", "from path A"], x_start + 520, y_path_b, 160, 95, is_pdb=True)
    cond_b3 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "1x #14 Cu", "GND"], x_start + 710, y_path_b, 105, 95)

    motor_r = ComponentBox("Motor R", ["750W hub", "INA226", "Current sense"], x_start + 840, y_path_b, 110, 95)
    cond_b4 = ConductorBox(["2x #12", "THWN-2", "stranded Cu", "2x #24 shield", "data"], x_start + 970, y_path_b, 105, 95)

    lights = ComponentBox("Lights/UI", ["Turn sig", "Brake LED", "Status"], x_start + 1100, y_path_b, 110, 95)

    # Draw path B
    for comp in [comp_b, fuse_b, pdb_b_label, motor_r, lights]:
        comp.draw(screen, font_label, font_spec)
    for cond in [cond_b1, cond_b2, cond_b3, cond_b4]:
        cond.draw(screen, font_spec)

    # Connection lines
    draw_connection_line(screen, comp_b.right(), comp_b.center_y(), cond_b1.x, cond_b1.y + cond_b1.h//2)
    draw_connection_line(screen, cond_b1.x + cond_b1.w, cond_b1.y + cond_b1.h//2, fuse_b.x, fuse_b.center_y())
    draw_connection_line(screen, fuse_b.right(), fuse_b.center_y(), cond_b2.x, cond_b2.y + cond_b2.h//2)
    draw_connection_line(screen, cond_b2.x + cond_b2.w, cond_b2.y + cond_b2.h//2, pdb_b_label.x, pdb_b_label.center_y())
    draw_connection_line(screen, pdb_b_label.right(), pdb_b_label.center_y(), cond_b3.x, cond_b3.y + cond_b3.h//2)
    draw_connection_line(screen, cond_b3.x + cond_b3.w, cond_b3.y + cond_b3.h//2, motor_r.x, motor_r.center_y())
    draw_connection_line(screen, motor_r.right(), motor_r.center_y(), cond_b4.x, cond_b4.y + cond_b4.h//2)
    draw_connection_line(screen, cond_b4.x + cond_b4.w, cond_b4.y + cond_b4.h//2, lights.x, lights.center_y())

    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png (1800x1000)")

    pygame.quit()

if __name__ == "__main__":
    main()
