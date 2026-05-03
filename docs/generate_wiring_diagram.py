#!/usr/bin/env python3
"""
eBike wiring diagram: Single PDB spanning both battery paths, only callout Battery B conductors.
"""

import pygame
from typing import List, Tuple

WIDTH, HEIGHT = 1800, 900
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
    pygame.display.set_caption("eBike Power Distribution - Dual Battery Single PDB")

    font_title = pygame.font.SysFont("arial", 18, bold=True)
    font_label = pygame.font.SysFont("arial", 10, bold=True)
    font_spec = pygame.font.SysFont("arial", 7)
    font_small = pygame.font.SysFont("arial", 8)

    screen.fill(BG_COLOR)

    # Title
    title = font_title.render("eBike Power Distribution - Single PDB Architecture", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))

    # ===== TOP PATH: BATTERY A =====
    top_y = 40

    batt_a = ComponentBox("Battery A", ["48V 20Ah", "LiFePO4", "SoC"], 50, top_y, 90, 80)
    fuse_a = ComponentBox("Fuse A", ["80A ANL", "2 AWG"], 180, top_y, 90, 80)

    # Large PDB box spanning both rows
    pdb_y = 40
    pdb = ComponentBox("Power Distribution Board", [
        "Fuse/Contactor A,B",
        "Buck Converters F,R",
        "INA226 Sensors",
        "Control Logic"
    ], 350, pdb_y, 180, 280, is_pdb=True)

    motor_f = ComponentBox("Motor F", ["750W hub", "INA226"], 600, top_y, 90, 80)
    sensors = ComponentBox("Sensors/UI", ["LCD", "Buttons", "Throttle"], 730, top_y, 100, 80)

    # Draw top path components
    batt_a.draw(screen, font_label, font_spec)
    fuse_a.draw(screen, font_label, font_spec)
    pdb.draw(screen, font_label, font_spec)
    motor_f.draw(screen, font_label, font_spec)
    sensors.draw(screen, font_label, font_spec)

    # Draw conductors (top path A - no callouts)
    # Batt A to Fuse A
    pygame.draw.line(screen, LINE_COLOR, (batt_a.right(), batt_a.center_y()), (fuse_a.x, fuse_a.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, ((batt_a.right() + fuse_a.x)//2, batt_a.center_y()), 6, width=2)

    # Fuse A to PDB
    pygame.draw.line(screen, LINE_COLOR, (fuse_a.right(), fuse_a.center_y()), (pdb.x, pdb.y + 40), width=2)
    pygame.draw.circle(screen, LINE_COLOR, ((fuse_a.right() + pdb.x)//2, (fuse_a.center_y() + pdb.y + 40)//2), 6, width=2)

    # PDB to Motor F
    pygame.draw.line(screen, LINE_COLOR, (pdb.right(), pdb.y + 40), (motor_f.x, motor_f.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, ((pdb.right() + motor_f.x)//2, (pdb.y + 40 + motor_f.center_y())//2), 6, width=2)

    # Motor F to Sensors
    pygame.draw.line(screen, LINE_COLOR, (motor_f.right(), motor_f.center_y()), (sensors.x, sensors.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, ((motor_f.right() + sensors.x)//2, motor_f.center_y()), 6, width=2)

    # ===== BOTTOM PATH: BATTERY B =====
    bottom_y = 280

    batt_b = ComponentBox("Battery B", ["48V 20Ah", "LiFePO4", "SoC"], 50, bottom_y, 90, 80)
    fuse_b = ComponentBox("Fuse B", ["80A ANL", "2 AWG"], 180, bottom_y, 90, 80)

    motor_r = ComponentBox("Motor R", ["750W hub", "INA226"], 600, bottom_y, 90, 80)
    controller = ComponentBox("Controller", ["Pico W", "WiFi", "Logic"], 730, bottom_y, 100, 80)

    # Draw bottom path components
    batt_b.draw(screen, font_label, font_spec)
    fuse_b.draw(screen, font_label, font_spec)
    motor_r.draw(screen, font_label, font_spec)
    controller.draw(screen, font_label, font_spec)

    # Draw conductors (bottom path B - WITH callouts)
    # Batt B to Fuse B
    x_b_to_f = (batt_b.right() + fuse_b.x) // 2
    y_b_to_f = batt_b.center_y()
    pygame.draw.line(screen, LINE_COLOR, (batt_b.right(), batt_b.center_y()), (fuse_b.x, fuse_b.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, (x_b_to_f, y_b_to_f), 6, width=2)

    # Fuse B to PDB
    x_f_to_pdb = (fuse_b.right() + pdb.x) // 2
    y_f_to_pdb_line = fuse_b.center_y()
    pygame.draw.line(screen, LINE_COLOR, (fuse_b.right(), fuse_b.center_y()), (pdb.x, pdb.y + 240), width=2)
    pygame.draw.circle(screen, LINE_COLOR, (x_f_to_pdb, (fuse_b.center_y() + pdb.y + 240)//2), 6, width=2)

    # PDB to Motor R
    x_pdb_to_motor = (pdb.right() + motor_r.x) // 2
    y_pdb_to_motor = pdb.y + 240
    pygame.draw.line(screen, LINE_COLOR, (pdb.right(), pdb.y + 240), (motor_r.x, motor_r.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, (x_pdb_to_motor, (y_pdb_to_motor + motor_r.center_y())//2), 6, width=2)

    # Motor R to Controller
    x_motor_to_ctrl = (motor_r.right() + controller.x) // 2
    y_motor_to_ctrl = motor_r.center_y()
    pygame.draw.line(screen, LINE_COLOR, (motor_r.right(), motor_r.center_y()), (controller.x, controller.center_y()), width=2)
    pygame.draw.circle(screen, LINE_COLOR, (x_motor_to_ctrl, y_motor_to_ctrl), 6, width=2)

    # ===== CONDUCTOR CALLOUTS (Battery B path only) =====
    bottom_callout_y = 550

    wire_specs = [
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #12 THWN-2", "stranded Cu", "1x #14 Cu GND", "1/2\" conduit"],
        ["2x #18 twisted", "pair shielded", "in 1/4\" conduit", ""],
    ]

    # Position callouts below Battery B path
    callout_positions = [
        (x_b_to_f - 50, bottom_callout_y),
        (x_f_to_pdb - 50, bottom_callout_y),
        (x_pdb_to_motor - 50, bottom_callout_y),
        (x_motor_to_ctrl - 50, bottom_callout_y),
    ]

    for i, specs in enumerate(wire_specs):
        wire_box = WireSpecBox(specs, callout_positions[i][0], callout_positions[i][1], 100, 90)
        wire_box.draw(screen, font_spec)

        # Vertical leader line
        leader_x = callout_positions[i][0] + 50
        pygame.draw.line(screen, LINE_COLOR, (leader_x, bottom_callout_y - 80), (leader_x, bottom_callout_y), width=1)

    # Note: "typical of 2"
    note_text = font_small.render("(Typical of 2 - Path A identical)", True, (100, 100, 100))
    screen.blit(note_text, (50, bottom_callout_y + 110))

    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png (1800x900)")

    pygame.quit()

if __name__ == "__main__":
    main()
