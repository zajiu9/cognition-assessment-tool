import streamlit as st
import pandas as pd
from io import BytesIO
import datetime

# 初始化session state
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        '患者姓名', 'MMSE', 'MoCA', '步行时间(秒)', '受教育程度', '年龄', '性别',
        '步速(m/s)', '评估结果', '评估时间'
    ])

# 用于删除行的键列表
if 'delete_keys' not in st.session_state:
    st.session_state.delete_keys = []


def evaluate_cognition(patient_name, mmse, moca, walk_time, education, age, gender):
    """评估认知功能并返回结果和步速"""
    # 1. 验证输入
    if age < 60:
        return "错误：年龄需≥60岁", None

    # 2. MMSE初步筛查
    if mmse < 16:
        return "中重度认知功能障碍", None

    # 教育分组定义
    low_edu = ["文盲", "小学"]
    mid_edu = ["初中", "高中/中专"]
    high_edu = ["大专", "本科", "硕士及以上"]

    # 3. MoCA判断
    is_mci = False
    if education in low_edu and moca <= 18:
        is_mci = True
    elif education in mid_edu and moca <= 21:
        is_mci = True
    elif education in high_edu and moca <= 23:
        is_mci = True

    # 计算步速（保留两位小数）
    gait_speed = round(4 / walk_time, 2) if walk_time > 0 else 0.00

    # 定义步速临界值
    slow_speed_threshold = 0
    if gender == "男":
        if 60 <= age <= 74:
            slow_speed_threshold = 0.67
        elif age >= 75:
            slow_speed_threshold = 0.54
    else:  # 女性
        if 60 <= age <= 74:
            slow_speed_threshold = 0.65
        elif age >= 75:
            slow_speed_threshold = 0.52

    # 4. 如果存在MCI
    if is_mci:
        if gait_speed < slow_speed_threshold:
            return "MCI合并步速减慢", gait_speed
        else:
            return "MCI（轻度认知障碍）", gait_speed

    # 5. MoCA达标的情况
    # 步速慢的情况
    if gait_speed < slow_speed_threshold:
        if education == "文盲":
            if mmse >= 17:
                return "MCR（运动认知风险综合征）", gait_speed
            else:
                return "步速减慢", gait_speed
        elif education == "小学":
            if mmse >= 20:
                return "MCR（运动认知风险综合征）", gait_speed
            else:
                return "步速减慢", gait_speed
        else:  # 其他教育程度
            if mmse >= 24:
                return "MCR（运动认知风险综合征）", gait_speed
            else:
                return "步速减慢", gait_speed
    # 步速正常的情况
    else:
        if education == "文盲":
            if mmse >= 17:
                return "认知功能正常", gait_speed
            else:
                return "矛盾 - MoCA正常但MMSE不达标", gait_speed
        elif education == "小学":
            if mmse >= 20:
                return "认知功能正常", gait_speed
            else:
                return "矛盾 - MoCA正常但MMSE不达标", gait_speed
        else:  # 其他教育程度
            if mmse >= 24:
                return "认知功能正常", gait_speed
            else:
                return "矛盾 - MoCA正常但MMSE不达标", gait_speed


