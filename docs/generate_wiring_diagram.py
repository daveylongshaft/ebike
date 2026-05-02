#!/usr/bin/env python3
"""
Generate single-line wiring diagram for eBike controller.
Uses pygame to draw a clean schematic showing:
- Commercial NRTL-licensed components (named)
- Conductors with ratings (AWG, amperage, voltage)
- Conduits/covering requirements
- Flow from batteries through distribution to motors

Usage:
    python generate_wiring_diagram.py

Output:
    wiring_diagram_singleline.png (1024x768)
"""

import pygame
import sys
from typing import Tuple, List

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

WIDTH, HEIGHT = 1024, 768
FPS = 60
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
LINE_COLOR = (40, 40, 40)
COMPONENT_COLOR = (200, 220, 255)
CONDUCTOR_COLOR = (200, 100, 50)

# Font sizes
TITLE_SIZE = 20
COMPONENT_SIZE = 14
LABEL_SIZE = 11
SMALL_SIZE = 9

# Component dimensions
COMP_WIDTH = 100
COMP_HEIGHT = 60

# Spacing
PADDING = 40
COL_SPACING = 140
ROW_SPACING = 100

# ═══════════════════════════════════════════════════════════════
# COMPONENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════

class Component:
    """Single-line schematic component."""
    def __init__(self, name: str, model: str, x: int, y: int, width: int = COMP_WIDTH, height: int = COMP_HEIGHT):
        self.name = name              # e.g., "Battery Pack"
        self.model = model            # e.g., "48V 20Ah LiFePO4"
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface: pygame.Surface, font_comp: pygame.font.Font, font_label: pygame.font.Font):
        """Draw component box and label."""
        # Box
        pygame.draw.rect(surface, COMPONENT_COLOR, self.rect, border_radius=5)
        pygame.draw.rect(surface, LINE_COLOR, self.rect, width=2, border_radius=5)

        # Text (component name)
        name_surf = font_comp.render(self.name, True, TEXT_COLOR)
        name_rect = name_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2 - 8))
        surface.blit(name_surf, name_rect)

        # Model (smaller text below)
        model_surf = font_label.render(self.model, True, (80, 80, 80))
        model_rect = model_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2 + 12))
        surface.blit(model_surf, model_rect)

    def center(self) -> Tuple[int, int]:
        """Return center point of component."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class Conductor:
    """Connection between components with rating labels."""
    def __init__(self, x1: int, y1: int, x2: int, y2: int, awg: str, amperage: str, voltage: str, conduit: str):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.awg = awg                # e.g., "4 AWG"
        self.amperage = amperage      # e.g., "80A max"
        self.voltage = voltage        # e.g., "48V DC"
        self.conduit = conduit        # e.g., "PVC conduit"

    def draw(self, surface: pygame.Surface, font_label: pygame.font.Font, font_small: pygame.font.Font):
        """Draw line and label."""
        # Draw line
        pygame.draw.line(surface, CONDUCTOR_COLOR, (self.x1, self.y1), (self.x2, self.y2), width=3)

        # Midpoint for labels
        mid_x = (self.x1 + self.x2) // 2
        mid_y = (self.y1 + self.y2) // 2

        # Offset for labels (above and below line)
        offset = 15

        # AWG + Amperage (above)
        label1 = f"{self.awg} / {self.amperage}"
        surf1 = font_small.render(label1, True, CONDUCTOR_COLOR)
        rect1 = surf1.get_rect(center=(mid_x, mid_y - offset))
        surface.blit(surf1, rect1)

        # Voltage + Conduit (below)
        label2 = f"{self.voltage} | {self.conduit}"
        surf2 = font_small.render(label2, True, CONDUCTOR_COLOR)
        rect2 = surf2.get_rect(center=(mid_x, mid_y + offset))
        surface.blit(surf2, rect2)


# ═══════════════════════════════════════════════════════════════
# MAIN DIAGRAM
# ═══════════════════════════════════════════════════════════════

def create_wiring_diagram():
    """Build and render the single-line wiring diagram."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("eBike Dual-Motor Controller - Single-Line Wiring Diagram")
    clock = pygame.time.Clock()

    # Fonts
    font_title = pygame.font.SysFont("arial", TITLE_SIZE, bold=True)
    font_comp = pygame.font.SysFont("arial", COMPONENT_SIZE, bold=True)
    font_label = pygame.font.SysFont("arial", LABEL_SIZE)
    font_small = pygame.font.SysFont("arial", SMALL_SIZE)

    # ═══════════════════════════════════════════════════════════
    # COMPONENT DEFINITIONS (position on canvas)
    # ═══════════════════════════════════════════════════════════

    components = [
        # Row 1: Input (Batteries)
        Component("Battery Pack A", "48V 20Ah LiFePO4", PADDING, PADDING),
        Component("Battery Pack B", "48V 20Ah LiFePO4", PADDING + COL_SPACING * 2, PADDING),

        # Row 2: Input Protection
        Component("XT90-S Connector", "Antispark (A)", PADDING, PADDING + ROW_SPACING),
        Component("XT90-S Connector", "Antispark (B)", PADDING + COL_SPACING * 2, PADDING + ROW_SPACING),

        # Row 3: Main Fusing
        Component("80A Fuse + Holder", "ANL inline (A)", PADDING, PADDING + ROW_SPACING * 2),
        Component("80A Fuse + Holder", "ANL inline (B)", PADDING + COL_SPACING * 2, PADDING + ROW_SPACING * 2),

        # Row 4: Battery Contactors
        Component("24V Contactor Relay", "40A (Battery A)", PADDING, PADDING + ROW_SPACING * 3),
        Component("24V Contactor Relay", "40A (Battery B)", PADDING + COL_SPACING * 2, PADDING + ROW_SPACING * 3),

        # Row 5: Power Bus (combined)
        Component("Power Distribution Bus", "48V Common (Bussbar)", PADDING + COL_SPACING, PADDING + ROW_SPACING * 4),

        # Row 6: Current Sensing (Battery input monitoring)
        Component("INA226 Shunt (A)", "0x40 I2C module", PADDING - 20, PADDING + ROW_SPACING * 5),
        Component("INA226 Shunt (B)", "0x41 I2C module", PADDING + COL_SPACING * 2.5, PADDING + ROW_SPACING * 5),

        # Row 7: Motor Buck Converters
        Component("48V PWM Buck Conv", "0-48V Motor Front", PADDING, PADDING + ROW_SPACING * 6),
        Component("48V PWM Buck Conv", "0-48V Motor Rear", PADDING + COL_SPACING * 2, PADDING + ROW_SPACING * 6),

        # Row 8: Motor Current Sensing
        Component("INA226 Shunt (F)", "0x42 I2C module", PADDING - 20, PADDING + ROW_SPACING * 7),
        Component("INA226 Shunt (R)", "0x43 I2C module", PADDING + COL_SPACING * 2.5, PADDING + ROW_SPACING * 7),

        # Row 9: Motors (output)
        Component("Hub Motor", "Front 750W", PADDING, PADDING + ROW_SPACING * 8),
        Component("Hub Motor", "Rear 750W", PADDING + COL_SPACING * 2, PADDING + ROW_SPACING * 8),

        # Control Board (right side, for reference)
        Component("Pico W MCU", "RP2040 + WiFi/BT", WIDTH - PADDING - COMP_WIDTH, PADDING + ROW_SPACING * 3),
        Component("LCD 20x4", "I2C HD44780", WIDTH - PADDING - COMP_WIDTH, PADDING + ROW_SPACING * 5),
        Component("ULN2003 Driver", "Relay Darlington", WIDTH - PADDING - COMP_WIDTH, PADDING + ROW_SPACING * 6),
    ]

    # ═══════════════════════════════════════════════════════════
    # CONDUCTOR CONNECTIONS
    # ═══════════════════════════════════════════════════════════

    conductors = []

    # Battery A → XT90-S → Fuse → Contactor → Bus
    batt_a = components[0]
    xt90_a = components[2]
    fuse_a = components[4]
    cont_a = components[6]
    bus = components[8]

    conductors.append(Conductor(
        batt_a.x + batt_a.width // 2, batt_a.y + batt_a.height,
        xt90_a.x + xt90_a.width // 2, xt90_a.y,
        "2 AWG", "80A max", "48V DC", "Heavy-duty insulation"
    ))

    conductors.append(Conductor(
        xt90_a.x + xt90_a.width // 2, xt90_a.y + xt90_a.height,
        fuse_a.x + fuse_a.width // 2, fuse_a.y,
        "2 AWG", "80A max", "48V DC", "PVC conduit"
    ))

    conductors.append(Conductor(
        fuse_a.x + fuse_a.width // 2, fuse_a.y + fuse_a.height,
        cont_a.x + cont_a.width // 2, cont_a.y,
        "2 AWG", "80A max", "48V DC", "PVC conduit"
    ))

    conductors.append(Conductor(
        cont_a.x + cont_a.width // 2, cont_a.y + cont_a.height,
        bus.x + bus.width // 2 - 30, bus.y,
        "4 AWG", "80A max", "48V DC", "Copper busbar"
    ))

    # Battery B → XT90-S → Fuse → Contactor → Bus (right side)
    batt_b = components[1]
    xt90_b = components[3]
    fuse_b = components[5]
    cont_b = components[7]

    conductors.append(Conductor(
        batt_b.x + batt_b.width // 2, batt_b.y + batt_b.height,
        xt90_b.x + xt90_b.width // 2, xt90_b.y,
        "2 AWG", "80A max", "48V DC", "Heavy-duty insulation"
    ))

    conductors.append(Conductor(
        xt90_b.x + xt90_b.width // 2, xt90_b.y + xt90_b.height,
        fuse_b.x + fuse_b.width // 2, fuse_b.y,
        "2 AWG", "80A max", "48V DC", "PVC conduit"
    ))

    conductors.append(Conductor(
        fuse_b.x + fuse_b.width // 2, fuse_b.y + fuse_b.height,
        cont_b.x + cont_b.width // 2, cont_b.y,
        "2 AWG", "80A max", "48V DC", "PVC conduit"
    ))

    conductors.append(Conductor(
        cont_b.x + cont_b.width // 2, cont_b.y + cont_b.height,
        bus.x + bus.width // 2 + 30, bus.y,
        "4 AWG", "80A max", "48V DC", "Copper busbar"
    ))

    # Bus → Current sense (Battery A & B monitoring)
    ina_a = components[9]
    ina_b = components[10]

    conductors.append(Conductor(
        bus.x + bus.width // 2 - 30, bus.y + bus.height,
        ina_a.x + ina_a.width // 2, ina_a.y,
        "4 AWG", "80A max", "48V DC", "0.1Ω shunt"
    ))

    conductors.append(Conductor(
        bus.x + bus.width // 2 + 30, bus.y + bus.height,
        ina_b.x + ina_b.width // 2, ina_b.y,
        "4 AWG", "80A max", "48V DC", "0.1Ω shunt"
    ))

    # Sense outputs → Buck Converters (Motor control)
    buck_f = components[11]
    buck_r = components[12]

    conductors.append(Conductor(
        ina_a.x + ina_a.width // 2, ina_a.y + ina_a.height,
        buck_f.x + buck_f.width // 2, buck_f.y,
        "4 AWG", "50A max", "48V DC", "PVC conduit"
    ))

    conductors.append(Conductor(
        ina_b.x + ina_b.width // 2, ina_b.y + ina_b.height,
        buck_r.x + buck_r.width // 2, buck_r.y,
        "4 AWG", "50A max", "48V DC", "PVC conduit"
    ))

    # Buck outputs → Motor current sense → Motors
    ina_f = components[13]
    ina_r = components[14]
    motor_f = components[15]
    motor_r = components[16]

    conductors.append(Conductor(
        buck_f.x + buck_f.width // 2, buck_f.y + buck_f.height,
        ina_f.x + ina_f.width // 2, ina_f.y,
        "6 AWG", "50A max", "0-48V PWM", "0.1Ω shunt"
    ))

    conductors.append(Conductor(
        ina_f.x + ina_f.width // 2, ina_f.y + ina_f.height,
        motor_f.x + motor_f.width // 2, motor_f.y,
        "6 AWG", "50A max", "0-48V PWM", "Silicone insulation"
    ))

    conductors.append(Conductor(
        buck_r.x + buck_r.width // 2, buck_r.y + buck_r.height,
        ina_r.x + ina_r.width // 2, ina_r.y,
        "6 AWG", "50A max", "0-48V PWM", "0.1Ω shunt"
    ))

    conductors.append(Conductor(
        ina_r.x + ina_r.width // 2, ina_r.y + ina_r.height,
        motor_r.x + motor_r.width // 2, motor_r.y,
        "6 AWG", "50A max", "0-48V PWM", "Silicone insulation"
    ))

    # Control connections (I2C bus annotation on right)
    pico = components[17]
    lcd = components[18]
    driver = components[19]

    # Draw I2C bus indicator (dashed line, informational)
    i2c_y = PADDING + ROW_SPACING * 5
    pygame.draw.line(screen, (150, 150, 255), (WIDTH - PADDING - COMP_WIDTH - 30, i2c_y),
                     (WIDTH - PADDING - 30, i2c_y), width=2)

    # ═══════════════════════════════════════════════════════════
    # RENDER AND SAVE
    # ═══════════════════════════════════════════════════════════

    # Clear
    screen.fill(BG_COLOR)

    # Title
    title_surf = font_title.render("eBike Dual-Motor Controller - Single-Line Wiring Diagram", True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 15))
    screen.blit(title_surf, title_rect)

    # Subtitle with note
    subtitle_surf = font_label.render("Commercial NRTL-licensed components with conductor ratings and covering requirements", True, (80, 80, 80))
    subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 30))
    screen.blit(subtitle_surf, subtitle_rect)

    # Draw conductors first (so they appear behind components)
    for conductor in conductors:
        conductor.draw(screen, font_label, font_small)

    # Draw components
    for component in components:
        component.draw(screen, font_comp, font_label)

    # Draw I2C label
    i2c_label = font_small.render("I2C bus (all sensors + LCD)", True, (100, 100, 200))
    screen.blit(i2c_label, (WIDTH - PADDING - COMP_WIDTH - 150, PADDING + ROW_SPACING * 5 - 10))

    # Draw ground reference (bottom)
    ground_y = HEIGHT - PADDING
    pygame.draw.line(screen, LINE_COLOR, (PADDING, ground_y), (WIDTH - PADDING, ground_y), width=2)
    ground_label = font_small.render("Ground / Return (All components referenced to common GND plane)", True, (100, 100, 100))
    screen.blit(ground_label, (PADDING, ground_y + 10))

    # Conductors
    for conductor in conductors:
        conductor.draw(screen, font_label, font_small)

    # Components
    for component in components:
        component.draw(screen, font_comp, font_label)

    # I2C label
    i2c_label = font_small.render("I2C bus (all sensors + LCD)", True, (100, 100, 200))
    screen.blit(i2c_label, (WIDTH - PADDING - COMP_WIDTH - 150, PADDING + ROW_SPACING * 5 - 10))

    # Ground
    ground_y = HEIGHT - PADDING
    pygame.draw.line(screen, LINE_COLOR, (PADDING, ground_y), (WIDTH - PADDING, ground_y), width=2)
    ground_label = font_small.render("Ground / Return (All components referenced to common GND plane)", True, (100, 100, 100))
    screen.blit(ground_label, (PADDING, ground_y + 10))

    # Save
    pygame.image.save(screen, "wiring_diagram_singleline.png")
    print("[OK] Saved: wiring_diagram_singleline.png (1024x768)")

    pygame.quit()


if __name__ == "__main__":
    create_wiring_diagram()
