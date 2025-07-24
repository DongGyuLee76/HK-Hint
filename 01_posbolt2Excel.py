import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 확장된 색상 팔레트 정의
EXTENDED_COLORS = (
    px.colors.qualitative.Set1 + 
    px.colors.qualitative.Set2 + 
    px.colors.qualitative.Set3 + 
    px.colors.qualitative.Pastel1 + 
    px.colors.qualitative.Pastel2
)

def main():
    st.title("Excel 데이터 박스플롯 시각화")
    st.sidebar.header("설정")
    
    # 파일 업로드
    uploaded_file = st.sidebar.file_uploader(
        "Excel 파일을 업로드하세요", 
        type=['xlsx', 'xls'],
        help="Excel 파일(.xlsx, .xls)만 업로드 가능합니다."
    )
    
    if uploaded_file is not None:
        try:
            # Excel 파일 읽기
            df = pd.read_excel(uploaded_file)
            
            st.success(f"파일이 성공적으로 로드되었습니다. (행: {len(df)}, 열: {len(df.columns)})")
            
            # 데이터 미리보기
            with st.expander("데이터 미리보기"):
                st.dataframe(df.head())
            
            # 그래프 설정 및 필터 적용
            process_graph_settings(df)
            
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("Excel 파일을 업로드해주세요.")
        
        # 샘플 데이터로 예시 보여주기
        st.subheader("예시")
        sample_data = create_sample_data()
        st.write("샘플 데이터:")
        st.dataframe(sample_data.head())
        
        # 샘플 그래프 설정
        process_graph_settings(sample_data)

def process_graph_settings(df):
    """그래프 설정 및 필터 처리 - 리렌더링 방지 버전"""
    
    st.sidebar.subheader("그래프 설정")
    
    # 숫자형 컬럼만 필터링
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if not numeric_columns:
        st.error("숫자형 데이터가 없습니다. 박스플롯을 그릴 수 없습니다.")
        return
    
    # 세션 상태 초기화
    initialize_session_state(numeric_columns, categorical_columns)
    
    # 그래프 설정 UI (세션 상태로 관리)
    setup_graph_controls(numeric_columns, categorical_columns)
    

    # 다중 데이터 필터 설정
    setup_data_filters_with_button(df)
    
    # 필터 컨트롤 표시
    setup_filter_controls()
    
    # 적용 버튼
    st.sidebar.markdown("---")
    apply_button = st.sidebar.button("🔄 그래프 적용", type="primary", use_container_width=True)
    
    # 적용 버튼이 눌렸을 때만 실제 처리
    if apply_button:
        # 세션 상태에서 설정값 가져오기
        settings = get_current_settings()
        
        # 다중 필터 적용
        filtered_df = apply_filters_to_data(df, settings['filters'])   
        
        # 데이터 수 정보 표시
        display_data_info(df, filtered_df)
        
        if not filtered_df.empty:
            create_boxplot(
                filtered_df, 
                settings['y_column'], 
                settings['x_column'], 
                settings['color_column'], 
                settings['show_points'], 
                settings['show_mean'],
                settings['filters']  # 다중 필터 정보 추가
            )


            show_statistics(filtered_df, settings['y_column'], settings['x_column'])
        else:
            st.warning("필터 조건에 맞는 데이터가 없습니다.")
    else:
        # 초기 데이터 수 정보만 표시
        display_data_info(df, df)
        st.info("그래프 설정을 완료한 후 '그래프 적용' 버튼을 눌러주세요.")

def initialize_session_state(numeric_columns, categorical_columns):
    """세션 상태 초기화"""
    if 'graph_y_column' not in st.session_state:
        st.session_state.graph_y_column = numeric_columns[0]
    if 'graph_x_column' not in st.session_state:
        st.session_state.graph_x_column = "없음"
    if 'graph_color_column' not in st.session_state:
        st.session_state.graph_color_column = "없음"
    if 'graph_show_points' not in st.session_state:
        st.session_state.graph_show_points = True
    if 'graph_show_mean' not in st.session_state:
        st.session_state.graph_show_mean = True
    # 다중 필터를 위한 리스트로 변경
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = []
    if 'filter_counter' not in st.session_state:
        st.session_state.filter_counter = 0

