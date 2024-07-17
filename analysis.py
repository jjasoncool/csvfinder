# analysis.py

import pandas as pd

def check_depth_anomalies(df):
    # 計算 Depth 的平均值和標準差
    mean_depth = df['Depth'].mean()
    std_depth = df['Depth'].std()

    # 找出超過三個標準差的值
    anomalies = df[(df['Depth'] < (mean_depth - 3 * std_depth)) | (df['Depth'] > (mean_depth + 3 * std_depth))]
    return anomalies

def filter_by_range(df, column, range_values):
    start, end = range_values
    # 過濾根據範圍
    return df[(df[column] < float(start)) | (df[column] > float(end))]

def analyze_data(df, params):
    # 在這裡新增你的分析邏輯
    # 根據 params 執行不同的分析
    results = []
    selected_option = params.get("selected_option")

    if selected_option == "SwathAngle":
        expected_columns = 3
        columns = ['BeamNo.', 'Pitch', 'Roll']
    elif selected_option == "TPU":
        expected_columns = 5
        columns = ['Longitude', 'Latitude', 'Depth', 'THU', 'TVU']
    else:
        return "Invalid option selected", []

    # 檢查欄位數量是否符合
    if len(df.columns) != expected_columns:
        return f"Expected {len(expected_columns)} columns, but got {len(df.columns)}", []

    # 重新命名欄位
    print(df)
    df.columns = columns
    print(df)
    filtered_dfs = []

    # 依據不同條件新增不同過濾方式
    if selected_option == "SwathAngle":
        # 在此處添加 SwathAngle 的特定過濾邏輯
        pass

    elif selected_option == "TPU":
        if params.get("depth_anomaly"):
            filtered_dfs.append(check_depth_anomalies(df))

        thu_range = params.get("thu_range")
        if thu_range and thu_range[0] is not None and thu_range[1] is not None:
            filtered_dfs.append(filter_by_range(df, 'THU', thu_range))

        tvu_range = params.get("tvu_range")
        if tvu_range and tvu_range[0] is not None and tvu_range[1] is not None:
            filtered_dfs.append(filter_by_range(df, 'TVU', tvu_range))

    if filtered_dfs:
        # 聯集所有過濾結果並移除重複值
        df = pd.concat(filtered_dfs).drop_duplicates().reset_index(drop=True)

    return df, columns
