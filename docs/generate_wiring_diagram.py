#!/usr/bin/env python3
"""
Generate wiring diagram for eBike controller with detailed callout specs.
Uses pygame to draw:
- Batteries (left) -> Distribution (center) -> Motors (right)
- Horizontal flow with top/bottom rows for inputs/outputs
- Bottom half: Detailed callout balloons with wire/component specs

Usage:
    python generate_wiring_diagram.py

Output:
    wiring_diagram_detailed.png (1400x1000)
"""

import pygame
import sys
from typing import Tuple, List

# ===================================================================
# CONSTANTS
# ===================================================================

WIDTH, HEIGHT = 1400, 1000
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (40, 40, 40)
COMPONENT_COLOR = (200, 220, 255)
CONDUCTOR_COLOR = (200, 100, 50)
CALLOUT_COLOR = (255, 240, 200)
CALLOUT_BORDER = (200, 150, 50)

# Font sizes
TITLE_SIZE = 18
COMPONENT_SIZE = 12
LABEL_SIZE = 10
SMALL_SIZE = 8
CALLOUT_SIZE = 9

# Component dimensions
COMP_WIDTH = 80
COMP_HEIGHT = 50
BATTERY_WIDTH = 70
BATTERY_HEIGHT = 50

# Diagram zones
TOP_ROW_Y = 80
MIDDLE_ROW_Y = 250
BOTTOM_ROW_Y = 420

BATTERY_X = 50
MOTOR_X = 1250
CENTER_X = 700

# Callout zone
CALLOUT_TOP = 500

# ===================================================================
# COMPONENT CLASS
# ===================================================================

class Component:
    """Single-line schematic component box."""
    def __init__(self, name: str, model: str, x: int, y: int, width: int = COMP_WIDTH, height: int = COMP_HEIGHT):
        self.name = name
        self.model = model
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, surface: pygame.Surface, font_comp: pygame.font.Font, font_label: pygame.font.Font):
        """Draw component box and labels."""
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, COMPONENT_COLOR, rect, border_radius=4)
        pygame.draw.rect(surface, LINE_COLOR, rect, width=2, border_radius=4)

        # Name (bold, smaller)
        name_surf = font_comp.render(self.name, True, TEXT_COLOR)
        name_rect = name_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2 - 8))
        surface.blit(name_surf, name_rect)

        # Model (smaller, gray)
        model_surf = font_label.render(self.model, True, (80, 80, 80))
        model_rect = model_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2 + 12))
        surface.blit(model_surf, model_rect)

# ===================================================================
# CONDUCTOR CLASS
# ===================================================================

class Conductor:
    """Conductor line between components with optional circle marker."""
    def __init__(self, x1: int, y1: int, x2: int, y2: int, awg: str, amperage: str, voltage: str, conduit: str, label_id: str = ""):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.awg = awg
        self.amperage = amperage
        self.voltage = voltage
        self.conduit = conduit
        self.label_id = label_id

    def draw(self, surface: pygame.Surface, font_label: pygame.font.Font = None, font_small: pygame.font.Font = None):
        """Draw line only (specs in callout)."""
        pygame.draw.line(surface, CONDUCTOR_COLOR, (self.x1, self.y1), (self.x2, self.y2), width=2)

    def draw_circle(self, surface: pygame.Surface, radius: int = 8):
        """Draw circle around midpoint."""
        mid_x = (self.x1 + self.x2) // 2
        mid_y = (self.y1 + self.y2) // 2
        pygame.draw.circle(surface, CONDUCTOR_COLOR, (mid_x, mid_y), radius, width=2)

# ===================================================================
# CALLOUT CLASS
# ===================================================================