def setup_graph_controls(numeric_columns, categorical_columns):
    """그래프 컨트롤 설정 - 리렌더링 방지"""
    
    # Y축 선택
    current_y_index = numeric_columns.index(st.session_state.graph_y_column) if st.session_state.graph_y_column in numeric_columns else 0
    new_y = st.sidebar.selectbox(
        "**Y축 (값) 선택:**",
        numeric_columns,
        index=current_y_index,
        key="y_column_selector",
        help="박스플롯으로 표시할 숫자형 데이터를 선택하세요."
    )
    if new_y != st.session_state.graph_y_column:
        st.session_state.graph_y_column = new_y
    
    # X축 선택
    x_options = ["없음"] + categorical_columns
    current_x_index = x_options.index(st.session_state.graph_x_column) if st.session_state.graph_x_column in x_options else 0
    
    if categorical_columns:
        new_x = st.sidebar.selectbox(
            "**X축 (그룹) 선택:**",
            x_options,
            index=current_x_index,
            key="x_column_selector",
            help="그룹별로 나누어 표시할 범주형 데이터를 선택하세요."
        )
        if new_x != st.session_state.graph_x_column:
            st.session_state.graph_x_column = new_x
    else:
        st.sidebar.info("범주형 데이터가 없어 전체 데이터로 박스플롯을 생성합니다.")
    
    # 색상 그룹 선택
    color_options = ["없음"] + categorical_columns
    current_color_index = color_options.index(st.session_state.graph_color_column) if st.session_state.graph_color_column in color_options else 0
    new_color = st.sidebar.selectbox(
        "**색상 그룹 (선택사항):**",
        color_options,
        index=current_color_index,
        key="color_column_selector",
        help="색상으로 구분할 추가 그룹을 선택하세요."
    )
    if new_color != st.session_state.graph_color_column:
        st.session_state.graph_color_column = new_color
    
    # 그래프 옵션
    st.sidebar.subheader("그래프 옵션")
    new_points = st.sidebar.checkbox(
        "개별 데이터 포인트 표시",
        value=st.session_state.graph_show_points,
        key="show_points_selector"
    )
    if new_points != st.session_state.graph_show_points:
        st.session_state.graph_show_points = new_points
    
    new_mean = st.sidebar.checkbox(
        "평균값 표시",
        value=st.session_state.graph_show_mean,
        key="show_mean_selector"
    )
    if new_mean != st.session_state.graph_show_mean:
        st.session_state.graph_show_mean = new_mean

def setup_data_filters_with_button(df):
    """다중 데이터 필터 설정"""
    st.sidebar.subheader("데이터 필터")
    
    # 현재 적용된 필터들 표시
    if st.session_state.active_filters:
        st.sidebar.write("**현재 적용된 필터:**")
        for i, filter_info in enumerate(st.session_state.active_filters):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if filter_info['type'] == 'categorical':
                    selected_count = len(filter_info['selected_values'])
                    total_count = len(filter_info['all_values'])
                    st.sidebar.caption(f"🔹 {filter_info['column']}: {selected_count}/{total_count}개 선택")
                else:
                    range_val = filter_info['selected_range']
                    st.sidebar.caption(f"🔹 {filter_info['column']}: {range_val[0]:.1f}\~{range_val[1]:.1f}")
            with col2:
                if st.button("❌", key=f"remove_filter_{i}", help="필터 제거"):
                    st.session_state.active_filters.pop(i)
                    st.rerun()
        st.sidebar.markdown("---")
    
    # 새 필터 추가
    st.sidebar.write("**새 필터 추가:**")
    
    # 이미 필터가 적용된 컬럼들 제외
    applied_columns = [f['column'] for f in st.session_state.active_filters]
    available_columns = [col for col in df.columns 
                        if df[col].dtype in ['object', 'category', 'int64', 'float64'] 
                        and col not in applied_columns]
    
    if not available_columns:
        st.sidebar.info("모든 사용 가능한 컬럼에 필터가 적용되었습니다.")
        return
    
    # 1단계: 새 필터할 컬럼 선택
    new_filter_column = st.sidebar.selectbox(
        "필터할 컬럼 선택:",
        ["선택안함"] + available_columns,
        key=f"new_filter_column_{st.session_state.filter_counter}"
    )
    
    if new_filter_column != "선택안함":
        # 2단계: 컬럼 데이터 로드 및 필터 설정
        if st.sidebar.button("➕ 필터 추가", key=f"add_filter_{st.session_state.filter_counter}"):
            add_new_filter(df, new_filter_column)
            st.session_state.filter_counter += 1
            st.rerun()

