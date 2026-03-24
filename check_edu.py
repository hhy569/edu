#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 功能：批量检测edu域名是否存活（筛选200/302状态码）
# 适配：Windows/Linux，无需纠结httpx参数，直接运行
import httpx
import asyncio
import sys

# ===================== 配置区（改这里就行） =====================
INPUT_FILE = "edu_domain.txt"   # 输入的域名列表文件（桌面）
OUTPUT_FILE = "alive_edu.txt"   # 输出的存活域名文件（桌面）
TARGET_STATUS = [200, 302]      # 筛选的状态码（你要的200/302）
MAX_TASKS = 10                  # 并发数（对应你的-t 10）
RATE_LIMIT = 5                  # 每秒请求数（对应你的-rate-limit 5）
TIMEOUT = 5                     # 超时时间（秒）
# ================================================================

async def check_single_domain(domain, semaphore):
    """检测单个域名是否存活"""
    async with semaphore:
        # 补全协议（避免域名无http开头）
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"
        
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT,
                verify=False,  # 忽略证书错误（适配edu站点自签证书）
                follow_redirects=True  # 跟随302跳转
            ) as client:
                response = await client.get(domain)
                # 筛选目标状态码
                if response.status_code in TARGET_STATUS:
                    print(f"[✅ 存活] {domain} (状态码: {response.status_code})")
                    return domain
                else:
                    print(f"[❌ 状态码不符] {domain} (状态码: {response.status_code})")
                    return None
        except httpx.ConnectError:
            print(f"[❌ 连接失败] {domain}")
            return None
        except httpx.TimeoutException:
            print(f"[❌ 超时] {domain}")
            return None
        except Exception as e:
            print(f"[❌ 异常] {domain} - {str(e)[:30]}")
            return None

async def batch_check():
    """批量检测主逻辑"""
    # 1. 读取域名列表
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]
        if not domains:
            print(f"[错误] {INPUT_FILE} 为空，请检查文件！")
            return
        print(f"[开始] 共检测 {len(domains)} 个edu域名...\n")
    except FileNotFoundError:
        print(f"[错误] 未找到 {INPUT_FILE}，请确保文件在桌面！")
        return

    # 2. 限速信号量（控制每秒请求数）
    semaphore = asyncio.Semaphore(RATE_LIMIT)
    
    # 3. 批量执行检测
    tasks = [check_single_domain(domain, semaphore) for domain in domains]
    results = await asyncio.gather(*tasks)
    
    # 4. 保存存活域名
    alive_domains = [d for d in results if d]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(alive_domains))
    
    # 5. 输出统计结果
    print(f"\n[完成] 检测结束！")
    print(f"- 总检测域名：{len(domains)}")
    print(f"- 存活域名：{len(alive_domains)}")
    print(f"- 结果已保存到：{OUTPUT_FILE}（桌面）")

if __name__ == "__main__":
    # Windows 兼容asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(batch_check())