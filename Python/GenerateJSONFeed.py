import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

def read_and_process_maven_artifacts(expire_hours=2):
    """
    读取、处理并返回符合条件的 Maven 构件信息
    Args:
        expire_hours: 过期时间（小时），默认2小时前
    Returns:
        list: 处理后的 Maven 构件信息列表，每个元素是包含 ts_publish, group_id, artifact_id 的字典
    """
    file_path = "../Feed/ReleaseQueue.txt"
    # 如果文件不存在，返回空列表
    if not os.path.exists(file_path):
        return []
    # 计算过期时间戳（当前时间减去指定小时数）
    current_time_ms = int(time.time() * 1000)  # 当前时间的毫秒时间戳
    expire_time_ms = current_time_ms - (expire_hours * 60 * 60 * 1000)
    # 用于去重的字典，键为 "group_id:artifact_id"，值为包含完整信息的字典
    unique_artifacts = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # 解析每一行
                parts = line.split("|")
                if len(parts) != 3:
                    continue
                try:
                    ts_publish = int(parts[0])
                    group_id = parts[1]
                    artifact_id = parts[2]
                    # 检查是否过期
                    if ts_publish < expire_time_ms:
                        print(f"构件 {group_id}:{artifact_id} 已到达过期时间，将会按计划删除")
                        continue
                    # 创建唯一键
                    unique_key = f"{group_id}:{artifact_id}"
                    # 如果这个构件已经存在，比较时间戳，保留最新的
                    if unique_key in unique_artifacts:
                        if ts_publish > unique_artifacts[unique_key]["ts_publish"]:
                            unique_artifacts[unique_key] = {
                                "ts_publish": ts_publish,
                                "group_id": group_id,
                                "artifact_id": artifact_id
                            }
                    else:
                        unique_artifacts[unique_key] = {
                            "ts_publish": ts_publish,
                            "group_id": group_id,
                            "artifact_id": artifact_id
                        }
                except (ValueError, IndexError):
                    # 跳过格式不正确的行
                    continue   
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []
    # 转换为列表并按时间戳从小到大排序
    result = list(unique_artifacts.values())
    result.sort(key=lambda x: x["ts_publish"])
    return result

def update_release_queue_file(artifactList):
    """
    将处理后的构件数据按照指定格式覆盖写入到文件中
    Args:
        artifactList: 处理后的构件数据列表，每个元素是包含 ts_publish, group_id, artifact_id 的字典
    Returns:
        bool: 操作是否成功
    """
    file_path = "../Feed/ReleaseQueue.txt"
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 以写入模式打开文件（会覆盖原有内容）
        with open(file_path, "w", encoding="utf-8") as f:
            for artifact in artifactList:
                # 按照指定格式生成每行内容
                cache_key = f"{artifact['ts_publish']}|{artifact['group_id']}|{artifact['artifact_id']}"
                f.write(f"{cache_key}\n")
        
        print(f"成功更新文件 {file_path}，写入 {len(artifactList)} 条记录")
        return True        
    except Exception as e:
        print(f"更新文件时出错: {e}")
        return False


