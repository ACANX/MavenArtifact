import os
import pathlib
import json
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone, timedelta

# 标记文件路径
FLAG_FILE = "./ApacheArtifact.flag"

def convertUtcMillisToBeijingStr(utc_millis):
    """
    将毫秒级UTC时间戳转换为北京时间的字符串格式
    格式: "YYYY-MM-DD HH:MM:SS.fff"
    """
    # 转换为秒（浮点数）
    utc_seconds = utc_millis / 1000.0
    # 创建UTC时间对象
    utc_time = datetime.fromtimestamp(utc_seconds, tz=timezone.utc)
    # 转换为北京时间 (UTC+8)
    beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
    # 格式化为目标字符串（毫秒保留3位）
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 截取微秒的前3位作为毫秒


# 获取索引文件路径
def getIndexFile() -> pathlib.Path:
    current_file = pathlib.Path(__file__).resolve()
    return current_file.parent.parent / "Maven" / "Artifact" / "_index.json"

# 获取扩展元数据索引文件路径
def getArtifactIndexFile() -> pathlib.Path:
    current_file = pathlib.Path(__file__).resolve()
    return current_file.parent.parent / "Maven" / "Version" / "_index.json"

# 读取索引文件中的时间戳
def readLastTimestamp() -> int:
    indexFile = getIndexFile()
    try:
        if indexFile.exists():
            with open(indexFile, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ts_update", 0)
    except Exception as e:
        print(f"❌ 读取索引文件失败: {e}")
    return 0

# 更新索引文件中的时间戳
def updateLastTimestamp(tsUpdate: int):
    indexFile = getIndexFile()
    try:
        indexFile.parent.mkdir(parents=True, exist_ok=True)
        with open(indexFile, "w", encoding="utf-8") as f:
            json.dump({"ts_update": tsUpdate}, f, indent=2)
        print(f"✅ 更新索引文件: {indexFile} (ts={tsUpdate})")
    except Exception as e:
        print(f"❌ 更新索引文件失败: {e}")

# 读取扩展元数据索引
def readExtMetadataIndex() -> List[str]:
    indexFile = getArtifactIndexFile()
    try:
        if indexFile.exists():
            with open(indexFile, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("list", {})
    except Exception as e:
        print(f"❌ 读取扩展元数据索引失败: {e}")
    return {}

# 更新扩展元数据索引
def updateArtifactIndex(artifactIndex: set[str]) -> None:
    indexFile = getArtifactIndexFile()
    try:
        indexFile.parent.mkdir(parents=True, exist_ok=True)
        # 读取现有索引（如果存在）
        current_data = {}
        if indexFile.exists():
            with open(indexFile, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        # 更新映射数据
        current_data["list"] = artifactIndex
        with open(indexFile, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 更新扩展元数据索引文件: {indexFile}")
    except Exception as e:
        print(f"❌ 更新扩展元数据索引失败: {e}")

def createMavenArtifactBadgeSvgFile(data: dict):
    """创建包含详细构件信息的 Maven 徽章 SVG 文件（垂直布局）"""
    # 安全提取构件数据
    group_id = data.get("group_id", "")
    artifact_id = data.get("artifact_id", "")
    latest_version = data.get("latest_version", "N/A")
    dep_count = data.get("dep_count", 0)
    ref_count = data.get("ref_count", 0)
    # 安全处理分类数据
    categories = data.get("categories", [])
    if not isinstance(categories, list):
        categories = []
    # 限制显示的分类数量
    displayed_categories = categories[:3]  # 最多显示3个分类
    categories_text = ", ".join(displayed_categories)
    if len(categories) > 3:
        categories_text += ", ..."
    # 获取当前 Python 文件的绝对路径
    current_file = pathlib.Path(__file__).resolve()
    # 构建目标路径: ../Maven/Badge/groupId/artifactId.svg
    target_dir = (
        current_file.parent              # PythonExec.py 所在目录
        .parent                          # 上一级目录 (../)
        / "Badge"                        # 进入 Badge 目录
        / group_id.replace(".", "/")     # 将 groupId 的点替换为路径分隔符
    )
    target_file = target_dir / f"{artifact_id}.svg"
    # 创建目录（如果不存在）
    target_dir.mkdir(parents=True, exist_ok=True)
    # 创建 SVG 文件内容 - 垂直布局
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240" viewBox="0 0 800 240">
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#4a90e2"/>
    <stop offset="100%" stop-color="#9013fe"/>
  </linearGradient>
  <rect width="100%" height="100%" rx="5" ry="5" fill="url(#grad)"/>
  <g transform="translate(15, 15)">
    <text x="0" y="10" font-family="Arial" font-size="18" fill="white" font-weight="bold" width="260">GroupID:</text>
    <text x="110" y="10" font-family="Arial" font-size="18" fill="white" font-weight="bold" width="460">{group_id}</text>
    <text x="0" y="40" font-family="Arial" font-size="18" fill="white" font-weight="bold" width="260">ArtifactID:</text>
    <text x="110" y="40" font-family="Arial" font-size="18" fill="white" font-weight="bold" width="460">{artifact_id}</text>    
    <text x="0" y="70" font-family="Arial" font-size="18" fill="white" font-weight="bold">最新版本:</text>
    <text x="110" y="70" font-family="Arial" font-size="18" fill="white" font-weight="bold"><tspan font-weight="bold">{latest_version}</tspan></text>
    <text x="0" y="100" font-family="Arial" font-size="18" fill="white" font-weight="bold">依赖数: </text>
    <text x="110" y="100" font-family="Arial" font-size="18" fill="white"><tspan font-weight="bold">{dep_count}</tspan></text>
    <text x="0" y="130" font-family="Arial" font-size="18" fill="white" font-weight="bold">引用量: </text>  
    <text x="110" y="130" font-family="Arial" font-size="18" fill="white"><tspan font-weight="bold">{ref_count}</tspan></text>  
    <text x="0" y="160" font-family="Arial" font-size="18" fill="white" font-weight="bold">分类:</text>
    <text x="10" y="190" font-family="Arial" font-size="10" fill="white"><tspan font-weight="bold">{categories_text}</tspan></text>
    <ellipse  cx="600" cy="120" rx="140" ry="60"  fill="#ff4081"/>
    <text x="600" y="120" text-anchor="middle" font-family="Arial" font-size="24" fill="white" font-weight="bold">MavenArtifactBadge</text>
  </g>
  <text x="720" y="225" font-family="Arial" font-size="3" fill="#d0d0d0">由MavenArtifactBadgeGenerator生成</text>
</svg>"""
    
    # 写入文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"✅ 徽章文件已创建: {target_file}")
    return target_file


def createMavenArtifactJsonFile(data: dict):
    """将构件数据以JSON格式保存到文件中"""
    # 安全提取构件数据
    group_id = data.get("group_id", "")
    artifact_id = data.get("artifact_id", "")
    if not group_id or not artifact_id:
        print("⚠️ 无法创建JSON文件: 缺少 group_id 或 artifact_id")
        return
    # 获取当前 Python 文件的绝对路径
    current_file = pathlib.Path(__file__).resolve()
    # 构建目标路径: ../Maven/Artifact/groupId/artifactId.json
    target_dir = (
        current_file.parent              # PythonExec.py 所在目录
        .parent                          # 上一级目录 (../)
        / "Maven"                        # 进入 Maven 目录
        / "Artifact"                     # 进入 Artifact 目录
        / group_id.replace(".", "/")     # 将 groupId 的点替换为路径分隔符
    )
    target_file = target_dir / f"{artifact_id}.json"
    # 创建目录（如果不存在）
    target_dir.mkdir(parents=True, exist_ok=True)
    # 准备要保存的数据（排除不需要的字段）
    save_data = {
        "id": data.get("id", ""),
        "description": data.get("description", ""),
        "group_id": group_id,
        "artifact_id": artifact_id,
        "version_latest": data.get("latest_version", "N/A"),
        "ts_publish": data.get("ts", 0),
        "dt_publish": convertUtcMillisToBeijingStr(data.get("ts_publish", 0)),
        "ts_update": int(time.time() * 1000),  # 添加当前时间戳作为最后更新时间
        "dt_update": convertUtcMillisToBeijingStr(int(time.time() * 1000)),
        "count_dep": data.get("dep_count", 0),
        "count_ref": data.get("ref_count", 0),
        "licenses": data.get("licenses", []),
        "categories": data.get("categories", []),
        "dsv": 1
    }
    try:
        # 写入JSON文件
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON文件已创建: {target_file}")
        return target_file
    except Exception as e:
        print(f"❌ 创建JSON文件失败: {e}")
        return None

def fetchMavenComponentsPage(page: int, searchTerm: str) -> List[Dict[str, Any]]:
    """从 Sonatype Central 获取指定页的 Maven 构件数据"""
    url = "https://central.sonatype.com/api/internal/browse/components"
    headers = {
        "User-Agent": "MavenBadgeGenerator/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "page": page,
        "size": 20,
        "searchTerm": searchTerm,
        "sortField": "publishedDate",
        "sortDirection": "desc",
        "filter": []
    }
    print(f"⏳ 正在获取第 {page+1} 页构件数据...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # 检查 HTTP 错误
        data = response.json()
        return data.get("components", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return []
    except json.JSONDecodeError:
        print("❌ 响应解析失败: 无效的 JSON 格式")
        return []

def parseComponentData(component: Dict[str, Any]) -> Dict[str, Any]:
    """解析单个构件元数据"""
    return {
        "id": component.get("id", ""),
        "group_id": component.get("namespace", ""),
        "artifact_id": component.get("name", ""),
        "latest_version": component.get("latestVersionInfo", {}).get("version", "N/A"),
        "ts_publish": component.get("latestVersionInfo", {}).get("timestampUnixWithMS", int(time.time() * 1000-300*1000)),
        "description": component.get("description", ""),
        "licenses": component.get("latestVersionInfo", {}).get("licenses", []),
        "dep_count": component.get("dependentOnCount", 0),
        "ref_count": component.get("dependencyOfCount", 0),
        "categories": component.get("categories", [])
    }

def collectComponents():
    """为所有获取到的构件生成徽章"""
    print(f"⏳开始采集SnoaType构件数据")
    # 读取上次处理的最新构件时间戳
    last_ts = readLastTimestamp()
    print(f"⏱️ 上次处理的最新构件时间戳: {last_ts}")
    # 读取扩展元数据索引
    artifactIndex = readExtMetadataIndex()
    print(f"📋 已加载扩展元数据索引: {len(artifactIndex)} 个构件记录")
    # 记录本次执行中最新构件的时间戳
    new_last_ts = None
    page = 0
    processed_count = 0
    while True:
        print("================================================================================================================================================================================")
        print(f"📌开始采集及处理第{page+1}页的SnoaType构件数据")
        components = fetchMavenComponentsPage(page, "")
        if not components:
            print("⏹️ 没有更多构件数据")
            break
        # 处理当前页的每个构件
        page_processed = 0
        page_last_ts = 0
        for component in components:
            data = parseComponentData(component)
            # 如果是第一页的第一个构件，记录为新的时间戳
            if page == 0 and new_last_ts is None:
                new_last_ts = data["ts"]
                print(f"📌 记录新时间戳: {new_last_ts}")            
            # 处理有效构件
            if data['group_id'] and data['artifact_id']:
                print(f"🔍 处理构件 (ts={data['ts']}):   {data['group_id']}:{data['artifact_id']}       {data['latest_version']}   依赖数量: {data['dep_count']}    被引用量: {data['ref_count']}")
                if data['categories']:
                    categories_str = ", ".join(data['categories'])
                    print(f"   分类: {categories_str}")
                else:
                    print("   分类: 无")
                # 创建徽章文件
                createMavenArtifactBadgeSvgFile(data)
                # 创建JSON数据文件
                createMavenArtifactJsonFile(data)
                # 更新扩展元数据索引
                key = f"data['group_id']}|{data['artifact_id']}"
                artifactIndex.add(key)
                print(f"   🔖 更新索引: {key}")
                processed_count += 1
                page_processed += 1
            else:
                print(f"⚠️ 跳过无效构件: {data.get('group_id', '')}:{data.get('artifact_id', '')}")
            # 更新最早的构件时间戳    
            page_last_ts = data["ts"]
        # 如果当前页没有处理任何构件或遇到已处理构件，停止翻页
        if page_processed == 0:
            print("⏹️ 当前页无新构件，停止翻页")
            break
        # 检查是否达到上次处理的时间点
        if page_last_ts < last_ts:
            print(f"⏹️ 遇到已处理构件 (ts={page_last_ts})，停止处理")
            break
        print(f"✅ 已处理完成第 {page+1} 页的数据，共更新{page_processed}条数据")    
        print("")    
        print("")    
        # 继续下一页
        page += 1
    # 更新扩展元数据索引文件
    if processed_count > 0:
        updateArtifactIndex(artifactIndex)
        print(f"✅ 已更新扩展元数据索引，新增 {processed_count} 条记录")
    else:
        print("ℹ️ 无新构件，无需更新扩展元数据索引")
    # 更新索引文件中的时间戳
    if new_last_ts is not None:
        updateLastTimestamp(new_last_ts)
    print(f"\n🎉 处理完成! 共处理 {processed_count} 个新构件")


def collectApacheComponents() -> bool:
    """获取所有（前300页）的Apache构件"""
    print(f"⏳开始采集Apache构件数据")
    try:
        # 读取扩展元数据索引
        artifactIndex = readExtMetadataIndex()
        print(f"📋 已加载扩展元数据索引: {len(artifactIndex)} 个构件记录")
        processed_count = 0
        for page in range(300, -1, -1):
            print("================================================================================================================================================================================")
            print(f"📌开始采集及处理第{page+1}页的Apache构件数据")
            components = fetchMavenComponentsPage(page, "org.apache.")
            if not components:
                print("⏹️ 没有更多构件数据")
                break
            # 处理当前页的每个构件
            page_processed = 0
            for component in components:
                data = parseComponentData(component)        
                # 处理有效构件
                if data['group_id'] and data['artifact_id']:
                    print(f"🔍 处理构件 (ts={data['ts']}):   {data['group_id']}:{data['artifact_id']}       {data['latest_version']}")
                    print(f"   依赖数量: {data['dep_count']}    被引用量: {data['ref_count']}")
                    if data['categories']:
                        categories_str = ", ".join(data['categories'])
                        print(f"   分类: {categories_str}")
                    else:
                        print("   分类: 无")
                    # 创建徽章文件
                    createMavenArtifactBadgeSvgFile(data)
                    # 创建JSON数据文件
                    createMavenArtifactJsonFile(data)
                    # 更新扩展元数据索引
                    key = f"{data['group_id']}:{data['artifact_id']}"
                    artifactIndex.add(key)
                    print(f"   🔖 更新扩展索引: {key} -> {data['ts']}")
                    processed_count += 1
                    page_processed += 1
                else:
                    print(f"⚠️ 跳过无效构件: {data.get('group_id', '')}:{data.get('artifact_id', '')}")            
            # 如果当前页没有处理任何构件或遇到已处理构件，停止翻页
            if page_processed == 0:
                print("⏹️ 当前页无新构件，停止翻页")
                break
            print(f"✅ 已处理完成第 {page+1} 页的数据，共更新{page_processed}条数据")
        # 更新扩展元数据索引文件
        if processed_count > 0:
            updateArtifactIndex(artifactIndex)
            print(f"✅ 已更新扩展元数据索引，新增 {processed_count} 条记录")
        else:
            print("ℹ️ 无新构件，无需更新扩展元数据索引")
        print(f"\n🎉 处理完成! 共处理 {processed_count} 个新构件")
        # 假设执行成功
        return True
    except Exception as e:
        print(f"Apache组件收集失败: {str(e)}")
        return False

def getCurrentWeekKey() -> str:
    """生成当前周的唯一标识（年+周数）"""
    today = date.today()
    year, week, _ = today.isocalendar()
    return f"{year}-{week:02d}"

def checkApacheFlag() -> Optional[str]:
    """检查标记文件是否存在并返回当前周标记"""
    if not os.path.exists(FLAG_FILE):
        return None
    try:
        with open(FLAG_FILE, "r") as f:
            return f.read().strip()
    except:
        return None

def updateApacheFlag():
    """更新标记文件为当前周"""
    week_key = getCurrentWeekKey()
    with open(FLAG_FILE, "w") as f:
        f.write(week_key)

def runComponentCollection():
    """执行组件收集的主控制逻辑"""
    current_week_key = getCurrentWeekKey()
    stored_week_key = checkApacheFlag()
    # 获取当前日期信息
    today = date.today()
    is_sunday = today.weekday() == 6  # 周天（0代表周一, 6代表周天）
    # 执行逻辑判断
    if is_sunday:
        if stored_week_key == current_week_key:
            print("✅ 本周Apache组件已收集，执行常规收集")
            collectComponents()
        else:
            print("⏳ 周一尝试执行Apache组件收集...")
            if collectApacheComponents():
                updateApacheFlag()
                print("✅ Apache组件收集成功，标记已更新")
            else:
                print("⚠️ Apache组件收集失败，执行常规收集")
                # collectComponents()
    else:
        if stored_week_key == current_week_key:
            print("✅ 本周Apache组件已收集，执行常规收集")
        else:
            print("📅 非周天，执行常规收集")
        collectComponents()

# 示例使用
if __name__ == "__main__":
    runComponentCollection()

