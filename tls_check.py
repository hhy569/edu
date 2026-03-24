#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 功能：批量检测edu站点是否支持TLS 1.0/1.1（可直接提报CNVD）
# 适配：Windows，无需OpenSSL，纯Python实现
import ssl
import socket
import asyncio
import sys

# ===================== 配置区 =====================
INPUT_FILE = "alive_edu.txt"    # 输入存活域名列表（刚才生成的）
OUTPUT_FILE = "tls_vuln.txt"    # 输出有漏洞的域名列表
TIMEOUT = 10                    # 连接超时时间（秒）
CHECK_PROTOCOLS = {
    "TLS 1.0": ssl.TLSVersion.TLSv1,
    "TLS 1.1": ssl.TLSVersion.TLSv1_1
}
# ==================================================

async def check_tls_protocol(domain, protocol_name, protocol_version):
    """检测单个域名是否支持指定TLS协议"""
    # 提取域名（去掉http/https前缀）
    if domain.startswith(("http://", "https://")):
        domain = domain.split("//")[1].split("/")[0]
    
    # 处理带端口的域名（如xxx.edu.cn:8443）
    host, port = (domain.split(":") + ["443"])[:2]
    port = int(port)
    
    try:
        # 创建SSL上下文
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = protocol_version
        context.maximum_version = protocol_version
        
        # 异步连接检测
        reader, writer = await asyncio.open_connection(host, port, ssl=context)
        writer.close()
        await writer.wait_closed()
        return True
    except (ssl.SSLError, ConnectionRefusedError, TimeoutError, OSError):
        return False
    except Exception:
        return False

async def check_single_domain(domain):
    """检测单个域名的TLS 1.0/1.1支持情况"""
    print(f"\n[检测中] {domain}")
    vuln_info = {
        "domain": domain,
        "tls_10": False,
        "tls_11": False
    }
    
    # 检测TLS 1.0
    vuln_info["tls_10"] = await check_tls_protocol(domain, "TLS 1.0", CHECK_PROTOCOLS["TLS 1.0"])
    # 检测TLS 1.1
    vuln_info["tls_11"] = await check_tls_protocol(domain, "TLS 1.1", CHECK_PROTOCOLS["TLS 1.1"])
    
    # 输出检测结果
    if vuln_info["tls_10"]:
        print(f"[❌ 漏洞] {domain} 支持 TLS 1.0（已废弃）")
    else:
        print(f"[✅ 安全] {domain} 禁用 TLS 1.0")
    
    if vuln_info["tls_11"]:
        print(f"[❌ 漏洞] {domain} 支持 TLS 1.1（已废弃）")
    else:
        print(f"[✅ 安全] {domain} 禁用 TLS 1.1")
    
    return vuln_info

async def batch_check_tls():
    """批量检测主逻辑"""
    # 1. 读取存活域名列表
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]
        if not domains:
            print(f"[错误] {INPUT_FILE} 为空，请先运行探活脚本！")
            return
        print(f"[开始] 共检测 {len(domains)} 个存活edu域名的TLS协议...")
    except FileNotFoundError:
        print(f"[错误] 未找到 {INPUT_FILE}，请确保文件在桌面！")
        return

    # 2. 批量检测
    tasks = [check_single_domain(domain) for domain in domains]
    results = await asyncio.gather(*tasks)
    
    # 3. 筛选有漏洞的域名并保存
    vuln_domains = []
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for res in results:
            if res["tls_10"] or res["tls_11"]:
                vuln_domains.append(res["domain"])
                f.write(f"域名：{res['domain']}\n")
                f.write(f"TLS 1.0：{'支持（漏洞）' if res['tls_10'] else '禁用'}\n")
                f.write(f"TLS 1.1：{'支持（漏洞）' if res['tls_11'] else '禁用'}\n")
                f.write("-" * 50 + "\n")
    
    # 4. 输出统计结果
    print(f"\n[完成] TLS协议检测结束！")
    print(f"- 总检测域名：{len(domains)}")
    print(f"- 存在TLS弱协议漏洞：{len(vuln_domains)} 个")
    print(f"- 漏洞详情已保存到：{OUTPUT_FILE}（桌面）")
    if vuln_domains:
        print(f"- 漏洞域名列表：{', '.join(vuln_domains)}")

if __name__ == "__main__":
    # Windows 兼容asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(batch_check_tls())