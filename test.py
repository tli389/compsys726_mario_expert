import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Define the size of the black background
height, width = 240, 300

# Create a black background
background = np.zeros((height, width), dtype=np.uint8)

# Define the rectangles for danger_of_enemy and danger_of_enemy_above
rectangles = [
    {"rect": (-33, -57, 100, 100), "color": "white", "label": "danger_of_enemy"},
    {"rect": (-13, 28, 50, 30), "color": "yellow", "label": "danger_of_enemy_above"},
]

# Plot the background
fig, ax = plt.subplots()
ax.imshow(background, cmap='gray')

# Add the rectangles
for r in rectangles:
    rect = patches.Rectangle(
        (r["rect"][0] + width // 2, height // 2 - r["rect"][1] - r["rect"][3]), 
        r["rect"][2], 
        r["rect"][3], 
        linewidth=1, 
        edgecolor=r["color"], 
        facecolor='none', 
        label=r["label"]
    )
    ax.add_patch(rect)

# Add legend
plt.legend()

# Display the plot
plt.show()
