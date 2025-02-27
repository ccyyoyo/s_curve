import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from models.s_curve import SCurve
from tkinter import messagebox
from tkinter import filedialog

class ProfileGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("S-Curve Motion Profile Generator")
        
        # 設定視窗最小大小
        self.root.minsize(800, 600)
        
        # 設定列和行的權重，使其可以隨視窗調整大小
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create input frame
        input_frame = ttk.Frame(root, padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input fields
        self.distance = tk.DoubleVar(value=1.0)
        self.max_speed = tk.DoubleVar(value=0.5)
        self.max_acceleration = tk.DoubleVar(value=1.0)
        self.max_jerk = tk.DoubleVar(value=2.0)
        
        # Create input labels and entries
        labels = ["Distance (m):", "Max Speed (m/s):", "Max Acceleration (m/s²):", "Max Jerk (m/s³):"]
        variables = [self.distance, self.max_speed, self.max_acceleration, self.max_jerk]
        
        for i, (label, var) in enumerate(zip(labels, variables)):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, padx=5, pady=5)
            ttk.Entry(input_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=5)
        
        # Generate button
        ttk.Button(input_frame, text="Generate Profile", command=self.generate_profile).grid(row=len(labels), column=0, columnspan=2, pady=10)
        
        # Add save button
        ttk.Button(input_frame, text="Save Plot", 
                   command=self.save_plot).grid(row=len(labels)+1, 
                                              column=0, 
                                              columnspan=2, 
                                              pady=5)
        
        # Create plot frame
        self.plot_frame = ttk.Frame(root, padding="10")
        self.plot_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 設置 matplotlib 支援中文字體
        plt.rcParams['font.family'] = ['Microsoft JhengHei', 'Arial']
        
        # Initialize plot with adjusted height and spacing
        self.fig, self.axs = plt.subplots(4, 1, figsize=(10, 10))
        
        # Adjust the spacing between subplots
        self.fig.subplots_adjust(
            top=0.95,      # 頂部邊距
            bottom=0.05,   # 底部邊距
            hspace=0.35    # 子圖之間的垂直間距
        )
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack()
        
        # 添加游標位置顯示
        self.cursor_text = self.fig.text(0.02, 0.98, '', fontsize=9)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.pack()

        # 添加垂直線和數值顯示
        self.vertical_line = None
        self.value_texts = []
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # 初始化繪圖相關的變數
        self.vertical_lines = []  # 存儲每個子圖的垂直線
        self.value_texts = []    # 存儲所有數值文字
        self.profile_data = None # 存儲運動曲線數據
        self.dt = None          # 存儲時間步長
        
        # 連接滑鼠事件
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def validate_inputs(self):
        try:
            distance = self.distance.get()
            max_speed = self.max_speed.get()
            max_acceleration = self.max_acceleration.get()
            max_jerk = self.max_jerk.get()
            
            if any(v <= 0 for v in [distance, max_speed, max_acceleration, max_jerk]):
                raise ValueError("All values must be positive")
            
            return True
        except tk.TclError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return False
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return False

    def generate_profile(self):
        if not self.validate_inputs():
            return

        # Clear previous plots
        for ax in self.axs:
            ax.clear()
            
        # Generate profile
        scurve = SCurve(
            self.distance.get(),
            self.max_speed.get(),
            self.max_acceleration.get(),
            self.max_jerk.get()
        )
        
        profile = scurve.calculate_profile()
        
        # 定義每個階段的顏色
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink']
        
        # 繪製每個階段
        for i in range(len(profile['time'])-1):
            stage = profile['stages'][i]
            
            # Position plot
            self.axs[0].plot(profile['time'][i:i+2], profile['position'][i:i+2], 
                            color=colors[stage], linewidth=1)
            self.axs[0].set_ylabel('Position (m)')
            
            # Velocity plot
            self.axs[1].plot(profile['time'][i:i+2], profile['velocity'][i:i+2], 
                            color=colors[stage], linewidth=1)
            self.axs[1].set_ylabel('Velocity (m/s)')
            
            # Acceleration plot
            self.axs[2].plot(profile['time'][i:i+2], profile['acceleration'][i:i+2], 
                            color=colors[stage], linewidth=1)
            self.axs[2].set_ylabel('Acceleration (m/s²)')
            
            # Jerk plot
            self.axs[3].plot(profile['time'][i:i+2], profile['jerk'][i:i+2], 
                            color=colors[stage], linewidth=1)
            self.axs[3].set_ylabel('Jerk (m/s³)')
        
        # 設置標題和標籤（使用中文）
        titles = ['位置曲線', '速度曲線', '加速度曲線', '加加速度曲線']
        ylabels = ['位置 (m)', '速度 (m/s)', '加速度 (m/s²)', '加加速度 (m/s³)']
        
        for ax, title, ylabel in zip(self.axs, titles, ylabels):
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_title(title, fontsize=10)
            ax.set_ylabel(ylabel, fontsize=9)
        
        self.axs[3].set_xlabel('時間 (s)', fontsize=9)
        
        # 添加圖例（使用中文）
        stage_names = ['加加速', '加速', '減加加速', '等速', '減加加速', '減速', '加加加速']
        legend_elements = [plt.Line2D([0], [0], color=colors[i], label=stage_names[i]) 
                          for i in range(len(colors))]
        self.axs[0].legend(handles=legend_elements, loc='upper right')
        
        # 設定每個子圖的標題和網格
        titles = ['Position Profile', 'Velocity Profile', 
                 'Acceleration Profile', 'Jerk Profile']
        
        for ax, title in zip(self.axs, titles):
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_title(title)
        
        # 保存profile數據供後續使用
        self.profile_data = profile
        self.dt = profile['time'][1] - profile['time'][0]  # 保存時間步長
        
        # Update canvas
        self.canvas.draw()

    def on_mouse_move(self, event):
        """處理滑鼠移動事件，顯示垂直線和對應的y值"""
        if not hasattr(self, 'profile_data') or not self.profile_data:
            return
            
        if event.inaxes:
            # 清除舊的垂直線
            while self.vertical_lines:
                line = self.vertical_lines.pop()
                line.remove() if line in line.axes.lines else None
                
            # 清除舊的文字
            while self.value_texts:
                text = self.value_texts.pop()
                text.remove() if text in text.axes.texts else None
                
            try:
                # 在每個子圖中添加垂直線
                for ax in self.axs:
                    line = ax.axvline(x=event.xdata, color='gray', linestyle='--', alpha=0.5)
                    self.vertical_lines.append(line)
                
                # 獲取當前x位置的索引
                x_idx = min(int(event.xdata / self.dt), len(self.profile_data['time']) - 1)
                if x_idx >= 0:
                    # 顯示每個曲線的值
                    keys = ['position', 'velocity', 'acceleration', 'jerk']
                    names = ['位置', '速度', '加速度', '加加速度']
                    units = ['m', 'm/s', 'm/s²', 'm/s³']
                    
                    for i, (key, name, unit) in enumerate(zip(keys, names, units)):
                        value = self.profile_data[key][x_idx]
                        text = self.axs[i].text(
                            0.02, 0.95, 
                            f'{name}: {value:.3f} {unit}',
                            transform=self.axs[i].transAxes,
                            verticalalignment='top',
                            bbox=dict(facecolor='white', alpha=0.7)
                        )
                        self.value_texts.append(text)
                
                # 重繪圖表
                self.canvas.draw_idle()
                
            except Exception as e:
                print(f"Error in on_mouse_move: {e}")

    def save_plot(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), 
                      ("All files", "*.*")]
        )
        if file_path:
            self.fig.savefig(file_path, dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfileGeneratorGUI(root)
    root.mainloop()
