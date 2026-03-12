from __future__ import annotations

from pathlib import Path

import streamlit as st

from image_manager.analytics import duplicate_groups, stale_images, top_favorites
from image_manager.config import load_config, save_config
from image_manager.db import connect_db, init_db
from image_manager.indexer import scan_and_index
from image_manager.search import semantic_search, mark_used

st.set_page_config(page_title="IM 图像管理器", layout="wide", page_icon="🖼️")

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.card {background: #f8fafc; border-radius: 14px; padding: 14px 16px; border: 1px solid #e2e8f0;}
.small {color: #64748b; font-size: 0.9rem;}
h1, h2, h3 {letter-spacing: 0.2px;}
</style>
""",
    unsafe_allow_html=True,
)

cfg = load_config()

st.title("🖼️ IM 图像管理器")
st.caption("快速检索表情包/截图/GIF：文字 + 语义 + 使用偏好分析")

with st.sidebar:
    st.header("⚙️ 设置")
    image_dir = st.text_input("图片根目录", value=cfg["image_dir"])
    db_path = st.text_input("索引数据库路径", value=cfg["db_path"])
    top_k = st.slider("检索返回数量", 6, 100, int(cfg["top_k"]))

    st.markdown("---")
    st.subheader("索引能力")
    enable_semantic = st.toggle("语义向量检索（推荐）", value=bool(cfg["enable_semantic"]))
    enable_caption = st.toggle("自动图片描述", value=bool(cfg["enable_caption"]))
    enable_ocr = st.toggle("OCR 文字识别", value=bool(cfg["enable_ocr"]))

    if st.button("💾 保存设置", use_container_width=True):
        save_config(
            {
                "image_dir": image_dir,
                "db_path": db_path,
                "top_k": top_k,
                "enable_semantic": enable_semantic,
                "enable_caption": enable_caption,
                "enable_ocr": enable_ocr,
            }
        )
        st.success("设置已保存")

conn = connect_db(db_path)
init_db(conn)

summary = conn.execute("SELECT COUNT(*) AS c, SUM(use_count) AS used FROM images").fetchone()
used_total = int(summary["used"] or 0)
count_total = int(summary["c"] or 0)

m1, m2, m3 = st.columns(3)
m1.metric("已索引图片", count_total)
m2.metric("累计使用记录", used_total)
m3.metric("当前返回上限", top_k)

left, right = st.columns([1, 2])
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📥 更新索引")
    st.markdown('<div class="small">首次索引耗时较长，后续将自动增量更新。</div>', unsafe_allow_html=True)
    if st.button("🔄 扫描并更新", use_container_width=True):
        progress = st.progress(0)
        status = st.empty()

        def cb(i, total, name):
            if total > 0:
                progress.progress(i / total)
                status.text(f"处理中: {name} ({i}/{total})")

        result = scan_and_index(
            conn,
            image_dir,
            cb,
            enable_semantic=enable_semantic,
            enable_caption=enable_caption,
            enable_ocr=enable_ocr,
        )
        st.success(
            f"完成：总数 {result['total']}，新增/更新 {result['indexed']}，跳过 {result['skipped']}，失败 {len(result['failed'])}"
        )
        if result["failed"]:
            with st.expander("查看失败列表（最多20条）"):
                st.write(result["failed"][:20])
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔎 智能搜索")
    query = st.text_input("输入关键词/自然语言（例：猫咪大笑 / 谢谢老板 / 跳舞小人）")
    do_search = st.button("搜索", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if do_search and query.strip():
    st.session_state["results"] = semantic_search(conn, query=query, top_k=top_k)
    st.session_state["query"] = query

results = st.session_state.get("results", [])
if results:
    st.subheader(f"搜索结果（{len(results)}）")
    cols_per_row = 4
    for idx in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, results[idx : idx + cols_per_row]):
            with col:
                p = Path(item["path"])
                if p.exists():
                    st.image(str(p), use_container_width=True)
                st.caption(f"匹配分数 {item['score']:.3f}")
                if item.get("caption"):
                    st.text((item["caption"] or "")[:42])
                if item.get("ocr_text"):
                    st.text((item["ocr_text"] or "")[:42])
                st.write(f"使用次数: {item.get('use_count') or 0}")
                if st.button("我用了这张", key=f"use_{item['id']}_{idx}"):
                    mark_used(conn, item["id"], st.session_state.get("query", ""))
                    st.toast("已记录使用")

st.divider()
st.subheader("📊 整理与分析")

fav_tab, dup_tab, stale_tab = st.tabs(["最常用", "重复图片", "长期未使用"])

with fav_tab:
    st.dataframe(top_favorites(conn, 30), use_container_width=True)

with dup_tab:
    st.dataframe(duplicate_groups(conn, 50), use_container_width=True)

with stale_tab:
    stale_days = st.slider("判定天数", 7, 365, 60)
    st.dataframe(stale_images(conn, stale_days, 200), use_container_width=True)
