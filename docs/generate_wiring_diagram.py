#!/usr/bin/env python3
"""
eBike wiring diagram: Component specs at top, simplified schematic below with PDB as single unit.
"""

import pygame
from typing import List, Tuple

WIDTH, HEIGHT = 1600, 1400
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (30, 30, 30)
BOX_BG = (245, 245, 245)
BOX_BORDER = (100, 100, 100)
PDB_BORDER = (200, 50, 50)
CALLOUT_BG = (255, 250, 220)

class SpecBox:
    """Component specification box."""
    def __init__(self, title: str, specs: List[str], x: int, y: int, w: int = 140, h: int = 95):
        self.title = title
        self.specs = specs
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, title_font, spec_font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, BOX_BG, rect)
        pygame.draw.rect(surface, BOX_BORDER, rect, width=1)

        title_text = title_font.render(self.title, True, TEXT_COLOR)
        surface.blit(title_text, (self.x + 5, self.y + 4))

        y_offset = self.y + 22
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 5, y_offset))
            y_offset += 13

class ComponentBox:
    """Simple component box for schematic."""
    def __init__(self, label: str, x: int, y: int, w: int = 70, h: int = 50):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, BOX_BG, rect)
        pygame.draw.rect(surface, BOX_BORDER, rect, width=2)
        text = font.render(self.label, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(self.x + self.w//2, self.y + self.h//2))
        surface.blit(text, text_rect)

    def center(self) -> Tuple[int, int]:
        return (self.x + self.w//2, self.y + self.h//2)

    def right(self) -> int:
        return self.x + self.w

    def left(self) -> int:
        return self.x

class PowerDistributionBoard:
    """Compound component wrapping internal distribution."""
    def __init__(self, x: int, y: int, w: int = 280, h: int = 150):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, (250, 250, 200), rect)
        pygame.draw.rect(surface, PDB_BORDER, rect, width=3)

        # Label
        label = font.render("Power Distribution Board", True, PDB_BORDER)
        label_rect = label.get_rect(center=(self.x + self.w//2, self.y - 12))
        surface.blit(label, label_rect)

    def center(self) -> Tuple[int, int]:
        return (self.x + self.w//2, self.y + self.h//2)

    def input_top(self) -> Tuple[int, int]:
        return (self.x + self.w//4, self.y)

    def input_bottom(self) -> Tuple[int, int]:
        return (self.x + self.w//4, self.y + self.h)

    def output_top(self) -> Tuple[int, int]:
        return (self.x + 3*self.w//4, self.y)

    def output_bottom(self) -> Tuple[int, int]:
        return (self.x + 3*self.w//4, self.y + self.h)

class ConductorCallout:
    """Callout for conductor specs with leader line."""
    def __init__(self, x: int, y: int, specs: List[str], leader_from: Tuple[int, int]):
        self.x = x
        self.y = y
        self.specs = specs
        self.leader_x, self.leader_y = leader_from
        self.w = 200
        self.h = 70

    def draw(self, surface, font):
        # Callout box
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, CALLOUT_BG, rect)
        pygame.draw.rect(surface, (180, 140, 80), rect, width=1)

        # Leader line
        pygame.draw.line(surface, (180, 140, 80), (self.leader_x, self.leader_y),
                        (self.x + 10, self.y + 10), width=1)

        # Text
        y_offset = self.y + 5
        for spec in self.specs:
            text = font.render(spec, True, TEXT_COLOR)
            surface.blit(text, (self.x + 5, y_offset))
            y_offset += 14

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Power Distribution - Complete Wiring Diagram")

    font_title = pygame.font.SysFont("arial", 24, bold=True)
    font_spec_title = pygame.font.SysFont("arial", 10, bold=True)
    font_spec = pygame.font.SysFont("arial", 9)
    font_component = pygame.font.SysFont("arial", 12, bold=True)
    font_conductor = pygame.font.SysFont("arial", 8)

    screen.fill(BG_COLOR)

    # Title
    title = font_title.render("eBike Dual-Motor Dual-Battery Power Distribution System", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))

    # ===== TOP SECTION: COMPONENT SPECS =====
    spec_y = 50

    specs_row1 = [
        SpecBox("Battery A", ["48V 20Ah", "LiFePO4", "SoC Monitor"], 30, spec_y),
        SpecBox("Fuse A", ["80A ANL", "2 AWG", "PVC conduit"], 190, spec_y),
        SpecBox("Contactor A", ["24V 40A", "Relay", "SoC control"], 350, spec_y),
        SpecBox("Power Bus", ["48V common", "Copper", "Busbar"], 510, spec_y),
        SpecBox("Buck F", ["48V 30A", "0-48V PWM", "CC mode"], 670, spec_y),
        SpecBox("Motor F", ["750W hub", "INA226 sense", "Current FB"], 830, spec_y),
        SpecBox("Wire Ratings", ["B-F: 2x#12", "F-C: 2x#12", "C-Bus: 4x#12"], 990, spec_y),
    ]

    specs_row2 = [
        SpecBox("Battery B", ["48V 20Ah", "LiFePO4", "SoC Monitor"], 30, spec_y + 110),
        SpecBox("Fuse B", ["80A ANL", "2 AWG", "PVC conduit"], 190, spec_y + 110),
        SpecBox("Contactor B", ["24V 40A", "Relay", "SoC control"], 350, spec_y + 110),
        SpecBox("Bus Return", ["Common GND", "Ground plane", "Shared"], 510, spec_y + 110),
        SpecBox("Buck R", ["48V 30A", "0-48V PWM", "CC mode"], 670, spec_y + 110),
        SpecBox("Motor R", ["750W hub", "INA226 sense", "Current FB"], 830, spec_y + 110),
        SpecBox("Signal Lines", ["2x#24 shield", "Data cable", "Liquid-tight"], 990, spec_y + 110),
    ]

    for spec in specs_row1 + specs_row2:
        spec.draw(screen, font_spec_title, font_spec)

    # ===== MIDDLE SECTION: SCHEMATIC WITH PDB =====
    schem_y = 300

    # Batteries
    batt_a = ComponentBox("Battery A", 100, schem_y, 80, 60)
    batt_b = ComponentBox("Battery B", 100, schem_y + 180, 80, 60)
    batt_a.draw(screen, font_component)
    batt_b.draw(screen, font_component)

    # Power Distribution Board (compound component)
    pdb = PowerDistributionBoard(350, schem_y + 30, 280, 150)
    pdb.draw(screen, font_spec_title)

    # Motors
    motor_f = ComponentBox("Motor F", 750, schem_y, 80, 60)
    motor_r = ComponentBox("Motor R", 750, schem_y + 180, 80, 60)
    motor_f.draw(screen, font_component)
    motor_r.draw(screen, font_component)

    # ===== CONNECTIONS (Lines only, no internal details) =====

    # Battery A to PDB input (top)
    line1_start = batt_a.center()
    line1_mid = (pdb.input_top()[0], line1_start[1])
    line1_end = pdb.input_top()
    pygame.draw.line(screen, LINE_COLOR, line1_start, line1_mid, width=2)
    pygame.draw.line(screen, LINE_COLOR, line1_mid, line1_end, width=2)

    # Battery B to PDB input (bottom)
    line2_start = batt_b.center()
    line2_mid = (pdb.input_bottom()[0], line2_start[1])
    line2_end = pdb.input_bottom()
    pygame.draw.line(screen, LINE_COLOR, line2_start, line2_mid, width=2)
    pygame.draw.line(screen, LINE_COLOR, line2_mid, line2_end, width=2)

    # PDB output (top) to Motor F
    line3_start = pdb.output_top()
    line3_mid = (motor_f.left(), line3_start[1])
    line3_end = motor_f.center()
    pygame.draw.line(screen, LINE_COLOR, line3_start, line3_mid, width=2)
    pygame.draw.line(screen, LINE_COLOR, line3_mid, line3_end, width=2)

    # PDB output (bottom) to Motor R
    line4_start = pdb.output_bottom()
    line4_mid = (motor_r.left(), line4_start[1])
    line4_end = motor_r.center()
    pygame.draw.line(screen, LINE_COLOR, line4_start, line4_mid, width=2)
    pygame.draw.line(screen, LINE_COLOR, line4_mid, line4_end, width=2)

    # ===== CONDUCTOR CALLOUTS WITH LEADER LINES =====
    conductor_specs = [
        ConductorCallout(250, 530, [
            "2x #12 THWN-2",
            "stranded Cu",
            "1x #14 solid Cu GND",
            "1/2\" non-metallic",
            "liquid-tight conduit"
        ], line1_mid),

        ConductorCallout(250, 700, [
            "2x #12 THWN-2",
            "stranded Cu",
            "1x #14 solid Cu GND",
            "1/2\" non-metallic",
            "liquid-tight conduit"
        ], line2_mid),

        ConductorCallout(900, 530, [
            "2x #12 THWN-2",
            "stranded Cu",
            "1x #14 solid Cu GND",
            "2x #24 Cu shielded",
            "data in 1/2\" conduit"
        ], line3_mid),

        ConductorCallout(900, 700, [
            "2x #12 THWN-2",
            "stranded Cu",
            "1x #14 solid Cu GND",
            "2x #24 Cu shielded",
            "data in 1/2\" conduit"
        ], line4_mid),
    ]

    for callout in conductor_specs:
        callout.draw(screen, font_conductor)

    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png (1600x1400)")

    pygame.quit()

if __name__ == "__main__":
    main()
