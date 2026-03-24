# edu
TLS 1.0/1.1 不安全协议支持 这个在edu类很常见 可以自动批量的验证 非常快
这种漏洞的话找起来还是简单的 可以先去搜索引擎 比如fofa上去找 然后全部下载到一个文件里 用我给的check_edu.py来探测存活的域名 再用给的tls_check.py来验证是否有TLS 1.0/1.1 漏洞
仅依赖Python内置库，无需额外安装第三方包
直接全在cmd执行其实也要更加方便
比如python tls_check.py --target xxxx.edu 就是一个单个目标检测
批量的扫就是python tls_check.py --file xxx.txt 

