"""Build a RAG vector index over all knowledge entries using ChromaDB + OpenAI embeddings."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

from ..config import BEST_PRACTICES_DIR, ENTRIES_DIR, REFERENCE_DIR, RAG_DB_DIR, build_index


def run(rebuild=False, cancel_event=None):
    from .embeddings import SiliconFlowEF

    index = build_index()
    print(f"技术条目总数: {len(index)}")

    documents = []
    metadatas = []
    ids = []

    seen_tids: set[str] = set()
    for md_file in sorted(ENTRIES_DIR.glob("t*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        tid = md_file.stem.split("_")[0]
        if tid not in index or tid in seen_tids:
            continue
        seen_tids.add(tid)
        meta = index[tid]
        text = md_file.read_text(encoding="utf-8")
        text = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL).strip()
        if len(text) < 50:
            continue
        documents.append(text)
        metadatas.append({
            "title_zh": meta.get("title_zh", ""),
            "title_en": meta.get("title_en", ""),
            "source_type": meta.get("source_type", ""),
            "wiki_covers_this": str(meta.get("wiki_covers_this", True)),
            "tags": ",".join(meta.get("tags", [])),
        })
        ids.append(tid)

    if cancel_event and cancel_event.is_set():
        return {"ok": False, "cancelled": True}

    print(f"文档数: {len(documents)}")

    seen_refs: set[str] = set()
    for md_file in sorted(REFERENCE_DIR.glob("*.md")):
        ref_id = f"ref_{md_file.stem[:60]}"
        if ref_id in seen_refs:
            continue
        seen_refs.add(ref_id)
        text = md_file.read_text(encoding="utf-8")
        documents.append(text[:12000])
        metadatas.append({
            "title_zh": md_file.stem,
            "title_en": "",
            "source_type": "reference",
            "wiki_covers_this": "true",
            "layer": "reference",
            "tags": "reference",
        })
        ids.append(ref_id)

    seen_practices: set[str] = set()
    for md_file in sorted(BEST_PRACTICES_DIR.glob("*.md")):
        practice_id = f"practice_{md_file.stem[:60]}"
        if practice_id in seen_practices:
            continue
        seen_practices.add(practice_id)
        text = md_file.read_text(encoding="utf-8")
        documents.append(text[:12000])
        metadatas.append({
            "title_zh": md_file.stem,
            "title_en": "",
            "source_type": "best_practice",
            "wiki_covers_this": "false",
            "layer": "best_practice",
            "tags": "best_practice",
        })
        ids.append(practice_id)

    print(
        f"总文档数: {len(documents)}  参考文档: {len(seen_refs)}  "
        f"最佳实践: {len(seen_practices)}"
    )

    try:
        import chromadb
    except ImportError:
        print("chromadb not installed, falling back to simple JSON export")
        out = RAG_DB_DIR.parent / "rag_index_export.json"
        export = [{"id": i, "text": d, "metadata": m} for i, d, m in zip(ids, documents, metadatas)]
        out.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"导出 {len(export)} 条到 {out}")
        return {"ok": True, "cancelled": False, "exported": len(export)}

    if cancel_event and cancel_event.is_set():
        return {"ok": False, "cancelled": True}

    sf_ef = SiliconFlowEF()

    client = chromadb.PersistentClient(path=str(RAG_DB_DIR))
    existing = [c.name for c in client.list_collections()]

    if rebuild or "techniques" not in existing:
        try:
            client.delete_collection("techniques")
        except Exception:
            pass
        collection = client.create_collection(
            name="techniques",
            embedding_function=sf_ef,
            metadata={"hnsw:space": "cosine"},
        )
        BATCH = 32
        for i in range(0, len(documents), BATCH):
            if cancel_event and cancel_event.is_set():
                return {"ok": False, "cancelled": True}
            batch_end = min(i + BATCH, len(documents))
            collection.add(
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end],
            )
            print(f"  indexed {batch_end}/{len(documents)}")
        print(f"\nRAG 索引构建完成！存储位置: data/knowledge/rag_chroma_db")
    else:
        collection = client.get_collection(name="techniques", embedding_function=sf_ef)
        print(f"加载已有索引，共 {collection.count()} 条")

    print(f"\n--- 查询测试 ---")
    for query in ["右键检测", "栈管理函数上下文", "NBT列表队列"]:
        results = collection.query(query_texts=[query], n_results=3)
        print(f"\n[{query}]")
        for rid, dist in zip(results["ids"][0], results["distances"][0]):
            meta = index.get(rid) or results["metadatas"][0][results["ids"][0].index(rid)]
            title = meta.get("title_zh") or meta.get("title_en", rid)
            print(f"  {rid}  {title}  (dist={dist:.3f})")

    return {"ok": True, "cancelled": False, "documents": len(documents)}


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    result = run(rebuild=rebuild)
    print(f"\nResult: {result}")