def add_new_filter(df, column):
    """새 필터를 추가하는 함수"""
    # 현재 적용된 필터들로 데이터를 먼저 필터링
    filtered_df = apply_current_filters(df)
    
    if df[column].dtype in ['object', 'category']:
        # 범주형 데이터
        unique_values = sorted(filtered_df[column].dropna().unique().tolist())
        filter_info = {
            'column': column,
            'type': 'categorical',
            'all_values': unique_values,
            'selected_values': unique_values.copy()  # 기본적으로 모든 값 선택
        }
    else:
        # 숫자형 데이터
        min_val = float(filtered_df[column].min())
        max_val = float(filtered_df[column].max())
        filter_info = {
            'column': column,
            'type': 'numeric',
            'min_val': min_val,
            'max_val': max_val,
            'selected_range': (min_val, max_val)
        }
    
    st.session_state.active_filters.append(filter_info)

def apply_current_filters(df):
    """현재 적용된 모든 필터를 데이터에 적용"""
    filtered_df = df.copy()
    
    for filter_info in st.session_state.active_filters:
        if filter_info['type'] == 'categorical':
            if filter_info['selected_values']:
                filtered_df = filtered_df[filtered_df[filter_info['column']].isin(filter_info['selected_values'])]
            else:
                filtered_df = filtered_df.iloc[0:0]  # 빈 데이터프레임
        else:  # numeric
            selected_range = filter_info['selected_range']
            filtered_df = filtered_df[
                (filtered_df[filter_info['column']] >= selected_range[0]) & 
                (filtered_df[filter_info['column']] <= selected_range[1])
            ]
    
    return filtered_df

def setup_filter_controls():
    """활성 필터들의 컨트롤 UI 표시"""
    if not st.session_state.active_filters:
        return
    
    st.sidebar.write("**필터 설정:**")
    
    for i, filter_info in enumerate(st.session_state.active_filters):
        with st.sidebar.expander(f"🔧 {filter_info['column']} 설정", expanded=False):
            if filter_info['type'] == 'categorical':
                # 범주형 필터 컨트롤
                unique_values = filter_info['all_values']
                
                # 전체 선택/해제 버튼
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("전체선택", key=f"select_all_{i}"):
                        st.session_state.active_filters[i]['selected_values'] = unique_values.copy()
                        st.rerun()
                with col2:
                    if st.button("전체해제", key=f"deselect_all_{i}"):
                        st.session_state.active_filters[i]['selected_values'] = []
                        st.rerun()
                
                # 각 값별 체크박스
                selected_values = filter_info['selected_values'].copy()
                
                for value in unique_values:
                    current_state = value in selected_values
                    new_state = st.checkbox(
                        f"{value}",
                        value=current_state,
                        key=f"filter_check_{i}_{value}"
                    )
                    
                    if new_state and value not in selected_values:
                        selected_values.append(value)
                    elif not new_state and value in selected_values:
                        selected_values.remove(value)
                
                st.session_state.active_filters[i]['selected_values'] = selected_values
                st.caption(f"선택된 항목: {len(selected_values)}/{len(unique_values)}")
                
            else:
                # 숫자형 필터 컨트롤
                min_val = filter_info['min_val']
                max_val = filter_info['max_val']
                current_range = filter_info['selected_range']
                
                if min_val != max_val:
                    st.write(f"전체 범위: {min_val:.2f} \~ {max_val:.2f}")
                    selected_range = st.slider(
                        "값 범위 선택:",
                        min_value=min_val,
                        max_value=max_val,
                        value=current_range,
                        key=f"filter_range_slider_{i}"
                    )
                    st.session_state.active_filters[i]['selected_range'] = selected_range
                    st.caption(f"선택 범위: {selected_range[0]:.2f} \~ {selected_range[1]:.2f}")


def get_current_settings():
    """현재 세션 상태에서 모든 설정값 가져오기"""
    settings = {
        'y_column': st.session_state.graph_y_column,
        'x_column': st.session_state.graph_x_column,
        'color_column': st.session_state.graph_color_column,
        'show_points': st.session_state.graph_show_points,
        'show_mean': st.session_state.graph_show_mean,
        'filters': st.session_state.active_filters.copy()  # 다중 필터 정보
    }
    
    return settings

