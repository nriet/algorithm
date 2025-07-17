import xarray as xr
import numpy as np
import json
import subprocess
from pathlib import Path

# 1. 读取 NetCDF 文件并提取指定要素的数据
def extract_variable_data(nc_file_path, variable_name, level):
    # 打开 NetCDF 文件
    ds = xr.open_dataset(nc_file_path)
    
    # 提取指定变量，并根据高度层进行选择
    if level is not None:
        data = ds[variable_name].isel(level=level)  # 根据高度层选择数据
    else:
        data = ds[variable_name]  # 如果没有高度层，直接提取变量
    
    # 处理缺失值 (根据文件中的 _FillValue)
    data = data.where(data != 9999.0)
    
    # 转换为 numpy 数组
    data_values = data.values
    
    # 获取经纬度信息
    lats = ds['lat'].values
    lons = ds['lon'].values
    
    return data_values, lats, lons

# 2. 准备 D3.js 脚本
def generate_d3_script(data, width, height, thresholds, smooth=True):
    js_data = json.dumps(data.flatten().tolist())
    
    script = f"""
    const d3 = require('d3-contour');
    
    const data = {js_data};
    const width = {width};
    const height = {height};
    const thresholds = {json.dumps(thresholds)};
    const smooth = {'true' if smooth else 'false'};
    
    const contours = d3.contours()
        .size([width, height])
        .thresholds(thresholds)
        .smooth(smooth)(data);
    
    console.log(JSON.stringify(contours));
    """
    
    return script

# 3. 使用 Node.js 执行 D3.js 脚本
def run_d3_contour(script):
    script_path = Path('main.js')
    script_path.write_text(script)
    
    try:
        # node_path = "/home/jovyan/.nvm/versions/node/v22.17.1/bin/node"  # 替换为你所需的 Node.js 版本
        node_path = "node"  # 替换为你所需的 Node.js 版本
        
        result = subprocess.run(
            [node_path, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        contours = json.loads(result.stdout)
        return contours
    except subprocess.CalledProcessError as e:
        print(f"Error running Node.js script: {e}")
        print(f"STDERR: {e.stderr}")
        return None
    finally:
        script_path.unlink(missing_ok=True)

# 统一接口入口
def process_netcdf(nc_file_path, variable_name, level, thresholds, output_json_path):
    # 1. 提取数据
    data, lats, lons = extract_variable_data(nc_file_path, variable_name, level)
    print(f"{variable_name} data shape: {data.shape}")
    
    # 2. 准备 D3.js 参数
    width = data.shape[1]  # 经度维度
    height = data.shape[0]  # 纬度维度
    #thresholds = [2, 3, 5]  # 等值线阈值 (根据要素类型调整)
    
    # 3. 生成 D3.js 脚本
    d3_script = generate_d3_script(
        data,
        width,
        height,
        thresholds,
        smooth=True
    )
    
    # 4. 运行 D3.js 并获取等值线
    contours = run_d3_contour(d3_script)
    
    if contours:
        print(f"Generated {len(contours)} contour lines")
        # 保存等值线数据
        with open(output_json_path, 'w') as f:
            json.dump(contours, f, indent=2)
        print(f"Contours saved to {output_json_path}")

# 主函数示例调用
if __name__ == '__main__':
    # 设置参数
    nc_file_path = 'data/test.nc'
    variable_name = 'tmax'  # 要素名称
    level = None  # 高度层（如果没有高度层，设为 None）
    output_json_path = 'data/tmax.json'  # 输出路径
    thresholds = [2]  # 等值线阈值 (根据要素类型调整)

    # 调用统一接口
    process_netcdf(nc_file_path, variable_name, level, thresholds, output_json_path)
