import xarray as xr
import numpy as np
import json
import subprocess
from pathlib import Path

# 1. 读取 NetCDF 文件并提取 ETO2M 数据
def extract_eto2m_data(nc_file_path):
    # 打开 NetCDF 文件
    ds = xr.open_dataset(nc_file_path)
    
    # 提取 ETO2M 变量 (2米温度)
    eto2m = ds['ETO2M']
    
    # 处理缺失值 (根据文件中的 _FillValue)
    eto2m = eto2m.where(eto2m != 9999.0)
    
    # 转换为 numpy 数组并转置 (如果需要调整维度顺序)
    data = eto2m.values
    
    # 获取经纬度信息
    lats = ds['g0_lat_0'].values
    lons = ds['g0_lon_0'].values
    
    return data, lats, lons

# 2. 准备 D3.js 脚本
def generate_d3_script(data, width, height, thresholds, smooth=True):
    # 将数据转换为 JavaScript 数组格式
    js_data = json.dumps(data.flatten().tolist())
    
    # 创建 D3.js 脚本
    script = f"""
    const d3 = require('d3-contour');
    
    // 输入数据
    const data = {js_data};
    const width = {width};
    const height = {height};
    const thresholds = {json.dumps(thresholds)};
    const smooth = {'true' if smooth else 'false'};
    
    // 生成等值线
    const contours = d3.contours()
        .size([width, height])
        .thresholds(thresholds)
        .smooth(smooth)(data);
    
    // 输出结果
    console.log(JSON.stringify(contours));
    """
    
    return script

# 3. 使用 Node.js 执行 D3.js 脚本
def run_d3_contour(script):
    # 创建临时脚本文件
    script_path = Path('temp_contour_script.js')
    script_path.write_text(script)
    
    try:
        # 指定 Node.js 的完整路径
        node_path = "node"  # 替换为你所需的 Node.js 版本
        
        # 执行 Node.js 脚本
        result = subprocess.run(
            [node_path, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 解析输出
        contours = json.loads(result.stdout)
        return contours
    except subprocess.CalledProcessError as e:
        print(f"Error running Node.js script: {e}")
        print(f"STDERR: {e.stderr}")
        return None
    finally:
        # 删除临时文件
        script_path.unlink(missing_ok=True)

# 主函数
def main():
    # NetCDF 文件路径
    nc_file_path = '/home/zhfx/data/NAFP/NAFP_EC_C1D_SURF_GLB_FTM/2024/202412/20241204/PRODUCT_20241204000000_072.nc'
    
    # 1. 提取数据
    eto2m_data, lats, lons = extract_eto2m_data(nc_file_path)
    print(f"ETO2M data shape: {eto2m_data.shape}")
    
    # 2. 准备 D3.js 参数
    width = eto2m_data.shape[1]  # 经度维度
    height = eto2m_data.shape[0]  # 纬度维度
    thresholds = [ 2, 3,5]    # 等值线阈值 (根据温度范围调整)
    
    # 3. 生成 D3.js 脚本
    d3_script = generate_d3_script(
        eto2m_data,
        width,
        height,
        thresholds,
        smooth=True
    )
    
    # 4. 运行 D3.js 并获取等值线
    contours = run_d3_contour(d3_script)
    
    if contours:
        print(f"Generated {len(contours)} contour lines")
        # 这里可以保存或处理等值线数据
        with open('contours.json', 'w') as f:
            json.dump(contours, f, indent=2)
        print("Contours saved to contours.json")

if __name__ == '__main__':
    main()