def apply_filters_to_data(df, filters_list):
    """다중 필터 설정을 실제 데이터에 적용하는 함수"""
    filtered_df = df.copy()
    
    for filter_info in filters_list:
        if filter_info['type'] == 'categorical':
            # 범주형 필터 적용
            if filter_info['selected_values']:
                filtered_df = filtered_df[filtered_df[filter_info['column']].isin(filter_info['selected_values'])]
            else:
                filtered_df = filtered_df.iloc[0:0]  # 빈 데이터프레임
        else:
            # 숫자형 필터 적용
            selected_range = filter_info['selected_range']
            filtered_df = filtered_df[
                (filtered_df[filter_info['column']] >= selected_range[0]) & 
                (filtered_df[filter_info['column']] <= selected_range[1])
            ]
    
    return filtered_df

def display_data_info(original_df, filtered_df):
    """데이터 수 정보 표시 함수"""
    # 메인 영역에 데이터 정보 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="전체 데이터 수",
            value=f"{len(original_df):,}개"
        )
    
    with col2:
        st.metric(
            label="필터 적용 후 데이터 수",
            value=f"{len(filtered_df):,}개",
            delta=f"{len(filtered_df) - len(original_df):,}개"
        )


def create_boxplot(df, y_column, x_column, color_column, show_points, show_mean, filter_info=None):
    
    # 결측값 제거
    if x_column != "없음" and color_column != "없음":
        plot_df = df[[y_column, x_column, color_column]].dropna()
    elif x_column != "없음":
        plot_df = df[[y_column, x_column]].dropna()
    else:
        plot_df = df[[y_column]].dropna()
    
    if plot_df.empty:
        st.error("선택한 컬럼에 유효한 데이터가 없습니다.")
        return
    
    fig = go.Figure()
    
    if x_column == "없음":
        # 단일 박스플롯
        data = plot_df[y_column]
        
        # 이상치 계산 (IQR 방법)
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        normal_data = data[(data >= lower_bound) & (data <= upper_bound)]
        
        # 박스플롯 추가
        fig.add_trace(go.Box(
            y=data,
            name=y_column,
            boxpoints=False,
            fillcolor='rgba(200,200,200,0.3)',
            line=dict(color='black'),
            showlegend=False
        ))
        
        if show_points:
            # 일반 데이터 포인트 (회색)
            fig.add_trace(go.Scatter(
                x=[y_column] * len(normal_data),
                y=normal_data,
                mode='markers',
                marker=dict(color='gray', size=6, opacity=0.6),
                name='데이터',
                showlegend=True
            ))
            
            # 이상치 (검정색)
            if len(outliers) > 0:
                fig.add_trace(go.Scatter(
                    x=[y_column] * len(outliers),
                    y=outliers,
                    mode='markers',
                    marker=dict(color='yellow', size=8),
                    name='이상치',
                    showlegend=True
                ))
        
        # 평균값 (큰 검정색 점과 값 표시)

        if show_mean:
            mean_val = group_data.mean()
            fig.add_trace(go.Scatter(
                x=[group],
                y=[mean_val],
                mode='markers+text',
                marker=dict(
                    color='black', 
                    size=15,
                    symbol='diamond',
                    line=dict(color='white', width=2)  # ← 이 라인 추가
                ),
                text=[f'{mean_val:.2f}'],
                textposition='top center',
                textfont=dict(  # ← 이 부분 전체 추가
                    size=11,
                    color='black',
                    family='Arial Bold'
                ),
                name='평균',
                showlegend=False,
                legendgroup='mean'
            ))

        title = f"{y_column} 분포"
        
    else:
        # 그룹별 박스플롯
        if color_column != "없음":
            # 색상 그룹이 있는 경우
            color_groups = sorted(plot_df[color_column].unique())  # 정렬 추가
            colors = EXTENDED_COLORS[:len(color_groups)]  # 확장된 색상 팔레트 사용
            color_map = {group: colors[i] for i, group in enumerate(color_groups)}
            
            groups = sorted(plot_df[x_column].unique())  # 정렬 추가
            
            # 각 색상 그룹별로 모든 X축 그룹의 데이터를 한 번에 처리
            for i, color_group in enumerate(color_groups):
                color_data = plot_df[plot_df[color_column] == color_group]
                
                if len(color_data) == 0:
                    continue
                
                # 해당 색상 그룹의 모든 데이터를 한 번에 박스플롯으로 생성
                fig.add_trace(go.Box(
                    x=color_data[x_column],  # 단순한 X축 값 사용
                    y=color_data[y_column],
                    name=f'{color_group}',
                    boxpoints=False,
                    fillcolor=color_map[color_group],
                    line=dict(color=color_map[color_group]),
                    legendgroup=color_group,
                    showlegend=True,  # 모든 색상 그룹을 범례에 표시
                    offsetgroup=color_group,  # 그룹별 오프셋 설정
                    boxmean=show_mean  # 평균 표시 옵션
                ))
                
                if show_points:
                    # 일반 데이터 포인트와 이상치 구분하여 표시
                    for group in groups:
                        group_color_data = color_data[color_data[x_column] == group][y_column]
                        if len(group_color_data) == 0:
                            continue
                        
                        # 이상치 계산
                        Q1 = group_color_data.quantile(0.25)
                        Q3 = group_color_data.quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        outliers = group_color_data[(group_color_data < lower_bound) | (group_color_data > upper_bound)]
                        normal_data = group_color_data[(group_color_data >= lower_bound) & (group_color_data <= upper_bound)]
                        
                        # 일반 데이터 포인트
                        if len(normal_data) > 0:
                            fig.add_trace(go.Scatter(
                                x=[group] * len(normal_data),
                                y=normal_data,
                                mode='markers',
                                marker=dict(color=color_map[color_group], size=4, opacity=0.6),
                                name=f'{color_group} 데이터',
                                showlegend=False,
                                legendgroup=f'{color_group}_normal',
                                offsetgroup=color_group
                            ))
                        
                        # 이상치
                        if len(outliers) > 0:
                            fig.add_trace(go.Scatter(
                                x=[group] * len(outliers),
                                y=outliers,
                                mode='markers',
                                marker=dict(color='yellow', size=6, symbol='x'),
                                name=f'{color_group} 이상치',
                                showlegend=False,
                                legendgroup=f'{color_group}_outliers',
                                offsetgroup=color_group
                            ))
            
            title = f'{y_column} by {x_column} (색상: {color_column})'
            
        else:
            # 색상 그룹이 없는 경우
            groups = sorted(plot_df[x_column].unique())  # 정렬 추가
            
            # 🔧 수정: 전체 데이터를 한 번에 박스플롯으로 생성
            fig.add_trace(go.Box(
                x=plot_df[x_column],  # ← 수정: 전체 X축 데이터를 직접 전달
                y=plot_df[y_column],  # ← 수정: 전체 Y축 데이터를 직접 전달
                name='박스플롯',  # ← 수정: 단순한 이름으로 변경
                boxpoints=False,
                fillcolor='rgba(200,200,200,0.3)',
                line=dict(color='black'),
                showlegend=False,  # 박스플롯은 범례에 표시하지 않음
                boxmean=False  # 평균 표시 옵션 추가
            ))



            # 개별 데이터 포인트 및 이상치 표시 (show_points가 True인 경우)
            if show_points:
                for i, group in enumerate(groups):
                    group_data = plot_df[plot_df[x_column] == group][y_column]
                    
                    if len(group_data) == 0:
                        continue
                    
                    # 이상치 계산
                    Q1 = group_data.quantile(0.25)
                    Q3 = group_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = group_data[(group_data < lower_bound) | (group_data > upper_bound)]
                    normal_data = group_data[(group_data >= lower_bound) & (group_data <= upper_bound)]
                    
                    # 일반 데이터 포인트 (회색)
                    if len(normal_data) > 0:
                        fig.add_trace(go.Scatter(
                            x=[group] * len(normal_data),
                            y=normal_data,
                            mode='markers',
                            marker=dict(color='gray', size=6, opacity=0.6),
                            name='데이터' if i == 0 else '',  # 첫 번째 그룹에서만 범례 표시
                            showlegend=True if i == 0 else False,
                            legendgroup='normal'
                        ))
                    
                    # 이상치 (검정색)
                    if len(outliers) > 0:
                        fig.add_trace(go.Scatter(
                            x=[group] * len(outliers),
                            y=outliers,
                            mode='markers',
                            marker=dict(color='yellow', size=8, symbol='x'),  # ← 수정: 이상치 심볼 변경
                            name='이상치' if i == 0 else '',  # 첫 번째 그룹에서만 범례 표시
                            showlegend=True if i == 0 else False,
                            legendgroup='outliers'
                        ))
            

            if show_mean:  # ← 조건문을 단순하게 변경
                for i, group in enumerate(groups):
                    group_data = plot_df[plot_df[x_column] == group][y_column]

                    if len(group_data) == 0:
                        continue

                    mean_val = group_data.mean()
                    fig.add_trace(go.Scatter(
                        x=[group],
                        y=[mean_val],
                        mode='markers+text',
                        marker=dict(
                            color='White',  # ← 색상 변경
                            size=8,  # ← 크기 증가
                            symbol='diamond',
                            line=dict(color='black', width=2)  # ← 테두리 추가
                        ),
                        text=[f'평균: {mean_val:.1f}'],  # ← 텍스트 형식 변경
                        textposition='top center',
                        textfont=dict(  # ← 이 부분 전체 추가
                            size=12,
                            color='white',
                            family='Arial Black'
                        ),
                        name='평균' if i == 0 else '',
                        showlegend=True if i == 0 else False,
                        legendgroup='mean'
                    ))

            title = f'{y_column} by {x_column}'
   
    
    # Y축 제목에 필터 정보 추가
    y_axis_title = y_column
    if filter_info and len(filter_info) > 0:
        filter_texts = []
        for f_info in filter_info:
            if f_info['type'] == 'categorical':
                selected_count = len(f_info['selected_values'])
                total_count = len(f_info['all_values'])
                if selected_count == total_count:
                    filter_texts.append(f"{f_info['column']}:전체")
                elif selected_count <= 2:
                    filter_texts.append(f"{f_info['column']}:{','.join(map(str, f_info['selected_values']))}")
                else:
                    filter_texts.append(f"{f_info['column']}:{selected_count}개")
            else:
                range_val = f_info['selected_range']
                filter_texts.append(f"{f_info['column']}:{range_val[0]:.1f}\~{range_val[1]:.1f}")
        
        if filter_texts:
            y_axis_title += f" (필터: {', '.join(filter_texts)})"

    