def generate_json_feed():
    # 使用默认的2小时过期时间
    artifactList = read_and_process_maven_artifacts()
    print(f"找到 {len(artifactList)} 个有效的 Maven 构件")
    
    # 创建JSON Feed的基本结构
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "构件发布Feed - Maven中央仓库",
        "home_page_url": "https://github.com/ACANX/MavenArtifact/tree/latest",
        "feed_url": "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/Feed/ReleaseQueue.json",
        "description": "Maven构件发布队列 - Powered by Maven中央仓库Feed",
        "icon": "https://unavatar.webp.se/central.sonatype.com?fallback=true",
        "favicon": "https://unavatar.webp.se/central.sonatype.com?fallback=True",
        "authors": [
            {
                "name": "Maven中央仓库",
                "url": "https://central.sonatype.com/search"
            },
            {
                "name": "ACANX",
                "url": "https://github.com/ACANX/MavenArtifact/tree/latest"
            }
        ],
        "items": []
    }
    
    # 处理每个构件
    for artifact in reversed(artifactList):
        # 解析groupId和artifactId
        group_id = artifact["group_id"]
        artifact_id = artifact["artifact_id"]
        group_id_path = group_id.replace('.', '/')
        
        # 尝试读取构件元数据文件
        artifact_paths = [
            f"../Artifact/{group_id_path}/{artifact_id}.json",
            f"../Maven/Artifact/{group_id_path}/{artifact_id}.json"
        ]
        
        metadata = None
        for path in artifact_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    break
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
        if not metadata:
            print(f"警告: 找不到构件元数据 {group_id}:{artifact_id}")
            continue
        else:
            print(f"找到构件元数据 {group_id}:{artifact_id} 文件")
        # 提取所需字段
        id_val = metadata.get('id', f"{group_id}:{artifact_id}")
        description = metadata.get('description', '')
        group_id_from_meta = metadata.get('group_id', group_id)
        artifact_id_from_meta = metadata.get('artifact_id', artifact_id)
        version_latest = metadata.get('version_latest', '')
        ts_publish = metadata.get('ts_publish', 0)
        ts_update = metadata.get('ts_update', 0)
        tags = metadata.get('tags', [])
        contributors = metadata.get('contributors', [])

        # 生成item
        item = {}
        # id节点
        item['id'] = f"{id_val}@{version_latest}"
        # url节点
        item['url'] = f"https://central.sonatype.com/artifact/{group_id_from_meta}/{artifact_id_from_meta}"
        # title节点
        if description:
            item['title'] = f"{group_id_from_meta}:{artifact_id_from_meta} {version_latest} 发布, {description}"
        else:
            item['title'] = f"{group_id_from_meta}:{artifact_id_from_meta} {version_latest} 发布"
        # content_html节点
        escaped_title = item['title'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        svg_url = f"https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/Badge/{group_id_path}/{artifact_id}.svg"
        # Maven仓库中查看此构件
        url_maven = f"https://repo1.maven.org/maven2/{group_id_path}/{artifact_id}/{version_latest}/"
        # MvnRepository中查看此构件
        url_mvnrepo = f"https://mvnrepository.com/artifact/{group_id}/{artifact_id}/{version_latest}"
        # 项目网址
        url_project = metadata.get('url_project', "")
        # 项目仓库
        url_scm = metadata.get('url_scm', "")
        # 项目HomePage
        url_home_page = metadata.get('home_page', "")

        segment_project = f"<a href=\"{url_project}\"><p><span>项目网址</span></p></a></br>"  if url_project else ""
        segment_scm = f"<a href=\"{url_scm}\"><p><span>仓库地址</span></p></a><br>"  if url_scm else ""
        segment_home_page = f"<a href=\"{url_home_page}\"><p><span>HomePage</span></p></a></br>"  if url_home_page else ""
        
        
        item['content_html'] = f"""<img src=\"https://mvnrepository.com/img/5fd7b8212ae965f2937e0384659a4fc8\" alt=\"{escaped_title}\" /></br>
          <img src=\"{svg_url}\" alt=\"{escaped_title}\" />
          </br>
          </br>
          
          <a href=\"{url_maven}\"><p><span>Maven中央仓库中下载此构件</span></p></a></br>
          <a href=\"{item['url']}\"><p><span>SonaTypeMavenCentralRepository网站中查看此构件</span></p></a></br>
          <a href=\"{url_mvnrepo}\"><p><span>MvnRepository中查看此构件</span></p></a></br>
          {segment_project}
          {segment_scm}
          {segment_home_page}</br>
          
          </br>  
          </br>  
          <h4>GAV坐标<h4>

          <pre>
            <code class=\"language-xml\">
                &lt;dependency&gt;
                    &lt;groupId&gt;{group_id_from_meta}&lt;/groupId&gt;
                    &lt;artifactId&gt;{artifact_id_from_meta}&lt;/artifactId&gt;
                    &lt;version&gt;{version_latest}&lt;/version&gt;
                &lt;/dependency&gt;
            </code>
          </pre>
          
        """
        
        # content_text和summary节点
        item['content_text'] = item['title']
        item['summary'] = item['title']
        
        # date_published和date_modified节点
        if ts_publish:
            item['date_published'] = datetime.fromtimestamp(ts_publish/1000, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if ts_update:
            item['date_modified'] = datetime.fromtimestamp(ts_update/1000, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')    
        # authors节点
        authors = [{"name": "MvnArtifactReleaseQueue"}]
        if contributors:
            for contributor in contributors:
                authors.append({"name": contributor})
            item['authors'] = authors
        # tags节点
        if not tags:
            tags = ["Artifact", "Maven", "Java"]
        item['tags'] = tags
        # attachments节点
        item['attachments'] = [
            {
                "url": "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/Feed/Artifact.svg",
                "mime_type": "image/svg+xml",
                "title": "最新版本元数据信息SVG",
                "size_in_bytes": 12345678,
                "duration_in_seconds": 10
            }
        ]
        feed['items'].append(item)
    # 将处理后的数据写回文件
    update_release_queue_file(artifactList)    
    return feed

def main():
    feed = generate_json_feed()
    if feed:
        # 确保输出目录存在
        output_dir = "../Feed"
        os.makedirs(output_dir, exist_ok=True)
        
        # 输出JSON Feed到指定路径
        output_path = os.path.join(output_dir, "ReleaseQueue.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(feed, f, ensure_ascii=False, indent=2)
        print(f"JSON Feed生成成功: {output_path}")
    else:
        print("JSON Feed生成失败")

if __name__ == "__main__":
    main()
