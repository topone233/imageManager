from __future__ import annotations


def top_favorites(conn, limit: int = 20):
    return conn.execute(
        """
        SELECT path, caption, use_count, last_used
        FROM images
        ORDER BY use_count DESC, last_used DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def stale_images(conn, days: int = 30, limit: int = 100):
    return conn.execute(
        """
        SELECT path, caption, use_count, last_used
        FROM images
        WHERE (last_used IS NULL OR datetime(last_used) < datetime('now', ?))
        ORDER BY COALESCE(last_used, '') ASC, use_count ASC
        LIMIT ?
        """,
        (f"-{days} days", limit),
    ).fetchall()


def duplicate_groups(conn, limit: int = 50):
    return conn.execute(
        """
        SELECT phash, COUNT(*) as cnt, GROUP_CONCAT(path, '\n') as paths
        FROM images
        WHERE phash IS NOT NULL
        GROUP BY phash
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
