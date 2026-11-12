"""
Standard sizes of the furniture, fixture and stair library (no GUI dependencies; used by gui/object_library.py
and the web editor). Values: (display name, width in inches, depth in inches).
"""

from .geometry import FurnitureType, FixtureType, StairType

# Standard dimensions for furniture and fixtures (in inches)
FURNITURE_CATALOG = {
    # Beds
    FurnitureType.BED_SINGLE: ("Single Bed", 39, 75),
    FurnitureType.BED_DOUBLE: ("Double Bed", 54, 75),
    FurnitureType.BED_QUEEN: ("Queen Bed", 60, 80),
    FurnitureType.BED_KING: ("King Bed", 76, 80),
    
    # Seating
    FurnitureType.SOFA: ("Sofa", 84, 36),
    FurnitureType.LOVESEAT: ("Loveseat", 58, 36),
    FurnitureType.CHAIR: ("Chair", 24, 24),
    FurnitureType.ARMCHAIR: ("Armchair", 36, 36),
    
    # Tables
    FurnitureType.TABLE_DINING: ("Dining Table", 72, 36),
    FurnitureType.TABLE_COFFEE: ("Coffee Table", 48, 24),
    FurnitureType.TABLE_SIDE: ("Side Table", 24, 24),
    FurnitureType.DESK: ("Desk", 60, 30),
    
    # Storage
    FurnitureType.DRESSER: ("Dresser", 48, 18),
    FurnitureType.NIGHTSTAND: ("Nightstand", 24, 18),
    FurnitureType.BOOKSHELF: ("Bookshelf", 36, 12),
    FurnitureType.CABINET: ("Cabinet", 36, 24),
    FurnitureType.WARDROBE: ("Wardrobe", 48, 24),
    FurnitureType.TV_STAND: ("TV Stand", 60, 18),
}

FIXTURE_CATALOG = {
    # Bathroom
    FixtureType.TOILET: ("Toilet", 20, 30),
    FixtureType.SINK: ("Sink", 24, 20),
    FixtureType.SINK_DOUBLE: ("Double Sink", 60, 22),
    FixtureType.BATHTUB: ("Bathtub", 60, 32),
    FixtureType.SHOWER: ("Shower", 36, 36),
    FixtureType.SHOWER_CORNER: ("Corner Shower", 36, 36),
    FixtureType.VANITY: ("Vanity", 48, 22),
    
    # Kitchen
    FixtureType.REFRIGERATOR: ("Refrigerator", 36, 30),
    FixtureType.STOVE: ("Stove/Range", 30, 24),
    FixtureType.OVEN: ("Wall Oven", 30, 24),
    FixtureType.DISHWASHER: ("Dishwasher", 24, 24),
    FixtureType.MICROWAVE: ("Microwave", 30, 16),
    FixtureType.SINK_KITCHEN: ("Kitchen Sink", 33, 22),
    
    # Laundry
    FixtureType.WASHER: ("Washer", 27, 28),
    FixtureType.DRYER: ("Dryer", 27, 28),
    
    # HVAC
    FixtureType.WATER_HEATER: ("Water Heater", 24, 24),
    FixtureType.FURNACE: ("Furnace", 36, 30),
    FixtureType.AC_UNIT: ("AC Unit", 30, 30),
}

STAIR_CATALOG = {
    StairType.STRAIGHT: ("Straight Stair", 36, 120),
    StairType.L_SHAPED: ("L-Shaped Stair", 72, 72),
    StairType.U_SHAPED: ("U-Shaped Stair", 72, 120),
    StairType.WINDER: ("Winder Stair", 60, 60),
    StairType.SPIRAL: ("Spiral Stair", 60, 60),
    StairType.CURVED: ("Curved Stair", 72, 96),
}
