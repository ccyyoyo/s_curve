import tkinter as tk
from gui.profile_generator_gui import ProfileGeneratorGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfileGeneratorGUI(root)
    root.mainloop()