# 레이아웃 업데이트
    fig.update_layout(
        title=title,
        xaxis_title=x_column if x_column != "없음" else "",
        yaxis_title=y_axis_title,
        height=600,
        showlegend=True,
        boxmode='group',  # 박스플롯을 그룹별로 나란히 배치
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        xaxis=dict(
            tickangle=0,  # X축 레이블을 가로로 표시 (0도)
            tickmode='linear',
            automargin=True  # 자동으로 여백 조정하여 레이블이 잘리지 않도록 함
        ),
        margin=dict(r=150)  # 범례 공간 확보
    )
   
    # 그래프 표시
    st.plotly_chart(fig, use_container_width=True)

def show_statistics(df, y_column, x_column):
    """통계 정보 표시 함수"""
    
    st.subheader("통계 정보")
    
    if x_column == "없음":
        # 전체 통계
        stats = df[y_column].describe()
        st.write("전체 데이터 통계:")
        st.dataframe(stats.to_frame().T)
    else:
        # 그룹별 통계
        grouped_stats = df.groupby(x_column)[y_column].describe()
        st.write(f"{x_column}별 {y_column} 통계:")
        st.dataframe(grouped_stats)
        
        # 그룹별 개수
        group_counts = df[x_column].value_counts().sort_index()
        st.write(f"{x_column}별 데이터 개수:")
        st.dataframe(group_counts.to_frame().T)

