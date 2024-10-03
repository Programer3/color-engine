import colorsys as clrs
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

def rgb_to_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def rgb_to_hsl(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = clrs.rgb_to_hls(r, g, b)
    return (h * 360, s * 100, l * 100)

def hsl_to_rgb(hsl):
    h, s, l = hsl[0] / 360.0, hsl[1] / 100.0, hsl[2] / 100.0
    r, g, b = clrs.hls_to_rgb(h, l, s)
    return tuple(int(x * 255) for x in (r, g, b))

def get_contrast_ratio(rgb1, rgb2):
    def get_luminance(rgb):
        rgb = [x / 255.0 for x in rgb]
        rgb = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    
    l1, l2 = get_luminance(rgb1), get_luminance(rgb2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

def adjust_hsl(hsl, hue_shift=0, saturation_adjust=0, lightness_adjust=0):
    return ((hsl[0] + hue_shift) % 360, 
            max(0, min(100, hsl[1] + saturation_adjust)),
            max(0, min(100, hsl[2] + lightness_adjust)))

def generate_harmony_colors(base_hsl, harmony_type):
    base_hue = base_hsl[0]
    harmonies = {
        '1': [base_hue, (base_hue + 180) % 360],
        '2': [base_hue, (base_hue + 30) % 360, (base_hue - 30) % 360],
        '3': [base_hue, (base_hue + 120) % 360, (base_hue - 120) % 360],
        '4': [base_hue, (base_hue + 90) % 360, (base_hue + 180) % 360, (base_hue + 270) % 360],
    }
    
    return [(h, base_hsl[1], base_hsl[2]) for h in harmonies[harmony_type]]

def generate_palette(colors, mode='light', harmony='1', hue_shift=0, saturation_adjust=0, lightness_adjust=0):
    if isinstance(colors, str):
        colors = {'primary': colors}
    
    # Convert input colors to HSL
    hsl_colors = {k: rgb_to_hsl(hex_to_rgb(v)) for k, v in colors.items()}
    
    # Generate harmony colors if not all colors are provided
    if 'primary' in hsl_colors and len(hsl_colors) < 3:
        harmony_colors = generate_harmony_colors(hsl_colors['primary'], harmony)
        if 'secondary' not in hsl_colors:
            hsl_colors['secondary'] = harmony_colors[1]
        if 'tertiary' not in hsl_colors and len(harmony_colors) > 2:
            hsl_colors['tertiary'] = harmony_colors[2]
    
    # Apply adjustments
    hsl_colors = {k: adjust_hsl(v, hue_shift, saturation_adjust, lightness_adjust) for k, v in hsl_colors.items()}
    
    # Generate shades
    def generate_shades(color):
        return [
            adjust_hsl(color, lightness_adjust=-30),
            color,
            adjust_hsl(color, lightness_adjust=30)
        ]
    
    palette = {k: [rgb_to_hex(hsl_to_rgb(shade)) for shade in generate_shades(v)] 
               for k, v in hsl_colors.items()}
    
    # Generate semantic colors
    semantic_hues = {'error': 0, 'success': 120, 'info': 200, 'warning': 40}
    semantic_colors = {k: rgb_to_hex(hsl_to_rgb(adjust_hsl((h, 100, 50), hue_shift, saturation_adjust, lightness_adjust))) 
                       for k, h in semantic_hues.items()}
    palette['semantic'] = semantic_colors
    
    # Generate surface colors
    surface_lightness = 95 if mode == 'light' else 20
    on_surface_lightness = 10 if mode == 'light' else 90
    palette['surface'] = {
        'background': rgb_to_hex(hsl_to_rgb((0, 0, surface_lightness))),
        'onSurface': rgb_to_hex(hsl_to_rgb((0, 0, on_surface_lightness))),
        'onSurfaceVariant': rgb_to_hex(hsl_to_rgb((0, 0, 50))),
        'inverseOnSurface': rgb_to_hex(hsl_to_rgb((0, 0, 100 - on_surface_lightness))),
    }
    
    # Generate brand colors
    palette['brand'] = {
        'newPrimary': palette['primary'][1],
        'inversePrimary': rgb_to_hex(hsl_to_rgb(adjust_hsl(hsl_colors['primary'], hue_shift=180))),
        'newAccent': palette['secondary'][1] if 'secondary' in palette else palette['primary'][2],
    }
    
    return palette

def visualize_palette(palette):
    fig, axs = plt.subplots(len(palette), 1, figsize=(12, 3 * len(palette)))
    fig.suptitle("Color Palette")
    
    for i, (color_type, colors) in enumerate(palette.items()):
        if isinstance(colors, dict):
            axs[i].bar(range(len(colors)), [1] * len(colors), color=list(colors.values()))
            axs[i].set_xticks(range(len(colors)))
            axs[i].set_xticklabels(list(colors.keys()))
        else:
            axs[i].bar(range(len(colors)), [1] * len(colors), color=colors)
            axs[i].set_xticks(range(len(colors)))
            axs[i].set_xticklabels(colors)
        axs[i].set_title(color_type.capitalize())
    
    plt.tight_layout()
    return fig

def get_user_input(prompt, options=None):
    while True:
        user_input = input(prompt)
        if options and user_input not in options:
            print(f"Invalid input. Please choose from {options}")
        else:
            return user_input

def main():
    print("Welcome to the Interactive Color Palette Generator!")
    
    # Step 1: Choose input type
    input_type = get_user_input("Choose input type (1 for single seed color, 2 for multiple colors): ", ['1', '2'])
    
    if input_type == '1':
        seed_color = get_user_input("Enter seed color (hex format, e.g., #4287f5): ")
        colors = seed_color
    else:
        colors = {}
        for color_type in ['primary', 'secondary', 'tertiary']:
            color = get_user_input(f"Enter {color_type} color (hex format, or press Enter to skip): ")
            if color:
                colors[color_type] = color
    
    # Step 2: Choose mode
    mode = get_user_input("Choose mode (light/dark): ", ['light', 'dark'])
    
    # Step 3: Choose harmony
    harmony = get_user_input("Choose harmony (1.complementary|2.analogous|3.triadic|4.tetradic): ", 
                             ['1', '2', '3', '4'])
    
    # Step 4: Adjust colors
    hue_shift = int(get_user_input("Enter hue shift (-180 to 180): "))
    saturation_adjust = int(get_user_input("Enter saturation adjustment (-100 to 100): "))
    lightness_adjust = int(get_user_input("Enter lightness adjustment (-100 to 100): "))
    
    # Generate palette
    palette = generate_palette(colors, mode, harmony, hue_shift, saturation_adjust, lightness_adjust)
    
    # Visualize palette
    fig = visualize_palette(palette)
    
    # Save palette as PNG
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cEngine_opt_{current_datetime}.png"
    fig.savefig(filename)
    print(f"Palette saved as {filename}")
    
    # Print palette
    print("\nGenerated Palette:")
    for color_type, colors in palette.items():
        print(f"{color_type.capitalize()}:")
        if isinstance(colors, dict):
            for name, color in colors.items():
                print(f"  {name}: {color}")
        else:
            print(f"  {colors}")

if __name__ == "__main__":
    main()