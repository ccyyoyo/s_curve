import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from models.s_curve import SCurve
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
                messagebox.showerror("錯誤", "所有參數必須大於0")
                return False
            
            return True
        except tk.TclError:
            messagebox.showerror("錯誤", "請輸入有效的數值")
            return False
        except ValueError as e:
            messagebox.showerror("錯誤", str(e))
            return False

    def _check_parameters(self, scurve):
        """檢查參數是否合理"""
        # 檢查加加速度是否小於加速度
        if scurve.max_jerk < scurve.max_acceleration:
            msg = f"加加速度 ({scurve.max_jerk:.2f}) 小於加速度 ({scurve.max_acceleration:.2f})！\n"
            msg += "加加速度應該大於加速度才能產生合理的運動規劃。"
            messagebox.showerror("參數錯誤", msg)
            return False
        
        # 檢查加加速度是否足夠大
        min_time_to_max_accel = scurve.max_acceleration / scurve.max_jerk
        if min_time_to_max_accel > 1.0:
            msg = f"加加速度值過小！需要 {min_time_to_max_accel:.2f} 秒才能達到最大加速度。\n"
            msg += "建議增加加加速度值或減小最大加速度。"
            messagebox.showwarning("參數警告", msg)
            return False
        
        # 檢查最大速度是否合理
        min_distance_for_max_speed = (scurve.max_speed ** 2) / scurve.max_acceleration
        if min_distance_for_max_speed > scurve.max_distance:
            msg = f"最大速度可能過高！\n"
            msg += f"在給定的加速度下，需要至少 {min_distance_for_max_speed:.2f}m 才能達到最大速度。"
            messagebox.showwarning("參數警告", msg)
            
        return True

    def generate_profile(self):
        """生成運動曲線並顯示"""
        try:
            # 檢查輸入參數
            if not self.validate_inputs():
                return
            
            # 建立 S-Curve 物件
            scurve = SCurve(
                self.distance.get(),
                self.max_speed.get(),
                self.max_acceleration.get(),
                self.max_jerk.get()
            )
            
            # 檢查參數是否合理
            if not self._check_parameters(scurve):
                return
            
            # 計算運動曲線
            profile = scurve.calculate_profile(dt=0.01)
            
            # 清除先前的圖表
            for ax in self.axs:
                ax.clear()
            
            # 首先繪製整體曲線
            self.axs[0].plot(profile['time'], profile['position'], 'k-', linewidth=0.5, alpha=0.3)
            self.axs[1].plot(profile['time'], profile['velocity'], 'k-', linewidth=0.5, alpha=0.3)
            self.axs[2].plot(profile['time'], profile['acceleration'], 'k-', linewidth=0.5, alpha=0.3)
            self.axs[3].plot(profile['time'], profile['jerk'], 'k-', linewidth=0.5, alpha=0.3)
            
            # 定義每個階段的顏色
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink']
            
            # 針對每個階段的數據查找階段變化點
            stage_changes = [0]  # 第一個點總是階段的開始
            stages = profile['stages']
            
            for i in range(1, len(stages)):
                if stages[i] != stages[i-1]:
                    stage_changes.append(i)
            stage_changes.append(len(stages) - 1)  # 最後一個點
            
            # 繪製每個階段的不同顏色
            for i in range(len(stage_changes) - 1):
                start_idx = stage_changes[i]
                end_idx = stage_changes[i + 1]
                stage = stages[start_idx]
                
                # 確保有足夠的數據點來繪製
                if end_idx - start_idx > 1:
                    self.axs[0].plot(profile['time'][start_idx:end_idx+1], 
                                    profile['position'][start_idx:end_idx+1], 
                                    color=colors[stage % len(colors)], linewidth=1.5)
                    
                    self.axs[1].plot(profile['time'][start_idx:end_idx+1], 
                                    profile['velocity'][start_idx:end_idx+1], 
                                    color=colors[stage % len(colors)], linewidth=1.5)
                    
                    self.axs[2].plot(profile['time'][start_idx:end_idx+1], 
                                    profile['acceleration'][start_idx:end_idx+1], 
                                    color=colors[stage % len(colors)], linewidth=1.5)
                    
                    self.axs[3].plot(profile['time'][start_idx:end_idx+1], 
                                    profile['jerk'][start_idx:end_idx+1], 
                                    color=colors[stage % len(colors)], linewidth=1.5)
            
            # 檢查階段之間的連續性
            for i in range(1, len(stage_changes)):
                idx = stage_changes[i]
                if idx > 0 and idx < len(profile['velocity']) - 1:
                    # 新增階段變換點標記
                    for j, ax in enumerate(self.axs):
                        keys = ['position', 'velocity', 'acceleration', 'jerk']
                        ax.plot(profile['time'][idx], profile[keys[j]][idx], 'ko', markersize=3)
            
            # 設置標題和標籤
            titles = ['位置曲線', '速度曲線', '加速度曲線', '加加速度曲線']
            ylabels = ['位置 (m)', '速度 (m/s)', '加速度 (m/s²)', '加加速度 (m/s³)']
            
            for ax, title, ylabel in zip(self.axs, titles, ylabels):
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.set_title(title, fontsize=10)
                ax.set_ylabel(ylabel, fontsize=9)
            
            self.axs[3].set_xlabel('時間 (s)', fontsize=9)
            
            # 添加圖例
            stage_names = ['加加速', '加速', '減加加速', '等速', '減加加速', '減速', '加加加速']
            legend_elements = []
            for i, name in enumerate(stage_names):
                if i < len(colors):
                    legend_elements.append(plt.Line2D([0], [0], color=colors[i], label=name))
            
            self.axs[0].legend(handles=legend_elements, loc='upper right')
            
            # 保存profile數據供後續使用
            self.profile_data = profile
            self.dt = profile['time'][1] - profile['time'][0]  # 保存時間步長
            
            # 在速度曲線上添加階段變化點的標註
            for i in range(1, len(stage_changes)):
                idx = stage_changes[i]
                if idx > 0 and idx < len(profile['velocity']):
                    t = profile['time'][idx]
                    v = profile['velocity'][idx]
                    self.axs[1].annotate(f'S{stages[idx]}', xy=(t, v), 
                                        xytext=(0, 10), textcoords='offset points',
                                        fontsize=8, ha='center',
                                        arrowprops=dict(arrowstyle='->', lw=0.5))
            
            # Update canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 顯示成功訊息
            messagebox.showinfo("成功", "運動曲線已生成！")
            
        except ValueError as e:
            messagebox.showerror("錯誤", str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()  # 在控制台打印詳細錯誤信息
            messagebox.showerror("錯誤", f"生成運動曲線時發生錯誤：{str(e)}")
            
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
        if not hasattr(self, 'profile_data') or self.profile_data is None:
            messagebox.showerror("錯誤", "請先生成運動曲線！")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), 
                      ("All files", "*.*")]
        )
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("成功", f"圖表已儲存至\n{file_path}")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存圖表時發生錯誤：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfileGeneratorGUI(root)
    root.mainloop()
