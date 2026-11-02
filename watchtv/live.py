import requests
import re
import os

# ========== 源配置，区分处理规则 ==========
# 格式：(url, 类型, 规则参数)
# type = "keyword" 关键词匹配模式
# type = "groupmap" 分组映射模式
SOURCE_LIST = [
    (   #"https://lihansong.top/iptv/src/yf.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt",
        "keyword",
        {
            "keywords": ["华数", "晴彩"],
            "out_group": "HS数字频道"
        }
    ),
    (
        "https://raw.githubusercontent.com/djshxjsh233/migu/refs/heads/main/live.txt",
        "groupmap",
        {
            "map": {
                "央视·省流": "HS咪咕",
                "卫视频道": "HS咪咕",
                "cgtn": "HS咪咕",
                "教育频道": "HS咪咕",
                "本地频道": "HS咪咕",
                "浙江": "Z视介"
            }
        }
    )
]


def parse_any(text: str):
    res = []
    extinf_line = None
    current_group = None
    for raw_line in text.splitlines():
        ln = raw_line.strip()
        if not ln:
            continue
        if ln.startswith("#EXTINF:"):
            extinf_line = ln
            continue
        if extinf_line is not None and not ln.startswith("#"):
            res.append((extinf_line, ln))
            extinf_line = None
            continue
        # 处理 #genre# txt格式
        if ',' in ln and not ln.startswith("#"):
            sp = ln.split(',', 1)
            name_part = sp[0].strip()
            url_part = sp[1].strip()
            if url_part == "#genre#":
                current_group = name_part
                continue
            if current_group:
                fake_ext = f'#EXTINF:-1 group-title="{current_group}",{name_part}'
            else:
                fake_ext = f'#EXTINF:-1,{name_part}'
            res.append((fake_ext, url_part))
    return res


def get_channel_name(extinf):
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return ""


def get_group_title(extinf):
    m = re.search(r'group-title="([^"]+)"', extinf)
    if m:
        return m.group(1).strip()
    return ""


def main():
    channel_list = []
    seen = set()

    for url, mode, cfg in SOURCE_LIST:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channels = parse_any(resp.text)
            for extinf, play_url in channels:
                ch_name = get_channel_name(extinf)
                ch_group = get_group_title(extinf)
                output_group = None

                if mode == "keyword":
                    # 华数、晴彩 关键词匹配
                    kw_list = cfg["keywords"]
                    if any(kw in ch_name or kw in ch_group for kw in kw_list):
                        output_group = cfg["out_group"]

                elif mode == "groupmap":
                    # 咪咕源，分组映射
                    group_map = cfg["map"]
                    if ch_group in group_map:
                        output_group = group_map[ch_group]

                if output_group is None:
                    continue

                # 去重：频道名+链接
                item_key = (ch_name, play_url)
                if item_key not in seen:
                    seen.add(item_key)
                    channel_list.append((output_group, ch_name, play_url))
        except Exception as e:
            print(f"⚠️ 拉取 {url} 失败：{e}")

    total_cnt = len(channel_list)
    print(f"✅筛选结束，共提取 {total_cnt} 个频道")
    out_dir = os.path.dirname(os.path.abspath(__file__))
    output_m3u = ["#EXTM3U"]
    for output_group, cname, curl in channel_list:
        fake_ext = f'#EXTINF:-1 group-title="{output_group}",{cname}'
        output_m3u.append(fake_ext)
        output_m3u.append(curl)

    m3u8_path = os.path.join(out_dir, "live.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_m3u))
    print(f"✅已输出 m3u8：{m3u8_path}")


if __name__ == "__main__":
    main()
