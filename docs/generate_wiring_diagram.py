#!/usr/bin/env python3
"""
eBike wiring diagram: Top row components, bottom row conductor specs, vertical leaders.
"""

import pygame
from typing import List, Tuple

WIDTH, HEIGHT = 1600, 900
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (0, 0, 0)
COMP_BG = (220, 220, 255)
COMP_BORDER = (50, 50, 150)
PDB_BG = (255, 250, 180)
PDB_BORDER = (200, 100, 50)
WIRE_BG = (240, 240, 240)
WIRE_BORDER = (100, 100, 100)

class ComponentBox:
    """Component specification box."""
    def __init__(self, label: str, specs: List[str], x: int, y: int, w: int = 100, h: int = 80, is_pdb: bool = False):
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
        label_rect = label_text.get_rect(center=(self.x + self.w//2, self.y + 6))
        surface.blit(label_text, label_rect)

        # Specs
        y_offset = self.y + 22
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 3, y_offset))
            y_offset += 11

    def center_x(self) -> int:
        return self.x + self.w // 2

    def right(self) -> int:
        return self.x + self.w

    def center_y(self) -> int:
        return self.y + self.h // 2

    def bottom(self) -> int:
        return self.y + self.h

class WireSpecBox:
    """Wire/conductor specification box (bottom row)."""
    def __init__(self, specs: List[str], x: int, y: int, w: int = 100, h: int = 90):
        self.specs = specs
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, surface, spec_font):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, WIRE_BG, rect)
        pygame.draw.rect(surface, WIRE_BORDER, rect, width=1)

        y_offset = self.y + 4
        for spec in self.specs:
            spec_text = spec_font.render(spec, True, TEXT_COLOR)
            surface.blit(spec_text, (self.x + 3, y_offset))
            y_offset += 11

    def center_x(self) -> int:
        return self.x + self.w // 2

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Power Distribution - Component & Conductor Flow")

    font_title = pygame.font.SysFont("arial", 18, bold=True)
    font_label = pygame.font.SysFont("arial", 10, bold=True)
    font_spec = pygame.font.SysFont("arial", 7)

    screen.fill(BG_COLOR)

    # Title
    title = font_title.render("eBike Power Distribution - Left to Right Verification", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))

    # ===== TOP ROW: COMPONENTS (Battery A Path) =====
    top_y = 40

    comps_a = [
        ComponentBox("Battery A", ["48V 20Ah", "LiFePO4", "SoC"], 50, top_y, 90, 80),
        ComponentBox("Fuse A", ["80A ANL", "2 AWG"], 180, top_y, 90, 80),
        ComponentBox("PDB", ["Contactors", "Bus", "Buck Conv"], 310, top_y, 130, 80, is_pdb=True),
        ComponentBox("Motor F", ["750W hub", "INA226"], 490, top_y, 90, 80),
        ComponentBox("Controller", ["Pico W", "WiFi"], 620, top_y, 90, 80),
    ]

    for comp in comps_a:
        comp.draw(screen, font_label, font_spec)

    # Draw horizontal conductor lines between components
    for i in range(len(comps_a) - 1):
        x1 = comps_a[i].right()
        x2 = comps_a[i+1].x
        y = comps_a[i].center_y()

        # Horizontal line
        pygame.draw.line(screen, LINE_COLOR, (x1, y), (x2, y), width=2)

        # Circle on the conductor line (midpoint)
        circle_x = (x1 + x2) // 2
        pygame.draw.circle(screen, LINE_COLOR, (circle_x, y), 6, width=2)

    # ===== VERTICAL LEADERS AND BOTTOM ROW: WIRE SPECS =====
    bottom_y = 280

    wire_specs_a = [
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "2x #24 shld", "1/2\" conduit"],
    ]

    # Position wire spec boxes between components
    wire_box_x_positions = []
    for i in range(len(comps_a) - 1):
        x1 = comps_a[i].right()
        x2 = comps_a[i+1].x
        mid_x = (x1 + x2) // 2
        wire_box_x_positions.append(mid_x - 50)  # Center the box on the midpoint

    for i, specs in enumerate(wire_specs_a):
        wire_box = WireSpecBox(specs, wire_box_x_positions[i], bottom_y, 100, 90)
        wire_box.draw(screen, font_spec)

        # Draw vertical leader line from conductor to wire spec box
        circle_x = (comps_a[i].right() + comps_a[i+1].x) // 2
        circle_y = comps_a[i].center_y()
        leader_top_y = comps_a[i].bottom() + 30
        leader_bottom_y = bottom_y

        pygame.draw.line(screen, LINE_COLOR, (circle_x, leader_top_y), (circle_x, leader_bottom_y), width=1)

    # ===== BOTTOM SECTION: BATTERY B PATH =====
    path_b_y = 500

    comps_b = [
        ComponentBox("Battery B", ["48V 20Ah", "LiFePO4", "SoC"], 50, path_b_y, 90, 80),
        ComponentBox("Fuse B", ["80A ANL", "2 AWG"], 180, path_b_y, 90, 80),
        ComponentBox("PDB", ["(shared)", "from path A"], 310, path_b_y, 130, 80, is_pdb=True),
        ComponentBox("Motor R", ["750W hub", "INA226"], 490, path_b_y, 90, 80),
        ComponentBox("Lights/UI", ["Turn sig", "Status LED"], 620, path_b_y, 90, 80),
    ]

    for comp in comps_b:
        comp.draw(screen, font_label, font_spec)

    # Draw horizontal conductor lines for path B
    for i in range(len(comps_b) - 1):
        x1 = comps_b[i].right()
        x2 = comps_b[i+1].x
        y = comps_b[i].center_y()

        pygame.draw.line(screen, LINE_COLOR, (x1, y), (x2, y), width=2)
        circle_x = (x1 + x2) // 2
        pygame.draw.circle(screen, LINE_COLOR, (circle_x, y), 6, width=2)

    # Wire specs for path B
    wire_specs_b = [
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #18 twisted", "pair shielded", "in 1/4\" conduit", ""],
    ]

    bottom_b_y = path_b_y + 280

    for i, specs in enumerate(wire_specs_b):
        wire_box = WireSpecBox(specs, wire_box_x_positions[i], bottom_b_y, 100, 90)
        wire_box.draw(screen, font_spec)

        # Vertical leader lines
        circle_x = (comps_b[i].right() + comps_b[i+1].x) // 2
        circle_y = comps_b[i].center_y()
        leader_top_y = comps_b[i].bottom() + 30
        leader_bottom_y = bottom_b_y

        pygame.draw.line(screen, LINE_COLOR, (circle_x, leader_top_y), (circle_x, leader_bottom_y), width=1)

    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png (1600x900)")

    pygame.quit()

if __name__ == "__main__":
    main()
