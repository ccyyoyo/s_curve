# S-Curve Motion Profile Generator Flowchart

```mermaid
flowchart TD
    A[開始] --> B[輸入參數:<br>距離、最大速度、<br>最大加速度、最大加加速度]
    B --> C[calculate_max_reachable_speed:<br>計算可達到的最大速度]
    
    subgraph 階段計算-generate_stages
    C --> D{距離足夠達到最大速度?<br>max_distance > 2*d_accel}
    D -->|是| E[生成7段式運動模型:<br>J1-A-J2-V-J3-D-J4]
    D -->|否| F[生成6段式運動模型:<br>J1-A-J2-J3-D-J4]
    end
    
    E --> G[計算各階段時間參數]
    F --> G
    
    G --> H[calculate_profile:<br>選擇計算方法]
    H -->|use_numpy=True| I[_calculate_profile_numpy]
    H -->|use_numpy=False| J[_calculate_profile_python]
    
    subgraph NumPy計算方法
    I --> K1[建立時間陣列]
    K1 --> L1[初始化位置、速度、加速度陣列]
    L1 --> M1[填充jerk陣列和階段索引]
    M1 --> N1[逐步計算加速度、速度、位置]
    N1 --> O1[根據當前階段調整參數]
    O1 --> P1{到達目標位置<br>且速度接近零?}
    P1 -->|否| N1
    P1 -->|是| Q1[裁剪數據陣列]
    end
    
    subgraph Python計算方法
    J --> K2[初始化Python列表]
    K2 --> L2[設置初始狀態]
    L2 --> M2[獲取當前jerk值]
    M2 --> N2[確定當前階段索引]
    N2 --> O2[更新加速度、速度、位置]
    O2 --> P2{到達目標位置<br>且速度接近零?}
    P2 -->|否| M2
    P2 -->|是| Q2[返回結果]
    end
    
    Q1 --> R[返回運動曲線數據]
    Q2 --> R
    
    R --> S[validate_profile:<br>驗證生成的曲線]
    S --> T[繪製曲線]
    T --> U[結束]
    
    %% 輔助方法
    V[_get_jerk_at_time:<br>獲取特定時間的jerk值] -.-> M2
    W[_check_motion_constraints:<br>檢查運動約束] -.-> O2