class Callout:
    """Spec callout balloon with optional leader line."""
    def __init__(self, x: int, y: int, text: List[str], leader_x: int = 0, leader_y: int = 0):
        self.x = x
        self.y = y
        self.text = text
        self.leader_x = leader_x
        self.leader_y = leader_y
        self.width = 200
        self.height = 80

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw balloon and leader line."""
        # Balloon box (rounded)
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.ellipse(surface, CALLOUT_COLOR, rect)
        pygame.draw.ellipse(surface, CALLOUT_BORDER, rect, width=2)

        # Leader line (pointer)
        if self.leader_x > 0:
            pygame.draw.line(surface, CALLOUT_BORDER, (self.leader_x, self.leader_y),
                           (self.x + 20, self.y + 20), width=1)

        # Text
        y_offset = self.y + 8
        for line in self.text:
            surf = font.render(line, True, TEXT_COLOR)
            surface.blit(surf, (self.x + 8, y_offset))
            y_offset += 18

# ===================================================================
# MAIN DIAGRAM
# ===================================================================

def create_wiring_diagram():
    """Build and render wiring diagram with batteries left, motors right, callouts below."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Dual-Motor Controller - Detailed Wiring Diagram")

    # Fonts
    font_title = pygame.font.SysFont("arial", TITLE_SIZE, bold=True)
    font_comp = pygame.font.SysFont("arial", COMPONENT_SIZE, bold=True)
    font_label = pygame.font.SysFont("arial", LABEL_SIZE)
    font_small = pygame.font.SysFont("arial", SMALL_SIZE)
    font_callout = pygame.font.SysFont("arial", CALLOUT_SIZE)

    # ===================================================================
    # COMPONENT DEFINITIONS - Left to Right Layout
    # ===================================================================

    # BATTERIES (left side, stacked vertically)
    batt_a = Component("Battery A", "48V 20Ah", BATTERY_X, TOP_ROW_Y, BATTERY_WIDTH, BATTERY_HEIGHT)
    batt_b = Component("Battery B", "48V 20Ah", BATTERY_X, BOTTOM_ROW_Y, BATTERY_WIDTH, BATTERY_HEIGHT)

    # DISTRIBUTION (center path)
    fuse_a = Component("Fuse A", "80A ANL", CENTER_X - 200, TOP_ROW_Y)
    fuse_b = Component("Fuse B", "80A ANL", CENTER_X - 200, BOTTOM_ROW_Y)
    cont_a = Component("Cont A", "24V 40A", CENTER_X - 100, TOP_ROW_Y)
    cont_b = Component("Cont B", "24V 40A", CENTER_X - 100, BOTTOM_ROW_Y)
    bus = Component("Power Bus", "48V Busbar", CENTER_X + 50, MIDDLE_ROW_Y - 20, COMP_WIDTH + 20, COMP_HEIGHT)
    buck_f = Component("Buck F", "0-48V PWM", CENTER_X + 150, TOP_ROW_Y)
    buck_r = Component("Buck R", "0-48V PWM", CENTER_X + 150, BOTTOM_ROW_Y)

    # MOTORS (right side, outputs)
    motor_f = Component("Motor F", "750W Hub", MOTOR_X, TOP_ROW_Y, BATTERY_WIDTH, BATTERY_HEIGHT)
    motor_r = Component("Motor R", "750W Hub", MOTOR_X, BOTTOM_ROW_Y, BATTERY_WIDTH, BATTERY_HEIGHT)

    # CONTROL (reference)
    pico = Component("Pico W", "MCU+WiFi", CENTER_X - 50, 20, 100, 40)
    lcd = Component("LCD", "20x4 I2C", CENTER_X + 70, 20, 80, 40)

    # ===================================================================
    # CONDUCTOR CONNECTIONS (simple lines, specs in callouts)
    # ===================================================================

    conductors = []

    # Battery A -> Fuse A -> Contactor A -> Bus
    c1 = Conductor(batt_a.x + BATTERY_WIDTH // 2, batt_a.y + BATTERY_HEIGHT,
                   fuse_a.x + COMP_WIDTH // 2, fuse_a.y, "2 AWG", "80A", "48V DC", "Insulation", "c1")
    c2 = Conductor(fuse_a.x + COMP_WIDTH // 2, fuse_a.y + COMP_HEIGHT,
                   cont_a.x + COMP_WIDTH // 2, cont_a.y, "2 AWG", "80A", "48V DC", "Conduit", "c2")
    c3 = Conductor(cont_a.x + COMP_WIDTH // 2, cont_a.y + COMP_HEIGHT,
                   bus.x + COMP_WIDTH // 2 - 30, bus.y + COMP_HEIGHT // 2, "4 AWG", "80A", "48V DC", "Busbar", "c3")
    conductors.extend([c1, c2, c3])

    # Battery B -> Fuse B -> Contactor B -> Bus
    c4 = Conductor(batt_b.x + BATTERY_WIDTH // 2, batt_b.y,
                   fuse_b.x + COMP_WIDTH // 2, fuse_b.y, "2 AWG", "80A", "48V DC", "Insulation", "c4")
    c5 = Conductor(fuse_b.x + COMP_WIDTH // 2, fuse_b.y - COMP_HEIGHT,
                   cont_b.x + COMP_WIDTH // 2, cont_b.y, "2 AWG", "80A", "48V DC", "Conduit", "c5")
    c6 = Conductor(cont_b.x + COMP_WIDTH // 2, cont_b.y - COMP_HEIGHT,
                   bus.x + COMP_WIDTH // 2 + 30, bus.y + COMP_HEIGHT // 2, "4 AWG", "80A", "48V DC", "Busbar", "c6")
    conductors.extend([c4, c5, c6])

    # Bus -> Buck Converters -> Motors
    c7 = Conductor(bus.x + COMP_WIDTH // 2 - 30, bus.y,
                   buck_f.x + COMP_WIDTH // 2, buck_f.y + COMP_HEIGHT, "4 AWG", "50A", "48V DC", "Conduit", "c7")
    c8 = Conductor(buck_f.x + COMP_WIDTH // 2, buck_f.y,
                   motor_f.x, motor_f.y + BATTERY_HEIGHT // 2, "6 AWG", "50A", "PWM", "Silicone", "c8")
    conductors.extend([c7, c8])

    c9 = Conductor(bus.x + COMP_WIDTH // 2 + 30, bus.y,
                   buck_r.x + COMP_WIDTH // 2, buck_r.y - COMP_HEIGHT, "4 AWG", "50A", "48V DC", "Conduit", "c9")
    c10 = Conductor(buck_r.x + COMP_WIDTH // 2, buck_r.y,
                    motor_r.x, motor_r.y + BATTERY_HEIGHT // 2, "6 AWG", "50A", "PWM", "Silicone", "c10")
    conductors.extend([c9, c10])

    # ===================================================================
    # CALLOUT SPECS (bottom half with leaders and balloons)
    # ===================================================================

    callouts = [
        Callout(50, CALLOUT_TOP, ["Battery Input:", "2 AWG 80A max", "48V DC", "Insulated"], 160, 130),
        Callout(280, CALLOUT_TOP, ["Fuse to Cont:", "2 AWG 80A max", "48V DC", "PVC conduit"], 390, 230),
        Callout(510, CALLOUT_TOP, ["Cont to Bus:", "4 AWG 80A max", "48V DC", "Copper"], 600, 300),
        Callout(740, CALLOUT_TOP, ["Bus to Buck:", "4 AWG 50A max", "48V DC", "Conduit"], 860, 300),
        Callout(970, CALLOUT_TOP, ["Buck to Motor:", "6 AWG 50A max", "0-48V PWM", "Silicone"], 1150, 130),

        Callout(50, CALLOUT_TOP + 150, ["Battery Pack", "48V 20Ah", "LiFePO4", "SoC Monitor"], 0, 0),
        Callout(280, CALLOUT_TOP + 150, ["80A Fuse", "ANL Holder", "Both Channels", "Circuit Protect"], 0, 0),
        Callout(510, CALLOUT_TOP + 150, ["Contactor", "24V 40A Relay", "SoC Control", "Switching"], 0, 0),
        Callout(740, CALLOUT_TOP + 150, ["PWM Buck", "48V 30A Conv", "0-48V Adjust", "CC Mode"], 0, 0),
        Callout(970, CALLOUT_TOP + 150, ["Hub Motor", "750W nom", "INA226 sense", "Current feedback"], 0, 0),
    ]

    # ===================================================================
    # RENDER AND SAVE
    # ===================================================================

    screen.fill(BG_COLOR)

    # Title
    title_surf = font_title.render("eBike Dual-Motor Dual-Battery Power Distribution", True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 10))
    screen.blit(title_surf, title_rect)

    # Draw conductors (lines only, specs in callouts)
    for conductor in conductors:
        conductor.draw(screen)

    # Draw circles around wire segments (every other conductor)
    for i, conductor in enumerate(conductors):
        if i % 2 == 0:
            conductor.draw_circle(screen, 8)

    # Draw all components
    for comp in [batt_a, batt_b, fuse_a, fuse_b, cont_a, cont_b, bus, buck_f, buck_r, motor_f, motor_r, pico, lcd]:
        comp.draw(screen, font_comp, font_label)

    # Draw callout balloons with spec details
    for callout in callouts:
        callout.draw(screen, font_callout)

    # Separator line
    separator_y = CALLOUT_TOP - 25
    pygame.draw.line(screen, (150, 150, 150), (40, separator_y), (WIDTH - 40, separator_y), width=1)

    # Footer
    footer = font_small.render("All components: Commercial NRTL-licensed | Conductors: AWG rated for temp and current | Specifications subject to load verification", True, (80, 80, 80))
    footer_rect = footer.get_rect(center=(WIDTH // 2, HEIGHT - 15))
    screen.blit(footer, footer_rect)

    # Save PNG
    pygame.image.save(screen, "wiring_diagram_detailed.png")
    print("[OK] Saved: wiring_diagram_detailed.png (1400x1000)")

    pygame.quit()


if __name__ == "__main__":
    create_wiring_diagram()
