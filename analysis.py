# analysis.py

import numpy as np
import pandas as pd

def add_filter_note_column(df, note):
    if df.empty:
        print("DataFrame is empty, skipping note addition.")
        return df
    df.loc[:, '_filter_note'] = note
    return df

def check_depth_anomalies(df):
    # 計算 Depth 的平均值和標準差
    mean_depth = df['Depth'].mean()
    std_depth = df['Depth'].std()

    # 找出超過三個標準差的值
    anomalies = df[(df['Depth'] < (mean_depth - 10 * std_depth)) | (df['Depth'] > (mean_depth + 10 * std_depth))]
    return anomalies

def filter_by_range(df, column, range_values):
    start, end = range_values
    # 過濾根據範圍
    return df[(df[column] < float(start)) | (df[column] > float(end))]

# 分切每個區段
def find_cutoff_points(df, column):
    # 找到分切點
    current_values = df[column].values
    diff_values = np.diff(current_values)
    cutoff_points = np.where(diff_values < 0)[0] + 1
    return cutoff_points

def split_into_segments(df, cutoff_points):
    segments = []
    start_idx = 0

    for cutoff in cutoff_points:
        first_value = df.iloc[start_idx]['Roll']
        last_value = df.iloc[cutoff - 1]['Roll']
        difference = abs(first_value - last_value)
        segments.append((cutoff, difference))
        start_idx = cutoff

    # Append the last segment
    if start_idx < len(df):
        first_value = df.iloc[start_idx]['Roll']
        last_value = df.iloc[-1]['Roll']
        difference = abs(first_value - last_value)
        segments.append((len(df), difference))

    return segments

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
        raise ValueError("Invalid option selected")

    # 檢查欄位數量是否符合
    if len(df.columns) != expected_columns:
        raise ValueError(f"Expected {expected_columns} columns, but got {len(df.columns)}")

    # 重新命名欄位
    df.columns = columns
    filtered_dfs = []

    # 依據不同條件新增不同過濾方式
    if selected_option == "SwathAngle":
        # 找到 cutoff 的 index
        cutoff_points = find_cutoff_points(df, 'BeamNo.')
        segments = split_into_segments(df, cutoff_points)
        for index, SAngle in segments:
            print(index, SAngle)
            # 在這裡對每個區間進行進一步的分析或處理
            if SAngle >= 130:
                new_row = pd.DataFrame({'Cutoff': [index], 'Difference': [SAngle]})
                filtered_dfs.append(new_row)
        # 更改顯示欄位
        columns = ['Cutoff', 'Difference']
        print(filtered_dfs)

    elif selected_option == "TPU":
        if params.get("depth_anomaly"):
            filtered_df = check_depth_anomalies(df)
            filtered_dfs.append(add_filter_note_column(filtered_df, "depth_anomaly"))

        thu_range = params.get("thu_range")
        if thu_range and thu_range[0] is not None and thu_range[1] is not None:
            filtered_df = filter_by_range(df, 'THU', thu_range)
            filtered_dfs.append(add_filter_note_column(filtered_df, "thu_range"))

        tvu_range = params.get("tvu_range")
        if tvu_range and tvu_range[0] is not None and tvu_range[1] is not None:
            filtered_df = filter_by_range(df, 'TVU', tvu_range)
            filtered_dfs.append(add_filter_note_column(filtered_df, "tvu_range"))

    if filtered_dfs:
        # 設定資料量上限
        max_data_limit = 10000  # 可根據需求調整這個閾值
        # 聯集所有過濾結果並移除重複值
        df = pd.concat(filtered_dfs).drop_duplicates().reset_index(drop=True)
        # 檢查總行數
        total_records = len(df)
        if total_records > max_data_limit:
            raise ValueError(f"錯誤資料過多，共有 {total_records} 筆資料，請確認檢查區間輸入是否正確")
    else:
        columns = ['Message']
        df = pd.DataFrame(columns=['Message'])
        df.loc[0] = '查無異常資料'

    return df, columns
