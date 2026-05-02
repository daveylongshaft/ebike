#!/usr/bin/env python3
"""
Generate clean wiring diagram for eBike controller.
Simple layout: batteries left -> distribution center -> motors right
Detailed spec boxes separated below for clarity.
"""

import pygame
from typing import List

WIDTH, HEIGHT = 1400, 900
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (30, 30, 30)
COMPONENT_BG = (240, 240, 240)
SPEC_BOX_BG = (245, 245, 245)
SPEC_BOX_BORDER = (150, 150, 150)

class Box:
    """Simple component box."""
    def __init__(self, label: str, x: int, y: int, w: int = 60, h: int = 50):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, COMPONENT_BG, rect)
        pygame.draw.rect(surface, LINE_COLOR, rect, width=2)
        text = font.render(self.label, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(self.x + self.w//2, self.y + self.h//2))
        surface.blit(text, text_rect)

    def right(self):
        return self.x + self.w

    def left(self):
        return self.x

    def top(self):
        return self.y

    def bottom(self):
        return self.y + self.h

    def center(self):
        return (self.x + self.w//2, self.y + self.h//2)

class SpecBox:
    """Detailed specification box."""
    def __init__(self, title: str, specs: List[str], x: int, y: int):
        self.title = title
        self.specs = specs
        self.x = x
        self.y = y
        self.w = 160
        self.h = 100

    def draw(self, surface, title_font, spec_font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, SPEC_BOX_BG, rect)
        pygame.draw.rect(surface, SPEC_BOX_BORDER, rect, width=1)

        # Title
        title_text = title_font.render(self.title, True, TEXT_COLOR)
        surface.blit(title_text, (self.x + 8, self.y + 5))

        # Specs
        y_offset = self.y + 28
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 8, y_offset))
            y_offset += 16

def draw_line(surface, x1, y1, x2, y2, label: str = "", font = None):
    """Draw line between points with optional label."""
    pygame.draw.line(surface, LINE_COLOR, (x1, y1), (x2, y2), width=2)
    if label and font:
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        text = font.render(label, True, (100, 100, 100))
        surface.blit(text, (mid_x - 15, mid_y - 10))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Power Distribution - Clean Wiring Diagram")

    font_title = pygame.font.SysFont("arial", 24, bold=True)
    font_component = pygame.font.SysFont("arial", 14, bold=True)
    font_label = pygame.font.SysFont("arial", 11)
    font_spec_title = pygame.font.SysFont("arial", 10, bold=True)
    font_spec = pygame.font.SysFont("arial", 9)

    screen.fill(BG_COLOR)

    # Title
    title = font_title.render("eBike Dual-Motor Dual-Battery Power Distribution", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 15))

    # ===== TOP FLOW (Battery A Path) =====
    y_top = 80

    batt_a = Box("B-A", 50, y_top)
    fuse_a = Box("F-A", 150, y_top)
    cont_a = Box("C-A", 250, y_top)
    bus_top = Box("BUS", 380, y_top - 15)
    buck_f = Box("BK-F", 520, y_top)
    motor_f = Box("M-F", 650, y_top)

    for box in [batt_a, fuse_a, cont_a, bus_top, buck_f, motor_f]:
        box.draw(screen, font_component)

    # Lines top path
    draw_line(screen, batt_a.right(), batt_a.center()[1], fuse_a.left(), fuse_a.center()[1], "", font_label)
    draw_line(screen, fuse_a.right(), fuse_a.center()[1], cont_a.left(), cont_a.center()[1], "", font_label)
    draw_line(screen, cont_a.right(), cont_a.center()[1], bus_top.left(), bus_top.center()[1], "", font_label)
    draw_line(screen, bus_top.right(), bus_top.center()[1], buck_f.left(), buck_f.center()[1], "", font_label)
    draw_line(screen, buck_f.right(), buck_f.center()[1], motor_f.left(), motor_f.center()[1], "", font_label)

    # ===== BOTTOM FLOW (Battery B Path) =====
    y_bot = 280

    batt_b = Box("B-B", 50, y_bot)
    fuse_b = Box("F-B", 150, y_bot)
    cont_b = Box("C-B", 250, y_bot)
    bus_bot = Box("BUS", 380, y_bot - 15)
    buck_r = Box("BK-R", 520, y_bot)
    motor_r = Box("M-R", 650, y_bot)

    for box in [batt_b, fuse_b, cont_b, bus_bot, buck_r, motor_r]:
        box.draw(screen, font_component)

    # Lines bottom path
    draw_line(screen, batt_b.right(), batt_b.center()[1], fuse_b.left(), fuse_b.center()[1], "", font_label)
    draw_line(screen, fuse_b.right(), fuse_b.center()[1], cont_b.left(), cont_b.center()[1], "", font_label)
    draw_line(screen, cont_b.right(), cont_b.center()[1], bus_bot.left(), bus_bot.center()[1], "", font_label)
    draw_line(screen, bus_bot.right(), bus_bot.center()[1], buck_r.left(), buck_r.center()[1], "", font_label)
    draw_line(screen, buck_r.right(), buck_r.center()[1], motor_r.left(), motor_r.center()[1], "", font_label)

    # ===== SPECIFICATION BOXES =====
    specs_y = 480

    specs = [
        SpecBox("Battery A", ["48V 20Ah", "LiFePO4", "SoC Monitor"], 30, specs_y),
        SpecBox("Fuse A", ["80A ANL", "PVC conduit", "2 AWG"], 210, specs_y),
        SpecBox("Contactor A", ["24V 40A", "SoC control", "Switching"], 390, specs_y),
        SpecBox("Power Bus", ["48V common", "Copper busbar", "From both"], 560, specs_y),
        SpecBox("Buck F", ["48V 30A", "0-48V PWM", "CC mode"], 750, specs_y),
        SpecBox("Motor F", ["750W hub", "INA226 sense", "Current FB"], 920, specs_y),

        SpecBox("Battery B", ["48V 20Ah", "LiFePO4", "SoC Monitor"], 30, specs_y + 140),
        SpecBox("Fuse B", ["80A ANL", "PVC conduit", "2 AWG"], 210, specs_y + 140),
        SpecBox("Contactor B", ["24V 40A", "SoC control", "Switching"], 390, specs_y + 140),
        SpecBox("Bus Return", ["Common GND", "All grounds", "Shared plane"], 560, specs_y + 140),
        SpecBox("Buck R", ["48V 30A", "0-48V PWM", "CC mode"], 750, specs_y + 140),
        SpecBox("Motor R", ["750W hub", "INA226 sense", "Current FB"], 920, specs_y + 140),
    ]

    for spec in specs:
        spec.draw(screen, font_spec_title, font_spec)

    # Wire spec box (right side)
    wire_spec = SpecBox("Wire Ratings", [
        "B-to-F: 2 AWG 80A",
        "F-to-C: 2 AWG 80A",
        "C-to-Bus: 4 AWG 80A",
        "Bus-to-Buck: 4 AWG 50A",
        "Buck-to-Motor: 6 AWG 50A"
    ], 1130, 480)
    wire_spec.draw(screen, font_spec_title, font_spec)

    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png")

    pygame.quit()

if __name__ == "__main__":
    main()
