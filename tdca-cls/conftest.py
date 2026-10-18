"""pytest 配置：tdca-cls 包路径注入（tdca-cls/ 目录为根）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
