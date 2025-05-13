import matplotlib.pyplot as plt
import numpy as np

# Your collected data (replace with actual values)
core_configs = [1, 2, 4, 8, 16, 32, 64]  # Number of cores used
runtimes = [546.2, 544.4, 303.1, 160.4, 98.2, 63.0, 42.0]

# Calculate speedup relative to 1-core
t1 = runtimes[0]  # Reference time (1-core)
speedup = [t1 / t for t in runtimes]

# Create figure
plt.figure(figsize=(10, 6))

# Plot empirical speedup
plt.plot(core_configs, speedup, 'bo-', label='Empirical Speedup', linewidth=2, markersize=8)

# Plot ideal linear speedup
ideal_speedup = core_configs
plt.plot(core_configs, ideal_speedup, 'r--', label='Ideal Speedup', linewidth=2)

# Customize plot
plt.xlabel('Number of Cores', fontsize=12)
plt.ylabel('Speedup (T₁/Tₙ)', fontsize=12)
plt.title('Empirical Speedup vs. Number of Cores', fontsize=14)
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.xticks(core_configs)
plt.xscale('log', base=2)
plt.yscale('log', base=2)
plt.legend()

# Annotate speedup values
for i, (n, s) in enumerate(zip(core_configs, speedup)):
    plt.annotate(f'{s:.1f}x', (n, s), textcoords="offset points", 
                 xytext=(0,10), ha='center', fontsize=9)

# Save and show plot
plt.tight_layout()
plt.savefig('scaling_analysis_climate_large.png', dpi=300)
plt.show()