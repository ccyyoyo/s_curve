# Motion Profile Generator

This project generates and visualizes motion profiles using S-curve acceleration. It allows users to input parameters such as distance, maximum speed, maximum acceleration, and maximum jerk, and then plots the resulting motion profile.

## Project Structure

```
motion-profile-generator
├── src
│   ├── main.py          # Entry point of the application
│   ├── models
│   │   ├── __init__.py  # Initializes the models package
│   │   └── s_curve.py   # Contains the SCurve class for motion profile calculations
│   ├── utils
│   │   ├── __init__.py  # Initializes the utils package
│   │   └── plotter.py    # Contains the plot_motion function for visualizing profiles
│   └── ui
│       ├── __init__.py  # Initializes the ui package
│       └── interface.py  # Contains the UserInterface class for user interaction
├── requirements.txt      # Lists the project dependencies
└── README.md             # Project documentation
```

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

1. Run the application:

```
python src/main.py
```

2. Input the desired parameters for distance, maximum speed, maximum acceleration, and maximum jerk in the user interface.
3. Click the button to generate and plot the motion profile.

## License

This project is licensed under the MIT License.