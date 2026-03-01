import os
import subprocess
import sys

# 构造包的根目录
package_root = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# 切换工作目录
os.chdir(package_root)

# 调用 python -m embykeeper，并传递收到的参数
subprocess.run([sys.executable,  "-m", "embykeeper", "-i", "-B", "./data"])
