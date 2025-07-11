import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import yaml
from datetime import datetime
import io

# 页面配置
st.set_page_config(
    page_title="交互式世界地图标点系统",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ 交互式世界地图标点系统")
st.markdown("点击地图添加标点，支持顺序调整和YAML导出")

# 初始化session state
if 'points' not in st.session_state:
    st.session_state.points = []
if 'point_counter' not in st.session_state:
    st.session_state.point_counter = 0

# 侧边栏控制面板
with st.sidebar:
    st.header("🎛️ 控制面板")
    
    # 手动刷新地图按钮
    if st.button("🔄 刷新地图", type="primary", help="手动刷新地图以显示最新标点"):
        st.rerun()
    
    # 清除所有标点
    if st.button("🗑️ 清除所有标点", type="secondary"):
        st.session_state.points = []
        st.session_state.point_counter = 0
        if 'last_click' in st.session_state:
            del st.session_state.last_click
        st.rerun()
    
    # 显示当前标点统计
    st.metric("📍 标点总数", len(st.session_state.points))
    
    # 地图设置
    st.subheader("🗺️ 地图设置")
    initial_lat = st.number_input("初始纬度", value=41.698984, format="%.4f")
    initial_lon = st.number_input("初始经度", value=273.763499, format="%.4f")
    zoom_level = st.slider("缩放级别", min_value=1, max_value=18, value=18)
    
    # 自动刷新设置
    st.subheader("⚙️ 行为设置")
    auto_refresh = st.checkbox("添加标点后自动刷新地图", value=False, 
                              help="关闭后需要手动点击'刷新地图'按钮来显示新标点")

# 主要内容区域
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🌍 世界地图")
    
    # 创建地图
    m = folium.Map(
        location=[initial_lat, initial_lon], 
        zoom_start=zoom_level,
        tiles='OpenStreetMap'
    )
    
    # 添加现有标点到地图
    for i, point in enumerate(st.session_state.points):
        folium.Marker(
            location=[point['lat'], point['lon']],
            popup=f"标点 {i+1}\n纬度: {point['lat']:.6f}\n经度: {point['lon']:.6f}",
            tooltip=f"标点 {i+1}",
            icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon')
        ).add_to(m)
        
        # 添加标点编号
        folium.Marker(
            location=[point['lat'], point['lon']],
            icon=folium.DivIcon(
                html=f"""<div style="
                    background-color: white;
                    border: 2px solid red;
                    border-radius: 50%;
                    width: 25px;
                    height: 25px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: bold;
                    font-size: 12px;
                    color: red;
                ">{i+1}</div>""",
                icon_size=(25, 25),
                icon_anchor=(12, 12)
            )
        ).add_to(m)
    
    # 如果有多个标点，绘制连线
    if len(st.session_state.points) > 1:
        coordinates = [[point['lat'], point['lon']] for point in st.session_state.points]
        folium.PolyLine(
            coordinates,
            color='blue',
            weight=3,
            opacity=0.7,
            popup="标点连线"
        ).add_to(m)
    
    # 显示地图并获取点击数据
    map_data = st_folium(m, width=800, height=500, returned_objects=["last_clicked"])
    
    # 处理地图点击事件
    if map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']
        
        # 检查是否是新的点击（避免重复添加）
        last_click_key = f"{lat}_{lon}"
        if 'last_click' not in st.session_state or st.session_state.last_click != last_click_key:
            # 添加新标点
            new_point = {
                'id': st.session_state.point_counter,
                'lat': lat,
                'lon': lon,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.points.append(new_point)
            st.session_state.point_counter += 1
            st.session_state.last_click = last_click_key
            
            # 显示添加成功消息
            st.success(f"✅ 已添加标点 {len(st.session_state.points)}: ({lat:.6f}, {lon:.6f})")
            
            # 根据用户设置决定是否自动刷新
            if auto_refresh:
                st.rerun()
            else:
                st.info("💡 点击侧边栏的'🔄 刷新地图'按钮来显示新标点")

with col2:
    st.subheader("📝 标点列表")
    
    if st.session_state.points:
        # 显示标点列表
        for i, point in enumerate(st.session_state.points):
            with st.container():
                st.markdown(f"""
                **标点 {i+1}**  
                📍 纬度: `{point['lat']:.6f}`  
                📍 经度: `{point['lon']:.6f}`  
                🕐 时间: `{point['timestamp']}`
                """)
                
                # 标点操作按钮
                col_up, col_down, col_del = st.columns(3)
                
                with col_up:
                    if st.button("⬆️", key=f"up_{point['id']}", disabled=(i == 0), help="向上移动标点"):
                        # 向上移动
                        st.session_state.points[i], st.session_state.points[i-1] = \
                            st.session_state.points[i-1], st.session_state.points[i]
                        st.success(f"标点 {i+1} 已向上移动")
                        st.rerun()
                
                with col_down:
                    if st.button("⬇️", key=f"down_{point['id']}", disabled=(i == len(st.session_state.points)-1), help="向下移动标点"):
                        # 向下移动
                        st.session_state.points[i], st.session_state.points[i+1] = \
                            st.session_state.points[i+1], st.session_state.points[i]
                        st.success(f"标点 {i+1} 已向下移动")
                        st.rerun()
                
                with col_del:
                    if st.button("🗑️", key=f"del_{point['id']}", help="删除此标点"):
                        # 删除标点
                        st.session_state.points.pop(i)
                        st.success(f"已删除标点 {i+1}")
                        st.rerun()
                
                st.divider()
        
        # 导出功能
        st.subheader("📤 导出数据")
        
        # 生成YAML数据
        yaml_data = {
            'waypoints': [
                [float(point['lat']), float(point['lon'])] 
                for point in st.session_state.points
            ],
            'metadata': {
                'total_points': len(st.session_state.points),
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'description': '交互式地图标点导出'
            }
        }
        
        # 转换为YAML字符串
        yaml_string = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # 显示YAML预览
        st.text_area("YAML 预览", yaml_string, height=200)
        
        # 下载按钮
        st.download_button(
            label="📥 下载 YAML 文件",
            data=yaml_string,
            file_name=f"waypoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
            mime="application/x-yaml"
        )
        
        # CSV导出（额外功能）
        df = pd.DataFrame([
            {'序号': i+1, '纬度': point['lat'], '经度': point['lon'], '添加时间': point['timestamp']}
            for i, point in enumerate(st.session_state.points)
        ])
        
        csv_string = df.to_csv(index=False)
        st.download_button(
            label="📊 下载 CSV 文件",
            data=csv_string,
            file_name=f"waypoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("🔍 点击地图添加标点")
        st.markdown("""
        **使用说明：**
        1. 在地图上点击添加标点
        2. 使用侧边栏的'🔄 刷新地图'显示新标点
        3. 可开启'自动刷新'避免手动刷新
        4. 使用 ⬆️⬇️ 按钮调整标点顺序
        5. 使用 🗑️ 按钮删除单个标点
        6. 点击导出按钮下载YAML文件
        """)

# 页面底部信息
st.markdown("---")
st.markdown("""
💡 **提示：** 
- 标点按照添加顺序编号，可以随时调整顺序
- 为了更好的用户体验，默认关闭自动刷新，手动刷新可避免界面跳动
- YAML文件包含经纬度坐标数组和元数据信息
- 点击地图后右侧会显示成功消息，如需在地图上看到标点请点击刷新按钮
""") 