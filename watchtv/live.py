import requests
import re
import os

# ========== 填写源的地址 ==========
URL_LIST = [
    "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
]

# ========== 关键词列表：包含任意一个就收录 ==========
KEYWORDS = ["华数", "晴彩"]
# 输出统一分组名
OUTPUT_GROUP_NAME = "HS数字频道"


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


def main():
    channel_list = []
    seen = set()

    for url in URL_LIST:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channels = parse_any(resp.text)
            for extinf, play_url in channels:
                ch_name = get_channel_name(extinf)
                # 只要包含任意一个关键词就收录
                if any(k in ch_name for k in KEYWORDS):
                    item_key = (ch_name, play_url)
                    if item_key not in seen:
                        seen.add(item_key)
                        channel_list.append((ch_name, play_url))
        except Exception as e:
            print(f"⚠️ 拉取 {url} 失败：{e}")

    total_cnt = len(channel_list)
    print(f"✅筛选结束，共提取 {total_cnt} 个【华数/晴彩】频道")

    output_m3u = ["#EXTM3U"]
    for cname, curl in channel_list:
        fake_ext = f'#EXTINF:-1 group-title="{OUTPUT_GROUP_NAME}",{cname}'
        output_m3u.append(fake_ext)
        output_m3u.append(curl)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    m3u8_path = os.path.join(out_dir, "live.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_m3u))  # ✅这里修正了，原来是 output_m3u8

    print(f"✅已输出 m3u8：{m3u8_path}")


if __name__ == "__main__":
    main()
