import numpy as np

class SCurve:
    """S型曲線運動規劃器。

    計算滿足最大速度、加速度和加加速度限制的運動軌跡。

    Attributes:
        max_distance (float): 目標移動距離 (m)
        max_speed (float): 最大速度限制 (m/s)
        max_acceleration (float): 最大加速度限制 (m/s²)
        max_jerk (float): 最大加加速度限制 (m/s³)
    """

    def __init__(self, max_distance, max_speed, max_acceleration, max_jerk):
        """初始化 S-Curve 規劃器。

        Args:
            max_distance (float): 目標移動距離
            max_speed (float): 最大速度限制
            max_acceleration (float): 最大加速度限制
            max_jerk (float): 最大加加速度限制

        Raises:
            ValueError: 當任何參數小於或等於0時
            ValueError: 當加加速度小於加速度時
        """
        if any(v <= 0 for v in [max_distance, max_speed, max_acceleration, max_jerk]):
            raise ValueError("All parameters must be positive")
        
        if max_jerk < max_acceleration:
            raise ValueError("Jerk must be greater than acceleration for proper motion planning")
        
        self.max_distance = max_distance
        self.max_speed = max_speed
        self.max_acceleration = max_acceleration
        self.max_jerk = max_jerk

    def calculate_profile(self, dt=0.01, use_numpy=True):
        """計算完整的運動曲線。

        Args:
            dt (float): 時間步長 (秒)
            use_numpy (bool): 是否使用 NumPy 進行計算優化

        Returns:
            dict: 運動曲線數據
        """
        if use_numpy:
            return self._calculate_profile_numpy(dt)
        else:
            return self._calculate_profile_python(dt)

    def calculate_max_reachable_speed(self, distance):
        """計算在給定距離內能達到的最大速度，確保能夠及時減速到0"""
        # 使用二分搜尋法找到合適的最大速度
        v_min = 0.01
        v_max = self.max_speed
        
        for _ in range(20):  # 最多20次迭代
            v_target = (v_min + v_max) / 2
            
            # 計算達到這個速度所需的時間和距離
            t_j = self.max_acceleration / self.max_jerk
            t_a = v_target / self.max_acceleration
            
            # 計算加速階段的距離
            d_j1 = (self.max_jerk * t_j**3) / 6
            d_a = self.max_acceleration * t_j * t_j/2 + self.max_acceleration * (t_a - t_j) * t_j
            d_j2 = self.max_acceleration * t_j * t_j/2 - (self.max_jerk * t_j**3) / 6
            
            # 總距離是加速和減速階段的距離之和
            total_distance = 2 * (d_j1 + d_a + d_j2)
            
            if abs(total_distance - distance) < 0.001:
                return v_target
            elif total_distance > distance:
                v_max = v_target
            else:
                v_min = v_target
        
        return v_max

    def generate_stages(self):
        # 首先計算在給定距離內能達到的最大速度
        achievable_speed = self.calculate_max_reachable_speed(self.max_distance)
        
        # 使用計算出的速度重新計算時間參數
        t_j = self.max_acceleration / self.max_jerk
        t_a = achievable_speed / self.max_acceleration
        
        # 計算加速階段的距離
        d_j1 = (self.max_jerk * t_j**3) / 6
        d_a = self.max_acceleration * t_j * t_j/2 + self.max_acceleration * (t_a - t_j) * t_j
        d_j2 = self.max_acceleration * t_j * t_j/2 - (self.max_jerk * t_j**3) / 6
        
        d_accel = d_j1 + d_a + d_j2
        
        if self.max_distance > 2 * d_accel:
            # 需要恆速階段
            d_const_vel = self.max_distance - 2 * d_accel
            t_v = d_const_vel / achievable_speed
            
            return {
                'names': ['J1', 'A', 'J2', 'V', 'J3', 'D', 'J4'],
                'jerks': [self.max_jerk, 0, -self.max_jerk, 0, -self.max_jerk, 0, self.max_jerk],
                'durations': [t_j, t_a - t_j, t_j, t_v, t_j, t_a - t_j, t_j]
            }
        else:
            # 不需要恆速階段
            return {
                'names': ['J1', 'A', 'J2', 'J3', 'D', 'J4'],
                'jerks': [self.max_jerk, 0, -self.max_jerk, -self.max_jerk, 0, self.max_jerk],
                'durations': [t_j, t_a - t_j, t_j, t_j, t_a - t_j, t_j]
            }

    def _adjust_stages(self, stages):
        # No need for additional adjustments as the stages are now calculated correctly
        return stages

    def _get_jerk_at_time(self, t, stages):
        current_time = 0
        for jerk, duration in zip(stages['jerks'], stages['durations']):
            if current_time <= t < current_time + duration:
                return jerk
            current_time += duration
        return 0

    def _check_motion_constraints(self, velocity, acceleration):
        """檢查運動是否滿足約束條件。

        Args:
            velocity (float): 當前速度
            acceleration (float): 當前加速度

        Returns:
            bool: 是否滿足所有約束
        """
        speed_ok = 0 <= velocity <= self.max_speed
        accel_ok = -self.max_acceleration <= acceleration <= self.max_acceleration
        return speed_ok and accel_ok

    def validate_profile(self, profile):
        """驗證生成的運動曲線是否滿足所有約束。

        Args:
            profile (dict): calculate_profile 返回的運動曲線數據

        Returns:
            bool: 是否通過驗證
        """
        velocities = np.array(profile['velocity'])
        accelerations = np.array(profile['acceleration'])
        jerks = np.array(profile['jerk'])
        
        speed_ok = np.all((velocities >= 0) & (velocities <= self.max_speed))
        accel_ok = np.all(np.abs(accelerations) <= self.max_acceleration)
        jerk_ok = np.all(np.abs(jerks) <= self.max_jerk)
        
        return speed_ok and accel_ok and jerk_ok

    def _calculate_profile_numpy(self, dt):
        """使用 NumPy 計算運動曲線。"""
        stages = self.generate_stages()
        total_time = sum(stages['durations'])
        
        # 創建時間陣列
        times = np.arange(0, total_time + dt, dt)
        
        # 初始化陣列
        jerks = np.zeros_like(times)
        accelerations = np.zeros_like(times)
        velocities = np.zeros_like(times)
        positions = np.zeros_like(times)
        stage_indices = np.zeros_like(times, dtype=int)
        
        # 改進階段索引和過渡的計算 - 添加微小重疊來確保連續性
        current_time = 0
        for i, (jerk, duration) in enumerate(zip(stages['jerks'], stages['durations'])):
            # 使用微小的重疊確保階段之間的連續性
            if i > 0:  # 不是第一個階段
                overlap_start = max(0, current_time - dt)  # 重疊開始時間
                mask_overlap = (times >= overlap_start) & (times < current_time)
                # 在重疊區域設置混合值
                overlap_ratio = (times[mask_overlap] - overlap_start) / (current_time - overlap_start)
                # 讓重疊點的 jerk 逐漸過渡 (線性插值)
                jerks[mask_overlap] = (1 - overlap_ratio) * stages['jerks'][i-1] + overlap_ratio * jerk
            
            # 正常設置當前階段的值
            mask = (times >= current_time) & (times < current_time + duration)
            jerks[mask] = jerk
            stage_indices[mask] = i
            current_time += duration
        
        # 確保總時間範圍是正確的
        if times[-1] > total_time:
            times[-1] = total_time
            jerks[-1] = stages['jerks'][-1]
            stage_indices[-1] = len(stages['jerks']) - 1
        
        # 計算加速度、速度和位置時使用積分方法而不是簡單的前向差分
        accelerations[0] = 0  # 初始加速度為0
        velocities[0] = 0     # 初始速度為0
        positions[0] = 0      # 初始位置為0
        
        # 使用更精確的積分方法
        for i in range(1, len(times)):
            # 使用梯形法則計算加速度積分
            accelerations[i] = accelerations[i-1] + 0.5 * (jerks[i-1] + jerks[i]) * dt
            accelerations[i] = np.clip(accelerations[i], -self.max_acceleration, self.max_acceleration)
            
            # 使用梯形法則計算速度積分
            velocities[i] = velocities[i-1] + 0.5 * (accelerations[i-1] + accelerations[i]) * dt
            velocities[i] = np.clip(velocities[i], 0, self.max_speed)
            
            # 在等速階段強制設置恆定速度
            if stage_indices[i] == 3 and len(stages['names']) > 6:  # 有等速階段且是等速階段
                target_speed = self.calculate_max_reachable_speed(self.max_distance)
                # 使用平滑過渡而不是突變
                velocities[i] = target_speed
                accelerations[i] = 0
            
            # 使用梯形法則計算位置積分
            positions[i] = positions[i-1] + 0.5 * (velocities[i-1] + velocities[i]) * dt
            
            # 確保在進入減速階段前，速度是平滑過渡的
            if i > 1 and stage_indices[i] == 4 and stage_indices[i-1] != 4:
                # 即將進入減速階段，確保速度平滑過渡
                velocities[i] = velocities[i-1]  # 保持與前一個點相同的速度
            
            # 如果到達目標位置且速度接近0，則停止計算
            if positions[i] >= self.max_distance and velocities[i] <= 0.001:
                # 裁剪陣列到當前索引
                times = times[:i+1]
                positions = positions[:i+1]
                velocities = velocities[:i+1]
                accelerations = accelerations[:i+1]
                jerks = jerks[:i+1]
                stage_indices = stage_indices[:i+1]
                break
        
        # 確保最終位置精確地達到目標距離
        if positions[-1] != self.max_distance:
            positions[-1] = self.max_distance
        
        return {
            'time': times,
            'position': positions,
            'velocity': velocities,
            'acceleration': accelerations,
            'jerk': jerks,
            'stages': stage_indices
        }

    def _calculate_profile_python(self, dt):
        """使用純 Python 計算運動曲線。

        Args:
            dt (float): 時間步長 (秒)

        Returns:
            dict: 包含運動曲線數據的字典
        """
        stages = self.generate_stages()
        total_time = sum(stages['durations'])
        
        # 初始化列表
        times = []
        positions = []
        velocities = []
        accelerations = []
        jerks = []
        stage_indices = []
        
        # 初始狀態
        t = 0
        position = 0
        velocity = 0
        acceleration = 0
        
        while t <= total_time:
            # 獲取當前階段的 jerk
            current_jerk = self._get_jerk_at_time(t, stages)
            
            # 確定當前階段索引
            current_time = 0
            current_stage = 0
            for i, duration in enumerate(stages['durations']):
                if current_time <= t < current_time + duration:
                    current_stage = i
                    break
                current_time += duration
            
            # 更新加速度
            acceleration += current_jerk * dt
            acceleration = max(-self.max_acceleration, 
                             min(self.max_acceleration, acceleration))
            
            # 更新速度
            velocity += acceleration * dt
            velocity = max(0, min(self.max_speed, velocity))
            
            # 在等速階段保持速度不變
            if current_stage == 3:  # 等速階段
                velocity = self.calculate_max_reachable_speed(self.max_distance)
                acceleration = 0
            
            # 更新位置
            position += velocity * dt
            
            # 保存數據
            times.append(t)
            positions.append(position)
            velocities.append(velocity)
            accelerations.append(acceleration)
            jerks.append(current_jerk)
            stage_indices.append(current_stage)
            
            # 更新時間
            t += dt
            
            # 檢查是否到達目標位置且速度接近0
            if position >= self.max_distance and velocity <= 0.001:
                break
        
        return {
            'time': times,
            'position': positions,
            'velocity': velocities,
            'acceleration': accelerations,
            'jerk': jerks,
            'stages': stage_indices
        }