def main():
    st.title("认知功能评估工具")
    st.subheader("请输入患者信息")

    # 创建输入表单
    with st.form("assessment_form"):
        patient_name = st.text_input("患者姓名")
        col1, col2 = st.columns(2)
        with col1:
            mmse = st.number_input("MMSE得分 (0-30)", min_value=0, max_value=30, step=1)
        with col2:
            moca = st.number_input("MoCA得分 (0-30)", min_value=0, max_value=30, step=1)

        # 修改：步行时间输入框默认值为None（显示为空）
        walk_time = st.number_input(
            "4米步行时间 (秒)",
            min_value=0.1,
            step=0.1,
            format="%.2f",
            value=None,  # 设置默认值为None，显示为空
            placeholder="输入时间（秒）"
        )

        col3, col4 = st.columns(2)
        with col3:
            education = st.selectbox("受教育程度",
                                     ["文盲", "小学", "初中", "高中/中专", "大专", "本科", "硕士及以上"])
        with col4:
            age = st.number_input("年龄 (≥60岁)", min_value=0, step=1)

        gender = st.selectbox("性别", ["男", "女"])

        submitted = st.form_submit_button("开始评估")

    if submitted:
        # 检查步行时间是否已输入
        if walk_time is None:
            st.error("请输入4米步行时间")
            return
        if walk_time <= 0:
            st.error("步行时间必须大于0")
            return

        # 执行评估
        result, gait_speed = evaluate_cognition(
            patient_name, mmse, moca, walk_time, education, age, gender
        )

        # 显示评估结果
        if result.startswith("错误") or result.startswith("中重度"):
            st.error(f"评估结果：{result}")
        elif result == "认知功能正常":
            st.success(f"评估结果：{result}")
        elif result.startswith("矛盾"):
            st.warning(f"评估结果：{result}")
        else:
            st.warning(f"评估结果：{result}")

        # 添加评估时间戳
        eval_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 将结果添加到历史记录
        new_entry = {
            '患者姓名': patient_name,
            'MMSE': mmse,
            'MoCA': moca,
            '步行时间(秒)': walk_time,
            '受教育程度': education,
            '年龄': age,
            '性别': gender,
            '步速(m/s)': f"{gait_speed:.2f}" if gait_speed is not None else "N/A",  # 保留两位小数
            '评估结果': result,
            '评估时间': eval_time
        }

        # 更新session state中的历史记录
        new_df = pd.DataFrame([new_entry])
        st.session_state.history = pd.concat([st.session_state.history, new_df], ignore_index=True)

    # 显示历史记录表格
    if not st.session_state.history.empty:
        st.subheader("评估历史记录")

        # 创建带删除按钮的表格
        for i in range(len(st.session_state.history)):
            row = st.session_state.history.iloc[i]
            cols = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1])

            # 显示数据
            cols[0].write(row['患者姓名'])
            cols[1].write(row['MMSE'])
            cols[2].write(row['MoCA'])
            cols[3].write(row['步行时间(秒)'])
            cols[4].write(row['受教育程度'])
            cols[5].write(row['年龄'])
            cols[6].write(row['性别'])
            cols[7].write(row['步速(m/s)'])  # 这里已经是两位小数的字符串
            cols[8].write(row['评估时间'])

            # 显示评估结果（带颜色）
            if "正常" in row['评估结果']:
                cols[9].success(row['评估结果'])
            elif "矛盾" in row['评估结果'] or "减慢" in row['评估结果'] or "MCR" in row['评估结果']:
                cols[9].warning(row['评估结果'])
            else:
                cols[9].error(row['评估结果'])

            # 删除按钮 - 使用唯一的键
            delete_key = f"delete_{i}_{row['评估时间']}"
            if cols[10].button("删除", key=delete_key):
                # 标记要删除的行
                st.session_state.delete_keys.append(i)

        # 处理删除请求
        if st.session_state.delete_keys:
            # 删除所有标记的行
            indices_to_delete = st.session_state.delete_keys
            st.session_state.history = st.session_state.history.drop(indices_to_delete).reset_index(drop=True)
            # 清空删除键列表
            st.session_state.delete_keys = []
            # 显示成功消息
            st.success(f"已删除 {len(indices_to_delete)} 条记录")
            # 使用st.experimental_rerun()刷新页面
            st.experimental_rerun()

        # 添加表头
        st.write("---")
        header_cols = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1])
        headers = ["患者姓名", "MMSE", "MoCA", "步行时间", "教育程度", "年龄", "性别", "步速", "评估时间", "评估结果",
                   "操作"]
        for col, header in zip(header_cols, headers):
            col.write(f"**{header}**")

        # 导出到Excel功能
        st.subheader("数据导出")
        if st.button("导出为Excel文件"):
            # 创建Excel文件
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.history.to_excel(writer, index=False, sheet_name='评估记录')
            output.seek(0)

            # 提供下载
            st.download_button(
                label="下载Excel文件",
                data=output,
                file_name=f"认知评估记录_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.ms-excel"
            )


if __name__ == "__main__":
    main()