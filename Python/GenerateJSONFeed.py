import json
import os
import time
from datetime import datetime
from urllib.parse import quote

def generate_json_feed():
    # 读取索引文件
    index_path = "../Maven/Version/_index.json"
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            # 从JSON对象的"list"子节点获取artifact_list
            artifact_list = index_data.get("list", [])
    except FileNotFoundError:
        print(f"错误: 找不到索引文件 {index_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 索引文件 {index_path} 格式不正确")
        return None
    
    # 创建JSON Feed的基本结构
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "构件发布队列 - Maven中央仓库RSS",
        "home_page_url": "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/",
        "feed_url": "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/Feed/ReleaseQueue.json",
        "description": "Maven构件发布队列 - Powered by Maven中央仓库RSS",
        "icon": "https://unavatar.webp.se/central.sonatype.com?fallback=true",
        "favicon": "https://unavatar.webp.se/central.sonatype.com?fallback=True",
        "authors": [
            {
                "name": "Maven中央仓库RSS",
                "url": "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/"
            }
        ],
        "items": []
    }
    
    # 处理每个构件
    for artifact_str in artifact_list:
        # 解析groupId和artifactId
        parts = artifact_str.split('|')
        if len(parts) < 2:
            print(f"警告: 跳过格式不正确的条目: {artifact_str}")
            continue
            
        group_id = parts[0]
        artifact_id = parts[1]
        group_id_path = group_id.replace('.', '/')
        
        # 尝试读取构件元数据文件
        artifact_paths = [
            f"../Maven/Artifact/{group_id_path}/{artifact_id}.json",
            f"../Artifact/{group_id_path}/{artifact_id}.json"
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
        item['url'] = "https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/"
        
        # title节点
        if description:
            item['title'] = f"{group_id_from_meta}:{artifact_id_from_meta} {version_latest} 发布, {description}"
        else:
            item['title'] = f"{group_id_from_meta}:{artifact_id_from_meta} {version_latest} 发布"
        
        # content_html节点
        escaped_title = item['title'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        svg_url = f"https://raw.githubusercontent.com/ACANX/MavenArtifact/refs/heads/latest/Badge/{group_id_path}/{artifact_id}.svg"
        item['content_html'] = f"<img src=\"{svg_url}\" alt=\"{escaped_title}\">{group_id_from_meta}:{artifact_id_from_meta} {version_latest} 发布</img>"
        
        # content_text和summary节点
        item['content_text'] = item['title']
        item['summary'] = item['title']
        
        # date_published和date_modified节点
        if ts_publish:
            item['date_published'] = datetime.utcfromtimestamp(ts_publish/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
        if ts_update:
            item['date_modified'] = datetime.utcfromtimestamp(ts_update/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # authors节点
        authors = [{"name": "MvnArtifactReleaseQueue"}]
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
                "url": svg_url,
                "mime_type": "image/svg+xml",
                "title": "最新版本元数据信息SVG",
                "size_in_bytes": 12345678,
                "duration_in_seconds": 10
            }
        ]
        
        feed['items'].append(item)
    
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
