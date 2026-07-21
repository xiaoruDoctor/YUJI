#!/usr/bin/env python3
"""启动羽迹本地视频切球网页。"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
