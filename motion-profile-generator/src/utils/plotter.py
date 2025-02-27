def plot_motion(distance_data, speed_data, acceleration_data, jerk_data):
    import matplotlib.pyplot as plt

    # Create subplots
    fig, axs = plt.subplots(4, 1, figsize=(10, 12))

    # Plot distance
    axs[0].plot(distance_data, label='Distance', color='blue')
    axs[0].set_title('Distance vs Time')
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('Distance')
    axs[0].legend()
    axs[0].grid()

    # Plot speed
    axs[1].plot(speed_data, label='Speed', color='orange')
    axs[1].set_title('Speed vs Time')
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('Speed')
    axs[1].legend()
    axs[1].grid()

    # Plot acceleration
    axs[2].plot(acceleration_data, label='Acceleration', color='green')
    axs[2].set_title('Acceleration vs Time')
    axs[2].set_xlabel('Time')
    axs[2].set_ylabel('Acceleration')
    axs[2].legend()
    axs[2].grid()

    # Plot jerk
    axs[3].plot(jerk_data, label='Jerk', color='red')
    axs[3].set_title('Jerk vs Time')
    axs[3].set_xlabel('Time')
    axs[3].set_ylabel('Jerk')
    axs[3].legend()
    axs[3].grid()

    # Adjust layout
    plt.tight_layout()
    plt.show()