def create_sample_data():
    """샘플 데이터 생성 함수"""
    np.random.seed(42)
    
    groups = ['Triangle', 'Hexagon', 'Round', 'Star', 'Square']
    categories = ['A', 'B', 'C']
    test_codes = ['TC001', 'TC002', 'TC003', 'TC004', 'TC005']
    air_pressures = ['LL02', 'LL09', 'LP42', 'LS09', 'LS88', 'MC3760A', 'MC3960A']
    test_places = ['Place1', 'Place2', 'Place3']
    
    data = []
    
    for group in groups:
        for category in categories:
            n_samples = np.random.randint(30, 50)
            if group == 'Triangle':
                values = np.random.normal(20, 15, n_samples)
            elif group == 'Hexagon':
                values = np.random.normal(18, 12, n_samples)
            elif group == 'Round':
                values = np.random.normal(22, 18, n_samples)
            elif group == 'Star':
                values = np.random.normal(25, 20, n_samples)
            else:  # Square
                values = np.random.normal(28, 22, n_samples)
            
            # 카테고리별 조정
            if category == 'B':
                values += 5
            elif category == 'C':
                values += 10
            
            # 일부 이상값 추가
            outliers = np.random.normal(70, 10, max(1, n_samples // 20))
            values = np.concatenate([values, outliers])
            
            for value in values:
                data.append({
                    'Group': group, 
                    'Time': max(0, value),
                    'Category': category,
                    'Test Code': np.random.choice(test_codes),
                    'Air Pressure': np.random.choice(air_pressures),
                    'Test Place': np.random.choice(test_places)
                })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Excel 박스플롯 시각화",
        page_icon="📊",
        layout="wide"
    )
    main()